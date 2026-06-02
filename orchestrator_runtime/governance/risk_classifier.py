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

    risk = goal.get("risk", "HIGH")
    auto_approve_orig = goal.get("auto_approve", False)
    rationale = goal.get("rationale", "")
    sandbox_only = _is_sandbox_only(rationale)

    # Updated threshold rules (AO1.2 relaxed):
    # LOW + auto_approve=true → APPROVED
    # MEDIUM + sandbox_only → APPROVED (relaxed threshold)
    # MEDIUM + production touch → PENDING_HUMAN
    # HIGH → always PENDING_HUMAN

    if risk == "LOW" and auto_approve_orig is True:
        decision = "APPROVED"
        reason = (
            f"Risk={risk}, auto_approve=true. Goal is sandbox-only/read-only with no production impact. "
            f"Auto-approved per AO1.2 risk classification rules."
        )
    elif risk == "MEDIUM" and sandbox_only:
        decision = "APPROVED"
        reason = (
            f"Risk={risk}, sandbox_only=true. Goal only touches sandbox/orchestrator_runtime/reports. "
            f"Auto-approved per relaxed AO1.2 threshold (MEDIUM + sandbox-only = APPROVED)."
        )
    elif risk == "MEDIUM" and not sandbox_only:
        decision = "PENDING_HUMAN"
        reason = (
            f"Risk={risk}, sandbox_only=false. Goal rationale indicates production/src/self_state touch. "
            f"Requires human approval regardless of sandbox classification."
        )
    elif risk == "HIGH":
        decision = "PENDING_HUMAN"
        reason = (
            f"Risk={risk}. High-risk goals (production files, config, self_state writes) always require "
            f"human approval. No relaxation permitted."
        )
    else:
        decision = "PENDING_HUMAN"
        reason = f"Risk={risk}. Default to PENDING_HUMAN."

    result = {
        "goal_id": goal_id,
        "title": goal.get("title", ""),
        "risk": risk,
        "auto_approve": decision == "APPROVED",
        "sandbox_only": sandbox_only,
        "decision": decision,
        "reason": reason,
        "classified_at": datetime.now(timezone.utc).isoformat(),
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