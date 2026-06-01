"""
MS-AO1 Self-Correcting Loop — AO1.3
Handles FAIL verdicts with bounded retries and escalation.

Rules:
  - On FAIL: generate revised prompt incorporating evaluator feedback
  - Max retries: 2 (configurable via max_retries parameter)
  - On repeated FAIL after max_retries: escalate to escalation_queue.json
  - On PASS: mark goal DONE in approval_log.json
  - Hard budget: never exceeds max_retries, no infinite loops

Usage:
    from orchestrator_runtime.governance.self_correcting_loop import SelfCorrectingLoop
    loop = SelfCorrectingLoop()
    result = loop.process_goal("GOAL_008", verdict="PASS", feedback="All checks passed.")
"""

import json
from pathlib import Path
from datetime import datetime, timezone

APPROVAL_LOG_PATH = Path(__file__).parent / "approval_log.json"
ESCALATION_QUEUE_PATH = Path(__file__).parent / "escalation_queue.json"
GOAL_QUEUE_PATH = Path(__file__).parent.parent / "goal_queue.json"

# AO2.2 notification integration (lazy import — fails gracefully if notifier not available)
try:
    from orchestrator_runtime.governance.notifier import Notifier
    _NOTIFIER = Notifier()
except ImportError:
    _NOTIFIER = None

# AO2.3 kill switch + budget integration
try:
    from orchestrator_runtime.governance.kill_switch import KillSwitch
    _KILL_SWITCH = KillSwitch()
except ImportError:
    _KILL_SWITCH = None

try:
    from orchestrator_runtime.governance.budget_manager import BudgetManager
    _BUDGET = BudgetManager()
except ImportError:
    _BUDGET = None


def _notify(event_type, goal_id=None, message=""):
    """Send notification if notifier available."""
    if _NOTIFIER is not None:
        try:
            _NOTIFIER.notify(event_type, goal_id=goal_id, message=message)
        except Exception:
            pass  # Notifications are best-effort, never block the loop


def _load_json(path, default=None):
    if default is None:
        default = {}
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def _save_json(path, data):
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    # Windows: rename cannot overwrite, so remove target first if it exists
    if path.exists():
        path.unlink()
    tmp.rename(path)


