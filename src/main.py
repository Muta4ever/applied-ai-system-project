"""
Command line runner for the Music Recommender Simulation.

Run from the project root:
    python -m src.main
"""

from src.recommender import load_songs, recommend_songs


def main() -> None:
    songs = load_songs("data/songs.csv")

    # User taste profile — edit these values to simulate different listeners.
    # favorite_genre : the genre they most want to hear
    # favorite_mood  : the emotional tone they're looking for right now
    # target_energy  : 0.0 = very calm, 1.0 = very intense
    # likes_acoustic : True = prefers acoustic/organic sound, False = prefers electronic
    user_prefs = {
        "favorite_genre": "lofi",
        "favorite_mood": "chill",
        "target_energy": 0.4,
        "likes_acoustic": True,
    }

    recommendations = recommend_songs(user_prefs, songs, k=5)

    print()
    print("=" * 52)
    print(f"  Taste profile: {user_prefs['favorite_genre']} / "
          f"{user_prefs['favorite_mood']} / "
          f"energy {user_prefs['target_energy']}")
    print("=" * 52)
    print(f"  Top {len(recommendations)} recommendations")
    print("=" * 52)

    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"\n  #{rank}  {song['title']}  —  {song['artist']}")
        print(f"       Score : {score:.2f} / 6.50")
        for reason in explanation.split(" | "):
            print(f"       + {reason}")

    print()


if __name__ == "__main__":
    main()
