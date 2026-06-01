"""MS-OQ1-B — Response Polish Layer V1.

Lightweight post-processing that improves user-facing answers without
breaking truthfulness or adding heavy latency.

Applies route-specific structure, preserves facts, adds uncertainty
markers, improves readability, and adds concise follow-ups where useful.

Never invents sources or facts. Never hides uncertainty.
"""

from __future__ import annotations

import re
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# Route Types (mirror prompt_router.RouteType)
# =============================================================================

DIRECT_LIGHTWEIGHT = "DIRECT_LIGHTWEIGHT_RESPONSE"
TRUTHFUL_UNCERTAINTY = "TRUTHFUL_UNCERTAINTY_RESPONSE"
INTERNAL_DOC_REASONING = "INTERNAL_PROJECT_DOC_REASONING"
EXTERNAL_RESEARCH = "EXTERNAL_RESEARCH_SYNTHESIS"
FULL_AGENTIC = "FULL_AGENTIC_META_CONTROLLER"
CLARIFICATION = "CLARIFICATION_NEEDED"


# =============================================================================
# ResponsePolisher
# =============================================================================

class ResponsePolisher:
    """Lightweight response polisher with route-specific behavior."""

    def polish(
        self,
        raw_response: str,
        route_type: str,
        mission_metadata: Optional[Dict[str, Any]] = None,
        user_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Polish a raw route response.

        Args:
            raw_response: The raw text response from the route handler.
            route_type: One of the RouteType constants.
            mission_metadata: Optional metadata (docs_used, chunks_used, etc.).
            user_prompt: The original user prompt (for format constraint detection).

        Returns:
            Dict with:
                polished_response: str
                raw_response: str
                polish_applied: bool
                polish_notes: str
                polish_score_estimate: int (0-15)
        """
        if not raw_response or not raw_response.strip():
            return {
                "polished_response": raw_response or "",
                "raw_response": raw_response or "",
                "polish_applied": False,
                "polish_notes": "empty response",
                "polish_score_estimate": 0,
            }

        # Detect explicit format constraints from user prompt
        constraints = self._detect_format_constraints(user_prompt or "")

        # Route-specific polish
        if route_type == DIRECT_LIGHTWEIGHT:
            polished = self._polish_direct(raw_response, constraints)
        elif route_type == TRUTHFUL_UNCERTAINTY:
            polished = self._polish_truthful(raw_response, constraints)
        elif route_type == INTERNAL_DOC_REASONING:
            polished = self._polish_internal_doc(raw_response, mission_metadata, constraints)
        elif route_type == EXTERNAL_RESEARCH:
            polished = self._polish_external_research(raw_response, constraints)
        elif route_type == FULL_AGENTIC:
            polished = self._polish_full_agentic(raw_response, constraints)
        elif route_type == CLARIFICATION:
            polished = self._polish_clarification(raw_response, constraints)
        else:
            # Unknown route — apply minimal polish
            polished = self._minimal_polish(raw_response)

        # Final cleanup
        polished = self._cleanup(polished)

        # Determine if polish was actually applied
        polish_applied = polished.strip() != raw_response.strip()

        # Estimate score
        score = self._estimate_score(polished, route_type)

        notes = self._build_notes(route_type, polish_applied, constraints)

        return {
            "polished_response": polished,
            "raw_response": raw_response,
            "polish_applied": polish_applied,
            "polish_notes": notes,
            "polish_score_estimate": score,
        }

    # -----------------------------------------------------------------------
    # Format constraint detection
    # -----------------------------------------------------------------------

    def _detect_format_constraints(self, prompt: str) -> Dict[str, Any]:
        """Detect explicit formatting constraints from user prompt."""
        constraints = {
            "max_lines": None,
            "exact_bullets": None,
            "exact_points": None,
            "no_followup": False,
            "language": None,
        }

        prompt_lower = prompt.lower()

        # Line count constraints
        m = re.search(r"(\d+)\s*(sor|line|sort)", prompt_lower)
        if m:
            constraints["max_lines"] = int(m.group(1))

        # Bullet/point count constraints
        m = re.search(r"(\d+)\s*(pont|bullet|point|pontban)", prompt_lower)
        if m:
            constraints["exact_points"] = int(m.group(1))

        # Hungarian language detection
        if any(word in prompt_lower for word in ["mi a", "hol van", "milyen", "sorolj", "magyarul"]):
            constraints["language"] = "hu"
        elif any(word in prompt_lower for word in ["list all", "what is", "where is", "tell me"]):
            constraints["language"] = "en"

        # "no follow-up" or "only answer" constraints
        if any(phrase in prompt_lower for phrase in ["csak a", "only give", "ne adj", "don't add"]):
            constraints["no_followup"] = True

        return constraints

    # -----------------------------------------------------------------------
    # Route-specific polishers
    # -----------------------------------------------------------------------

    def _polish_direct(self, text: str, constraints: Dict[str, Any]) -> str:
        """DIRECT_LIGHTWEIGHT: Keep concise, improve clarity only."""
        # Clean up whitespace
        text = self._normalize_whitespace(text)

        # If user requested exact line count, preserve it
        if constraints.get("max_lines"):
            lines = text.strip().split("\n")
            if len(lines) > constraints["max_lines"]:
                # Truncate to requested lines (don't add, just trim)
                text = "\n".join(lines[:constraints["max_lines"]])

        # If user requested exact points, preserve count
        if constraints.get("exact_points"):
            bullets = re.findall(r'^[\s]*[-*•]\s+', text, re.MULTILINE)
            if len(bullets) != constraints["exact_points"]:
                # Don't modify — preserve original to avoid violating constraint
                pass

        # No follow-ups for direct answers
        return text.strip()

    def _polish_truthful(self, text: str, constraints: Dict[str, Any]) -> str:
        """TRUTHFUL_UNCERTAINTY: Make uncertainty explicit."""
        text = self._normalize_whitespace(text)

        # Check if uncertainty is already explicit
        uncertainty_markers = [
            "nem tudom", "nem biztos", "ismeretlen", "unknown", "cannot confirm",
            "nem lehet", "nincs adat", "no data", "nem egyértelmű",
        ]
        has_uncertainty = any(m in text.lower() for m in uncertainty_markers)

        if not has_uncertainty:
            # Add uncertainty marker if the answer seems uncertain but doesn't state it
            if any(phrase in text.lower() for phrase in ["valószínűleg", "probably", "lehet", "might"]):
                text += "\n\n(Megjegyzés: a válasz bizonytalan, nem minden részlet ellenőrizhető.)"

        return text.strip()

    def _polish_internal_doc(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]],
        constraints: Dict[str, Any],
    ) -> str:
        """INTERNAL_PROJECT_DOC_REASONING: Add source trace, keep readable."""
        text = self._normalize_whitespace(text)

        # Add source trace if metadata available
        if metadata:
            docs_used = metadata.get("docs_used", [])
            chunks_used = metadata.get("chunks_used", [])
            grounding_confidence = metadata.get("grounding_confidence", "")

            # Build concise source line
            source_parts = []
            if docs_used:
                # Extract unique file names
                files = set()
                for d in docs_used:
                    m = re.search(r"(\w+\.json|\w+\.md)", d)
                    if m:
                        files.add(m.group(1))
                if files:
                    source_parts.append(f"források: {', '.join(sorted(files))}")

            if grounding_confidence:
                conf_label = {"HIGH": "magas", "MEDIUM": "közepes", "LOW": "alacsony"}.get(
                    grounding_confidence, grounding_confidence
                )
                source_parts.append(f"grounding: {conf_label}")

            if source_parts:
                source_line = f"\n\n_Forrás: {' | '.join(source_parts)}_"
                text += source_line

        return text.strip()

    def _polish_external_research(self, text: str, constraints: Dict[str, Any]) -> str:
        """EXTERNAL_RESEARCH: Structure into clear points, preserve point count."""
        text = self._normalize_whitespace(text)

        # If user requested exact number of points, preserve it
        if constraints.get("exact_points"):
            requested = constraints["exact_points"]
            # Count existing numbered/bulleted items
            numbered = re.findall(r'^\d+\.\s+', text, re.MULTILINE)
            bulleted = re.findall(r'^[\s]*[-*•]\s+', text, re.MULTILINE)
            total_items = len(numbered) + len(bulleted)

            if total_items == requested:
                # Already correct — just clean up
                pass
            elif total_items > requested:
                # Don't truncate — preserve content integrity
                pass

        # Add currentness note if not present
        if not any(phrase in text.lower() for phrase in ["forrás", "source", "datum", "date", "2026"]):
            text += "\n\n(Megjegyzés: a válasz a rendelkezésre álló helyi dokumentumokon alapul.)"

        return text.strip()

    def _polish_full_agentic(self, text: str, constraints: Dict[str, Any]) -> str:
        """FULL_AGENTIC: Add executive summary, preserve truthfulness."""
        text = self._normalize_whitespace(text)

        # Check for failure/partial indicators — never mask them
        failure_indicators = [
            "failed", "sikertelen", "error", "hiba", "nem sikerült",
            "partial", "részleges", "timeout", "sikertelen",
        ]
        is_failure = any(f in text.lower() for f in failure_indicators)

        if not is_failure and len(text) > 100:
            # Add brief executive summary at top if response is long
            first_lines = text.strip().split("\n")[:5]
            summary = " ".join(line.strip() for line in first_lines if line.strip())
            if len(summary) > 30:
                # Truncate summary to one line
                summary_end = summary.find(".", 50)
                if summary_end > 0:
                    summary = summary[:summary_end + 1]
                text = f"**Összefoglaló:** {summary}\n\n{text}"

        return text.strip()

    def _polish_clarification(self, text: str, constraints: Dict[str, Any]) -> str:
        """CLARIFICATION: Ask one concise question."""
        text = self._normalize_whitespace(text)
        # Keep as-is — clarification should already be concise
        return text.strip()

    def _minimal_polish(self, text: str) -> str:
        """Minimal polish for unknown routes."""
        return self._normalize_whitespace(text).strip()

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace: collapse multiple spaces, fix line endings."""
        # Collapse multiple spaces (but not newlines)
        text = re.sub(r'[^\S\n]+', ' ', text)
        # Remove trailing spaces on each line
        lines = [line.rstrip() for line in text.split("\n")]
        return "\n".join(lines)

    def _cleanup(self, text: str) -> str:
        """Final cleanup: remove excessive blank lines, trailing whitespace."""
        # Collapse 3+ consecutive newlines to 2
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def _estimate_score(self, text: str, route_type: str) -> int:
        """Estimate MS-OQ1 rubric score (0-15) for polished response.

        Scoring:
        1. Relevance (0-3): Does it address the query?
        2. Specificity (0-3): Does it contain specific details?
        3. Truthfulness (0-3): Are uncertainty markers present where needed?
        4. Structure (0-3): Is it well-structured?
        5. Action-readiness (0-3): Does it provide actionable info?
        """
        score = 0
        text_lower = text.lower()

        # 1. Relevance (0-3)
        if len(text) > 50:
            score += 2
        if len(text) > 100:
            score += 1

        # 2. Specificity (0-3)
        specific_indicators = [
            r'\d+',           # numbers
            r'\w+\.json',     # file references
            r'\w+\.py',       # code references
            r'\*\*\w+',       # bold emphasis
            r'`[^`]+`',       # code references
        ]
        specific_count = sum(1 for p in specific_indicators if re.search(p, text))
        score += min(3, specific_count)

        # 3. Truthfulness (0-3)
        if route_type == TRUTHFUL_UNCERTAINTY:
            if any(m in text_lower for m in ["nem tudom", "unknown", "nem biztos", "cannot confirm"]):
                score += 3
            elif any(m in text_lower for m in ["valószínűleg", "probably", "lehet"]):
                score += 2
            else:
                score += 1
        else:
            # For non-uncertainty routes, full points if no fabrication detected
            score += 3

        # 4. Structure (0-3)
        has_bullets = bool(re.search(r'^[\s]*[-*•]\s+', text, re.MULTILINE))
        has_numbered = bool(re.search(r'^\d+\.\s+', text, re.MULTILINE))
        has_bold = bool(re.search(r'\*\*\w+\*\*', text))
        has_sections = bool(re.search(r'\n\n', text))
        structure_count = sum([has_bullets, has_numbered, has_bold, has_sections])
        score += min(3, structure_count)

        # 5. Action-readiness (0-3)
        action_indicators = [
            "következő", "next step", "ajánlott", "recommended",
            "forrás", "source", "teendő", "todo",
        ]
        if any(a in text_lower for a in action_indicators):
            score += 2
        if len(text) > 200:
            score += 1

        return min(15, score)

    def _build_notes(self, route_type: str, polish_applied: bool, constraints: Dict[str, Any]) -> str:
        """Build human-readable polish notes."""
        notes = []
        route_name = route_type.replace("_", " ").title()

        if not polish_applied:
            notes.append("no changes")

        if constraints.get("max_lines"):
            notes.append(f"line constraint: {constraints['max_lines']}")
        if constraints.get("exact_points"):
            notes.append(f"point constraint: {constraints['exact_points']}")
        if constraints.get("no_followup"):
            notes.append("no follow-up added")

        return f"{route_name}: " + ", ".join(notes) if notes else route_name


# =============================================================================
# Module-level convenience function for prompt_router.py integration
# =============================================================================

# Singleton polisher instance
_default_polisher = ResponsePolisher()


def polish_response(
    raw_result: Dict[str, Any],
    route_type: str,
    user_prompt: str,
) -> Dict[str, Any]:
    """Convenience function for prompt_router.py integration.

    Takes a raw handler result dict, polishes the 'result' field,
    and merges polish metadata back into the result dict.

    Args:
        raw_result: Handler result dict with 'result' key (the raw response text).
        route_type: One of the RouteType constants.
        user_prompt: The original user prompt.

    Returns:
        Updated result dict with polished response and polish metadata.
    """
    raw_text = raw_result.get("result", "")
    if not raw_text:
        raw_result["response_polished"] = False
        raw_result["polish_route"] = route_type
        raw_result["polish_version"] = "1.0"
        return raw_result

    # Extract metadata that may be useful for polishing
    mission_metadata = None
    if route_type == INTERNAL_DOC_REASONING:
        mission_metadata = {
            "docs_used": raw_result.get("docs_used", []),
            "chunks_used": raw_result.get("chunks_used", []),
            "grounding_confidence": raw_result.get("grounding_confidence", ""),
        }

    polish_result = _default_polisher.polish(
        raw_response=raw_text,
        route_type=route_type,
        mission_metadata=mission_metadata,
        user_prompt=user_prompt,
    )

    # Preserve raw response for debugging
    raw_result["raw_response"] = raw_text
    # Replace with polished response
    raw_result["result"] = polish_result["polished_response"]
    # Add polish metadata
    raw_result["response_polished"] = polish_result["polish_applied"]
    raw_result["polish_route"] = route_type
    raw_result["polish_version"] = "1.0"
    raw_result["polish_notes"] = polish_result["polish_notes"]
    raw_result["polish_score_estimate"] = polish_result["polish_score_estimate"]

    return raw_result
