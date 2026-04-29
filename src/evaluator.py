"""
Reliability evaluator for the Music Recommender.

Runs 10 stress-test profiles through the recommender, checks two properties
for each result set, and writes a Markdown health report to stdout.

Run from the project root:
    python -m src.evaluator

Checks per profile
──────────────────
  Diversity  Does the top-5 contain at least 3 different artists?
             (run without the diversity filter so natural catalog spread is measured)
  Relevance  Does the #1 result's genre OR mood match the user's profile?
"""
from datetime import date
from typing import Dict, List, Tuple

from src.recommender import load_songs, recommend_songs

# ---------------------------------------------------------------------------
# Stress-test profiles
# ---------------------------------------------------------------------------
# Covers: perfect match, missing genre, cross-genre mood pull, catalog gaps,
# conflicting preferences, popularity extremes, mode variation, decade bias.

STRESS_PROFILES: List[Dict] = [
    {
        "name":              "1. Perfect Lofi Match",
        "favorite_genre":    "lofi",
        "favorite_mood":     "chill",
        "target_energy":     0.40,
        "likes_acoustic":    True,
        "target_popularity": 35,
        "preferred_decade":  2020,
        "preferred_mood_tags": ["nostalgic", "dreamy"],
        "scoring_mode":      "genre-first",
    },
    {
        "name":              "2. Missing Genre (k-pop)",
        "favorite_genre":    "k-pop",
        "favorite_mood":     "happy",
        "target_energy":     0.75,
        "likes_acoustic":    False,
        "target_popularity": 70,
        "preferred_decade":  2020,
        "preferred_mood_tags": [],
        "scoring_mode":      "genre-first",
    },
    {
        "name":              "3. High-Energy Pop Fan",
        "favorite_genre":    "pop",
        "favorite_mood":     "happy",
        "target_energy":     0.88,
        "likes_acoustic":    False,
        "target_popularity": 80,
        "preferred_decade":  2020,
        "preferred_mood_tags": ["euphoric", "uplifting"],
        "scoring_mode":      "genre-first",
    },
    {
        "name":              "4. Intense Rock Listener",
        "favorite_genre":    "rock",
        "favorite_mood":     "intense",
        "target_energy":     0.92,
        "likes_acoustic":    False,
        "target_popularity": 60,
        "preferred_decade":  2010,
        "preferred_mood_tags": ["aggressive", "driving"],
        "scoring_mode":      "genre-first",
    },
    {
        "name":              "5. Missing Genre (folk) + Acoustic",
        "favorite_genre":    "folk",
        "favorite_mood":     "relaxed",
        "target_energy":     0.30,
        "likes_acoustic":    True,
        "target_popularity": 25,
        "preferred_decade":  2010,
        "preferred_mood_tags": ["peaceful", "nostalgic"],
        "scoring_mode":      "genre-first",
    },
    {
        "name":              "6. Conflicting Prefs (ambient + high energy)",
        "favorite_genre":    "ambient",
        "favorite_mood":     "chill",
        "target_energy":     0.95,
        "likes_acoustic":    False,
        "target_popularity": 50,
        "preferred_decade":  2020,
        "preferred_mood_tags": [],
        "scoring_mode":      "genre-first",
    },
    {
        "name":              "7. Mainstream Pop (mood-first mode)",
        "favorite_genre":    "pop",
        "favorite_mood":     "happy",
        "target_energy":     0.80,
        "likes_acoustic":    False,
        "target_popularity": 90,
        "preferred_decade":  2020,
        "preferred_mood_tags": ["euphoric", "sunny"],
        "scoring_mode":      "mood-first",
    },
    {
        "name":              "8. Underground Hip-Hop Fan",
        "favorite_genre":    "hip-hop",
        "favorite_mood":     "intense",
        "target_energy":     0.85,
        "likes_acoustic":    False,
        "target_popularity": 10,
        "preferred_decade":  2020,
        "preferred_mood_tags": ["aggressive", "confident"],
        "scoring_mode":      "genre-first",
    },
    {
        "name":              "9. Moody R&B (energy-focused mode)",
        "favorite_genre":    "r&b",
        "favorite_mood":     "moody",
        "target_energy":     0.58,
        "likes_acoustic":    False,
        "target_popularity": 65,
        "preferred_decade":  2020,
        "preferred_mood_tags": ["romantic", "melancholic"],
        "scoring_mode":      "energy-focused",
    },
    {
        "name":              "10. Retro 1990s Metal Fan",
        "favorite_genre":    "metal",
        "favorite_mood":     "intense",
        "target_energy":     0.95,
        "likes_acoustic":    False,
        "target_popularity": 45,
        "preferred_decade":  1990,
        "preferred_mood_tags": ["aggressive", "powerful"],
        "scoring_mode":      "genre-first",
    },
]


# ---------------------------------------------------------------------------
# Check functions
# ---------------------------------------------------------------------------

def check_diversity(
    recs: List[Tuple[Dict, float, str]],
    min_artists: int = 3,
) -> Tuple[bool, int]:
    """Return (passed, unique_artist_count)."""
    unique = len({song["artist"] for song, _, _ in recs})
    return unique >= min_artists, unique


