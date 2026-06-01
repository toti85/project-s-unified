"""
run_archive.py — Run Folder Creation, Archiving, and Retrieval

Responsibilities:
    - Create run folders under runs/{run_id}/
    - Archive completed runs
    - List available runs
    - Retrieve run metadata

Run folder structure:
    runs/{run_id}/
    ├── state.md         # State machine log
    ├── verdict.json     # Verdict for this run
    └── notes.md         # Human/evaluator notes

Status:
    - Scaffold only (Phase 0)
    - No deep logic implemented yet
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


# ── Constants ────────────────────────────────────────────────

RUNTIME_ROOT = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))) / "orchestrator_runtime"
RUNS_DIR = RUNTIME_ROOT / "runs"


# ── Implementation ───────────────────────────────────────────


def generate_next_run_id() -> str:
    """
    Generate the next available run ID based on existing runs.

    Format: FA1_NNN where NNN is the next sequential number.

    Returns:
        The next run ID string.
    """
    import re
    if not RUNS_DIR.exists():
        return "FA1_001"
    max_num = 0
    for d in RUNS_DIR.iterdir():
        if d.is_dir():
            m = re.match(r"FA(\d+)_(\d+)", d.name)
            if m and int(m.group(1)) == 1:
                max_num = max(max_num, int(m.group(2)))
    return f"FA1_{max_num + 1:03d}"


def create_run_folder(run_id: str) -> Path:
    """
    Create a new run folder with initial skeleton files.

    Creates:
        runs/{run_id}/state.md
        runs/{run_id}/notes.md

    Args:
        run_id: Unique run identifier (e.g., FA1_001)

    Returns:
        Path to the created run folder.
    """
    folder = RUNS_DIR / run_id
    folder.mkdir(parents=True, exist_ok=True)
    # Create initial state.md
    state_file = folder / "state.md"
    state_file.write_text(
        f"# Run State: {run_id}\n\n"
        f"Created: {datetime.utcnow().isoformat()}Z\n\n"
        f"## State History\n\n"
        f"- [{datetime.utcnow().isoformat()}Z] NEW_GOAL\n",
        encoding="utf-8"
    )
    # Create empty notes.md
    notes_file = folder / "notes.md"
    notes_file.write_text(f"# Run Notes: {run_id}\n\n", encoding="utf-8")
    return folder


def archive_run(run_id: str) -> Path:
    """
    Mark a run as archived by appending timestamp to state.md.

    Args:
        run_id: The run identifier

    Returns:
        Path to the archived run folder.
    """
    folder = RUNS_DIR / run_id
    if not folder.exists():
        raise FileNotFoundError(f"Run folder not found: {run_id}")
    state_file = folder / "state.md"
    if state_file.exists():
        state_file.write_text(
            state_file.read_text(encoding="utf-8") +
            f"\n- [{datetime.utcnow().isoformat()}Z] ARCHIVED\n",
            encoding="utf-8"
        )
    return folder


def list_runs() -> list[dict[str, Any]]:
    """
    List all available runs with their metadata.

    Returns:
        List of run dictionaries with run_id, state, and created_at.
    """
    if not RUNS_DIR.exists():
        return []
    runs = []
    for d in sorted(RUNS_DIR.iterdir()):
        if not d.is_dir():
            continue
        run_info = {"run_id": d.name, "state": "unknown", "created_at": ""}
        # Try to read state.json
        state_json = d / "state.json"
        if state_json.exists():
            data = json.loads(state_json.read_text(encoding="utf-8"))
            run_info["state"] = data.get("current_state", "unknown")
            run_info["created_at"] = data.get("updated_at", "")
        # Try to read verdict.json
        verdict_json = d / "verdict.json"
        if verdict_json.exists():
            vdata = json.loads(verdict_json.read_text(encoding="utf-8"))
            run_info["verdict"] = vdata.get("status", "unknown")
        runs.append(run_info)
    return runs


def get_run_folder(run_id: str) -> Optional[Path]:
    """
    Get the path to a run folder.

    Args:
        run_id: The run identifier

    Returns:
        Path to the run folder, or None if not found.
    """
    folder = RUNS_DIR / run_id
    return folder if folder.exists() else None


def get_run_status(run_id: str) -> Optional[str]:
    """
    Get the current state of a run.

    Args:
        run_id: The run identifier

    Returns:
        Current state string, or None if run not found.
    """
    state_json = RUNS_DIR / run_id / "state.json"
    if not state_json.exists():
        return None
    data = json.loads(state_json.read_text(encoding="utf-8"))
    return data.get("current_state")


def save_run_notes(run_id: str, notes: str) -> Path:
    """
    Save human/evaluator notes to a run's notes.md file.

    Args:
        run_id: The run identifier
        notes: The notes text to save

    Returns:
        Path to the saved notes file.
    """
    folder = RUNS_DIR / run_id
    folder.mkdir(parents=True, exist_ok=True)
    notes_file = folder / "notes.md"
    notes_file.write_text(notes, encoding="utf-8")
    return notes_file


def load_run_notes(run_id: str) -> Optional[str]:
    """
    Load notes from a run's notes.md file.

    Args:
        run_id: The run identifier

    Returns:
        The notes text, or None if not found.
    """
    notes_file = RUNS_DIR / run_id / "notes.md"
    if not notes_file.exists():
        return None
    return notes_file.read_text(encoding="utf-8")


def generate_evidence(run_id: str) -> str:
    """
    Generate evidence.md combining all run artifacts.

    Args:
        run_id: The run identifier

    Returns:
        Evidence markdown text.
    """
    folder = RUNS_DIR / run_id
    if not folder.exists():
        return f"# Evidence: {run_id}\n\nNo run folder found.\n"
    lines = [f"# Evidence: {run_id}", ""]
    for fname in ["goal.md", "prompt.md", "output.md", "verdict.json"]:
        fpath = folder / fname
        if fpath.exists():
            lines.append(f"## {fname}")
            lines.append("```")
            lines.append(fpath.read_text(encoding="utf-8").rstrip())
            lines.append("```")
            lines.append("")
    return "\n".join(lines)


# ── End of implementation ────────────────────────────────────
