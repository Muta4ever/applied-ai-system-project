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

## 7. Advanced Features Added (Phase 5–6)

### Agentic Self-Correction Loop

The biggest addition to VibeFinder is a `RecommendationAgent` class (`src/agent.py`) that uses Claude as an LLM-powered critic. After the recommender returns its top-5 results, the agent analyzes whether those results genuinely match what the user asked for and returns:

- A **confidence score** (0.0–1.0): how well the results match the user's intent
- A **mismatch reason**: a plain-English explanation of what went wrong
- **Suggested weights**: a new set of scoring weights that would surface better results (only when confidence < 0.7)

If the agent's confidence falls below 0.7, `src/main.py` re-runs `recommend_songs()` with the agent's corrected weights and logs the before/after improvement.

**Why this matters:** The agent detects mismatches that the evaluator cannot catch with simple rules — specifically the energy gap in the Conflicting Prefs profile. The scoring function alone had no way to know its results were wrong; the LLM could see it immediately by comparing the user's stated target energy (0.95) with the actual energies returned (avg 0.40).

**Implementation choices:**
- **Forced tool use** (`tool_choice: {type: "tool", name: "submit_critique"}`) guarantees structured JSON output rather than prose — no parsing, no fallback handling
- **Prompt caching** (`cache_control: {type: "ephemeral"}`) on the static system prompt reduces token cost on repeated calls
- **`weights_override` parameter** in `recommend_songs()` lets the agent inject one-off weights without modifying the shared `SCORING_MODES` dict

### Reliability Evaluator (`src/evaluator.py`)

A standalone evaluation script that runs 10 stress-test profiles through the recommender and checks two properties for each result set:

- **Diversity:** Does the top-5 contain at least 3 different artists? (measured without the diversity filter so natural catalog spread is tested)
- **Relevance:** Does the #1 result's genre OR mood match the user's profile?

The 10 profiles cover: perfect match, missing genre (k-pop), missing genre (folk), high-energy pop, intense rock, conflicting preferences, mainstream pop (mood-first mode), underground hip-hop, moody R&B (energy-focused mode), retro 1990s metal.

---

## 8. Evaluation

### Original 5-Profile Experiment

| Profile | Key finding |
|---|---|
| Chill Lofi Student | Top 2 results were perfect lofi-chill matches (6.48 and 6.45/6.50). System worked as expected. |
| High-Energy Pop Fan | `Sunrise City` was a clear #1. `Gym Hero` ranked #2 without a mood match — genre alone carried it. |
| Intense Rock Listener | `Storm Runner` won cleanly. `Gym Hero` (pop) and `Drop Zone` (EDM) ranked #2 and #3 via mood+energy match. |
| Obscure Taste (no genre match) | System degraded gracefully. `Coffee Shop Stories` rose on mood+energy+acoustic, scoring 3.48/6.50. |
| Conflicting Prefs (high energy + chill) | `Spacewalk Thoughts` ranked #1 despite energy 0.28 vs target 0.95. Genre+mood locked in the winner. |

**Experiment — weight shift:** Halving genre weight and doubling energy weight did not change the winner. Confirmed the issue is a catalog gap, not a weight problem. This is the known mismatch the agentic critic is designed to detect.

**What surprised me:** I expected the "Intense Rock" profile to return only rock songs, but `Gym Hero` (pop) and `Drop Zone` (EDM) appeared because "intense" mood + high energy pulled them up. The system cares more about emotional feel than genre when a mood is well-represented.

### Extended 10-Profile Reliability Test (`src/evaluator.py`)

Run with `python -m src.evaluator` — produces a full Markdown health report.

