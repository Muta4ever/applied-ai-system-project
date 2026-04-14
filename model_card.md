# Model Card: Music Recommender Simulation

## 1. Model Name

**VibeFinder 1.0**

---

## 2. Intended Use and Non-Intended Use

**Intended use:** VibeFinder suggests the top 5 songs from an 18-song catalog based on a listener's stated preferences for genre, mood, energy level, and acoustic/electronic feel. It is designed for classroom exploration of how content-based recommendation systems work. It assumes the user can accurately describe their own taste in a short profile. It does not learn or adapt over time.

**Non-intended use:** VibeFinder should not be used as an actual music product, deployed on a platform, or treated as a representative model of how industrial recommenders work. It should not be used to make decisions about which artists or genres deserve visibility — its tiny catalog already reflects the tastes of whoever built it, and using it at scale would amplify that bias. It is not designed to work across languages, cultures, or accessibility needs.

---

## 3. How the Model Works

VibeFinder looks at every song in the catalog and gives each one a score based on how well it matches what the listener said they want. It awards the most points for a genre match (because genre is usually the strongest signal of taste), fewer points for a mood match, and then a smaller bonus for songs whose energy level is close to the listener's target — not just high or low, but *close* to what they asked for. There is also a small bonus for acoustic-sounding songs when the listener said they prefer that feel.

Once every song has a number, VibeFinder sorts them from highest to lowest and hands back the top five. The listener also sees a short explanation for each pick — "genre match: lofi (+3.0)" — so the recommendation is never a black box.

---

## 4. Data

The catalog contains **18 songs** across 9 genres: pop, lofi, rock, jazz, ambient, synthwave, indie pop, country, hip-hop, classical, R&B, EDM, metal, and reggae. Moods covered include happy, chill, intense, relaxed, focused, and moody.

8 songs were added manually to expand the original 10-song starter set, specifically to cover genres not represented in the original data. The catalog still skews toward electronic and Western music. It has no songs with lyrics-based attributes (theme, language, or sentiment from text), no live recordings, and no non-English-language genres such as K-pop, Afrobeats, or Latin music.

---

## 5. Strengths

- **Clear genre preferences work well.** When a user has a genre that exists in the catalog (lofi, pop, rock), the top results feel intuitively correct. The "Chill Lofi Student" profile returned Midnight Coding and Library Rain as #1 and #2 — both exactly right.
- **Transparent explanations.** Every recommendation comes with a breakdown. This is something real systems like Spotify rarely show.
- **Graceful degradation.** When a genre is missing (e.g., "bossa nova"), the system still returns reasonable songs based on mood and energy rather than crashing or returning nothing.

---

## 6. Limitations and Bias

**Genre dominance is the biggest structural bias.** A genre match is worth 3 points — more than a mood match (2 points) and an energy match (max 1 point) combined. This means a song with the right genre but the wrong mood will often beat a song with the right mood and energy but the wrong genre. For example, a jazz fan asking for "intense" music will get jazz recommendations even if none of the jazz songs in the catalog are intense.

**Conflicting preferences expose a catalog gap, not a weight problem.** The "Conflicting Prefs" profile (ambient / chill / energy 0.95) revealed that even when the genre weight was halved and the energy weight was doubled in an experiment, `Spacewalk Thoughts` still ranked #1 — because the catalog simply contains no high-energy ambient songs. Tuning weights alone cannot fix a dataset problem.

**Small catalog limits diversity.** With only 18 songs, many profiles share the same top results. A lofi student and an acoustic jazz fan will see overlapping picks because there are only a few acoustic options in the catalog.

**The acoustic bonus threshold is arbitrary.** Songs with acousticness of 0.59 get no bonus; songs with 0.61 get +0.50. This binary cut can feel unfair to songs that are nearly acoustic but fall just below the line.

**No personalization over time.** The system does not track skips, replays, or ratings. Every run with the same profile returns the same results regardless of what the user actually liked.

