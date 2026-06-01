"""
filesystem_orchestrator.py — Goal/Prompt Lifecycle Management

Responsibilities:
    - Read goal from inbox/goal.md
    - Draft Cline prompt into cline_inbox/next_prompt.md
    - Read Cline output from cline_outbox/last_output.md
    - Coordinate with state_machine for lifecycle transitions
    - Orchestrate the full semi-automated loop

Runtime paths:
    - inbox/goal.md
    - cline_inbox/next_prompt.md
    - cline_outbox/last_output.md

Status:
    - FA1.2: Fully implemented (placeholder prompt/eval logic)
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


from .state_machine import RunState, StateMachine

logger = logging.getLogger(__name__)
from .verdict_schema import VerdictStatus


# ── Constants ────────────────────────────────────────────────

RUNTIME_ROOT = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))) / "orchestrator_runtime"


# ── Data Models ──────────────────────────────────────────────


@dataclass
class Goal:
    """Represents a parsed goal from inbox/goal.md."""
    text: str
    acceptance_criteria: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    raw: str = ""


@dataclass
class Verdict:
    """Represents an evaluation verdict."""
    run_id: str
    goal: str
    status: VerdictStatus
    confidence: float
    summary: str
    evidence_files: list[str] = field(default_factory=list)
    files_changed: list[str] = field(default_factory=list)
    tests_run: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    next_action: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat() + "Z"


# ── FilesystemOrchestrator ───────────────────────────────────


class FilesystemOrchestrator:
    """
    Semi-automated filesystem orchestrator for MS-FA1.

    Coordinates the full loop:
        1. Read goal from inbox
        2. Draft prompt (placeholder)
        3. Human review gate
        4. Wait for Cline output
        5. Evaluate output (placeholder)
        6. Human review gate
        7. Issue verdict
        8. Archive run
    """

    def __init__(self, runtime_root: Optional[Path] = None):
        self.runtime_root = runtime_root or RUNTIME_ROOT
        self.runs_dir = self.runtime_root / "runs"
        self.inbox = self.runtime_root / "inbox"
        self.cline_inbox = self.runtime_root / "cline_inbox"
        self.cline_outbox = self.runtime_root / "cline_outbox"
        self.sandbox = self.runtime_root / "sandbox"
        self._current_run_id: Optional[str] = None
        self._state_machine: Optional[StateMachine] = None

    # ── Goal reading ─────────────────────────────────────────

    def read_goal(self) -> Optional[Goal]:
        """
        Read the current goal from inbox/goal.md.

        Returns:
            Parsed Goal object, or None if file is empty/missing.
        """
        goal_path = self.inbox / "goal.md"
        if not goal_path.exists():
            return None

        raw = goal_path.read_text(encoding="utf-8").strip()
        if not raw:
            return None

        # Parse acceptance criteria (markdown checklist items)
        criteria = []
        for line in raw.splitlines():
            m = re.match(r"-\s*\[.\]\s*(.+)", line)
            if m:
                criteria.append(m.group(1).strip())

        # Parse constraints
        constraints = []
        in_constraints = False
        for line in raw.splitlines():
            if "## Constraints" in line or "### Constraints" in line:
                in_constraints = True
                continue
            if in_constraints and line.startswith("##"):
                in_constraints = False
            if in_constraints and line.strip().startswith("-"):
                constraints.append(line.strip()[1:].strip())

        # Extract main text (first non-header, non-list paragraph)
        text = raw.split("\n\n")[0]
        # Strip headers
        text = re.sub(r"^#+\s*", "", text).strip()

        return Goal(
            text=text or "Sandbox task",
            acceptance_criteria=criteria,
            constraints=constraints,
            raw=raw,
        )

    # ── Run creation ─────────────────────────────────────────

    def create_run(self, goal: Goal) -> str:
        """
        Create a new run folder and initialize state machine.

        Args:
            goal: The parsed goal

        Returns:
            The new run_id (e.g., FA1_002)
        """
        run_id = self._generate_next_run_id()
        run_folder = self.runs_dir / run_id
        run_folder.mkdir(parents=True, exist_ok=True)

        # Save goal to run folder
        goal_file = run_folder / "goal.md"
        goal_file.write_text(goal.raw or goal.text, encoding="utf-8")

        # Initialize state machine
        sm = StateMachine(run_id=run_id)
        sm._persist()  # Save initial state

        self._current_run_id = run_id
        self._state_machine = sm

        return run_id

    # ── Config loading ───────────────────────────────────────

    def _load_orchestrator_config(self) -> dict[str, Any]:
        """Load orchestrator config from config.json."""
        config_path = self.runtime_root / "config.json"
        if config_path.exists():
            return json.loads(config_path.read_text(encoding="utf-8"))
        return {}

    # ── Prompt drafting (AI-integrated with deterministic fallback) ──

    def draft_prompt(self, run_id: Optional[str] = None, auto_mode: bool = True) -> str:
        """
        Draft a Cline prompt from the run's goal.

        Uses AI-based prompt drafting if enabled in config.json,
        falls back to deterministic template on any failure.

        Args:
            run_id: Run to draft for (defaults to current)
            auto_mode: If True (default), skip HUMAN_REVIEW for sandbox tasks.
                      If False, always pause at HUMAN_REVIEW.

        Returns:
            The drafted prompt text
        """
        run_id = run_id or self._current_run_id
        if not run_id:
            raise RuntimeError("No active run. Call create_run() first.")

        self._load_state_machine(run_id)

        goal_path = self.runs_dir / run_id / "goal.md"
        goal_text = goal_path.read_text(encoding="utf-8").strip() if goal_path.exists() else "Sandbox task"

        # Build safety policy text
        safety_policy = (
            f"Work only in sandbox: {self.sandbox}\n"
            "Do NOT modify any files outside the sandbox\n"
            "Do NOT modify any config, router, or server files\n"
            "Do NOT make external network calls"
        )

        # Try AI-based prompt drafting if enabled in config
        config = self._load_orchestrator_config()
        prompt_drafter_config = config.get("prompt_drafter", {})
        ai_enabled = prompt_drafter_config.get("enabled", False)

        if ai_enabled:
            try:
                from .ai_client import OrchestratorAIClient, AIConfig
                ai_prompt_config = AIConfig(
                    enabled=True,
                    provider=prompt_drafter_config.get("provider", "openrouter"),
                    model=prompt_drafter_config.get("model", "qwen/qwen3.6-35b-a3b"),
                    timeout=30,
                    fallback_on_error=config.get("fallback_on_error", True),
                )
                ai_client = OrchestratorAIClient(prompt_config=ai_prompt_config)
                ai_prompt = ai_client.draft_cline_prompt(
                    goal_text=goal_text,
                    safety_policy=safety_policy,
                    sandbox_path=str(self.sandbox),
                )
                # Validate AI prompt contains required sections
                if self._prompt_has_required_sections(ai_prompt, self.sandbox):
                    prompt = ai_prompt
                    draft_method = "ai"
                else:
                    prompt = self._deterministic_prompt(run_id, goal_text, self.sandbox, self.cline_outbox)
                    draft_method = "deterministic (AI prompt missing required sections)"
            except Exception as e:
                logger.warning("AI prompt drafting failed, using deterministic fallback: %s", e)
                prompt = self._deterministic_prompt(run_id, goal_text, self.sandbox, self.cline_outbox)
                draft_method = "deterministic (AI failed)"
        else:
            prompt = self._deterministic_prompt(run_id, goal_text, self.sandbox, self.cline_outbox)
            draft_method = "deterministic (AI disabled)"

        # Save to run folder
        (self.runs_dir / run_id / "prompt.md").write_text(prompt, encoding="utf-8")

        # Copy to cline_inbox
        self.cline_inbox.mkdir(parents=True, exist_ok=True)
        (self.cline_inbox / "next_prompt.md").write_text(prompt, encoding="utf-8")

        # State transition
        self._state_machine.transition(RunState.PROMPT_DRAFTED, f"Prompt drafted ({draft_method})")

        # Auto mode: skip HUMAN_REVIEW for sandbox tasks
        if auto_mode:
            self._state_machine.transition(RunState.IN_PROGRESS, "Auto mode: sandbox task, skipping human review")
        else:
            self._state_machine.transition(RunState.HUMAN_REVIEW, "Awaiting human review")

        return prompt

    def _prompt_has_required_sections(self, prompt: str, sandbox_path: Path) -> bool:
        """Validate that a prompt contains all required safety sections."""
        prompt_lower = prompt.lower()
        sandbox_str = str(sandbox_path).lower()
        # Check for allowed directory reference
        has_sandbox = sandbox_str in prompt_lower or "sandbox" in prompt_lower
        # Check for forbidden paths
        has_forbidden = "forbidden" in prompt_lower or "do not" in prompt_lower or "not modify" in prompt_lower
        # Check for deliverables
        has_deliverables = "deliverable" in prompt_lower or "create" in prompt_lower
        # Check for testing
        has_testing = "test" in prompt_lower
        # Check for output location
        has_output = "output" in prompt_lower or "report" in prompt_lower or "last_output" in prompt_lower
        return has_sandbox and has_forbidden and has_deliverables and has_testing and has_output

    def _deterministic_prompt(
        self,
        run_id: str,
        goal_text: str,
        sandbox: Path,
        cline_outbox: Path,
    ) -> str:
        """Generate a deterministic prompt template (fallback)."""
        return f"""# Cline Prompt: {run_id}

