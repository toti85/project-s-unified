"""
verdict_evaluator.py — Placeholder Verdict Evaluator

Conservative heuristic evaluator for FA1.2.
FA1.3+ will replace with AI-based evaluation (SAI evaluator integration).

Status:
    - FA1.2: Fully implemented (placeholder)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from .verdict_schema import VerdictStatus


@dataclass
class EvaluationResult:
    """Result of evaluating Cline output."""
    status: VerdictStatus
    confidence: float
    reasoning: str
    matched_criteria: list[str] = field(default_factory=list)
    unmet_criteria: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)


class VerdictEvaluator:
    """
    Placeholder evaluator for FA1.2.

    Conservative heuristics:
    - Output must be non-empty (> 50 chars)
    - If tests mentioned, "OK" or "PASSED" pattern found
    - No obvious error patterns
    - If uncertain → NEEDS_HUMAN
    - Only PASS if all criteria clearly met
    - FIX only for obvious failures
    """

    def evaluate(
        self,
        run_id: str,
        output_text: str,
        acceptance_criteria: Optional[list[str]] = None,
    ) -> EvaluationResult:
        """
        Evaluate Cline output against acceptance criteria.

        Args:
            run_id: Run identifier
            output_text: Raw output from Cline
            acceptance_criteria: List of criteria to check

        Returns:
            EvaluationResult with status, confidence, and reasoning
        """
        acceptance_criteria = acceptance_criteria or []
        issues: list[str] = []
        matched: list[str] = []
        unmet: list[str] = []
        confidence = 1.0

        # ── Check output length ──────────────────────────────
        if len(output_text) < 50:
            issues.append("Output too short (< 50 chars)")
            confidence -= 0.3

        # ── Check for test patterns ──────────────────────────
        has_test_mention = bool(re.search(r"test|unittest|pytest", output_text, re.IGNORECASE))
        has_test_pass = bool(re.search(r"\bOK\b|\bPASSED\b|all.*pass", output_text, re.IGNORECASE))
        has_test_fail = bool(re.search(r"\bFAILED\b|\bERROR\b|\bfailures?\b", output_text, re.IGNORECASE))

        if has_test_mention:
            if has_test_pass:
                matched.append("Tests passed (OK/PASSED pattern found)")
            else:
                issues.append("Tests mentioned but no pass pattern found")
                confidence -= 0.4
                unmet.append("Test success confirmation")

        if has_test_fail:
            issues.append("Test failure pattern detected")
            confidence -= 0.5
            unmet.append("No test failures")

        # ── Check for error patterns ─────────────────────────
        has_error = bool(re.search(r"\berror\b|\bexception\b|\btraceback\b", output_text, re.IGNORECASE))
        if has_error:
            issues.append("Error/exception pattern in output")
            confidence -= 0.3
            unmet.append("No errors in output")

        # ── Check acceptance criteria keywords ───────────────
        output_lower = output_text.lower()
        for criterion in acceptance_criteria:
            criterion_lower = criterion.lower()
            # Check if key words from criterion appear in output
            key_words = [w for w in criterion_lower.split() if len(w) > 3]
            found = any(w in output_lower for w in key_words)
            if found:
                matched.append(f"Criterion matched: {criterion}")
            else:
                # Don't penalize heavily for unmatched criteria keywords
                # (output may describe work differently)
                pass

        # ── Determine status ─────────────────────────────────
        confidence = max(0.0, min(1.0, confidence))

        if confidence >= 0.8 and not issues:
            status = VerdictStatus.PASS
            reasoning = f"Confidence {confidence:.2f}. No issues detected."
        elif has_test_fail:
            status = VerdictStatus.FIX
            reasoning = f"Test failures detected. Confidence {confidence:.2f}. Issues: {', '.join(issues)}"
        else:
            status = VerdictStatus.NEEDS_HUMAN
            reasoning = f"Conservative evaluation: human review needed. Confidence {confidence:.2f}. Issues: {', '.join(issues)}"

        return EvaluationResult(
            status=status,
            confidence=confidence,
            reasoning=reasoning,
            matched_criteria=matched,
            unmet_criteria=unmet,
            issues=issues,
        )