---

## 7. Evaluation

Five user profiles were tested:

| Profile | Key finding |
|---|---|
| Chill Lofi Student | Top 2 results were perfect lofi-chill matches (6.48 and 6.45/6.50). System worked as expected. |
| High-Energy Pop Fan | `Sunrise City` was a clear #1. `Gym Hero` ranked #2 without a mood match — genre alone carried it. |
| Intense Rock Listener | `Storm Runner` won cleanly. Interesting: `Gym Hero` (pop) and `Drop Zone` (EDM) ranked #2 and #3 — they matched "intense" mood and high energy even without matching genre. |
| Obscure Taste (no genre match) | System degraded gracefully. `Coffee Shop Stories` rose on mood+energy+acoustic, scoring 3.48/6.50. No crash, reasonable results. |
| Conflicting Prefs (high energy + chill) | `Spacewalk Thoughts` ranked #1 at 5.33/6.50 despite its energy (0.28) being far from target (0.95). Genre+mood locked in the winner before energy could matter. |

**Experiment — weight shift:** Halving the genre weight and doubling the energy weight for the Conflicting Prefs profile changed scores but not the winner. Spacewalk Thoughts still ranked #1. This confirmed that the issue is not the weights but the catalog: no high-energy ambient songs exist in the data.

**What surprised me:** I expected the "Intense Rock" profile to return only rock songs, but `Gym Hero` (pop) and `Drop Zone` (EDM) appeared because the "intense" mood match was strong enough to pull them up. The system cares more about emotional feel than genre when a mood is well-represented.

---

## 8. Future Work

- **Expand the catalog** to 100+ songs so genre and mood combinations are actually populated. The current 18 songs create artificial filter bubbles.
- **Make weights tunable** without changing code — store them in a config dict so teachers and students can experiment without touching the scoring function.
- **Add a diversity penalty** so the top 5 results always include at least 2 different genres, preventing a single genre from monopolizing the list.
- **Track feedback within a session** — if the user skips a song, reduce that song's genre weight slightly for the next run.
- **Replace the binary acoustic threshold** with a smooth proximity score, the same way energy is handled.

---

## 9. Personal Reflection

**Biggest learning moment:** The weight-shift experiment. I expected that halving the genre weight and doubling the energy weight would change which song ranked first for the "conflicting preferences" profile. It didn't — `Spacewalk Thoughts` still won. That forced me to realize the problem wasn't the math; it was the dataset. No high-energy ambient songs exist in the catalog, so no weight adjustment could surface one. That gap between "fixing the algorithm" and "fixing the data" is something real ML engineers deal with constantly, and I didn't fully understand it until I hit it myself.

**How AI tools helped — and when I had to double-check:** AI was useful for generating the scoring formula structure and explaining the difference between `sorted()` and `.sort()` clearly. It was less reliable when suggesting weights — the first suggestion gave genre and mood equal weight, which made the rankings feel flat. I had to test it with adversarial profiles before realizing genre needed to score higher. The AI gave me a starting point; the actual testing revealed what needed to change. You can't skip the running-and-looking step.

**What surprised me about simple algorithms "feeling" like recommendations:** The "Intense Rock" profile returned `Gym Hero` (pop) and `Drop Zone` (EDM) in the top 5. Those felt wrong at first — but then I looked at the scores: both songs matched "intense" mood and had energy above 0.85. The algorithm wasn't broken; it was being consistent in a way that crossed genre lines. Real music taste does that too — a rock fan at the gym might actually like `Drop Zone`. The "feeling" of intelligence came from the mood feature doing real work, not from the system being smart.

**What I would try next:** I'd replace the four-field profile with a set of songs the user already likes — letting the system infer their preferences from their own history instead of asking them to describe themselves. That's closer to how Spotify actually works, and it would immediately fix the "conflicting preferences" problem because the data would be self-consistent.
