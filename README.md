# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

Replace this paragraph with your own summary of what your version does.

---

## How The System Works

Real-world recommenders like Spotify use two main strategies: **collaborative filtering** (finding users with similar taste and borrowing their history) and **content-based filtering** (matching song attributes directly to a user's stated preferences). This simulation uses **content-based filtering** — no play history needed, just song attributes and a user taste profile.

The system prioritizes three things: matching genre first (strongest signal of taste), matching mood second, and then rewarding songs whose energy level is close to the user's target — not just high or low, but *close*.

### Song Features Used

Each `Song` object stores:
- `genre` — categorical (pop, lofi, rock, jazz, ambient, synthwave, indie pop)
- `mood` — categorical (happy, chill, intense, relaxed, focused, moody)
- `energy` — float 0.0–1.0 (how intense/active the track feels)
- `tempo_bpm` — numeric (beats per minute)
- `valence` — float 0.0–1.0 (musical positivity/happiness)
- `danceability` — float 0.0–1.0 (how suitable for dancing)
- `acousticness` — float 0.0–1.0 (acoustic vs electronic feel)

### UserProfile Fields

Each `UserProfile` stores:
- `favorite_genre` — the genre the user most wants to hear
- `favorite_mood` — the emotional tone they're looking for
- `target_energy` — their preferred energy level (0.0 = very calm, 1.0 = very intense)
- `likes_acoustic` — boolean preference for acoustic vs electronic sound

### Scoring Rule (per song)

```
score = genre_match (3.0 pts)
      + mood_match  (2.0 pts)
      + energy_proximity  (1.0 - |song.energy - user.target_energy|)
```

Categorical features get a fixed bonus for exact matches. Numerical features use a proximity formula that gives full credit for a perfect match and decreases as the song drifts from the user's preference.

### Ranking Rule

All songs are scored, then sorted highest-to-lowest. The top `k` results are returned as recommendations.

---

## Data Flow

```mermaid
flowchart TD
    A([User Profile\ngenre · mood · energy · likes_acoustic]) --> B[Load songs.csv\n18 songs]
    B --> C{For each song...}
    C --> D[Score: Genre match?\n+3.0 pts if yes]
    D --> E[Score: Mood match?\n+2.0 pts if yes]
    E --> F[Score: Energy proximity\n1.0 − |song.energy − target_energy|]
    F --> G[Score: Acoustic bonus?\n+0.5 pts if likes_acoustic and acousticness > 0.6]
    G --> H[(song, total_score, explanation)]
    H --> C
    C --> I[Sort all songs\nhigh → low score]
    I --> J([Top K Recommendations])
```

---

## Algorithm Recipe

| Feature | Type | Rule | Max Points |
|---|---|---|---|
| `genre` | categorical | +3.0 if `song.genre == favorite_genre` | 3.0 |
| `mood` | categorical | +2.0 if `song.mood == favorite_mood` | 2.0 |
| `energy` | float 0–1 | `1.0 - abs(song.energy - target_energy)` | 1.0 |
| `acousticness` | float 0–1 | +0.5 if `likes_acoustic` and `song.acousticness > 0.6` | 0.5 |

**Max score: 6.5** — a perfect match on every dimension.

### Expected Bias

- **Genre over-weighting:** A 3-point genre bonus means a song with the right genre but wrong mood will beat a song with the right mood but wrong genre. A jazz fan asking for "chill" music could miss a great ambient track.
- **Mood blindness across genres:** The system treats genre and mood as independent, but "chill pop" and "chill lofi" are very different experiences — the genre weight may dominate unfairly.
- **Energy proximity is narrow:** Songs within 0.1 energy of the user's target score nearly the same, which may not reflect how sensitive real listeners are to intensity differences.
- **Acoustic bonus is binary:** The 0.6 threshold is arbitrary — a song at 0.59 acousticness gets no bonus despite being nearly acoustic.

You can include a simple diagram or bullet list if helpful.

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Experiments You Tried

**5 diverse user profiles tested** — including two adversarial edge cases:

| Profile | What it tested | Key result |
|---|---|---|
| Chill Lofi Student | Normal, well-matched profile | Near-perfect top 2 (6.48 and 6.45 / 6.50) |
| High-Energy Pop Fan | Genre + high energy | `Sunrise City` clear #1; genre carried `Gym Hero` to #2 without mood match |
| Intense Rock Listener | Genre + extreme energy | `Storm Runner` won; `Gym Hero` (pop) and `Drop Zone` (EDM) appeared via mood match |
| Obscure Taste (no genre match) | Missing genre in catalog | Degraded gracefully; `Coffee Shop Stories` surfaced on mood + acoustic |
| Conflicting Prefs (ambient / chill / energy 0.95) | Contradictory preferences | `Spacewalk Thoughts` won despite energy 0.28 vs target 0.95 |

**Weight-shift experiment:** Halved genre weight (3.0 → 1.5), doubled energy weight (1.0 → 2.0 max) on the Conflicting Prefs profile. The ranking did not change. `Spacewalk Thoughts` still ranked #1 — confirming the issue was a catalog gap (no high-energy ambient songs exist), not a weight problem. Tuning math cannot fix missing data.

---

## Limitations and Risks

- **Tiny catalog creates false filter bubbles.** 18 songs means many profiles share the same top results. A lofi fan and a classical fan will see overlapping picks because there are only a few acoustic songs to choose from.
- **Genre weight dominates unfairly.** At 3.0 points, a genre match outscores a perfect mood + energy match combined. A jazz fan asking for "intense" music gets jazz songs even if none of them are intense.
- **No understanding of lyrics, language, or culture.** The system treats all music as a set of numbers. It cannot distinguish a love song from a protest anthem, or represent Latin, African, or Asian music traditions.
- **Static — no learning.** Skipping a song has no effect. The same profile always returns the same list, no matter how many times you run it.
- **Acoustic threshold is a hard cutoff.** A song with acousticness 0.59 scores the same as one with 0.10 — both get zero acoustic bonus despite sounding very different.

See [model_card.md](model_card.md) for a full analysis.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Recommenders turn data into predictions by reducing a person — with all their history, moods, and context — into a small set of numbers, then finding songs whose numbers are closest. That compression is where both the power and the risk live. The power: a four-field profile can produce results that genuinely feel right, especially for clear, stable preferences like "chill lofi." The risk: anything the profile doesn't capture — cultural background, current mood, what you listened to yesterday — simply doesn't exist to the algorithm.

Bias shows up in at least two ways in this system. First, in the weights: genre scores three times higher than energy, which means a song can win on category alone even if it totally mismatches the user's emotional state. Second, and more subtly, in the catalog itself: the 18-song dataset reflects the taste of whoever built it. Genres like Afrobeats, Latin, or K-pop don't appear, so users whose taste lives in those spaces will always receive poor recommendations — not because the algorithm treated them unfairly, but because they were never represented in the data to begin with. That's the harder problem, and it scales: the same dynamic plays out in every real-world recommender that was trained on data from a non-representative user base.



