"""
ai_client.py — Minimal AI Client Abstraction for MS-FA1 Orchestrator

Provides:
    - AI-based prompt drafting
    - AI-based output evaluation
    - Fallback to placeholder logic on failure
    - No hardcoded API keys
    - No secrets in logs
    - Timeout support

Model policy v1:
    - OpenRouter Qwen3.6 baseline
    - Local models via parity tests later
    - Fallback on error
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from .verdict_schema import VerdictStatus

logger = logging.getLogger(__name__)


# ── Config ───────────────────────────────────────────────────


@dataclass
class AIConfig:
    """Configuration for AI client."""
    enabled: bool = True
    provider: str = "openrouter"
    model: str = "qwen/qwen3.6-35b-a3b"
    api_url: str = ""
    timeout: int = 30
    fallback_on_error: bool = True


# ── Verdict Data Model ──────────────────────────────────────


@dataclass
class AIVerdict:
    """Verdict returned by AI evaluator."""
    run_id: str
    goal: str
    status: str  # PASS / FIX / STOP / NEEDS_HUMAN / ERROR
    confidence: float
    summary: str
    evidence_files: list[str] = field(default_factory=list)
    files_changed: list[str] = field(default_factory=list)
    tests_run: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    next_action: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "goal": self.goal,
            "status": self.status,
            "confidence": self.confidence,
            "summary": self.summary,
            "evidence_files": self.evidence_files,
            "files_changed": self.files_changed,
            "tests_run": self.tests_run,
            "risks": self.risks,
            "next_action": self.next_action,
        }


# ── OrchestratorAIClient ────────────────────────────────────


class OrchestratorAIClient:
    """
    Minimal AI client for orchestrator prompt drafting and evaluation.

    Supports OpenRouter-compatible API.
    Falls back to placeholder logic on failure.
    """

    def __init__(
        self,
        prompt_config: Optional[AIConfig] = None,
        eval_config: Optional[AIConfig] = None,
    ):
        self.prompt_config = prompt_config or AIConfig()
        self.eval_config = eval_config or AIConfig()
        self._api_key = self._load_api_key()
        self._api_url = os.environ.get(
            "OPENROUTER_API_URL",
            "https://openrouter.ai/api/v1/chat/completions",
        )

    def _load_api_key(self) -> str:
        """
        Load OPENROUTER_API_KEY with priority:
        1. Environment variable (already set)
        2. .env.local file
        3. Empty string (will trigger fallback)

        Never prints the actual key value.
        """
        # Priority 1: environment variable
        key = os.environ.get("OPENROUTER_API_KEY", "").strip()
        if key:
            logger.info("OPENROUTER_API_KEY loaded: yes (env)")
            return key

        # Priority 2: .env.local file
        # __file__ is src/orchestrator/ai_client.py
        # dirname(dirname(__file__)) = src/
        # dirname(dirname(dirname(__file__))) = project root (C:\ProjectS-Unified)
        project_root = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        env_local = project_root / ".env.local"
        if env_local.exists():
            try:
                for line in env_local.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        if k.strip() == "OPENROUTER_API_KEY":
                            key = v.strip()
                            if key:
                                logger.info("OPENROUTER_API_KEY loaded: yes (.env.local)")
                                return key
            except Exception as e:
                logger.warning("Failed to read .env.local: %s", e)

        logger.info("OPENROUTER_API_KEY loaded: no")
        return ""

    # ── Prompt Drafting ──────────────────────────────────────

    def draft_cline_prompt(
        self,
        goal_text: str,
        safety_policy: str = "",
        sandbox_path: str = "",
    ) -> str:
        """
        Draft a structured Cline prompt using AI.

        Falls back to placeholder prompt on failure.

        Args:
            goal_text: The goal description
            safety_policy: Safety constraints text
            sandbox_path: Allowed sandbox directory

        Returns:
            Drafted prompt text
        """
        if not self.prompt_config.enabled:
            return self._placeholder_prompt(goal_text, sandbox_path, safety_policy)

        try:
            prompt = self._call_ai(
                system=self._prompt_drafter_system(),
                user=self._prompt_drafter_user(goal_text, sandbox_path, safety_policy),
                config=self.prompt_config,
            )
            if prompt and len(prompt) > 50:
                return prompt
        except Exception as e:
            logger.warning("AI prompt drafting failed, using fallback: %s", e)

        return self._placeholder_prompt(goal_text, sandbox_path, safety_policy)

    # ── Output Evaluation ────────────────────────────────────

    def evaluate_cline_output(
        self,
        run_id: str,
        goal_text: str,
        prompt_text: str,
        output_text: str,
        acceptance_criteria: list[str] = None,
    ) -> AIVerdict:
        """
        Evaluate Cline output using AI.

        Falls back to heuristic evaluation on failure.

        Args:
            run_id: Run identifier
            goal_text: The goal description
            prompt_text: The prompt given to Cline
            output_text: Cline's output
            acceptance_criteria: List of acceptance criteria

        Returns:
            AIVerdict object
        """
        if not self.eval_config.enabled:
            return self._heuristic_verdict(run_id, goal_text, output_text)

        try:
            response = self._call_ai(
                system=self._evaluator_system(),
                user=self._evaluator_user(
                    run_id, goal_text, prompt_text, output_text, acceptance_criteria or []
                ),
                config=self.eval_config,
            )
            if response:
                verdict = self._parse_ai_verdict(response, run_id, goal_text)
                if verdict:
                    return verdict
        except Exception as e:
            logger.warning("AI evaluation failed, using fallback: %s", e)

        return self._heuristic_verdict(run_id, goal_text, output_text)

    # ── AI API Call ──────────────────────────────────────────

    def _call_ai(
        self,
        system: str,
        user: str,
        config: AIConfig,
    ) -> str:
        """
        Call OpenRouter-compatible API.

        Returns:
            AI response text, or empty string on failure.
        """
        if not self._api_key:
            raise RuntimeError("OPENROUTER_API_KEY not set")

        import urllib.request
        import urllib.error

        url = config.api_url or self._api_url
        if not url:
            url = self._api_url

        payload = {
            "model": config.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "max_tokens": 2000,
            "temperature": 0.3,
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        timeout = config.timeout or 30
        start = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                elapsed = time.monotonic() - start
                logger.info("AI call completed in %.1fs", elapsed)
                return content or ""
        except urllib.error.URLError as e:
            raise RuntimeError(f"AI API call failed: {e}")
        except Exception as e:
            raise RuntimeError(f"AI API call error: {e}")

    # ── Prompt Drafter Prompts ───────────────────────────────

    def _prompt_drafter_system(self) -> str:
        return (
            "You are a prompt drafter for the MS-FA1 filesystem automation pipeline.\n"
            "Generate a structured Cline prompt for a sandbox task.\n"
            "The prompt must include all safety constraints and clear deliverables.\n"
            "Output the prompt as plain markdown text."
        )

    def _prompt_drafter_user(
        self,
        goal_text: str,
        sandbox_path: str,
        safety_policy: str,
    ) -> str:
        return (
            f"## Goal\n{goal_text}\n\n"
            f"## Sandbox Directory\n{sandbox_path}\n\n"
            f"## Safety Policy\n{safety_policy or 'Work only in sandbox. No production files. No config changes. No network calls.'}\n\n"
            "Generate a complete Cline prompt with:\n"
            "1. Goal description\n"
            "2. Allowed directory (sandbox only)\n"
            "3. Forbidden paths\n"
            "4. Required deliverables\n"
            "5. Test instructions\n"
            "6. Output/report location\n"
            "7. Safety constraints"
        )

    # ── Evaluator Prompts ────────────────────────────────────

    def _evaluator_system(self) -> str:
        return (
            "You are an evaluator for the MS-FA1 filesystem automation pipeline.\n"
            "Evaluate Cline's output against the goal and acceptance criteria.\n"
            "Be conservative: PASS only if evidence is clear.\n"
            "NEEDS_HUMAN on ambiguity, production file changes, path escape, missing tests, or unclear output.\n"
            "Return a valid JSON verdict object with these fields:\n"
            '{"run_id":"","goal":"","status":"PASS|FIX|STOP|NEEDS_HUMAN|ERROR",'
            '"confidence":0.0,"summary":"","evidence_files":[],"files_changed":[],'
            '"tests_run":[],"risks":[],"next_action":""}'
        )

    def _evaluator_user(
        self,
        run_id: str,
        goal_text: str,
        prompt_text: str,
        output_text: str,
        acceptance_criteria: list[str],
    ) -> str:
        criteria_text = "\n".join(f"- {c}" for c in acceptance_criteria) if acceptance_criteria else "None specified"
        return (
            f"## Run ID\n{run_id}\n\n"
            f"## Goal\n{goal_text}\n\n"
            f"## Prompt Given\n{prompt_text}\n\n"
            f"## Cline Output\n{output_text}\n\n"
            f"## Acceptance Criteria\n{criteria_text}\n\n"
            "Evaluate and return a JSON verdict."
        )

    # ── Verdict Parsing ──────────────────────────────────────

    def _parse_ai_verdict(self, response: str, run_id: str, goal: str) -> Optional[AIVerdict]:
        """Parse AI response into AIVerdict. Returns None if invalid."""
        try:
            # Try to extract JSON from response
            text = response.strip()
            # Handle markdown code blocks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            data = json.loads(text)
            status = data.get("status", "NEEDS_HUMAN").upper()
            if status not in ("PASS", "FIX", "STOP", "NEEDS_HUMAN", "ERROR"):
                status = "NEEDS_HUMAN"

            return AIVerdict(
                run_id=run_id,
                goal=goal,
                status=status,
                confidence=float(data.get("confidence", 0.5)),
                summary=data.get("summary", "AI evaluation"),
                evidence_files=data.get("evidence_files", []),
                files_changed=data.get("files_changed", []),
                tests_run=data.get("tests_run", []),
                risks=data.get("risks", []),
                next_action=data.get("next_action", ""),
            )
        except (json.JSONDecodeError, ValueError, KeyError):
            return None

    # ── Fallback: Placeholder Prompt ─────────────────────────

    def _placeholder_prompt(
        self,
        goal_text: str,
        sandbox_path: str,
        safety_policy: str,
    ) -> str:
        return (
            f"# Cline Prompt\n\n"
            f"## Goal\n{goal_text}\n\n"
            f"## Allowed Directory\n{sandbox_path}\n\n"
            f"## Forbidden Paths\n- Any path outside {sandbox_path}\n"
            "- No config, router, or server files\n"
            "- No production files\n\n"
            f"## Safety Constraints\n{safety_policy or 'Sandbox only. No network calls.'}\n\n"
            "## Deliverables\nCreate requested files in sandbox. Include unit tests.\n\n"
            "## Testing\nRun all tests. All must pass.\n\n"
            "## Final Output\nWrite report to cline_outbox/last_output.md\n"
        )

    # ── Fallback: Heuristic Verdict ──────────────────────────

    def _heuristic_verdict(self, run_id: str, goal: str, output: str) -> AIVerdict:
        """Conservative heuristic evaluation."""
        import re
        issues = []
        confidence = 1.0

        if len(output) < 50:
            issues.append("Output too short")
            confidence -= 0.3

        has_test_pass = bool(re.search(r"\bOK\b|\bPASSED\b|all.*pass", output, re.IGNORECASE))
        has_test_fail = bool(re.search(r"\bFAILED\b|\bERROR\b|\bfailures?\b", output, re.IGNORECASE))
        has_error = bool(re.search(r"\berror\b|\bexception\b|\btraceback\b", output, re.IGNORECASE))

        if has_test_fail:
            issues.append("Test failure detected")
            confidence -= 0.5
        if has_error:
            issues.append("Error pattern in output")
            confidence -= 0.3

        if confidence >= 0.8 and not issues:
            status = "PASS"
        elif has_test_fail:
            status = "FIX"
        else:
            status = "NEEDS_HUMAN"

        return AIVerdict(
            run_id=run_id,
            goal=goal,
            status=status,
            confidence=max(0.0, min(1.0, confidence)),
            summary=f"Heuristic evaluation: {status} (confidence {confidence:.2f})",
            risks=issues,
            next_action="Archive" if status == "PASS" else "Review",
        )