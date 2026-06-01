"""
cline_bridge.py — Filesystem-based Bridge to Cline

No UI automation in FA1.2.
Just file I/O coordination between orchestrator and Cline.

Status:
    - FA1.2: Fully implemented (placeholder)
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Optional


# ── Constants ────────────────────────────────────────────────

RUNTIME_ROOT = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))) / "orchestrator_runtime"


class ClineBridge:
    """
    Filesystem-based bridge to Cline.

    Coordinates file I/O:
        - Write prompts to cline_inbox/next_prompt.md
        - Read output from cline_outbox/last_output.md
        - Poll for output readiness
    """

    def __init__(self, runtime_root: Optional[Path] = None):
        self.runtime_root = runtime_root or RUNTIME_ROOT
        self.cline_inbox = self.runtime_root / "cline_inbox"
        self.cline_outbox = self.runtime_root / "cline_outbox"
        self._current_run_id: Optional[str] = None

    def write_prompt(self, prompt_text: str, run_id: str) -> Path:
        """
        Write a prompt to cline_inbox/next_prompt.md with metadata header.

        Args:
            prompt_text: The prompt content
            run_id: Current run identifier

        Returns:
            Path to the written prompt file
        """
        self.cline_inbox.mkdir(parents=True, exist_ok=True)
        self._current_run_id = run_id

        prompt_path = self.cline_inbox / "next_prompt.md"
        prompt_path.write_text(prompt_text, encoding="utf-8")
        return prompt_path

    def read_output(self) -> Optional[str]:
        """
        Read Cline output from cline_outbox/last_output.md.

        Returns:
            Output text, or None if file doesn't exist or is empty
        """
        output_path = self.cline_outbox / "last_output.md"
        if not output_path.exists():
            return None

        content = output_path.read_text(encoding="utf-8").strip()
        if not content:
            return None
        return content

    def clear_output(self, backup_path: Optional[Path] = None) -> None:
        """
        Clear last_output.md after receiving it.

        Args:
            backup_path: Optional path to backup output to first
        """
        output_path = self.cline_outbox / "last_output.md"
        if not output_path.exists():
            return

        # Backup if requested
        if backup_path:
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            backup_path.write_text(
                output_path.read_text(encoding="utf-8"),
                encoding="utf-8",
            )

        # Clear the file (write empty placeholder)
        output_path.write_text("# Awaiting Cline Output\n\nOutput will appear here after Cline execution.\n", encoding="utf-8")

    def is_output_ready(self) -> bool:
        """
        Check if last_output.md exists and has content.

        Returns:
            True if output is ready to be read
        """
        output_path = self.cline_outbox / "last_output.md"
        if not output_path.exists():
            return False

        content = output_path.read_text(encoding="utf-8").strip()
        # Check it's not just the placeholder
        return len(content) > 50