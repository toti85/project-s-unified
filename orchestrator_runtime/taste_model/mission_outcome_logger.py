"""
mission_outcome_logger.py — Taste Model foundation logger.

Append-only JSONL ledger of mission outcomes.
Pure Python stdlib — no external dependencies.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── Paths ──────────────────────────────────────────────────────────────

_HERE = Path(__file__).parent
_LOG_FILE = _HERE / "mission_outcomes.jsonl"

# ── Valid enum values ──────────────────────────────────────────────────

_VALID_CLAIMED = {
    "completed", "partial", "partial_pass", "draft_only",
    "completed_but_no_push", "false_declaration", "blocked",
    "failed", "deception",
}
# actual_status may also include free-form like "draft_executed_as_t37"
_VALID_ACTUAL = _VALID_CLAIMED | {"deception", "partial_pass"}

_VALID_RUNTIME = {True, False, "partial"}

_MISSION_ID_RE = re.compile(r"^[A-Z0-9_\-]+$")


# ── Public API ─────────────────────────────────────────────────────────

def get_log_path() -> Path:
    """Return the absolute path to mission_outcomes.jsonl."""
    return _LOG_FILE


def validate_record(record: dict[str, Any]) -> None:
    """
    Validate a mission outcome record dict.
    Raises ValueError with a descriptive message on the first failing check.
    """
    required = {
        "mission_id", "date", "claimed_status", "actual_status",
        "model_used", "runtime_validated", "value_immediate",
        "patterns", "notes", "logged_at",
    }
    missing = required - record.keys()
    if missing:
        raise ValueError(f"Missing required fields: {sorted(missing)}")

    mid = record["mission_id"]
    if not isinstance(mid, str) or not _MISSION_ID_RE.match(mid):
        raise ValueError(f"mission_id must be an uppercase alphanumeric string, got: {mid!r}")

    date = record["date"]
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except (ValueError, TypeError):
        raise ValueError(f"date must be YYYY-MM-DD, got: {date!r}")

    claimed = record["claimed_status"]
    if claimed not in _VALID_CLAIMED:
        # allow draft_executed_as_t<N> style
        if not (isinstance(claimed, str) and claimed.startswith("draft_executed_as_")):
            raise ValueError(f"claimed_status invalid: {claimed!r}")

    actual = record["actual_status"]
    if actual not in _VALID_ACTUAL:
        if not (isinstance(actual, str) and actual.startswith("draft_executed_as_")):
            raise ValueError(f"actual_status invalid: {actual!r}")

    rv = record["runtime_validated"]
    if rv not in _VALID_RUNTIME:
        raise ValueError(f"runtime_validated must be true/false/'partial', got: {rv!r}")

    vi = record["value_immediate"]
    if not isinstance(vi, int) or not (1 <= vi <= 5):
        raise ValueError(f"value_immediate must be int 1-5, got: {vi!r}")

    patterns = record["patterns"]
    if not isinstance(patterns, list) or not all(isinstance(p, str) for p in patterns):
        raise ValueError("patterns must be a list of strings")

    notes = record["notes"]
    if not isinstance(notes, str) or len(notes) > 200:
        raise ValueError(f"notes must be a string ≤200 chars, got length {len(notes)!r}")


def log_outcome(
    mission_id: str,
    date: str,
    claimed_status: str,
    actual_status: str,
    model_used: str,
    runtime_validated: "bool | str",
    value_immediate: int,
    patterns: "list[str]",
    notes: str,
    logged_at: "str | None" = None,
) -> dict[str, Any]:
    """
    Append one mission outcome record to mission_outcomes.jsonl.

    Returns the written record dict.
    Raises ValueError if the record fails validation.
    NEVER overwrites or edits existing records — always appends.
    """
    if logged_at is None:
        logged_at = datetime.now(timezone.utc).isoformat()

    record: dict[str, Any] = {
        "mission_id": mission_id,
        "date": date,
        "claimed_status": claimed_status,
        "actual_status": actual_status,
        "model_used": model_used,
        "runtime_validated": runtime_validated,
        "value_immediate": value_immediate,
        "patterns": patterns,
        "notes": notes,
        "logged_at": logged_at,
    }

    validate_record(record)

    log_path = get_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    line = json.dumps(record, ensure_ascii=False)
    with open(log_path, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")

    return record


def load_all() -> list[dict[str, Any]]:
    """Load all records from mission_outcomes.jsonl. Returns empty list if file absent."""
    log_path = get_log_path()
    if not log_path.exists():
        return []
    records = []
    with open(log_path, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Corrupt JSONL at line {lineno}: {exc}") from exc
    return records


# ── CLI entrypoint (basic self-test) ──────────────────────────────────

if __name__ == "__main__":
    import sys

    if "--selftest" in sys.argv:
        r = log_outcome(
            mission_id="TEST_SELFTEST",
            date="2026-06-15",
            claimed_status="completed",
            actual_status="completed",
            model_used="selftest",
            runtime_validated=True,
            value_immediate=3,
            patterns=["selftest"],
            notes="logger self-test record",
        )
        print("Logged:", json.dumps(r, ensure_ascii=False))
        records = load_all()
        print(f"Total records in log: {len(records)}")
    else:
        print(f"Log path: {get_log_path()}")
        records = load_all()
        print(f"Records in log: {len(records)}")
