"""
state_machine.py — Run State Transitions and Tracking

Responsibilities:
    - Define valid run states
    - Track state transitions for a run
    - Persist state to runs/{run_id}/state.json (atomic write)
    - Raise StateTransitionError on invalid transitions

States:
    NEW_GOAL → PROMPT_DRAFTED → HUMAN_REVIEW → IN_PROGRESS
    → CLINE_OUTPUT_RECEIVED → EVALUATING_OUTPUT → VERDICT_ISSUED → ARCHIVED

Status:
    - FA1.2: Fully implemented
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Tuple


logger = logging.getLogger(__name__)


# ── Constants ────────────────────────────────────────────────

RUNTIME_ROOT = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))) / "orchestrator_runtime"
RUNS_DIR = RUNTIME_ROOT / "runs"


# ── Exceptions ───────────────────────────────────────────────


class StateTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""

    def __init__(self, from_state: str, to_state: str, run_id: str = ""):
        self.from_state = from_state
        self.to_state = to_state
        self.run_id = run_id
        msg = f"Invalid transition: {from_state} → {to_state}"
        if run_id:
            msg += f" (run {run_id})"
        super().__init__(msg)


# ── State Definitions ────────────────────────────────────────


class RunState(str, Enum):
    """Valid states for a run in the MS-FA1 pipeline."""

    NEW_GOAL = "NEW_GOAL"
    PROMPT_DRAFTED = "PROMPT_DRAFTED"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    IN_PROGRESS = "IN_PROGRESS"
    CLINE_OUTPUT_RECEIVED = "CLINE_OUTPUT_RECEIVED"
    EVALUATING_OUTPUT = "EVALUATING_OUTPUT"
    VERDICT_ISSUED = "VERDICT_ISSUED"
    ARCHIVED = "ARCHIVED"


# Valid transitions: from_state → [to_states]
VALID_TRANSITIONS: dict[RunState, list[RunState]] = {
    RunState.NEW_GOAL: [RunState.PROMPT_DRAFTED],
    RunState.PROMPT_DRAFTED: [RunState.HUMAN_REVIEW, RunState.IN_PROGRESS],  # IN_PROGRESS for auto mode
    RunState.HUMAN_REVIEW: [RunState.IN_PROGRESS],
    RunState.IN_PROGRESS: [RunState.CLINE_OUTPUT_RECEIVED],
    RunState.CLINE_OUTPUT_RECEIVED: [RunState.EVALUATING_OUTPUT],
    RunState.EVALUATING_OUTPUT: [RunState.VERDICT_ISSUED],
    RunState.VERDICT_ISSUED: [RunState.ARCHIVED],
    RunState.ARCHIVED: [],
}


# ── StateMachine ─────────────────────────────────────────────


class StateMachine:
    """Manages state transitions for a single run."""

    def __init__(self, run_id: str, current_state: RunState = RunState.NEW_GOAL, runs_dir: Optional[Path] = None):
        self.run_id = run_id
        self.current_state = current_state
        self.history: list[dict[str, Any]] = []
        self._runs_dir = runs_dir or RUNS_DIR
        self._record_initial()

    # ── Core transitions ─────────────────────────────────────

    def transition(self, new_state: RunState, reason: str = "") -> bool:
        """
        Transition to a new state.

        Args:
            new_state: Target state
            reason: Optional human-readable reason

        Returns:
            True if transition succeeded

        Raises:
            StateTransitionError: If transition is invalid
        """
        if not self.can_transition(new_state):
            raise StateTransitionError(
                from_state=self.current_state.value,
                to_state=new_state.value,
                run_id=self.run_id,
            )

        old_state = self.current_state
        self.current_state = new_state
        entry = {
            "from": old_state.value,
            "to": new_state.value,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "reason": reason,
        }
        self.history.append(entry)
        self._persist()
        logger.info("State transition: %s → %s (run %s)", old_state.value, new_state.value, self.run_id)
        return True

    def can_transition(self, target: RunState) -> bool:
        """Check if a transition to *target* is allowed from the current state."""
        allowed = VALID_TRANSITIONS.get(self.current_state, [])
        return target in allowed

    # ── Persistence ──────────────────────────────────────────

    def _record_initial(self) -> None:
        """Record the initial state in history."""
        self.history.append({
            "from": None,
            "to": self.current_state.value,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "reason": "Run created",
        })

    def _persist(self) -> None:
        """Atomically write state.json to the run folder."""
        run_folder = self._runs_dir / self.run_id
        run_folder.mkdir(parents=True, exist_ok=True)
        state_path = run_folder / "state.json"

        data = {
            "run_id": self.run_id,
            "current_state": self.current_state.value,
            "history": self.history,
            "updated_at": datetime.utcnow().isoformat() + "Z",
        }

        # Atomic write: temp file → rename
        fd, tmp_path = tempfile.mkstemp(dir=str(run_folder), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, str(state_path))
        except Exception:
            # Clean up temp file on failure
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    @classmethod
    def load(cls, run_id: str, runs_dir: Optional[Path] = None) -> "StateMachine":
        """
        Load a StateMachine from runs/{run_id}/state.json.

        Args:
            run_id: The run identifier
            runs_dir: Optional custom runs directory

        Returns:
            Restored StateMachine instance

        Raises:
            FileNotFoundError: If state.json does not exist
        """
        state_path = (runs_dir or RUNS_DIR) / run_id / "state.json"
        if not state_path.exists():
            raise FileNotFoundError(f"State file not found for run {run_id}: {state_path}")

        with open(state_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        sm = cls.__new__(cls)
        sm.run_id = run_id
        sm.current_state = RunState(data["current_state"])
        sm.history = data.get("history", [])
        sm._runs_dir = runs_dir or RUNS_DIR
        return sm

    # ── Inspection ───────────────────────────────────────────

    def get_history(self) -> list[dict[str, Any]]:
        """Return the full state transition history."""
        return list(self.history)

    def __repr__(self) -> str:
        return f"<StateMachine run={self.run_id} state={self.current_state.value}>"
