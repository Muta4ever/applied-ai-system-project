import csv
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class Song:
    """Represents a single song and its audio attributes."""
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float


@dataclass
class UserProfile:
    """Stores a listener's taste preferences used to score songs."""
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool


# ---------------------------------------------------------------------------
# Core scoring — shared by both the OOP and functional APIs
# ---------------------------------------------------------------------------

def _score_and_explain(
    genre: str,
    mood: str,
    energy: float,
    acousticness: float,
    fav_genre: str,
    fav_mood: str,
    target_energy: float,
    likes_acoustic: bool,
) -> Tuple[float, List[str]]:
    """
    Score a single song against user preferences and return (score, reasons).

    Scoring recipe
    --------------
    +3.0  exact genre match
    +2.0  exact mood match
    +0.0–1.0  energy proximity: 1.0 − |song.energy − target_energy|
    +0.5  acoustic bonus when likes_acoustic=True and acousticness > 0.6
    Max possible score: 6.5
    """
    score = 0.0
    reasons: List[str] = []

    # Genre match (strongest signal)
    if genre == fav_genre:
        score += 3.0
        reasons.append(f"genre match: {genre} (+3.0)")

    # Mood match
    if mood == fav_mood:
        score += 2.0
        reasons.append(f"mood match: {mood} (+2.0)")

    # Energy proximity — rewards closeness, not just high or low values
    energy_pts = round(1.0 - abs(energy - target_energy), 2)
    score += energy_pts
    reasons.append(
        f"energy proximity: {energy:.2f} vs target {target_energy:.2f} (+{energy_pts:.2f})"
    )

    # Acoustic bonus
    if likes_acoustic and acousticness > 0.6:
        score += 0.5
        reasons.append(f"acoustic bonus: {acousticness:.2f} > 0.6 (+0.50)")

    return round(score, 2), reasons


# ---------------------------------------------------------------------------
# OOP API — used by tests/test_recommender.py
# ---------------------------------------------------------------------------

class Recommender:
    """Ranks a catalog of Song objects against a UserProfile."""

    def __init__(self, songs: List[Song]):
        self.songs = songs

    def _score(self, user: UserProfile, song: Song) -> Tuple[float, List[str]]:
        """Return (score, reasons) for one song given the user profile."""
        return _score_and_explain(
            song.genre, song.mood, song.energy, song.acousticness,
            user.favorite_genre, user.favorite_mood,
            user.target_energy, user.likes_acoustic,
        )

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top-k Song objects sorted from highest to lowest score."""
        # sorted() builds a new list and never mutates self.songs
        return sorted(self.songs, key=lambda s: self._score(user, s)[0], reverse=True)[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a human-readable explanation of why a song was recommended."""
        _, reasons = self._score(user, song)
        return " | ".join(reasons)


# ---------------------------------------------------------------------------
# Functional API — used by src/main.py
# ---------------------------------------------------------------------------

def load_songs(csv_path: str) -> List[Dict]:
    """Read songs.csv and return a list of dicts with numeric fields converted."""
    songs: List[Dict] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["id"] = int(row["id"])
            row["energy"] = float(row["energy"])
            row["tempo_bpm"] = float(row["tempo_bpm"])
            row["valence"] = float(row["valence"])
            row["danceability"] = float(row["danceability"])
            row["acousticness"] = float(row["acousticness"])
            songs.append(row)
    print(f"Loaded {len(songs)} songs.")
    return songs


def recommend_songs(
    user_prefs: Dict, songs: List[Dict], k: int = 5
) -> List[Tuple[Dict, float, str]]:
    """
    Score every song against user_prefs, sort high-to-low, return top k.

    Each item in the returned list is a tuple of (song_dict, score, explanation).

    sorted() vs .sort()
    -------------------
    sorted() creates a brand-new sorted list — the original `songs` list is
    left untouched. list.sort() sorts in place and returns None, which would
    mutate the caller's data. sorted() is the right choice here.
    """
    scored: List[Tuple[Dict, float, str]] = []
    for song in songs:
        score, reasons = _score_and_explain(
            song["genre"], song["mood"], song["energy"], song["acousticness"],
            user_prefs["favorite_genre"], user_prefs["favorite_mood"],
            user_prefs["target_energy"], user_prefs["likes_acoustic"],
        )
        scored.append((song, score, " | ".join(reasons)))

    return sorted(scored, key=lambda item: item[1], reverse=True)[:k]