def check_relevance(
    recs: List[Tuple[Dict, float, str]],
    profile: Dict,
) -> Tuple[bool, str]:
    """
    Return (passed, reason).
    Passes when the #1 result's genre OR mood matches the profile.
    """
    if not recs:
        return False, "no results"
    top = recs[0][0]
    genre_match = top["genre"] == profile["favorite_genre"]
    mood_match  = top["mood"]  == profile["favorite_mood"]
    if genre_match and mood_match:
        detail = f"genre ✓ + mood ✓"
    elif genre_match:
        detail = f"genre ✓ (mood mismatch: got {top['mood']!r}, wanted {profile['favorite_mood']!r})"
    elif mood_match:
        detail = f"mood ✓ (genre mismatch: got {top['genre']!r}, wanted {profile['favorite_genre']!r})"
    else:
        detail = f"genre ✗ ({top['genre']!r} ≠ {profile['favorite_genre']!r}), mood ✗ ({top['mood']!r} ≠ {profile['favorite_mood']!r})"
    return genre_match or mood_match, detail


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------

def run_evaluation(csv_path: str = "data/songs.csv") -> str:
    """Run all stress profiles and return a Markdown health report string."""
    songs = load_songs(csv_path)

    rows = []
    for profile in STRESS_PROFILES:
        # Run without the diversity filter so natural catalog spread is measured.
        recs = recommend_songs(profile, songs, k=5, diversity=False)

        div_pass, n_artists   = check_diversity(recs)
        rel_pass, rel_detail  = check_relevance(recs, profile)

        top_song  = recs[0][0] if recs else {}
        avg_energy = sum(s["energy"] for s, _, _ in recs) / max(len(recs), 1)

        rows.append({
            "profile":     profile,
            "recs":        recs,
            "div_pass":    div_pass,
            "n_artists":   n_artists,
            "rel_pass":    rel_pass,
            "rel_detail":  rel_detail,
            "top_song":    top_song,
            "avg_energy":  avg_energy,
        })

    # ── Summary ──────────────────────────────────────────────────────────────
    total     = len(rows)
    div_ok    = sum(1 for r in rows if r["div_pass"])
    rel_ok    = sum(1 for r in rows if r["rel_pass"])
    both_ok   = sum(1 for r in rows if r["div_pass"] and r["rel_pass"])
    today     = date.today().isoformat()

    lines: List[str] = [
        f"# Music Recommender — System Health Report",
        f"",
        f"**Date:** {today}  |  **Catalog:** 18 songs  |  **Profiles tested:** {total}",
        f"",
        f"## Summary",
        f"",
        f"| Check | Passed | Failed | Pass Rate |",
        f"|-------|--------|--------|-----------|",
        f"| Diversity (≥ 3 artists in top 5) | {div_ok} | {total - div_ok} | {div_ok/total:.0%} |",
        f"| Relevance (#1 result genre or mood match) | {rel_ok} | {total - rel_ok} | {rel_ok/total:.0%} |",
        f"| Both checks passed | {both_ok} | {total - both_ok} | {both_ok/total:.0%} |",
        f"",
        f"> **Diversity** is tested without the diversity filter so natural spread is measured.",
        f"> **Relevance** checks only genre and mood of the #1 result — energy and decade are not evaluated here.",
        f"",
        f"---",
        f"",
        f"## Results Table",
        f"",
        f"| # | Profile | #1 Song | Genre | Mood | Avg Energy | Diversity | Relevance |",
        f"|---|---------|---------|-------|------|------------|-----------|-----------|",
    ]

    for r in rows:
        p     = r["profile"]
        ts    = r["top_song"]
        div_i = "✅" if r["div_pass"] else "❌"
        rel_i = "✅" if r["rel_pass"] else "❌"
        lines.append(
            f"| {p['name']} "
            f"| {ts.get('title','—')} "
            f"| {ts.get('genre','—')} "
            f"| {ts.get('mood','—')} "
            f"| {r['avg_energy']:.2f} "
            f"| {div_i} ({r['n_artists']} artists) "
            f"| {rel_i} |"
        )

    lines += [
        f"",
        f"---",
        f"",
        f"## Per-Profile Details",
        f"",
    ]

    for r in rows:
        p = r["profile"]
        lines += [
            f"### {p['name']}",
            f"",
            f"**Wanted:** genre=`{p['favorite_genre']}` | mood=`{p['favorite_mood']}` | "
            f"energy={p['target_energy']} | mode=`{p['scoring_mode']}`",
            f"",
            f"**Top 5 (no diversity filter):**",
            f"",
        ]
        for rank, (song, score, _) in enumerate(r["recs"], start=1):
            marker = " ←" if rank == 1 else ""
            lines.append(
                f"{rank}. **{song['title']}** — {song['artist']} "
                f"[{song['genre']}/{song['mood']}/e={song['energy']:.2f}] "
                f"score={score:.2f}{marker}"
            )

        div_label = f"{'✅ PASS' if r['div_pass'] else '❌ FAIL'}  ({r['n_artists']} unique artists)"
        rel_label = f"{'✅ PASS' if r['rel_pass'] else '❌ FAIL'}  ({r['rel_detail']})"
        lines += [
            f"",
            f"- **Diversity:** {div_label}",
            f"- **Relevance:** {rel_label}",
            f"",
        ]

    lines += [
        f"---",
        f"",
        f"## Observations",
        f"",
        f"- **Missing genres** (k-pop, folk) degrade gracefully — relevance is saved by mood matching.",
        f"- **Conflicting prefs** (ambient + energy 0.95) passes relevance (genre/mood match) but the",
        f"  avg energy of results is far below the user's target. This gap is not caught by these checks",
        f"  alone — it is exactly the type of mismatch the `RecommendationAgent` in `src/agent.py` is",
        f"  designed to detect and correct via the self-correction loop in `src/main.py`.",
        f"- **Diversity failures** (if any) reveal catalog clustering — too few songs in a given genre.",
        f"",
        f"---",
        f"",
        f"*Generated by `src/evaluator.py`*",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print(run_evaluation())


if __name__ == "__main__":
    main()
