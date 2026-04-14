import csv
from typing import List, Dict, Tuple
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Challenge 2: Scoring Modes (Strategy Pattern)
#
# Each mode is a plain dict of feature -> weight.
# Swapping modes changes which features dominate without touching the math.
#
# Max possible score per mode:
#   genre-first   : 3.0 + 1.5 + 0.8 + 0.4 + 1.0 (2 tags) + 0.5 + 0.5 = 8.2
#   mood-first    : 1.5 + 3.0 + 0.8 + 0.4 + 2.0 (2 tags) + 0.5 + 0.3 = 8.5
#   energy-focused: 1.0 + 1.0 + 3.0 + 0.4 + 1.0 (2 tags) + 0.5 + 0.3 = 7.2
# ---------------------------------------------------------------------------

SCORING_MODES: Dict[str, Dict[str, float]] = {
    "genre-first": {
        "genre":     3.0,   # genre is the primary signal
        "mood":      1.5,
        "energy":    0.8,   # multiplier on the 0–1 proximity value
        "acoustic":  0.4,
        "mood_tags": 0.5,   # awarded per matching tag, capped at 2 tags
        "popularity": 0.5,  # multiplier on the 0–1 proximity value
        "decade":    0.5,   # exact match; 0.5× for adjacent decade
    },
    "mood-first": {
        "genre":     1.5,
        "mood":      3.0,   # mood is the primary signal
        "energy":    0.8,
        "acoustic":  0.4,
        "mood_tags": 1.0,   # detailed tags matter more here
        "popularity": 0.5,
        "decade":    0.3,
    },
    "energy-focused": {
        "genre":     1.0,
        "mood":      1.0,
        "energy":    3.0,   # energy proximity is the primary signal
        "acoustic":  0.4,
        "mood_tags": 0.5,
        "popularity": 0.5,
        "decade":    0.3,
    },
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Song:
    """Represents a single song and its audio/metadata attributes."""
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
    # Challenge 1 — new attributes (default values keep existing tests passing)
    popularity: int = 50            # 0–100 mainstream appeal
    release_decade: int = 2020      # e.g. 1990, 2000, 2010, 2020
    mood_tags: str = ""             # comma-separated: "nostalgic,dreamy,euphoric"


@dataclass
class UserProfile:
    """Stores a listener's taste preferences and chosen scoring mode."""
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool
    # Challenge 1 — new preference fields
    target_popularity: int = 50                             # 0=underground, 100=mainstream
    preferred_decade: int = 2020                            # preferred era
    preferred_mood_tags: List[str] = field(default_factory=list)  # e.g. ["nostalgic","dreamy"]
    # Challenge 2 — scoring mode
    scoring_mode: str = "genre-first"


# ---------------------------------------------------------------------------
# Core scoring — shared by both the OOP and functional APIs
# ---------------------------------------------------------------------------

def _score_song(
    song: Dict,
    user: Dict,
    weights: Dict[str, float],
) -> Tuple[float, List[str]]:
    """
    Score one song dict against one user dict using the supplied weight set.

    Returns (total_score, reasons) where reasons is a list of human-readable
    strings explaining each contribution to the score.

    Challenge 1 features: popularity proximity, release decade, mood tags.
    Challenge 2: weights are injected from the chosen SCORING_MODE.
    """
    score = 0.0
    reasons: List[str] = []

    # --- Genre match ---
    if song["genre"] == user["favorite_genre"]:
        pts = weights["genre"]
        score += pts
        reasons.append(f"genre match: {song['genre']} (+{pts:.1f})")

    # --- Mood match ---
    if song["mood"] == user["favorite_mood"]:
        pts = weights["mood"]
        score += pts
        reasons.append(f"mood match: {song['mood']} (+{pts:.1f})")

    # --- Energy proximity ---
    # Rewards closeness to target, not just high or low values.
    # Multiplied by the mode weight so energy-focused mode amplifies this.
    raw_proximity = 1.0 - abs(song["energy"] - user["target_energy"])
    energy_pts = round(weights["energy"] * raw_proximity, 2)
    score += energy_pts
    reasons.append(
        f"energy: {song['energy']:.2f} vs target {user['target_energy']:.2f}"
        f" (+{energy_pts:.2f})"
    )

    # --- Acoustic bonus ---
    if user["likes_acoustic"] and song.get("acousticness", 0) > 0.6:
        pts = weights["acoustic"]
        score += pts
        reasons.append(f"acoustic bonus: {song.get('acousticness', 0):.2f} (+{pts:.1f})")

    # --- Challenge 1: Mood tags ---
    # Award points for each user preferred_mood_tag that appears in the song.
    # Capped at 2 matching tags so a single feature can't dominate.
    song_tags = {t.strip() for t in song.get("mood_tags", "").split(",") if t.strip()}
    user_tags = set(user.get("preferred_mood_tags", []))
    matching = sorted(song_tags & user_tags)
    tag_count = min(len(matching), 2)
    if tag_count > 0:
        pts = round(tag_count * weights["mood_tags"], 2)
        score += pts
        reasons.append(f"mood tags ({', '.join(matching)}) (+{pts:.2f})")

    # --- Challenge 1: Popularity proximity ---
    target_pop = user.get("target_popularity", 50)
    pop_proximity = 1.0 - abs(song.get("popularity", 50) - target_pop) / 100.0
    pop_pts = round(weights["popularity"] * pop_proximity, 2)
    if pop_pts > 0.05:   # suppress near-zero noise from the reasons list
        score += pop_pts
        reasons.append(
            f"popularity: {song.get('popularity', 50)} vs target {target_pop}"
            f" (+{pop_pts:.2f})"
        )

    # --- Challenge 1: Release decade ---
    preferred_decade = user.get("preferred_decade")
    if preferred_decade:
        decade_diff = abs(song.get("release_decade", 2020) - preferred_decade)
        if decade_diff == 0:
            decade_pts = weights["decade"]
        elif decade_diff == 10:
            decade_pts = round(weights["decade"] * 0.5, 2)
        else:
            decade_pts = 0.0
        if decade_pts > 0:
            score += decade_pts
            reasons.append(
                f"decade: {song.get('release_decade', 2020)} (+{decade_pts:.2f})"
            )

    return round(score, 2), reasons


# ---------------------------------------------------------------------------
# Challenge 3: Diversity filter
#
# Strategy: greedily walk the sorted scored list and skip any song that
# would push the artist or genre count over the allowed cap.
# This is a post-processing step — scores are never modified.
# ---------------------------------------------------------------------------

def _apply_diversity(
    scored: List[Tuple[Dict, float, str]],
    k: int,
    max_per_artist: int = 1,
    max_per_genre: int = 2,
) -> List[Tuple[Dict, float, str]]:
    """
    Return up to k results from a pre-sorted scored list, enforcing
    per-artist and per-genre caps.

    A song is skipped (not penalized) if its artist or genre has already
    filled its slot. The next highest-scoring eligible song takes its place.
    """
    artist_counts: Dict[str, int] = {}
    genre_counts: Dict[str, int] = {}
    result: List[Tuple[Dict, float, str]] = []

    for song, score, explanation in scored:
        artist = song["artist"]
        genre = song["genre"]

        if artist_counts.get(artist, 0) >= max_per_artist:
            continue
        if genre_counts.get(genre, 0) >= max_per_genre:
            continue

        artist_counts[artist] = artist_counts.get(artist, 0) + 1
        genre_counts[genre] = genre_counts.get(genre, 0) + 1
        result.append((song, score, explanation))

        if len(result) == k:
            break

    return result


# ---------------------------------------------------------------------------
# OOP API — used by tests/test_recommender.py
# ---------------------------------------------------------------------------

class Recommender:
    """Ranks a catalog of Song objects against a UserProfile."""

    def __init__(self, songs: List[Song]):
        self.songs = songs

    def _song_to_dict(self, song: Song) -> Dict:
        return {
            "genre": song.genre, "mood": song.mood, "energy": song.energy,
            "acousticness": song.acousticness, "artist": song.artist,
            "popularity": song.popularity, "release_decade": song.release_decade,
            "mood_tags": song.mood_tags,
        }

    def _profile_to_dict(self, user: UserProfile) -> Dict:
        return {
            "favorite_genre": user.favorite_genre,
            "favorite_mood": user.favorite_mood,
            "target_energy": user.target_energy,
            "likes_acoustic": user.likes_acoustic,
            "target_popularity": user.target_popularity,
            "preferred_decade": user.preferred_decade,
            "preferred_mood_tags": user.preferred_mood_tags,
        }

    def _score(self, user: UserProfile, song: Song) -> Tuple[float, List[str]]:
        """Score one Song against a UserProfile using the profile's chosen mode."""
        weights = SCORING_MODES.get(user.scoring_mode, SCORING_MODES["genre-first"])
        return _score_song(self._song_to_dict(song), self._profile_to_dict(user), weights)

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top-k Song objects sorted from highest to lowest score."""
        return sorted(self.songs, key=lambda s: self._score(user, s)[0], reverse=True)[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a human-readable explanation of why a song was recommended."""
        _, reasons = self._score(user, song)
        return " | ".join(reasons)


# ---------------------------------------------------------------------------
# Functional API — used by src/main.py
# ---------------------------------------------------------------------------

def load_songs(csv_path: str) -> List[Dict]:
    """Read songs.csv and return a list of dicts with all numeric fields converted."""
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
            row["popularity"] = int(row.get("popularity", 50))
            row["release_decade"] = int(row.get("release_decade", 2020))
            # mood_tags stays as a raw comma-separated string; _score_song splits it
            songs.append(row)
    print(f"Loaded {len(songs)} songs.")
    return songs


def recommend_songs(
    user_prefs: Dict,
    songs: List[Dict],
    k: int = 5,
    diversity: bool = True,
    max_per_artist: int = 1,
    max_per_genre: int = 2,
) -> List[Tuple[Dict, float, str]]:
    """
    Score every song, sort high-to-low, apply optional diversity filter, return top k.

    Each item returned is a tuple of (song_dict, score, explanation_string).

    Challenge 2: reads scoring_mode from user_prefs to pick the weight set.
    Challenge 3: diversity=True enforces per-artist and per-genre caps.
    """
    mode_name = user_prefs.get("scoring_mode", "genre-first")
    weights = SCORING_MODES.get(mode_name, SCORING_MODES["genre-first"])

    scored: List[Tuple[Dict, float, str]] = []
    for song in songs:
        score, reasons = _score_song(song, user_prefs, weights)
        scored.append((song, score, " | ".join(reasons)))

    # sorted() builds a new list; never mutates the caller's songs list
    ranked = sorted(scored, key=lambda item: item[1], reverse=True)

    if diversity:
        return _apply_diversity(ranked, k, max_per_artist, max_per_genre)
    return ranked[:k]
