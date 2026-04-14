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

Use this section to document the experiments you ran. For example:

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this


---

## 7. `model_card_template.md`

Combines reflection and model card framing from the Module 3 guidance. :contentReference[oaicite:2]{index=2}  

```markdown
# 🎧 Model Card - Music Recommender Simulation

## 1. Model Name

Give your recommender a name, for example:

> VibeFinder 1.0

---

## 2. Intended Use

- What is this system trying to do
- Who is it for

Example:

> This model suggests 3 to 5 songs from a small catalog based on a user's preferred genre, mood, and energy level. It is for classroom exploration only, not for real users.

---

## 3. How It Works (Short Explanation)

Describe your scoring logic in plain language.

- What features of each song does it consider
- What information about the user does it use
- How does it turn those into a number

Try to avoid code in this section, treat it like an explanation to a non programmer.

---

## 4. Data

Describe your dataset.

- How many songs are in `data/songs.csv`
- Did you add or remove any songs
- What kinds of genres or moods are represented
- Whose taste does this data mostly reflect

---

## 5. Strengths

Where does your recommender work well

You can think about:
- Situations where the top results "felt right"
- Particular user profiles it served well
- Simplicity or transparency benefits

---

## 6. Limitations and Bias

Where does your recommender struggle

Some prompts:
- Does it ignore some genres or moods
- Does it treat all users as if they have the same taste shape
- Is it biased toward high energy or one genre by default
- How could this be unfair if used in a real product

---

## 7. Evaluation

How did you check your system

Examples:
- You tried multiple user profiles and wrote down whether the results matched your expectations
- You compared your simulation to what a real app like Spotify or YouTube tends to recommend
- You wrote tests for your scoring logic

You do not need a numeric metric, but if you used one, explain what it measures.

---

## 8. Future Work

If you had more time, how would you improve this recommender

Examples:

- Add support for multiple users and "group vibe" recommendations
- Balance diversity of songs instead of always picking the closest match
- Use more features, like tempo ranges or lyric themes

---

## 9. Personal Reflection

A few sentences about what you learned:

- What surprised you about how your system behaved
- How did building this change how you think about real music recommenders
- Where do you think human judgment still matters, even if the model seems "smart"