class SelfCorrectingLoop:
    def __init__(self, max_retries=2):
        self.max_retries = max_retries

    def process_goal(self, goal_id, verdict, feedback="", retry_count=0):
        """
        Process a goal through the self-correcting loop.

        Args:
            goal_id: Goal identifier (e.g., "GOAL_008")
            verdict: "PASS" or "FAIL"
            feedback: Evaluator feedback / reason
            retry_count: Current retry attempt (0 = first attempt)

        Returns:
            dict with status, action, and details
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        # AO2.3: check kill switch before processing
        if _KILL_SWITCH is not None and _KILL_SWITCH.is_active():
            ks_status = _KILL_SWITCH.status()
            return {
                "goal_id": goal_id,
                "status": "BLOCKED",
                "action": "KILL_SWITCH",
                "reason": f"Kill switch active: {ks_status.get('reason', '')}",
                "timestamp": timestamp,
            }

        # AO2.3: check budget before processing
        if _BUDGET is not None and not _BUDGET.can_run():
            return {
                "goal_id": goal_id,
                "status": "BLOCKED",
                "action": "BUDGET_EXHAUSTED",
                "reason": f"Daily budget exhausted. Remaining: {_BUDGET.remaining()}",
                "timestamp": timestamp,
            }

        if verdict == "PASS":
            # AO2.3: increment budget on PASS
            if _BUDGET is not None:
                try:
                    _BUDGET.increment()
                except Exception:
                    pass
            return self._handle_pass(goal_id, feedback, timestamp)
        elif verdict == "FAIL":
            return self._handle_fail(goal_id, feedback, retry_count, timestamp)
        else:
            return {
                "goal_id": goal_id,
                "status": "ERROR",
                "action": "ESCALATE",
                "reason": f"Unknown verdict: {verdict}",
                "timestamp": timestamp,
            }

    def _handle_pass(self, goal_id, feedback, timestamp):
        """Mark goal as DONE in approval log."""
        log = _load_json(APPROVAL_LOG_PATH, {"entries": []})

        # Find and update the goal entry
        for entry in log["entries"]:
            if entry.get("goal_id") == goal_id:
                entry["final_verdict"] = "PASS"
                entry["final_status"] = "DONE"
                entry["final_feedback"] = feedback
                entry["completed_at"] = timestamp
                break
        else:
            # No existing entry — create one
            log["entries"].append({
                "goal_id": goal_id,
                "final_verdict": "PASS",
                "final_status": "DONE",
                "final_feedback": feedback,
                "completed_at": timestamp,
            })

        _save_json(APPROVAL_LOG_PATH, log)

        _notify("GOAL_DONE", goal_id=goal_id, message=f"PASS — {feedback}")

        return {
            "goal_id": goal_id,
            "status": "PASS",
            "action": "DONE",
            "reason": f"Goal passed. Marked DONE in approval log.",
            "timestamp": timestamp,
        }

    def _handle_fail(self, goal_id, feedback, retry_count, timestamp):
        """Handle FAIL with bounded retry or escalation."""
        if retry_count < self.max_retries:
            # Generate revised prompt for retry
            revised_prompt = self._generate_revised_prompt(goal_id, feedback)
            return {
                "goal_id": goal_id,
                "status": "FAIL",
                "action": "RETRY",
                "retry_count": retry_count + 1,
                "max_retries": self.max_retries,
                "revised_prompt": revised_prompt,
                "reason": f"FAIL on attempt {retry_count + 1}/{self.max_retries}. Generating revised prompt with evaluator feedback.",
                "timestamp": timestamp,
            }
        else:
            # Max retries exceeded — escalate
            _notify("GOAL_FAILED", goal_id=goal_id, message=f"FAIL after {retry_count + 1} attempts — {feedback}")
            return self._escalate(goal_id, feedback, retry_count, timestamp)

    def _generate_revised_prompt(self, goal_id, feedback):
        """
        Generate a revised prompt incorporating evaluator feedback.

        This is a template-based approach. In production, this could use
        an LLM to generate more sophisticated revisions.
        """
        # Load goal details for context
        queue = _load_json(GOAL_QUEUE_PATH, {"goals": []})
        goal_title = ""
        for g in queue.get("goals", []):
            if g.get("id") == goal_id:
                goal_title = g.get("title", "")
                break

        revised = (
            f"REVISED PROMPT for {goal_id}: {goal_title}\n"
            f"---\n"
            f"Previous attempt failed. Evaluator feedback:\n"
            f"{feedback}\n"
            f"---\n"
            f"Instructions: Address the evaluator feedback above. "
            f"Focus on the specific issues identified. "
            f"Do not repeat the same approach that failed.\n"
        )
        return revised

    def _escalate(self, goal_id, feedback, retry_count, timestamp):
        """Escalate goal to human review after max retries exhausted."""
        escalation = {
            "goal_id": goal_id,
            "reason": f"Max retries ({self.max_retries}) exhausted. Goal requires human review.",
            "feedback": feedback,
            "attempts": retry_count + 1,
            "escalated_at": timestamp,
            "status": "ESCALATED",
        }

        # Write to escalation queue
        queue = _load_json(ESCALATION_QUEUE_PATH, {"entries": []})
        queue["entries"].append(escalation)
        _save_json(ESCALATION_QUEUE_PATH, queue)

        # Also update approval log
        log = _load_json(APPROVAL_LOG_PATH, {"entries": []})
        for entry in log["entries"]:
            if entry.get("goal_id") == goal_id:
                entry["final_verdict"] = "FAIL"
                entry["final_status"] = "ESCALATED"
                entry["final_feedback"] = feedback
                entry["escalated_at"] = timestamp
                break
        else:
            log["entries"].append({
                "goal_id": goal_id,
                "final_verdict": "FAIL",
                "final_status": "ESCALATED",
                "final_feedback": feedback,
                "escalated_at": timestamp,
            })
        _save_json(APPROVAL_LOG_PATH, log)

        _notify("ESCALATION", goal_id=goal_id, message=f"ESCALATED — {escalation['reason']}")

        return {
            "goal_id": goal_id,
            "status": "FAIL",
            "action": "ESCALATED",
            "reason": escalation["reason"],
            "escalation_queue": str(ESCALATION_QUEUE_PATH),
            "timestamp": timestamp,
        }

    def get_escalation_queue(self):
        """Return current escalation queue."""
        return _load_json(ESCALATION_QUEUE_PATH, {"entries": []})

    def get_goal_status(self, goal_id):
        """Check current status of a goal in the approval log."""
        log = _load_json(APPROVAL_LOG_PATH, {"entries": []})
        for entry in log["entries"]:
            if entry.get("goal_id") == goal_id:
                return entry
        return None


if __name__ == "__main__":
    import sys
    loop = SelfCorrectingLoop(max_retries=2)

    if len(sys.argv) > 2:
        goal_id = sys.argv[1]
        verdict = sys.argv[2]
        feedback = sys.argv[3] if len(sys.argv) > 3 else ""
        result = loop.process_goal(goal_id, verdict, feedback)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("Usage: python self_correcting_loop.py <GOAL_ID> <PASS|FAIL> [feedback]")
        print("\nDemo: Simulating FAIL → RETRY → FAIL → RETRY → FAIL → ESCALATE")
        for i in range(3):
            r = loop.process_goal("DEMO_GOAL", "FAIL", f"Attempt {i+1} failed.", retry_count=i)
            print(f"\nAttempt {i+1}: action={r['action']}")
        print(f"\nEscalation queue: {loop.get_escalation_queue()}")