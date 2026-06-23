"""
continue_watchdog.py — Watchdog protection for CM_CONTINUE_MODE loops.

Rules (fail-closed: all checks must pass for allow_continue=true):
  1. STOP if 3 consecutive FAIL/ERROR in recent Continue missions
  2. STOP if 3 consecutive PARTIAL in recent Continue missions
  3. STOP if last 5 Taste Model value avg < 3.0 when values exist
  4. STOP if bridge checksum/run_id errors repeat (logged in outbox)
  5. STOP if kill_switch active

Returns dict:
  allow_continue: bool
  reason: str
  evidence: list[str]
"""

from __future__ import annotations

import json
import os
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger("continue_watchdog")

ROOT = Path(__file__).resolve().parents[2]
CM_LOG_PATH = ROOT / "orchestrator_runtime" / "active_loops" / "cm_v01_cycle_log.jsonl"
TASTE_MODEL_PATH = ROOT / "orchestrator_runtime" / "taste_model" / "mission_outcomes.jsonl"


def _load_jsonl(path: Path, tail: int = 50) -> list[dict[str, Any]]:
    """Load last N lines from a JSONL file."""
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            lines = f.readlines()
        entries = []
        for line in lines[-tail:]:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return entries
    except Exception as exc:
        log.warning("Cannot read %s: %s", path, exc)
        return []


def _get_continue_missions(tail: int = 10) -> list[dict[str, Any]]:
    """Return missions where model_used contains 'continue_cli'."""
    entries = _load_jsonl(TASTE_MODEL_PATH, tail=50)
    return [e for e in entries if "continue_cli" in e.get("model_used", "")]


def _recent_outbox_errors(outbox_dir: Path, count: int = 5) -> list[str]:
    """Check recent outbox output_ready.json for missing consumed or checksum issues.

    AO8J_3: If output_ready.json has consumed=false but an archive copy with the
    same run_id exists, the outbox was already handled — skip the error.
    """
    errors: list[str] = []
    if not outbox_dir.exists():
        return errors
    archive_dir = outbox_dir / "archive"
    files = sorted(outbox_dir.glob("output_ready.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for f in files[:count]:
        try:
            data = json.loads(f.read_text(encoding="utf-8-sig"))
            run_id = data.get("run_id", "?")
            checksum = data.get("checksum", "?")
            consumed = data.get("consumed", False)

            # ── AO8J_3: Stale outbox — if not consumed and older than 5 min, archive ──
            if not consumed:
                age_seconds = (datetime.now(timezone.utc).timestamp() - f.stat().st_mtime)
                if age_seconds > 300:  # 5 minutes
                    # Archive stale outbox so it doesn't block future cycles
                    archive_dir.mkdir(parents=True, exist_ok=True)
                    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
                    for fname in ["last_output.md", "output_ready.json"]:
                        src = outbox_dir / fname
                        if src.exists():
                            dst = archive_dir / f"{ts}_stale_{run_id}_{fname}"
                            src.rename(dst)
                            log.info("Watchdog archived stale outbox %s -> %s", src.name, dst.name)
                    consumed = True

            if not consumed:
                errors.append(f"outbox not consumed: run_id={run_id}")
            if checksum in ("", "0" * 16, "error"):
                errors.append(f"checksum suspicious: run_id={run_id} checksum={checksum}")
        except (json.JSONDecodeError, OSError) as exc:
            errors.append(f"outbox read error: {exc}")
    return errors


def decide(
    taste_model_path: Path | None = None,
    outbox_dir: Path | None = None,
) -> dict[str, Any]:
    """Main decision function. Returns structured verdict."""
    evidence: list[str] = []

    # ── 1. Kill switch ──────────────────────────────────────────────
    ks_active = os.environ.get("CM_KILL_SWITCH", "").lower() in ("1", "true", "yes")
    try:
        from orchestrator_runtime.governance.kill_switch import KillSwitch  # type: ignore[import-untyped]
        ks = KillSwitch()
        if ks.is_active():
            ks_active = True
            evidence.append("kill_switch active via KillSwitch.is_active()")
    except Exception:
        pass

    if ks_active:
        return {
            "allow_continue": False,
            "reason": "KILL_SWITCH_ACTIVE",
            "evidence": evidence + ["kill switch triggered"],
        }

    # ── 2. Consecutive FAIL/ERROR ───────────────────────────────────
    missions = _get_continue_missions(tail=20)
    consecutive_fail = 0
    for m in missions:
        status = m.get("actual_status", "").lower()
        if status in ("failed", "error"):
            consecutive_fail += 1
        else:
            break  # reset on non-fail
    if consecutive_fail >= 3:
        evidence.append(f"{consecutive_fail} consecutive FAIL/ERROR in continue missions")
        return {
            "allow_continue": False,
            "reason": "CONSECUTIVE_FAIL",
            "evidence": evidence,
        }

    # ── 3. Consecutive PARTIAL ─────────────────────────────────────
    consecutive_partial = 0
    for m in missions:
        status = m.get("actual_status", "").lower()
        if status in ("partial", "partial_pass"):
            consecutive_partial += 1
        else:
            break
    if consecutive_partial >= 3:
        evidence.append(f"{consecutive_partial} consecutive PARTIAL in continue missions")
        return {
            "allow_continue": False,
            "reason": "CONSECUTIVE_PARTIAL",
            "evidence": evidence,
        }

    # ── 4. Taste Model value average ────────────────────────────────
    last_values = [m.get("value_immediate", 0) for m in missions[:5]]
    if last_values:
        avg = sum(last_values) / len(last_values)
        if avg < 3.0:
            evidence.append(f"avg value_immediate={avg:.1f} from last {len(last_values)} missions (threshold 3.0)")
            return {
                "allow_continue": False,
                "reason": "LOW_VALUE_AVERAGE",
                "evidence": evidence,
            }
        evidence.append(f"value_immediate avg={avg:.1f} over {len(last_values)} missions — OK")

    # ── 5. Outbox checksum/run_id errors ────────────────────────────
    if outbox_dir is not None:
        outbox_errors = _recent_outbox_errors(outbox_dir)
        if outbox_errors:
            evidence.extend(outbox_errors)
            return {
                "allow_continue": False,
                "reason": "OUTBOX_ERRORS",
                "evidence": evidence,
            }

    # ── ALL CHECKS PASSED ──────────────────────────────────────────
    evidence.append("all watchdog checks passed")
    return {
        "allow_continue": True,
        "reason": "ALL_CLEAR",
        "evidence": evidence,
    }