| Check | Passed | Failed | Pass Rate |
|---|---|---|---|
| Diversity (≥ 3 artists in top 5) | 10 | 0 | 100% |
| Relevance (#1 result genre or mood match) | 10 | 0 | 100% |
| Both checks passed | 10 | 0 | 100% |

Key findings from the 10-profile run:
- **Missing genres (k-pop, folk):** Relevance is saved by mood matching — the system degrades gracefully every time.
- **Conflicting prefs (ambient + energy 0.95):** Passes both evaluator checks (genre match on ambient, 4 unique artists) but the agent catches what the evaluator misses — average energy of results is 0.40, far from the 0.95 target.
- **Scoring modes (mood-first, energy-focused):** Both modes produced passing results, confirming the mode-switching logic works correctly.

### Agentic Self-Correction Results

On the Conflicting Prefs profile, the agent returned confidence ≈ 0.15 (well below 0.7). After applying corrected weights (energy weight boosted from 0.8 → 3.0):

| Metric | Before | After | Target |
|---|---|---|---|
| Avg energy of top 5 | 0.40 | 0.87 | 0.95 |
| Top song genre | ambient | rock | ambient |

The agent could not find high-energy ambient songs (none exist in the catalog) but correctly redirected toward the highest-energy songs available. The before/after energy improvement of +0.47 is visible and logged in the terminal output.

---

## 9. Future Work

- **Expand the catalog** to 100+ songs so genre and mood combinations are actually populated. The current 18 songs create artificial filter bubbles.
- **Make weights tunable** without changing code — store them in a config dict so teachers and students can experiment without touching the scoring function.
- **Add a diversity penalty** so the top 5 results always include at least 2 different genres, preventing a single genre from monopolizing the list.
- **Track feedback within a session** — if the user skips a song, reduce that song's genre weight slightly for the next run.
- **Replace the binary acoustic threshold** with a smooth proximity score, the same way energy is handled.

---

## 10. Personal Reflection

**Biggest learning moment:** The weight-shift experiment. I expected that halving the genre weight and doubling the energy weight would change which song ranked first for the "conflicting preferences" profile. It didn't — `Spacewalk Thoughts` still won. That forced me to realize the problem wasn't the math; it was the dataset. No high-energy ambient songs exist in the catalog, so no weight adjustment could surface one. That gap between "fixing the algorithm" and "fixing the data" is something real ML engineers deal with constantly, and I didn't fully understand it until I hit it myself.

**How AI tools helped — and when I had to double-check:** AI was useful for generating the scoring formula structure and explaining the difference between `sorted()` and `.sort()` clearly. It was less reliable when suggesting weights — the first suggestion gave genre and mood equal weight, which made the rankings feel flat. I had to test it with adversarial profiles before realizing genre needed to score higher. The AI gave me a starting point; the actual testing revealed what needed to change. You can't skip the running-and-looking step.

**What surprised me about simple algorithms "feeling" like recommendations:** The "Intense Rock" profile returned `Gym Hero` (pop) and `Drop Zone` (EDM) in the top 5. Those felt wrong at first — but then I looked at the scores: both songs matched "intense" mood and had energy above 0.85. The algorithm wasn't broken; it was being consistent in a way that crossed genre lines. Real music taste does that too — a rock fan at the gym might actually like `Drop Zone`. The "feeling" of intelligence came from the mood feature doing real work, not from the system being smart.

**What I would try next:** I'd replace the four-field profile with a set of songs the user already likes — letting the system infer their preferences from their own history instead of asking them to describe themselves. That's closer to how Spotify actually works, and it would immediately fix the "conflicting preferences" problem because the data would be self-consistent.

---

## 11. AI Collaboration Log

### How Claude was used during development

Throughout this project I used Claude (via Claude Code and the Anthropic API) in three ways:

1. **Design sounding board** — I described the scoring function structure and asked Claude to identify edge cases. It flagged the energy-proximity formula before I ran tests, correctly predicting that a song with energy 0.01 would outrank a song at 0.50 when the target was 0.00, even though both "feel" similar to a human.
2. **Code scaffolding** — I prompted Claude to generate the initial `_score_song` function signature and the `SCORING_MODES` dict structure. This saved time on boilerplate and let me focus on the weights and testing logic.
3. **The agent itself** — `RecommendationAgent` calls Claude via the Anthropic API at runtime. Claude's role in the running system is to critique the scorer's output and suggest better weights. This is not just a development tool; it is a live component of the pipeline.

### One instance where AI gave a helpful suggestion

When implementing the `submit_critique` tool, Claude suggested using `tool_choice: {type: "tool", name: "submit_critique"}` to force the model to always return structured output rather than prose. I had originally planned to ask for JSON in the system prompt and parse it with regex — Claude's approach is strictly better: it guarantees the schema, removes parsing fragility, and fails loudly (missing field) rather than silently (bad parse). I adopted it immediately.

### One instance where AI's suggestion was flawed

When I first asked Claude to propose default scoring weights, it suggested equal weights for genre and mood (both 2.0). In practice this made the rankings feel flat — too many songs tied at similar scores. When I tested the "High-Energy Pop Fan" profile, the correct pop/happy song was only barely ahead of an ambient/chill song because the mood match offset the genre advantage. The correct fix (genre=3.0, mood=1.5) came from testing adversarial profiles and observing where the rankings broke down, not from the AI's initial suggestion. Claude gave a reasonable default; domain testing revealed what actually worked.

---

## 12. Portfolio Reflection

**What this project says about me as an AI engineer:**

VibeFinder demonstrates that I understand where AI belongs in a system — and where it does not. I built the scoring engine as a deterministic, explainable rule-based system because that is the right tool for that job: fast, auditable, and predictable. I brought in Claude only at the evaluation layer, where the task — "does this recommendation set match the user's intent?" — genuinely requires language understanding and holistic judgment that a formula cannot express.

The self-correction loop shows I can integrate LLM calls into a production-style workflow rather than using them as a black box. I used forced tool use to guarantee structured output, prompt caching to reduce token cost on repeated calls, and a confidence threshold to avoid unnecessary API calls when the first result is already good. I also built a separate deterministic evaluator (`src/evaluator.py`) to test the scorer independently of the LLM, which means the reliability of the core system is not coupled to API availability or LLM non-determinism.

The lesson I am most proud of: I ran into a real ML problem — tuning weights could not fix a catalog gap — and instead of hacking around it, I designed the agent to detect and communicate the gap rather than pretend it isn't there. That is the kind of honest, observable failure mode that trustworthy AI systems need.
