"""
Command line runner for the Music Recommender Simulation.

Run from the project root:
    python -m src.main
"""

from src.recommender import load_songs, recommend_songs, SCORING_MODES

# ---------------------------------------------------------------------------
# A single taste profile — run through all three scoring modes so you can
# see how changing the strategy changes what gets recommended.
# ---------------------------------------------------------------------------

BASE_PROFILE = {
    "favorite_genre":     "lofi",
    "favorite_mood":      "chill",
    "target_energy":      0.40,
    "likes_acoustic":     True,
    "target_popularity":  35,           # prefers underground/indie feel
    "preferred_decade":   2020,
    "preferred_mood_tags": ["nostalgic", "dreamy"],
}


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


def main() -> None:
    songs = load_songs("data/songs.csv")

    # -----------------------------------------------------------------------
    # Challenge 2: Run the same profile through each scoring mode
    # -----------------------------------------------------------------------
    for mode_name in SCORING_MODES:
        profile = {**BASE_PROFILE, "scoring_mode": mode_name}
        recs = recommend_songs(profile, songs, k=5, diversity=True)
        print_header(f"Scoring mode: {mode_name.upper()}", mode_name, profile)
        print_results(recs)

    # -----------------------------------------------------------------------
    # Challenge 3: Show diversity ON vs OFF for genre-first
    # -----------------------------------------------------------------------
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


if __name__ == "__main__":
    main()
