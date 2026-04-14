"""
Command line runner for the Music Recommender Simulation.

Run from the project root:
    python -m src.main
"""

from src.recommender import load_songs, recommend_songs


# ---------------------------------------------------------------------------
# User profiles — edit or add new ones to experiment
# ---------------------------------------------------------------------------

PROFILES = {
    "Chill Lofi Student": {
        "favorite_genre": "lofi",
        "favorite_mood": "chill",
        "target_energy": 0.4,
        "likes_acoustic": True,
    },
    "High-Energy Pop Fan": {
        "favorite_genre": "pop",
        "favorite_mood": "happy",
        "target_energy": 0.85,
        "likes_acoustic": False,
    },
    "Intense Rock Listener": {
        "favorite_genre": "rock",
        "favorite_mood": "intense",
        "target_energy": 0.92,
        "likes_acoustic": False,
    },
    # Adversarial: genre has no match in catalog at all
    "Obscure Taste (no genre match)": {
        "favorite_genre": "bossa nova",
        "favorite_mood": "relaxed",
        "target_energy": 0.35,
        "likes_acoustic": True,
    },
    # Adversarial: conflicting — asks for high energy but chill mood
    "Conflicting Prefs (high energy + chill)": {
        "favorite_genre": "ambient",
        "favorite_mood": "chill",
        "target_energy": 0.95,
        "likes_acoustic": False,
    },
}


def print_recommendations(name: str, user_prefs: dict, songs: list, k: int = 5) -> None:
    """Print a formatted recommendation block for one user profile."""
    recs = recommend_songs(user_prefs, songs, k=k)
    print()
    print("=" * 60)
    print(f"  Profile : {name}")
    print(f"  Prefs   : {user_prefs['favorite_genre']} / "
          f"{user_prefs['favorite_mood']} / "
          f"energy {user_prefs['target_energy']} / "
          f"acoustic={user_prefs['likes_acoustic']}")
    print("=" * 60)
    for rank, (song, score, explanation) in enumerate(recs, start=1):
        print(f"\n  #{rank}  {song['title']}  —  {song['artist']}")
        print(f"       Score : {score:.2f} / 6.50")
        for reason in explanation.split(" | "):
            print(f"       + {reason}")
    print()


def experiment(songs: list) -> None:
    """
    Weight-shift experiment: halve genre weight, double energy weight.

    Original : genre=3.0  mood=2.0  energy proximity (max 1.0)
    Shifted  : genre=1.5  mood=2.0  energy proximity x2 (max 2.0)

    We use the 'Conflicting Prefs' profile because it has the sharpest
    conflict between energy (0.95 target) and catalog reality.
    """
    profile = PROFILES["Conflicting Prefs (high energy + chill)"]

    def score_shifted(song: dict) -> tuple:
        score = 0.0
        reasons = []
        if song["genre"] == profile["favorite_genre"]:
            score += 1.5                              # was 3.0
            reasons.append(f"genre match (+1.5)")
        if song["mood"] == profile["favorite_mood"]:
            score += 2.0
            reasons.append(f"mood match (+2.0)")
        energy_pts = round(2.0 * (1.0 - abs(song["energy"] - profile["target_energy"])), 2)
            # was 1x, now 2x                          ^^^
        score += energy_pts
        reasons.append(f"energy x2: {song['energy']:.2f} vs {profile['target_energy']:.2f} (+{energy_pts:.2f})")
        if profile["likes_acoustic"] and song["acousticness"] > 0.6:
            score += 0.5
            reasons.append("acoustic bonus (+0.50)")
        return round(score, 2), " | ".join(reasons)

    scored = sorted(
        [(s, *score_shifted(s)) for s in songs],
        key=lambda t: t[1], reverse=True
    )[:5]

    print()
    print("=" * 60)
    print("  EXPERIMENT: weight shift — genre halved, energy doubled")
    print(f"  Profile : Conflicting Prefs (ambient / chill / energy 0.95)")
    print("=" * 60)
    for rank, (song, score, explanation) in enumerate(scored, start=1):
        print(f"\n  #{rank}  {song['title']}  —  {song['artist']}")
        print(f"       Score : {score:.2f} / 7.50")   # new max: 1.5+2.0+2.0+0.5
        for reason in explanation.split(" | "):
            print(f"       + {reason}")
    print()


def main() -> None:
    songs = load_songs("data/songs.csv")

    for name, prefs in PROFILES.items():
        print_recommendations(name, prefs, songs)

    experiment(songs)


if __name__ == "__main__":
    main()