**Run ID:** {run_id}
**Drafted:** {datetime.utcnow().isoformat()}Z

---

## INSTRUCTIONS

**IMPORTANT: Read all instructions before starting.**

### SAFETY BOUNDARY — DO NOT VIOLATE

- You may **ONLY** modify files under `{sandbox}`
- Do **NOT** modify any files outside the sandbox
- Do **NOT** modify any config, router, or server files
- Do **NOT** make external network calls

### TASK

{goal_text}

### Deliverables

Create the requested files in the sandbox directory.
Include unit tests where applicable.

### Testing

- Run all tests before completing
- All tests must pass

### Final Output

After completing the task, write your final report to:

```
{cline_outbox / "last_output.md"}
```

The report must include:
- What was created/modified
- Test results
- Any issues encountered
- Files changed (full paths)

---
"""

    # ── Cline output handling ────────────────────────────────

    def mark_in_progress(self, run_id: Optional[str] = None) -> None:
        """Mark run as in progress (after human review)."""
        run_id = run_id or self._current_run_id
        self._load_state_machine(run_id)
        self._state_machine.transition(RunState.IN_PROGRESS, "Human approved, Cline executing")

    def receive_output(self, run_id: Optional[str] = None) -> Optional[str]:
        """
        Read Cline output from cline_outbox/last_output.md.

        Args:
            run_id: Run to receive for

        Returns:
            Output text, or None if not yet written
        """
        run_id = run_id or self._current_run_id
        output_path = self.cline_outbox / "last_output.md"

        if not output_path.exists():
            return None

        content = output_path.read_text(encoding="utf-8").strip()
        if not content:
            return None

        # Save to run folder
        (self.runs_dir / run_id / "output.md").write_text(content, encoding="utf-8")

        # State transition
        self._load_state_machine(run_id)
        self._state_machine.transition(RunState.CLINE_OUTPUT_RECEIVED, "Cline output received")

        return content

    def wait_for_cline_output(self, run_id: Optional[str] = None, timeout: Optional[int] = None, poll_interval: float = 2.0) -> Optional[str]:
        """
        Poll for Cline output.

        Args:
            run_id: Run to wait for
            timeout: Seconds to wait (None = wait forever)
            poll_interval: Seconds between polls

        Returns:
            Output text, or None on timeout
        """
        start = time.monotonic()
        while True:
            output = self.receive_output(run_id)
            if output:
                return output
            if timeout and (time.monotonic() - start) >= timeout:
                return None
            time.sleep(poll_interval)

    # ── Evaluation (AI-integrated with heuristic fallback) ───

    def evaluate_output(self, run_id: Optional[str] = None) -> Verdict:
        """
        Evaluate Cline output using AI if enabled, heuristic fallback otherwise.

        Uses AI-based evaluation if verdict_evaluator.enabled in config.json.
        Falls back to heuristic evaluation on any AI failure.

        Args:
            run_id: Run to evaluate

        Returns:
            Verdict object
        """
        run_id = run_id or self._current_run_id
        self._load_state_machine(run_id)

        # Read output
        output_path = self.runs_dir / run_id / "output.md"
        output_text = output_path.read_text(encoding="utf-8") if output_path.exists() else ""

        # Read goal for acceptance criteria
        goal_path = self.runs_dir / run_id / "goal.md"
        goal_text = goal_path.read_text(encoding="utf-8") if goal_path.exists() else ""

        # Read prompt if available
        prompt_path = self.runs_dir / run_id / "prompt.md"
        prompt_text = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else ""

        # Parse acceptance criteria from goal
        acceptance_criteria = []
        for line in goal_text.splitlines():
            m = re.match(r"-\s*\[.\]\s*(.+)", line)
            if m:
                acceptance_criteria.append(m.group(1).strip())

        # Try AI-based evaluation if enabled in config
        config = self._load_orchestrator_config()
        eval_config = config.get("verdict_evaluator", {})
        ai_eval_enabled = eval_config.get("enabled", False)

        if ai_eval_enabled:
            try:
                from .ai_client import OrchestratorAIClient, AIConfig as AIClientConfig
                ai_client_config = AIClientConfig(
                    enabled=True,
                    provider=eval_config.get("provider", "openrouter"),
                    model=eval_config.get("model", "qwen/qwen3.6-35b-a3b"),
                    timeout=30,
                    fallback_on_error=config.get("fallback_on_error", True),
                )
                ai_client = OrchestratorAIClient(eval_config=ai_client_config)
                ai_verdict = ai_client.evaluate_cline_output(
                    run_id=run_id,
                    goal_text=goal_text,
                    prompt_text=prompt_text,
                    output_text=output_text,
                    acceptance_criteria=acceptance_criteria,
                )
                # Validate verdict status is valid
                if ai_verdict.status in ("PASS", "FIX", "STOP", "NEEDS_HUMAN", "ERROR"):
                    verdict = Verdict(
                        run_id=ai_verdict.run_id,
                        goal=ai_verdict.goal,
                        status=VerdictStatus(ai_verdict.status),
                        confidence=ai_verdict.confidence,
                        summary=ai_verdict.summary,
                        evidence_files=ai_verdict.evidence_files,
                        files_changed=ai_verdict.files_changed,
                        tests_run=ai_verdict.tests_run,
                        risks=ai_verdict.risks,
                        next_action=ai_verdict.next_action,
                    )
                    eval_method = "ai"
                else:
                    raise ValueError(f"Invalid verdict status: {ai_verdict.status}")
            except Exception as e:
                logger.warning("AI evaluation failed, using heuristic fallback: %s", e)
                verdict = self._heuristic_evaluate(run_id, goal_text, output_text)
                eval_method = "heuristic (AI failed)"
        else:
            verdict = self._heuristic_evaluate(run_id, goal_text, output_text)
            eval_method = "heuristic (AI disabled)"

        # State transition
        self._state_machine.transition(RunState.EVALUATING_OUTPUT, f"Evaluating output ({eval_method})")

        return verdict

    def _heuristic_evaluate(self, run_id: str, goal_text: str, output_text: str) -> Verdict:
        """
        Conservative heuristic evaluator.

        Rules:
        - Output must be non-empty (> 50 chars)
        - If tests mentioned, "OK" or "PASSED" pattern found
        - No obvious error patterns
        - If uncertain → NEEDS_HUMAN
        """
        issues = []
        confidence = 1.0

        # Check output length
        if len(output_text) < 50:
            issues.append("Output too short (< 50 chars)")
            confidence -= 0.3

        # Check for test success patterns
        has_test_mention = bool(re.search(r"test|unittest|pytest", output_text, re.IGNORECASE))
        has_test_pass = bool(re.search(r"\bOK\b|\bPASSED\b|all.*pass", output_text, re.IGNORECASE))
        has_test_fail = bool(re.search(r"\bFAILED\b|\bERROR\b|\bfailures?\b", output_text, re.IGNORECASE))

        if has_test_mention and not has_test_pass:
            issues.append("Tests mentioned but no pass pattern found")
            confidence -= 0.4

        if has_test_fail:
            issues.append("Test failure pattern detected")
            confidence -= 0.5

        # Check for error patterns
        has_error = bool(re.search(r"\berror\b|\bexception\b|\btraceback\b", output_text, re.IGNORECASE))
        if has_error:
            issues.append("Error/exception pattern in output")
            confidence -= 0.3

        # Determine status
        if confidence >= 0.8 and not issues:
            status = VerdictStatus.PASS
        elif confidence >= 0.5:
            status = VerdictStatus.NEEDS_HUMAN
        else:
            status = VerdictStatus.FIX if has_test_fail else VerdictStatus.NEEDS_HUMAN

        # Conservative: if uncertain, default to NEEDS_HUMAN
        if issues and not has_test_fail:
            status = VerdictStatus.NEEDS_HUMAN

        return Verdict(
            run_id=run_id,
            goal=goal_text[:200],
            status=status,
            confidence=max(0.0, min(1.0, confidence)),
            summary=f"Placeholder evaluation: {status.value} (confidence {confidence:.2f})",
            risks=issues,
            next_action=self._suggest_next_action(status),
        )

    def _suggest_next_action(self, status: VerdictStatus) -> str:
        if status == VerdictStatus.PASS:
            return "Archive run and proceed to next task."
        elif status == VerdictStatus.FIX:
            return "Review issues, fix, and re-run."
        elif status == VerdictStatus.NEEDS_HUMAN:
            return "Human review required before proceeding."
        else:
            return "Stop and investigate."

    # ── Verdict issuance ─────────────────────────────────────

    def issue_verdict(self, run_id: Optional[str] = None, verdict: Optional[Verdict] = None) -> Verdict:
        """
        Issue and save a verdict for a run.

        Args:
            run_id: Run to issue verdict for
            verdict: Verdict to save (auto-evaluate if None)

        Returns:
            The issued verdict
        """
        run_id = run_id or self._current_run_id
        self._load_state_machine(run_id)

        if verdict is None:
            verdict = self.evaluate_output(run_id)

        # Save verdict.json
        verdict_path = self.runs_dir / run_id / "verdict.json"
        verdict_data = {
            "run_id": verdict.run_id,
            "goal": verdict.goal,
            "status": verdict.status.value,
            "confidence": verdict.confidence,
            "summary": verdict.summary,
            "evidence_files": verdict.evidence_files,
            "files_changed": verdict.files_changed,
            "tests_run": verdict.tests_run,
            "risks": verdict.risks,
            "next_action": verdict.next_action,
            "created_at": verdict.created_at,
        }
        verdict_path.write_text(
            json.dumps(verdict_data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        # State transition
        self._state_machine.transition(RunState.VERDICT_ISSUED, f"Verdict: {verdict.status.value}")

        return verdict

    # ── Archiving ────────────────────────────────────────────

    def archive_run(self, run_id: Optional[str] = None) -> Path:
        """
        Archive a completed run.

        Args:
            run_id: Run to archive

        Returns:
            Path to the archived run folder
        """
        run_id = run_id or self._current_run_id
        self._load_state_machine(run_id)

        # Generate evidence.md
        evidence = self._generate_evidence(run_id)
        (self.runs_dir / run_id / "evidence.md").write_text(evidence, encoding="utf-8")

        # Final state transition
        self._state_machine.transition(RunState.ARCHIVED, "Run archived")

        return self.runs_dir / run_id

    def _generate_evidence(self, run_id: str) -> str:
        """Generate evidence.md combining all run artifacts."""
        run_folder = self.runs_dir / run_id
        lines = [f"# Evidence: {run_id}", ""]

        for fname in ["goal.md", "prompt.md", "output.md", "verdict.json"]:
            fpath = run_folder / fname
            if fpath.exists():
                lines.append(f"## {fname}")
                lines.append("```")
                lines.append(fpath.read_text(encoding="utf-8").rstrip())
                lines.append("```")
                lines.append("")

        return "\n".join(lines)

    # ── Iteration support ────────────────────────────────────

    def _get_iter_folder(self, run_id: str, iter_num: int) -> Path:
        """Get path to iteration folder."""
        iter_dir = self.runs_dir / run_id / "iterations" / f"iter_{iter_num:03d}"
        iter_dir.mkdir(parents=True, exist_ok=True)
        return iter_dir

    def save_iteration(self, run_id: str, iter_num: int, prompt: str, output: str, verdict: Verdict) -> Path:
        """Save iteration artifacts."""
        folder = self._get_iter_folder(run_id, iter_num)
        (folder / "prompt.md").write_text(prompt, encoding="utf-8")
        (folder / "output.md").write_text(output, encoding="utf-8")
        (folder / "verdict.json").write_text(
            json.dumps({
                "run_id": verdict.run_id,
                "goal": verdict.goal,
                "status": verdict.status.value,
                "confidence": verdict.confidence,
                "summary": verdict.summary,
                "risks": verdict.risks,
                "next_action": verdict.next_action,
            }, indent=2) + "\n",
            encoding="utf-8",
        )
        return folder

    def generate_fix_prompt(self, run_id: str, previous_output: str, verdict: Verdict) -> str:
        """
        Generate a follow-up correction prompt for FIX verdicts.

        Uses AI prompt drafter if available, falls back to deterministic prompt.
        """
        goal_path = self.runs_dir / run_id / "goal.md"
        goal_text = goal_path.read_text(encoding="utf-8") if goal_path.exists() else "Unknown goal"

        # Try AI-based fix prompt
        try:
            from .ai_client import OrchestratorAIClient, AIConfig
            ai_client = OrchestratorAIClient(
                prompt_config=AIConfig(enabled=False),  # Use deterministic for reliability
                eval_config=AIConfig(enabled=False),
            )
        except ImportError:
            ai_client = None

        unmet = "; ".join(verdict.risks) if verdict.risks else "Criteria not fully met"

        fix_prompt = (
            f"# Cline Fix Prompt: {run_id}\n\n"
            f"## Original Goal\n{goal_text}\n\n"
            f"## Previous Output Summary\n{previous_output[:500]}\n\n"
            f"## Failed/Unmet Criteria\n{unmet}\n\n"
            f"## Previous Verdict\n{verdict.status.value} (confidence: {verdict.confidence:.2f})\n\n"
            f"## Allowed Directory\n{self.sandbox}\n\n"
            f"## Forbidden Paths\n- Any path outside {self.sandbox}\n"
            "- No config, router, or server files\n"
            "- No production files\n\n"
            "## Instructions\n"
            "1. Review the previous output and identify what needs to be fixed.\n"
            "2. Modify only files in the sandbox directory.\n"
            "3. Fix the issues listed in Failed/Unmet Criteria.\n"
            "4. Run all tests. All must pass.\n"
            "5. Write updated report to cline_outbox/last_output.md.\n"
        )
        return fix_prompt

    def save_final_verdict(self, run_id: str, verdict: Verdict) -> Path:
        """Save final verdict for a run."""
        path = self.runs_dir / run_id / "final_verdict.json"
        path.write_text(
            json.dumps({
                "run_id": verdict.run_id,
                "goal": verdict.goal,
                "status": verdict.status.value,
                "confidence": verdict.confidence,
                "summary": verdict.summary,
                "evidence_files": verdict.evidence_files,
                "files_changed": verdict.files_changed,
                "tests_run": verdict.tests_run,
                "risks": verdict.risks,
                "next_action": verdict.next_action,
                "created_at": verdict.created_at,
            }, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return path

    # ── Full loop with iterations (for CLI) ──────────────────

    def run_loop(
        self,
        goal_text: Optional[str] = None,
        max_iterations: int = 2,
    ) -> dict[str, Any]:
        """
        Execute the full multi-iteration loop.

        Args:
            goal_text: Optional goal text (reads from inbox if None)
            max_iterations: Maximum number of iterations (default 2)

        Returns:
            Dict with run_id, verdict, iterations, and summary
        """
        # Step 1: Read goal
        if goal_text:
            goal = Goal(text=goal_text, raw=goal_text)
            self.inbox.mkdir(parents=True, exist_ok=True)
            (self.inbox / "goal.md").write_text(goal_text, encoding="utf-8")
        else:
            goal = self.read_goal()
            if not goal:
                raise RuntimeError("No goal found in inbox/goal.md")

        # Step 2: Create run
        run_id = self.create_run(goal)

        # Load goal text for prompts
        goal_path = self.runs_dir / run_id / "goal.md"
        goal_text_actual = goal_path.read_text(encoding="utf-8") if goal_path.exists() else goal.text

        iterations_done = 0
        final_verdict = None

        for iter_num in range(1, max_iterations + 1):
            iterations_done = iter_num

            # Draft prompt (initial or fix)
            if iter_num == 1:
                prompt = self.draft_prompt(run_id, auto_mode=True)
            else:
                # FIX iteration — generate fix prompt
                prompt = self.generate_fix_prompt(run_id, final_verdict.summary if final_verdict else "", final_verdict or Verdict(
                    run_id=run_id, goal=goal_text_actual,
                    status=VerdictStatus.FIX, confidence=0.5, summary="Previous iteration needs fix"
                ))
                # Save fix prompt
                (self.runs_dir / run_id / "prompt.md").write_text(prompt, encoding="utf-8")
                (self.cline_inbox / "next_prompt.md").write_text(prompt, encoding="utf-8")
                # Transition state for new iteration
                self._load_state_machine(run_id)
                # Reset state machine for new iteration if archived
                if self._state_machine.current_state == RunState.ARCHIVED:
                    self._state_machine.current_state = RunState.PROMPT_DRAFTED
                    self._state_machine._persist()
                elif self._state_machine.can_transition(RunState.PROMPT_DRAFTED):
                    self._state_machine.transition(RunState.PROMPT_DRAFTED, f"Fix iteration {iter_num}")
                self._state_machine.transition(RunState.IN_PROGRESS, f"Fix iteration {iter_num} in progress")

            # Receive output
            output = self.receive_output(run_id)
            if not output:
                output = f"No output received for iteration {iter_num}"
                (self.cline_outbox / "last_output.md").write_text(output, encoding="utf-8")
                output = self.receive_output(run_id)

            # Evaluate
            verdict = self.evaluate_output(run_id)

            # Save iteration artifacts
            self.save_iteration(run_id, iter_num, prompt, output or "", verdict)

            final_verdict = verdict

            # Check verdict
            if verdict.status == VerdictStatus.PASS:
                self.issue_verdict(run_id, verdict=verdict)
                self.archive_run(run_id)
                break
            elif verdict.status in (VerdictStatus.NEEDS_HUMAN, VerdictStatus.STOP, VerdictStatus.ERROR):
                self.issue_verdict(run_id, verdict=verdict)
                break
            elif verdict.status == VerdictStatus.FIX and iter_num >= max_iterations:
                # Max iterations reached — escalate
                final_verdict = Verdict(
                    run_id=run_id,
                    goal=verdict.goal,
                    status=VerdictStatus.NEEDS_HUMAN,
                    confidence=verdict.confidence,
                    summary=f"Max iterations ({max_iterations}) reached. FIX verdict persisted.",
                    risks=verdict.risks + ["Max iterations exhausted"],
                    next_action="Human review required.",
                )
                self.issue_verdict(run_id, verdict=final_verdict)
                break
            else:
                # FIX and more iterations allowed — continue loop
                self.issue_verdict(run_id, verdict=verdict)
                continue

        # Save final verdict
        if final_verdict:
            self.save_final_verdict(run_id, final_verdict)

        return {
            "run_id": run_id,
            "verdict": final_verdict.status.value if final_verdict else "UNKNOWN",
            "iterations": iterations_done,
            "max_iterations": max_iterations,
            "confidence": final_verdict.confidence if final_verdict else 0.0,
        }

    # ── Helpers ──────────────────────────────────────────────

    def _generate_next_run_id(self) -> str:
        """Generate next FA1_NNN run ID."""
        if not self.runs_dir.exists():
            return "FA1_001"

        max_num = 0
        for d in self.runs_dir.iterdir():
            if d.is_dir():
                m = re.match(r"FA(\d+)_(\d+)", d.name)
                if m and int(m.group(1)) == 1:
                    max_num = max(max_num, int(m.group(2)))

        return f"FA1_{max_num + 1:03d}"

    def _load_state_machine(self, run_id: str) -> None:
        """Load or create state machine for a run."""
        if self._state_machine and self._state_machine.run_id == run_id:
            return
        self._state_machine = StateMachine.load(run_id)
        self._current_run_id = run_id



