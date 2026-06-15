"""
sai_gateway_adapter.py — SAI governance gateway adapter (production).

Provides:
  sai_pre_execution_gate(mission_id, goal_id)  → structured gate decision
  write_sai_output_to_outbox(mission_id, content, iteration, metadata)  → RISK_010 compliant write
  build_sai_handoff_content(mission_id, result)  → markdown summary

Design rules:
  - No SAI execution, no model API calls, no SuperIntelligentAI instantiation.
  - Fail-closed: unknown mission_id → DENY.
  - All exceptions return structured error dict, never propagate to caller.
  - RISK_010 strictly enforced: last_output.md FIRST, checksum, output_ready.json LAST.

Usage:
  from orchestrator_runtime.governance.sai_gateway_adapter import (
      sai_pre_execution_gate, write_sai_output_to_outbox, build_sai_handoff_content
  )
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── Paths ──────────────────────────────────────────────────────────────
_GOVERNANCE = Path(__file__).parent
_ROOT = _GOVERNANCE.parent.parent
_CLINE_OUTBOX = _ROOT / "orchestrator_runtime" / "cline_outbox"
_GOAL_QUEUE = _ROOT / "orchestrator_runtime" / "goal_queue.json"

if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ── Internal helpers ───────────────────────────────────────────────────

def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_file_16(path: Path) -> str:
    """SHA-256 of file bytes, first 16 hex chars — matches bridge_runner.compute_checksum."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def _check_kill_switch() -> dict[str, Any]:
    try:
        from orchestrator_runtime.governance.kill_switch import KillSwitch
        ks = KillSwitch()
        active = ks.is_active()
        return {"active": active, "detail": ks.status().get("reason", "") if active else "inactive", "available": True}
    except Exception as exc:
        return {"active": False, "detail": f"unavailable: {exc}", "available": False}


def _check_budget() -> dict[str, Any]:
    try:
        from orchestrator_runtime.governance.budget_manager import BudgetManager
        bm = BudgetManager()
        remaining = bm.remaining()
        can = remaining > 0
        return {"can_run": can, "remaining": remaining, "available": True}
    except Exception as exc:
        return {"can_run": True, "remaining": None, "available": False, "detail": str(exc)}


def _classify(goal_id: str) -> dict[str, Any]:
    try:
        from orchestrator_runtime.governance.risk_classifier import classify_execution_request
        result = classify_execution_request(goal_id)
        return {"available": True, "result": result}
    except Exception as exc:
        return {
            "available": False,
            "result": {
                "goal_id": goal_id,
                "risk": "HIGH",
                "gateway_decision": "DENY",
                "reason": f"risk_classifier unavailable ({exc}); fail-closed DENY.",
            },
        }


def _goal_known(goal_id: str) -> bool:
    try:
        with _GOAL_QUEUE.open(encoding="utf-8") as fh:
            data = json.load(fh)
        return any(g.get("id") == goal_id for g in data.get("goals", []))
    except Exception:
        return False


# ── Public API: Gate ───────────────────────────────────────────────────

def sai_pre_execution_gate(
    mission_id: str,
    goal_id: str | None = None,
) -> dict[str, Any]:
    """
    Classify an SAI execution request through all governance controls.

    Parameters
    ----------
    mission_id : str
        The SAI mission identifier (used for logging / output_ready.json).
    goal_id : str | None
        The goal_queue.json entry to classify against. Defaults to mission_id.
        For SAI missions with UUID-style IDs, pass the corresponding goal_id explicitly.

    Returns
    -------
    dict with keys:
      allowed          bool   — True only if gateway_action == ALLOW
      gateway_action   str    — ALLOW | PAUSE | DENY
      risk_level       str    — LOW | MEDIUM | HIGH
      reason           str
      mission_id       str
      goal_id          str
      checks           dict   — per-control sub-results
      evaluated_at     str    — ISO timestamp

    Fail-closed: unknown goal_id → DENY, never raises.
    Does NOT execute SAI. Does NOT instantiate SuperIntelligentAI.
    """
    effective_goal = goal_id or mission_id
    evaluated_at = _ts()
    checks: dict[str, Any] = {}

    try:
        # ── Gate 0: Kill switch ────────────────────────────────────────
        ks = _check_kill_switch()
        checks["kill_switch"] = ks
        if ks["active"]:
            return {
                "allowed": False,
                "gateway_action": "DENY",
                "risk_level": "HIGH",
                "reason": f"Kill switch ACTIVE — all execution blocked. ({ks['detail']})",
                "mission_id": mission_id,
                "goal_id": effective_goal,
                "checks": checks,
                "evaluated_at": evaluated_at,
            }

        # ── Gate 1: Budget ─────────────────────────────────────────────
        budget = _check_budget()
        checks["budget"] = budget
        if not budget["can_run"]:
            return {
                "allowed": False,
                "gateway_action": "DENY",
                "risk_level": "HIGH",
                "reason": f"Daily budget exhausted (remaining={budget.get('remaining', 0)}).",
                "mission_id": mission_id,
                "goal_id": effective_goal,
                "checks": checks,
                "evaluated_at": evaluated_at,
            }

        # ── Gate 2: Goal queue lookup ──────────────────────────────────
        known = _goal_known(effective_goal)
        checks["goal_queue"] = {"found": known, "looked_up": effective_goal}

        # ── Gate 3: Risk classification ────────────────────────────────
        cls_result = _classify(effective_goal)
        checks["risk_classifier"] = {"available": cls_result["available"], "result": cls_result["result"]}
        cls = cls_result["result"]
        gateway_action = cls.get("gateway_decision", "DENY")
        risk_level = cls.get("risk", "HIGH")
        reason = cls.get("reason", "No reason provided.")

        # ── Fail-closed override for unknown goals ─────────────────────
        if not known:
            gateway_action = "DENY"
            risk_level = "HIGH"
            reason = (
                f"Goal '{effective_goal}' not found in goal_queue.json. "
                f"Fail-closed DENY. Register goal to enable gateway evaluation."
            )

        return {
            "allowed": gateway_action == "ALLOW",
            "gateway_action": gateway_action,
            "risk_level": risk_level,
            "reason": reason,
            "mission_id": mission_id,
            "goal_id": effective_goal,
            "checks": checks,
            "evaluated_at": evaluated_at,
        }

    except Exception as exc:
        # Absolute fallback — fail-closed
        return {
            "allowed": False,
            "gateway_action": "DENY",
            "risk_level": "HIGH",
            "reason": f"Gateway evaluation crashed ({exc}); fail-closed DENY.",
            "mission_id": mission_id,
            "goal_id": effective_goal,
            "checks": checks,
            "evaluated_at": evaluated_at,
        }


