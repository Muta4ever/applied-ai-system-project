"""
Command line runner for the Music Recommender Simulation.

Run from the project root:
    python -m src.main
"""
import logging

from src.recommender import load_songs, recommend_songs, SCORING_MODES
from src.agent import RecommendationAgent

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s — %(message)s")

# ---------------------------------------------------------------------------
# Profiles
# ---------------------------------------------------------------------------

BASE_PROFILE = {
    "favorite_genre":     "lofi",
    "favorite_mood":      "chill",
    "target_energy":      0.40,
    "likes_acoustic":     True,
    "target_popularity":  35,
    "preferred_decade":   2020,
    "preferred_mood_tags": ["nostalgic", "dreamy"],
}

# Conflicting prefs: ambient genre + chill mood BUT very high energy target.
# The genre-first mode will return low-energy ambient songs, which is a known
# mismatch — a good demo case for the agent's self-correction loop.
CONFLICTING_PROFILE = {
    "favorite_genre":     "ambient",
    "favorite_mood":      "chill",
    "target_energy":      0.95,
    "likes_acoustic":     False,
    "target_popularity":  50,
    "preferred_decade":   2020,
    "preferred_mood_tags": [],
    "scoring_mode":       "genre-first",
}


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def print_header(label: str, mode: str, profile: dict) -> None:
    bar = "=" * 62
    print(f"\n{bar}")
    print(f"  {label}")
    print(f"  Mode    : {mode}")
    print(f"  Profile : {profile['favorite_genre']} / {profile['favorite_mood']} / "
          f"energy {profile['target_energy']} / "
          f"pop target {profile['target_popularity']} / "
          f"decade {profile['preferred_decade']}")
    print(f"  Tags    : {', '.join(profile['preferred_mood_tags'])}")
    print(bar)


def print_results(recs: list) -> None:
    for rank, (song, score, explanation) in enumerate(recs, start=1):
        print(f"\n  #{rank}  {song['title']}  —  {song['artist']}")
        print(f"       [{song['genre']} / {song['mood']} / "
              f"pop {song['popularity']} / {song['release_decade']}s / "
              f"tags: {song['mood_tags']}]")
        print(f"       Score : {score:.2f}")
        for reason in explanation.split(" | "):
            print(f"         + {reason}")
    print()


# ---------------------------------------------------------------------------
# Agentic self-correction loop
# ---------------------------------------------------------------------------

def run_agentic_demo(songs: list, profile: dict) -> None:
    """
    Agentic self-correction loop:
      1. Get recommendations with standard (genre-first) weights.
      2. RecommendationAgent critiques the results via Claude.
      3. If confidence < 0.7, re-run once with agent-suggested weights.
      4. Log Before / After so the improvement is visible.
    """
    bar = "=" * 62
    agent = RecommendationAgent()

    print(f"\n{bar}")
    print("  AGENTIC SELF-CORRECTION DEMO")
    print(f"  Profile : {profile['favorite_genre']} / {profile['favorite_mood']} / "
          f"energy {profile['target_energy']}")
    print(f"  (genre-first mode — known mismatch: high energy target, low-energy catalog)")
    print(bar)

    # ── Step 1: initial pass ────────────────────────────────────────────────
    print("\n[Step 1] Running standard recommendations (genre-first)...")
    initial_recs = recommend_songs(profile, songs, k=5, diversity=True)

    print("\n  ── Before correction ──")
    print_results(initial_recs)

    # ── Step 2: agent critique ──────────────────────────────────────────────
    print("[Step 2] Calling RecommendationAgent for critique...")
    confidence, suggested_weights, reason = agent.analyze(profile, initial_recs)

    print(f"\n  Agent confidence : {confidence:.2f}  "
          f"(threshold = {RecommendationAgent.CONFIDENCE_THRESHOLD})")

    if confidence >= RecommendationAgent.CONFIDENCE_THRESHOLD:
        print("  Agent verdict    : Results look good — no correction needed.\n")
        return

    print(f"  Agent verdict    : LOW CONFIDENCE")
    print(f"  Mismatch reason  : {reason}")
    print(f"  Suggested weights: {suggested_weights}")

    # ── Step 3: corrected pass ──────────────────────────────────────────────
    print("\n[Step 3] Re-running with agent-corrected weights...")
    corrected_recs = recommend_songs(
        profile, songs, k=5, diversity=True,
        weights_override=suggested_weights,
    )

    print("\n  ── After correction ──")
    print_results(corrected_recs)

    # ── Diff ────────────────────────────────────────────────────────────────
    before_titles = [s["title"] for s, _, _ in initial_recs]
    after_titles  = [s["title"] for s, _, _ in corrected_recs]
    added   = [t for t in after_titles  if t not in before_titles]
    removed = [t for t in before_titles if t not in after_titles]
    if added or removed:
        print(f"  Changes → added  : {added}")
        print(f"            removed: {removed}")
    avg_energy_before = sum(s["energy"] for s, _, _ in initial_recs)  / len(initial_recs)
    avg_energy_after  = sum(s["energy"] for s, _, _ in corrected_recs) / len(corrected_recs)
    print(f"\n  Avg energy before: {avg_energy_before:.2f}  |  after: {avg_energy_after:.2f}  "
          f"(target: {profile['target_energy']})")
    print()


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    songs = load_songs("data/songs.csv")

    # ── Challenge 2: Run the same profile through each scoring mode ──────────
    for mode_name in SCORING_MODES:
        profile = {**BASE_PROFILE, "scoring_mode": mode_name}
        recs = recommend_songs(profile, songs, k=5, diversity=True)
        print_header(f"Scoring mode: {mode_name.upper()}", mode_name, profile)
        print_results(recs)

    # ── Challenge 3: Diversity ON vs OFF ─────────────────────────────────────
    profile = {**BASE_PROFILE, "scoring_mode": "genre-first"}

    print("\n" + "=" * 62)
    print("  DIVERSITY COMPARISON  (genre-first mode, lofi/chill profile)")
    print("=" * 62)

    print("\n  [diversity=OFF — top 5 by score only]")
    no_div = recommend_songs(profile, songs, k=5, diversity=False)
    for rank, (song, score, _) in enumerate(no_div, start=1):
        print(f"  #{rank}  {song['title']:30s}  {song['artist']:20s}  "
              f"genre={song['genre']:10s}  score={score:.2f}")

    print("\n  [diversity=ON — max 1 per artist, max 2 per genre]")
    with_div = recommend_songs(profile, songs, k=5, diversity=True)
    for rank, (song, score, _) in enumerate(with_div, start=1):
        print(f"  #{rank}  {song['title']:30s}  {song['artist']:20s}  "
              f"genre={song['genre']:10s}  score={score:.2f}")
    print()

    # ── Agentic self-correction demo ─────────────────────────────────────────
    run_agentic_demo(songs, CONFLICTING_PROFILE)


if __name__ == "__main__":
    main()
