"""
RecommendationAgent — LLM-powered critic for the Music Recommender.

Uses Claude with tool use to inspect top-5 results and suggest scoring-weight
overrides when recommendations don't match the user's intent.
"""
import logging
from typing import Dict, List, Optional, Tuple

import anthropic

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt — cached across calls (stable content, never changes)
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You are an expert music recommendation critic. Your job is to judge whether \
a set of recommended songs genuinely matches what a listener asked for.

You receive:
1. A user taste profile (preferred genre, mood, energy level, acoustic preference).
2. The top 5 songs the recommender returned, with scores and score breakdowns.

Your task:
- Decide how well the results match the user's stated intent (0.0 = completely wrong, 1.0 = perfect).
- Identify concrete mismatches. Examples:
    * User wants "intense" mood but all 5 results are "chill".
    * User has energy target 0.95 but every result has energy below 0.35.
    * User wanted "rock" but genre scoring was dominated by the wrong mode.
- If confidence is below 0.7, propose new feature weights that would surface better results.
  Higher values make that feature more influential in scoring.
  Reference ranges: genre 1.0–4.0, mood 1.0–4.0, energy 0.5–3.0, acoustic 0.2–0.8,
  mood_tags 0.3–1.5, popularity 0.2–0.8, decade 0.2–0.8.

Always call the submit_critique tool — do not reply in plain prose."""


class RecommendationAgent:
    """
    Critiques top-5 recommendations and proposes weight overrides when the
    results don't align with the user's intent.

    Usage::

        agent = RecommendationAgent()
        confidence, weights, reason = agent.analyze(profile, top_5)
        if confidence < 0.7:
            corrected = recommend_songs(profile, songs, weights_override=weights)
    """

    CONFIDENCE_THRESHOLD = 0.7

    _TOOL: Dict = {
        "name": "submit_critique",
        "description": (
            "Submit your quality critique of the recommendation results. "
            "Provide suggested_weights only when confidence < 0.7."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "confidence": {
                    "type": "number",
                    "description": (
                        "0.0–1.0. How well do the top-5 songs match what the user asked for? "
                        "1.0 = perfect match, 0.0 = completely wrong."
                    ),
                },
                "mismatch_reason": {
                    "type": "string",
                    "description": (
                        "Concise explanation of the main mismatch. "
                        "Empty string when confidence >= 0.7."
                    ),
                },
                "suggested_weights": {
                    "type": "object",
                    "description": (
                        "Override weights for the scoring function. "
                        "Supply only when confidence < 0.7."
                    ),
                    "properties": {
                        "genre":      {"type": "number"},
                        "mood":       {"type": "number"},
                        "energy":     {"type": "number"},
                        "acoustic":   {"type": "number"},
                        "mood_tags":  {"type": "number"},
                        "popularity": {"type": "number"},
                        "decade":     {"type": "number"},
                    },
                    "required": [
                        "genre", "mood", "energy", "acoustic",
                        "mood_tags", "popularity", "decade",
                    ],
                },
            },
            "required": ["confidence", "mismatch_reason"],
        },
    }

    def __init__(self, model: str = "claude-haiku-4-5") -> None:
        self.client = anthropic.Anthropic()
        self.model = model

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _format_profile(profile: Dict) -> str:
        return (
            f"  genre='{profile.get('favorite_genre', '?')}' | "
            f"mood='{profile.get('favorite_mood', '?')}' | "
            f"energy_target={profile.get('target_energy', '?')} | "
            f"likes_acoustic={profile.get('likes_acoustic', False)} | "
            f"scoring_mode='{profile.get('scoring_mode', 'genre-first')}'"
        )

    @staticmethod
    def _format_results(top_5: List[Tuple[Dict, float, str]]) -> str:
        lines = []
        for rank, (song, score, explanation) in enumerate(top_5, start=1):
            lines.append(
                f"  {rank}. \"{song['title']}\" — {song['artist']} "
                f"[genre={song['genre']}, mood={song['mood']}, energy={song['energy']:.2f}] "
                f"score={score:.2f}"
            )
            lines.append(f"     breakdown: {explanation}")
        return "\n".join(lines)

    def _build_user_message(
        self,
        profile: Dict,
        top_5: List[Tuple[Dict, float, str]],
    ) -> str:
        return (
            "## User Profile\n"
            f"{self._format_profile(profile)}\n\n"
            "## Top 5 Recommendations\n"
            f"{self._format_results(top_5)}\n\n"
            "Analyze whether these results genuinely match the user's intent, "
            "then call submit_critique."
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(
        self,
        profile: Dict,
        top_5: List[Tuple[Dict, float, str]],
    ) -> Tuple[float, Optional[Dict[str, float]], str]:
        """
        Critique top-5 recommendations against the user profile.

        Returns:
            (confidence, suggested_weights_or_None, mismatch_reason)

        ``suggested_weights`` is ``None`` when confidence >= CONFIDENCE_THRESHOLD.
        On API errors returns (1.0, None, error_message) so the caller can
        proceed without correction rather than crashing.
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=512,
                system=[
                    {
                        "type": "text",
                        "text": _SYSTEM_PROMPT,
                        # Cache the static system prompt — saves tokens on repeated calls.
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                tools=[self._TOOL],
                # Force the tool call so we always get structured output.
                tool_choice={"type": "tool", "name": "submit_critique"},
                messages=[
                    {
                        "role": "user",
                        "content": self._build_user_message(profile, top_5),
                    }
                ],
            )
        except anthropic.APIError as exc:
            logger.error("RecommendationAgent API error: %s", exc)
            return 1.0, None, f"API error — correction skipped: {exc}"

        for block in response.content:
            if block.type == "tool_use" and block.name == "submit_critique":
                inp = block.input
                confidence: float = float(inp.get("confidence", 1.0))
                reason: str = inp.get("mismatch_reason", "")
                weights: Optional[Dict[str, float]] = (
                    inp.get("suggested_weights")
                    if confidence < self.CONFIDENCE_THRESHOLD
                    else None
                )
                logger.info(
                    "Agent critique — confidence=%.2f | cache_read=%s tokens | reason=%r",
                    confidence,
                    getattr(response.usage, "cache_read_input_tokens", "?"),
                    reason,
                )
                return confidence, weights, reason

        logger.warning("submit_critique was not called — treating as fully confident")
        return 1.0, None, ""
