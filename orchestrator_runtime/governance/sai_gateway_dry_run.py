"""
sai_gateway_dry_run.py — SAI governance gateway dry-run adapter.

DRY RUN ONLY. Does NOT execute SuperIntelligentAI. Does NOT call any model API.
Does NOT write to cline_outbox.

Purpose:
  Prove that SAI execution requests can be routed through existing governance
  controls (risk_classifier, kill_switch, budget_manager) before SAI is touched.

Usage:
  python orchestrator_runtime/governance/sai_gateway_dry_run.py <goal_id>
  python orchestrator_runtime/governance/sai_gateway_dry_run.py --batch

Fail-closed: unknown mission_id → DENY (safe default).
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── Paths ──────────────────────────────────────────────────────────────
_GOVERNANCE = Path(__file__).parent
_ROOT = _GOVERNANCE.parent.parent
_GOAL_QUEUE = _ROOT / "orchestrator_runtime" / "goal_queue.json"

# ── Ensure governance modules are importable ───────────────────────────
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ── Internal helpers ───────────────────────────────────────────────────

def _load_goal_queue() -> dict[str, Any]:
    try:
        with _GOAL_QUEUE.open(encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as exc:
        return {"_load_error": str(exc), "goals": []}


def _check_kill_switch() -> dict[str, Any]:
    """Check kill switch. Returns {'active': bool, 'detail': str}."""
    try:
        from orchestrator_runtime.governance.kill_switch import KillSwitch
        ks = KillSwitch()
        active = ks.is_active()
        status = ks.status()
        return {
            "active": active,
            "detail": status.get("reason", "") if active else "inactive",
            "available": True,
        }
    except Exception as exc:
        return {"active": False, "detail": f"kill_switch unavailable: {exc}", "available": False}


def _check_budget() -> dict[str, Any]:
    """Check daily budget. Returns {'can_run': bool, 'remaining': int|None}."""
    try:
        from orchestrator_runtime.governance.budget_manager import BudgetManager
        bm = BudgetManager()
        can = bm.can_run()
        st = bm.state()
        limit = st.get("limit", "?")
        count = st.get("count", "?")
        remaining = (limit - count) if isinstance(limit, int) and isinstance(count, int) else None
        return {
            "can_run": bool(can),
            "remaining": remaining,
            "limit": limit,
            "count": count,
            "available": True,
        }
    except Exception as exc:
        return {"can_run": True, "remaining": None, "detail": f"budget_manager unavailable: {exc}", "available": False}


def _classify_goal(goal_id: str) -> dict[str, Any]:
    """Call risk_classifier. Returns classification dict."""
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


# ── Public API ─────────────────────────────────────────────────────────

def sai_gateway_dry_run(goal_id: str) -> dict[str, Any]:
    """
    Dry-run SAI governance gate for a given goal_id / mission_id.

    Returns a structured decision dict. NEVER executes SAI.
    Fail-closed: any unknown or unclassifiable goal_id → DENY.

    Return fields:
      mission_id          the input goal_id
      known_goal          whether goal_id found in goal_queue.json
      risk_level          LOW / MEDIUM / HIGH (from classifier, else HIGH)
      gateway_action      ALLOW | PAUSE | DENY
      would_execute_sai   always False (dry-run)
      reason              human-readable decision rationale
      checks              sub-results for each governance control
      dry_run             always True
      evaluated_at        ISO timestamp
    """
    evaluated_at = datetime.now(timezone.utc).isoformat()
    checks: dict[str, Any] = {}

    # ── Step 1: Kill switch ────────────────────────────────────────────
    ks = _check_kill_switch()
    checks["kill_switch"] = ks
    if ks["active"]:
        return {
            "mission_id": goal_id,
            "known_goal": False,
            "risk_level": "HIGH",
            "gateway_action": "DENY",
            "would_execute_sai": False,
            "reason": f"Kill switch is ACTIVE — all execution blocked. ({ks['detail']})",
            "checks": checks,
            "dry_run": True,
            "evaluated_at": evaluated_at,
        }

    # ── Step 2: Budget check ───────────────────────────────────────────
    budget = _check_budget()
    checks["budget"] = budget
    if not budget["can_run"]:
        return {
            "mission_id": goal_id,
            "known_goal": False,
            "risk_level": "HIGH",
            "gateway_action": "DENY",
            "would_execute_sai": False,
            "reason": f"Daily budget exhausted (remaining={budget.get('remaining', 0)}). Execution blocked.",
            "checks": checks,
            "dry_run": True,
            "evaluated_at": evaluated_at,
        }

    # ── Step 3: Goal queue lookup ──────────────────────────────────────
    queue = _load_goal_queue()
    goals = queue.get("goals", [])
    known_goal = any(g.get("id") == goal_id for g in goals)
    checks["goal_queue"] = {
        "looked_up": goal_id,
        "found": known_goal,
        "total_goals": len(goals),
        "load_error": queue.get("_load_error"),
    }

    # ── Step 4: Risk classification ────────────────────────────────────
    classification = _classify_goal(goal_id)
    checks["risk_classifier"] = {
        "available": classification["available"],
        "result": classification["result"],
    }
    cls = classification["result"]
    gateway_decision = cls.get("gateway_decision", "DENY")
    risk_level = cls.get("risk", "HIGH")
    reason = cls.get("reason", "No reason provided.")

    # ── Step 5: Compose decision ───────────────────────────────────────
    if not known_goal:
        # Fail-closed: unknown goal_id always DENY regardless of classifier
        # (classifier itself already returns DENY for unknown goals, but be explicit)
        gateway_decision = "DENY"
        risk_level = "HIGH"
        reason = (
            f"Goal ID '{goal_id}' not found in goal_queue.json. "
            f"Fail-closed: DENY by default. "
            f"Register goal in goal_queue.json to enable gateway evaluation."
        )

    return {
        "mission_id": goal_id,
        "known_goal": known_goal,
        "risk_level": risk_level,
        "gateway_action": gateway_decision,
        "would_execute_sai": False,  # DRY RUN — never True
        "reason": reason,
        "checks": checks,
        "dry_run": True,
        "evaluated_at": evaluated_at,
    }


# ── CLI ────────────────────────────────────────────────────────────────

_BATCH_CASES = [
    ("GOAL_007", "Known LOW-risk goal (Generate Progress Report)"),
    ("AO3_HARD_T3_HIGH", "Known HIGH-risk goal (Modify production config)"),
    ("SAI_FAKE_UNKNOWN_001", "Unknown fake mission_id"),
]


def _print_result(result: dict, label: str = "") -> None:
    sep = "─" * 60
    print(sep)
    if label:
        print(f"  CASE: {label}")
    print(f"  mission_id     : {result['mission_id']}")
    print(f"  known_goal     : {result['known_goal']}")
    print(f"  risk_level     : {result['risk_level']}")
    print(f"  gateway_action : {result['gateway_action']}")
    print(f"  would_exec_sai : {result['would_execute_sai']}")
    print(f"  dry_run        : {result['dry_run']}")
    print(f"  reason         : {result['reason']}")
    ks = result["checks"].get("kill_switch", {})
    bud = result["checks"].get("budget", {})
    rc = result["checks"].get("risk_classifier", {})
    gq = result["checks"].get("goal_queue", {})
    print(f"  checks:")
    print(f"    kill_switch  : active={ks.get('active')}  available={ks.get('available')}")
    print(f"    budget       : can_run={bud.get('can_run')}  remaining={bud.get('remaining')}  available={bud.get('available')}")
    print(f"    goal_queue   : found={gq.get('found')}  total={gq.get('total_goals')}")
    print(f"    risk_classif : available={rc.get('available')}  decision={rc.get('result',{}).get('gateway_decision')}")
    print(f"  evaluated_at   : {result['evaluated_at']}")
    print(sep)


def main() -> int:
    args = sys.argv[1:]

    if not args or "--batch" in args:
        print("SAI GATEWAY DRY-RUN — BATCH MODE")
        print("SuperIntelligentAI is NOT executed. DRY RUN ONLY.\n")
        for goal_id, label in _BATCH_CASES:
            result = sai_gateway_dry_run(goal_id)
            _print_result(result, label)
            print()
        return 0

    if "--json" in args:
        args.remove("--json")
        goal_id = args[0] if args else "UNKNOWN"
        result = sai_gateway_dry_run(goal_id)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    goal_id = args[0]
    result = sai_gateway_dry_run(goal_id)
    _print_result(result, f"Single dry-run: {goal_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
