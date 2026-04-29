# VibeFinder 1.0 — System Architecture

## Full System Diagram

```mermaid
flowchart TD
    A([User Profile\ngenre · mood · energy\nacoustic · scoring_mode]) --> B
    CSV[(data/songs.csv\n18 songs · 9 genres)] --> B

    B["recommend_songs()\nsrc/recommender.py\nScores every song using SCORING_MODES\nApplies optional diversity filter"]

    B --> C[Top-5 Results\nwith scores & breakdowns]

    C --> D["RecommendationAgent.analyze()\nsrc/agent.py"]

    D --> E["Claude API\nclaude-haiku-4-5\nForced tool use: submit_critique\nPrompt caching on system prompt"]

    E --> F{confidence ≥ 0.7?}

    F -->|YES — results look good| G([Final Top-5 Recommendations\nno correction needed])

    F -->|NO — mismatch detected| H["suggested_weights dict\n+ mismatch_reason string"]

    H --> I["recommend_songs(weights_override=...)\nRe-run with agent-corrected weights"]

    I --> J([Corrected Top-5\nBefore vs After energy logged to terminal])

    subgraph evaluator ["src/evaluator.py — Reliability Harness (human reviews report)"]
        K[10 stress-test profiles] --> L["recommend_songs(diversity=False)\nNatural catalog spread measured"]
        L --> M["check_diversity()\n≥ 3 unique artists in top-5?"]
        L --> N["check_relevance()\n#1 result genre OR mood matches profile?"]
        M --> O([Markdown Health Report\npass rates · per-profile details])
        N --> O
    end

    subgraph tests ["pytest — Unit Tests"]
        P["tests/test_recommender.py"] --> Q([2 tests pass\nsorting correctness · explanation strings])
    end
```

## Data Flow Summary

| Step | Component | Input | Output |
|---|---|---|---|
| 1 | `load_songs()` | `data/songs.csv` | list of 18 song dicts |
| 2 | `_score_song()` | song dict + user profile + weights | (score, reasons list) |
| 3 | `recommend_songs()` | user profile + all songs | top-k (song, score, explanation) tuples |
| 4 | `RecommendationAgent.analyze()` | user profile + top-5 | confidence, suggested_weights, mismatch_reason |
| 5 | Claude API (`submit_critique` tool) | formatted profile + results | structured JSON critique |
| 6 | `recommend_songs(weights_override=...)` | original profile + agent weights | corrected top-5 |
| 7 | `run_evaluation()` | 10 stress profiles | Markdown health report string |

## Where Humans Are Involved

- **Profile design** — the user defines their taste profile and picks a scoring mode
- **Evaluation review** — a human reads the Markdown health report to judge whether pass rates are acceptable
- **Agent oversight** — the `mismatch_reason` and `suggested_weights` are logged so a human can inspect what the LLM detected and why
