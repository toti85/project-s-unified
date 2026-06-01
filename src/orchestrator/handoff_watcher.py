"""
handoff_watcher.py — File-Based Handoff Polling for MS-FA1

Responsibilities:
    - Write prompt_ready.json when prompt is drafted
    - Watch for output_ready.json from Cline
    - Validate run_id / iteration
    - Read last_output.md
    - Trigger evaluator
    - Continue loop or archive

No UI automation. No keyboard/mouse. No VS Code automation.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .state_machine import RunState
from .verdict_schema import VerdictStatus

logger = logging.getLogger(__name__)


# ── Data Models ──────────────────────────────────────────────


@dataclass
class HandoffSignal:
    """Handoff protocol signal."""
    run_id: str
    iteration: int
    timestamp: str
    status: str  # "ready" | "consumed"
    checksum: str = ""
    consumed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "iteration": self.iteration,
            "timestamp": self.timestamp,
            "status": self.status,
            "checksum": self.checksum,
            "consumed": self.consumed,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HandoffSignal":
        return cls(
            run_id=data.get("run_id", ""),
            iteration=data.get("iteration", 1),
            timestamp=data.get("timestamp", ""),
            status=data.get("status", "ready"),
            checksum=data.get("checksum", ""),
            consumed=data.get("consumed", False),
        )


# ── HandoffWatcher ───────────────────────────────────────────


class HandoffWatcher:
    """
    File-based handoff polling between Project-S and Cline.

    Watches for output_ready.json, validates, reads output,
    triggers evaluation, and continues the loop.
    """

    def __init__(self, runtime_root: Optional[Path] = None):
        from .filesystem_orchestrator import RUNTIME_ROOT
        self.runtime_root = runtime_root or RUNTIME_ROOT
        self.cline_inbox = self.runtime_root / "cline_inbox"
        self.cline_outbox = self.runtime_root / "cline_outbox"

    # ── Prepare Handoff (Project-S → Cline) ──────────────────

    def prepare_handoff(self, run_id: str, iteration: int, prompt_text: str) -> Path:
        """
        Write prompt_ready.json to signal Cline that a prompt is ready.

        Args:
            run_id: Run identifier
            iteration: Current iteration number
            prompt_text: The prompt text

        Returns:
            Path to prompt_ready.json
        """
        checksum = hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()[:16]
        signal = HandoffSignal(
            run_id=run_id,
            iteration=iteration,
            timestamp=datetime.utcnow().isoformat() + "Z",
            status="ready",
            checksum=checksum,
        )
        path = self.cline_inbox / "prompt_ready.json"
        path.write_text(json.dumps(signal.to_dict(), indent=2) + "\n", encoding="utf-8")
        logger.info("Handoff prepared: %s iter %d", run_id, iteration)
        return path

    # ── Consume Output (Cline → Project-S) ───────────────────

    def consume_output(self, run_id: str, expected_iteration: int) -> Optional[str]:
        """
        Read and consume output_ready.json + last_output.md.

        Args:
            run_id: Expected run ID
            expected_iteration: Expected iteration number

        Returns:
            Output text, or None if not ready/valid
        """
        ready_path = self.cline_outbox / "output_ready.json"
        if not ready_path.exists():
            return None

        data = json.loads(ready_path.read_text(encoding="utf-8"))
        signal = HandoffSignal.from_dict(data)

        # Validate run_id
        if signal.run_id != run_id:
            logger.warning("Run ID mismatch: expected %s, got %s", run_id, signal.run_id)
            return None

        # Validate iteration
        if signal.iteration != expected_iteration:
            logger.warning(
                "Iteration mismatch for %s: expected %d, got %d",
                run_id, expected_iteration, signal.iteration,
            )
            return None

        # Check if already consumed
        if signal.consumed:
            logger.info("Output already consumed for %s iter %d", run_id, signal.iteration)
            return None

        # Mark as consumed
        signal.consumed = True
        signal.status = "consumed"
        ready_path.write_text(json.dumps(signal.to_dict(), indent=2) + "\n", encoding="utf-8")

        # Read output
        output_path = self.cline_outbox / "last_output.md"
        if not output_path.exists():
            logger.warning("output_ready.json exists but last_output.md missing")
            return None

        output_text = output_path.read_text(encoding="utf-8").strip()

        # Validate checksum if present
        if signal.checksum:
            actual_checksum = hashlib.sha256(output_text.encode("utf-8")).hexdigest()[:16]
            if actual_checksum != signal.checksum:
                logger.warning("Checksum mismatch for %s", run_id)
                # Don't fail on checksum mismatch — just warn

        logger.info("Output consumed: %s iter %d", run_id, signal.iteration)
        return output_text

    # ── Watch for Output ─────────────────────────────────────

    def watch_for_output(
        self,
        run_id: str,
        iteration: int,
        timeout: int = 300,
        poll_interval: float = 3.0,
    ) -> Optional[str]:
        """
        Poll for output_ready.json with timeout.

        Args:
            run_id: Expected run ID
            iteration: Expected iteration
            timeout: Seconds to wait (default 5 min)
            poll_interval: Seconds between polls

        Returns:
            Output text, or None on timeout
        """
        start = time.monotonic()
        while (time.monotonic() - start) < timeout:
            output = self.consume_output(run_id, iteration)
            if output is not None:
                return output
            time.sleep(poll_interval)

        logger.warning("Watch timeout for %s iter %d after %.0fs", run_id, iteration, timeout)
        return None

    # ── Check if Output Ready ────────────────────────────────

    def is_output_ready(self, run_id: str, iteration: int) -> bool:
        """Check if output_ready.json exists and matches run_id/iteration."""
        ready_path = self.cline_outbox / "output_ready.json"
        if not ready_path.exists():
            return False
        try:
            data = json.loads(ready_path.read_text(encoding="utf-8"))
            signal = HandoffSignal.from_dict(data)
            return (
                signal.run_id == run_id
                and signal.iteration == iteration
                and not signal.consumed
            )
        except (json.JSONDecodeError, KeyError):
            return False

    # ── Write Output Ready (for testing/simulation) ──────────

    def write_output_ready(self, run_id: str, iteration: int, output_text: str) -> Path:
        """
        Write output_ready.json (used by Cline or for testing).

        Args:
            run_id: Run identifier
            iteration: Iteration number
            output_text: The output text

        Returns:
            Path to output_ready.json
        """
        checksum = hashlib.sha256(output_text.encode("utf-8")).hexdigest()[:16]
        signal = HandoffSignal(
            run_id=run_id,
            iteration=iteration,
            timestamp=datetime.utcnow().isoformat() + "Z",
            status="ready",
            checksum=checksum,
        )
        path = self.cline_outbox / "output_ready.json"
        path.write_text(json.dumps(signal.to_dict(), indent=2) + "\n", encoding="utf-8")
        return path