# ── Public API: Output writer ──────────────────────────────────────────

def write_sai_output_to_outbox(
    mission_id: str,
    content: str,
    iteration: int = 1,
    metadata: dict[str, Any] | None = None,
    goal_id: str | None = None,
) -> dict[str, Any]:
    """
    Write SAI execution result to FA1_HANDOFF_V1 format so bridge_runner can consume it.

    RISK_010 order strictly enforced:
      1. last_output.md written FIRST
      2. SHA-256 checksum computed from the final file bytes
      3. output_ready.json written LAST (consumed=false)

    Parameters
    ----------
    mission_id : str        Used as run_id fallback if goal_id is not provided.
    content    : str        The SAI execution output (markdown).
    iteration  : int        Expected iteration number (default 1).
    metadata   : dict       Optional extra fields merged into output_ready.json.
    goal_id    : str | None When provided, used as run_id instead of mission_id so
                            bridge_runner can match it against goal_queue.json and
                            proceed to the verdict step without a DENY.

    Returns
    -------
    dict with keys:
      success     bool
      run_id      str
      checksum    str    — first 16 hex chars of SHA-256(last_output.md)
      last_output_path   str
      output_ready_path  str
      error       str | None
    """
    try:
        _CLINE_OUTBOX.mkdir(parents=True, exist_ok=True)

        last_output_path = _CLINE_OUTBOX / "last_output.md"
        output_ready_path = _CLINE_OUTBOX / "output_ready.json"

        # ── Step 1: Write last_output.md FIRST ────────────────────────
        last_output_path.write_text(content, encoding="utf-8")

        # ── Step 2: Compute checksum from FINAL file bytes ────────────
        checksum = _sha256_file_16(last_output_path)

        # ── Step 3: Write output_ready.json LAST ──────────────────────
        run_id = goal_id if goal_id else mission_id
        ready: dict[str, Any] = {
            "run_id": run_id,
            "iteration": iteration,
            "timestamp": _ts(),
            "status": "ready",
            "checksum": checksum,
            "consumed": False,
        }
        if metadata:
            ready.update(metadata)

        tmp = output_ready_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(ready, indent=4, ensure_ascii=False), encoding="utf-8")
        tmp.replace(output_ready_path)  # atomic rename

        return {
            "success": True,
            "run_id": run_id,
            "checksum": checksum,
            "last_output_path": str(last_output_path),
            "output_ready_path": str(output_ready_path),
            "error": None,
        }

    except Exception as exc:
        return {
            "success": False,
            "run_id": goal_id if goal_id else mission_id,
            "checksum": None,
            "last_output_path": None,
            "output_ready_path": None,
            "error": str(exc),
        }


# ── Public API: Content builder ────────────────────────────────────────

def build_sai_handoff_content(mission_id: str, result: dict[str, Any]) -> str:
    """
    Build a markdown handoff document from a SAI execution result dict.

    Parameters
    ----------
    mission_id : str
    result     : dict   SAI result with keys like 'output', 'success', 'error'.

    Returns
    -------
    str  — markdown content ready for last_output.md
    """
    success = result.get("success", False)
    output = result.get("output", "")
    error = result.get("error", "")
    replan_count = result.get("replan_count", 0)
    status_label = "COMPLETE" if success else "FAILED"

    lines = [
        f"# SAI Mission {mission_id} — {status_label}",
        "",
        f"**run_id:** {mission_id}",
        f"**generated:** {_ts()}",
        f"**success:** {success}",
        f"**replan_count:** {replan_count}",
        "",
        "## Output",
        "",
        output if output else "(no output)",
    ]
    if error:
        lines += ["", "## Error", "", error]

    extras = {k: v for k, v in result.items() if k not in {"output", "success", "error", "replan_count", "evaluation_result"}}
    if extras:
        lines += ["", "## Metadata", "", f"```json", json.dumps(extras, indent=2, ensure_ascii=False, default=str), "```"]

    return "\n".join(lines) + "\n"


# ── CLI self-test ──────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    goal = sys.argv[1] if len(sys.argv) > 1 else "GOAL_007"
    mission = sys.argv[2] if len(sys.argv) > 2 else goal
    print(f"sai_pre_execution_gate({mission!r}, goal_id={goal!r})")
    decision = sai_pre_execution_gate(mission, goal_id=goal)
    print(json.dumps(decision, indent=2, ensure_ascii=False))
