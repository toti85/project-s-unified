"""
MS-AO1 Risk Classifier — AO1.2
Classifies goals from goal_queue.json and determines auto-approval eligibility.

Rules:
  LOW  + auto_approve=true  → APPROVED
  LOW  + auto_approve=false → PENDING_HUMAN
  MEDIUM → PENDING_HUMAN
  HIGH   → PENDING_HUMAN

Usage:
  from orchestrator_runtime.governance.risk_classifier import classify_goal
  result = classify_goal("GOAL_007")
"""

import json
from pathlib import Path
from datetime import datetime, timezone

GOAL_QUEUE_PATH = Path(__file__).parent.parent.parent / "orchestrator_runtime" / "goal_queue.json"
APPROVAL_LOG_PATH = Path(__file__).parent / "approval_log.json"

# AO2.2 notification integration (lazy import — fails gracefully)
try:
    from orchestrator_runtime.governance.notifier import Notifier
    _NOTIFIER = Notifier()
except ImportError:
    _NOTIFIER = None


def _notify(event_type, goal_id=None, message=""):
    """Send notification if notifier available."""
    if _NOTIFIER is not None:
        try:
            _NOTIFIER.notify(event_type, goal_id=goal_id, message=message)
        except Exception:
            pass


def load_goal_queue():
    """Load goal_queue.json and return parsed data."""
    with open(GOAL_QUEUE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_approval_log():
    """Load or initialize approval_log.json."""
    if APPROVAL_LOG_PATH.exists():
        with open(APPROVAL_LOG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"entries": []}


def save_approval_log(log_data):
    """Save approval_log.json atomically."""
    tmp_path = APPROVAL_LOG_PATH.with_suffix(".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)
    # Windows: rename cannot overwrite, so remove target first if it exists
    if APPROVAL_LOG_PATH.exists():
        APPROVAL_LOG_PATH.unlink()
    tmp_path.rename(APPROVAL_LOG_PATH)


# Production-touching keywords — if rationale contains any, goal is NOT sandbox-only
_PRODUCTION_KEYWORDS = [
    "self_state.json", "src/", "config/", "interactive_layer",
    "router/", "camera", "API key", "secret",
]

# Keywords that indicate production touch ONLY when NOT in negative context
_PRODUCTION_CONTEXT_KEYWORDS = [
    "production", "server",
]

# Negative context patterns that negate production keywords
_NEGATIVE_PATTERNS = [
    "no production", "not production", "no server", "not server",
    "without production", "without touching", "no ... touched",
]


def _is_sandbox_only(rationale):
    """Check if a goal's rationale indicates sandbox-only work."""
    if not rationale:
        return True  # Default: assume sandbox-only if no rationale
    lower = rationale.lower()

    # Check direct production keywords (always indicate non-sandbox)
    for kw in _PRODUCTION_KEYWORDS:
        if kw.lower() in lower:
            return False

    # Check context-dependent keywords (only if not in negative context)
    for kw in _PRODUCTION_CONTEXT_KEYWORDS:
        if kw.lower() in lower:
            # Check if it's in a negative context
            is_negative = any(pat.replace("...", "").strip() in lower for pat in _NEGATIVE_PATTERNS)
            if not is_negative:
                return False

    return True


def _normalize_risk(value):
    """Normalize risk string to LOW/MEDIUM/HIGH with HIGH as safe default."""
    risk = str(value or "HIGH").upper().strip()
    if risk not in {"LOW", "MEDIUM", "HIGH"}:
        return "HIGH"
    return risk


def classify_goal_record(goal: dict, goal_id: str = "UNKNOWN") -> dict:
    """
    Classify an in-memory goal record into explicit gateway behavior.

    Gateway policy:
      LOW    -> ALLOW (auto-approve)
      MEDIUM -> PAUSE (manual approval required)
      HIGH   -> DENY (blocked)
    """
    if not goal:
        return {
            "goal_id": goal_id,
            "title": "UNKNOWN",
            "risk": "HIGH",
            "sandbox_only": False,
            "gateway_decision": "DENY",
            "decision": "BLOCKED_POLICY",
            "reason": "Goal record missing. Default deny for safety.",
            "classified_at": datetime.now(timezone.utc).isoformat(),
        }

    risk = _normalize_risk(goal.get("risk", "HIGH"))
    rationale = goal.get("rationale", "")
    sandbox_only = _is_sandbox_only(rationale)

    if risk == "LOW":
        gateway_decision = "ALLOW"
        decision = "APPROVED"
        reason = "LOW risk request auto-approved by gateway policy."
    elif risk == "MEDIUM":
        gateway_decision = "PAUSE"
        decision = "PENDING_HUMAN"
        reason = "MEDIUM risk request paused for explicit human approval."
    else:
        gateway_decision = "DENY"
        decision = "BLOCKED_POLICY"
        reason = "HIGH risk request is blocked by policy."

    return {
        "goal_id": goal.get("id", goal_id),
        "title": goal.get("title", ""),
        "risk": risk,
        "sandbox_only": sandbox_only,
        "gateway_decision": gateway_decision,
        "decision": decision,
        "reason": reason,
        "classified_at": datetime.now(timezone.utc).isoformat(),
    }


def classify_execution_request(goal_id: str) -> dict:
    """Classify an execution request by goal_id using goal_queue.json."""
    queue = load_goal_queue()
    goal = None
    candidates = [goal_id]
    if isinstance(goal_id, str) and goal_id.startswith("AO3_"):
        candidates.append(goal_id[4:])

    for g in queue.get("goals", []):
        gid = g.get("id")
        if gid in candidates:
            goal = g
            break

    if goal is None:
        result = {
            "goal_id": goal_id,
            "title": "UNKNOWN",
            "risk": "HIGH",
            "sandbox_only": False,
            "gateway_decision": "DENY",
            "decision": "BLOCKED_POLICY",
            "reason": f"Goal {goal_id} not found in goal_queue.json. Default deny.",
            "classified_at": datetime.now(timezone.utc).isoformat(),
        }
    else:
        result = classify_goal_record(goal, goal_id=goal_id)

    log_data = load_approval_log()
    log_data["entries"].append(result)
    save_approval_log(log_data)

    if result["gateway_decision"] == "DENY":
        _notify("ESCALATION", goal_id=goal_id, message=f"Gateway DENY — {result['reason']}")
    elif result["gateway_decision"] == "PAUSE":
        _notify("ESCALATION", goal_id=goal_id, message=f"Gateway PAUSE — {result['reason']}")
    else:
        _notify("GOAL_APPROVED", goal_id=goal_id, message=f"Gateway ALLOW — {result['reason']}")

    return result


def classify_goal(goal_id):
    """
    Classify a goal by ID.

    Returns dict:
    {
      "goal_id": str,
      "title": str,
      "risk": "LOW" | "MEDIUM" | "HIGH",
      "auto_approve": bool,
      "sandbox_only": bool,
      "decision": "APPROVED" | "PENDING_HUMAN",
      "reason": str,
      "classified_at": ISO timestamp
    }
    """
    queue = load_goal_queue()
    goal = None
    for g in queue.get("goals", []):
        if g.get("id") == goal_id:
            goal = g
            break

    if goal is None:
        return {
            "goal_id": goal_id,
            "title": "UNKNOWN",
            "risk": "HIGH",
            "auto_approve": False,
            "sandbox_only": False,
            "decision": "PENDING_HUMAN",
            "reason": f"Goal {goal_id} not found in goal_queue.json. Defaulting to HIGH risk, human approval required.",
            "classified_at": datetime.now(timezone.utc).isoformat(),
        }

    gateway_result = classify_goal_record(goal, goal_id=goal_id)

    # Backward-compatible shape for existing callers.
    result = {
        "goal_id": gateway_result["goal_id"],
        "title": gateway_result["title"],
        "risk": gateway_result["risk"],
        "auto_approve": gateway_result["gateway_decision"] == "ALLOW",
        "sandbox_only": gateway_result["sandbox_only"],
        "decision": "APPROVED" if gateway_result["gateway_decision"] == "ALLOW" else "PENDING_HUMAN",
        "reason": gateway_result["reason"],
        "gateway_decision": gateway_result["gateway_decision"],
        "classified_at": gateway_result["classified_at"],
    }

    # Log the classification
    log_data = load_approval_log()
    log_data["entries"].append(result)
    save_approval_log(log_data)

    # AO2.2: notify on HIGH risk classification
    if risk == "HIGH":
        _notify("ESCALATION", goal_id=goal_id, message=f"HIGH risk classified — {goal.get('title', '')} requires human approval")
    elif decision == "APPROVED":
        _notify("GOAL_APPROVED", goal_id=goal_id, message=f"{risk} risk auto-approved — {goal.get('title', '')}")

    return result


def list_pending():
    """List all PENDING_HUMAN goals from approval log."""
    log_data = load_approval_log()
    return [e for e in log_data.get("entries", []) if e.get("decision") == "PENDING_HUMAN"]


def list_approved():
    """List all APPROVED goals from approval log."""
    log_data = load_approval_log()
    return [e for e in log_data.get("entries", []) if e.get("decision") == "APPROVED"]


# Approved adjustments file for threshold overrides
_APPROVED_ADJUSTMENTS_PATH = Path(__file__).parent / "approved_adjustments.json"
# Default thresholds
_DEFAULT_THRESHOLDS = {
    "MEDIUM_AUTO_APPROVE": False,
    "LOW_AUTO_APPROVE": True,
}


def load_threshold_adjustments():
    """
    Load threshold adjustments from approved_adjustments.json.
    If file doesn't exist, returns defaults (no change).
    Logs applied adjustments to trigger_log.jsonl.
    """
    # Default thresholds
    thresholds = dict(_DEFAULT_THRESHOLDS)

    if not _APPROVED_ADJUSTMENTS_PATH.exists():
        return thresholds

    try:
        with open(_APPROVED_ADJUSTMENTS_PATH, "r", encoding="utf-8") as f:
            adjustments = json.load(f)
    except (json.JSONDecodeError, IOError):
        return thresholds

    # Apply approved adjustments
    approved = adjustments.get("approved", [])
    for adj in approved:
        key = adj.get("key", "")
        value = adj.get("value")
        if key in thresholds and value is not None:
            thresholds[key] = value

    # Log applied adjustments to trigger_log.jsonl
    try:
        from orchestrator_runtime.governance.file_watcher import _log_event as _fw_log
        _fw_log("threshold_adjustments_applied", {
            "source": "approved_adjustments.json",
            "adjustments": {k: v for k, v in thresholds.items() if k in _DEFAULT_THRESHOLDS and v != _DEFAULT_THRESHOLDS.get(k)},
        })
    except ImportError:
        pass

    return thresholds


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        goal_id = sys.argv[1]
    else:
        goal_id = "GOAL_007"
    result = classify_goal(goal_id)
    print(json.dumps(result, indent=2, ensure_ascii=False))