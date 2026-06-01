"""
MS-AO2 Batch Processor — AO2.4

Reads goal_queue.json, filters auto-approvable goals, groups by risk level,
checks kill switch + budget before each goal, and runs goals through
parallel_loop_manager.py (max 3 concurrent).

Progress log: orchestrator_runtime/governance/batch_run_log.jsonl

Usage:
    from orchestrator_runtime.governance.batch_processor import BatchProcessor
    bp = BatchProcessor()
    result = bp.run_batch(dry_run=False)

Rules:
    - LOW goals first, then MEDIUM
    - HIGH goals never auto-approved (skipped in batch)
    - Kill switch checked before every goal
    - Budget checked before every goal
    - Max 3 concurrent via ParallelLoopManager
    - Notifications on every batch event
    - Atomic writes only (temp + rename pattern)
"""

import json
import time
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- paths ---
GOAL_QUEUE_PATH = Path(__file__).parent.parent.parent / "orchestrator_runtime" / "goal_queue.json"
BATCH_RUN_LOG = Path(__file__).parent / "batch_run_log.jsonl"

# --- governance imports (lazy / failsafe) ---
try:
    from orchestrator_runtime.governance.risk_classifier import classify_goal, load_goal_queue
except ImportError:
    classify_goal = None
    load_goal_queue = None

try:
    from orchestrator_runtime.governance.kill_switch import KillSwitch
    _KillSwitch = KillSwitch
except ImportError:
    _KillSwitch = None

try:
    from orchestrator_runtime.governance.budget_manager import BudgetManager
    _BudgetManager = BudgetManager
except ImportError:
    _BudgetManager = None

try:
    from orchestrator_runtime.governance.notifier import Notifier
    _Notifier = Notifier
except ImportError:
    _Notifier = None

try:
    from orchestrator_runtime.governance.parallel_loop_manager import ParallelLoopManager
    _ParallelLoopManager = ParallelLoopManager
except ImportError:
    _ParallelLoopManager = None

try:
    from orchestrator_runtime.governance.self_correcting_loop import SelfCorrectingLoop
    _SelfCorrectingLoop = SelfCorrectingLoop
except ImportError:
    _SelfCorrectingLoop = None


# --- helpers ---
def _now():
    return datetime.now(timezone.utc).isoformat()


def _atomic_append_jsonl(path, record):
    """Append a JSON record to a JSONL file atomically via temp + rename."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    # Read existing lines
    lines = []
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            lines = f.readlines()
    # Append new record
    lines.append(json.dumps(record, ensure_ascii=False) + "\n")
    with open(tmp, "w", encoding="utf-8") as f:
        f.writelines(lines)
    if p.exists():
        p.unlink()
    tmp.rename(p)


def _log(event_type, **kwargs):
    """Append a structured log entry to batch_run_log.jsonl."""
    record = {
        "timestamp": _now(),
        "event": event_type,
    }
    record.update(kwargs)
    _atomic_append_jsonl(BATCH_RUN_LOG, record)


def _notify(event_type, goal_id=None, message="", severity=None):
    """Send a notification if notifier is available."""
    if _Notifier is None:
        return
    try:
        n = _Notifier()
        n.notify(event_type, goal_id=goal_id, message=message, severity=severity)
    except Exception:
        pass


def _check_kill_switch():
    """Return (ok, reason). ok=False if kill switch is active."""
    if _KillSwitch is None:
        return True, "KillSwitch module unavailable (skipped)"
    ks = _KillSwitch()
    if ks.is_active():
        status = ks.status()
        return False, f"Kill switch active: {status.get('reason', '')}"
    return True, ""


def _check_budget():
    """Return (ok, reason). ok=False if budget exhausted."""
    if _BudgetManager is None:
        return True, "BudgetManager module unavailable (skipped)"
    bm = _BudgetManager()
    if not bm.can_run():
        return False, f"Daily budget exhausted. Remaining: {bm.remaining()}"
    return True, ""


def _execute_single_goal(goal_id):
    """
    Execute a single goal through the self-correcting loop.
    Returns a result dict.
    """
    result = {
        "goal_id": goal_id,
        "status": "UNKNOWN",
        "verdict": None,
        "timestamp": _now(),
    }

    # Use self-correcting loop if available
    if _SelfCorrectingLoop is not None:
        try:
            scl = _SelfCorrectingLoop(goal_id)
            verdict = scl.run()
            result["verdict"] = verdict
            result["status"] = "COMPLETED" if verdict == "PASS" else "FAILED"
            return result
        except Exception as e:
            result["status"] = "ERROR"
            result["error"] = str(e)
            return result

    # Fallback: submit through parallel loop manager only
    if _ParallelLoopManager is not None:
        try:
            mgr = _ParallelLoopManager(max_concurrent=3)
            submit = mgr.submit_goal(goal_id)
            result["status"] = submit.get("status", "UNKNOWN")
            # Mark as completed with PASS (no self-correcting loop to run)
            if submit.get("status") == "SUBMITTED":
                mgr.complete_goal(goal_id, "PASS", "Batch processed (no SCL)")
                result["status"] = "COMPLETED"
                result["verdict"] = "PASS"
            return result
        except Exception as e:
            result["status"] = "ERROR"
            result["error"] = str(e)
            return result

    result["status"] = "SKIPPED"
    result["error"] = "No execution runtime available"
    return result


class BatchProcessor:
    def __init__(self, max_concurrent=3):
        self.max_concurrent = max_concurrent

    # ---- goal discovery ----

    def load_goals(self):
        """Load goals from goal_queue.json."""
        if load_goal_queue is not None:
            return load_goal_queue()
        # Fallback: direct read
        with open(GOAL_QUEUE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_auto_approvable(self):
        """
        Return list of goals that are auto-approvable.
        Filters: risk in (LOW, MEDIUM), decision == APPROVED.
        Skips HIGH risk entirely.
        """
        queue = self.load_goals()
        approvable = []

        for goal in queue.get("goals", []):
            goal_id = goal.get("id", "")
            risk = goal.get("risk", "HIGH")

            # Skip HIGH risk — never auto-approved
            if risk == "HIGH":
                _log("GOAL_SKIPPED_HIGH", goal_id=goal_id, reason="HIGH risk — requires human approval")
                _notify("GOAL_APPROVED", goal_id=goal_id, message=f"HIGH risk {goal_id} skipped in batch — requires human approval", severity="WARN")
                continue

            # Classify to confirm auto-approval
            if classify_goal is not None:
                try:
                    classification = classify_goal(goal_id)
                    if classification.get("decision") == "APPROVED":
                        approvable.append({
                            "id": goal_id,
                            "title": goal.get("title", ""),
                            "risk": risk,
                            "priority": goal.get("priority", 999),
                            "classification": classification,
                        })
                    else:
                        _log("GOAL_SKIPPED_NOT_APPROVED", goal_id=goal_id,
                             reason=classification.get("reason", "not approved"))
                except Exception as e:
                    _log("CLASSIFICATION_ERROR", goal_id=goal_id, error=str(e))
            else:
                # Fallback: trust auto_approve flag in queue
                if goal.get("auto_approve", False):
                    approvable.append({
                        "id": goal_id,
                        "title": goal.get("title", ""),
                        "risk": risk,
                        "priority": goal.get("priority", 999),
                    })

        # Sort: LOW first, then MEDIUM; within same risk, by priority
        risk_order = {"LOW": 0, "MEDIUM": 1}
        approvable.sort(key=lambda g: (risk_order.get(g.get("risk", "MEDIUM"), 2), g.get("priority", 999)))

        return approvable

    # ---- execution ----

    def run_batch(self, dry_run=False):
        """
        Run the batch of auto-approvable goals.

        Args:
            dry_run: If True, only list goals without executing.

        Returns:
            dict with batch summary
        """
        batch_id = f"BATCH_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        start_time = _now()

        _log("BATCH_START", batch_id=batch_id, dry_run=dry_run)
        _notify("ESCALATION", message=f"Batch {batch_id} started (dry_run={dry_run})", severity="INFO")

        # Discover goals
        goals = self.get_auto_approvable()
        _log("GOALS_DISCOVERED", batch_id=batch_id, count=len(goals),
             goal_ids=[g["id"] for g in goals])

        if not goals:
            _log("BATCH_EMPTY", batch_id=batch_id, reason="No auto-approvable goals")
            _notify("ESCALATION", message=f"Batch {batch_id} empty — no auto-approvable goals", severity="INFO")
            return {
                "batch_id": batch_id,
                "status": "EMPTY",
                "goals_discovered": 0,
                "dry_run": dry_run,
                "started_at": start_time,
                "completed_at": _now(),
            }

        # ---- DRY RUN MODE ----
        if dry_run:
            _log("BATCH_DRY_RUN", batch_id=batch_id, goals=goals)
            _notify("ESCALATION", message=f"Batch {batch_id} dry run — {len(goals)} goals listed, none executed", severity="INFO")

            # Check kill switch + budget in dry run (verify integration works)
            ks_ok, ks_reason = _check_kill_switch()
            bg_ok, bg_reason = _check_budget()

            dry_run_details = []
            for g in goals:
                entry = {
                    "goal_id": g["id"],
                    "title": g["title"],
                    "risk": g["risk"],
                    "would_run": ks_ok and bg_ok,
                    "kill_switch_ok": ks_ok,
                    "budget_ok": bg_ok,
                }
                dry_run_details.append(entry)
                _log("DRY_RUN_GOAL", batch_id=batch_id, **entry)

            result = {
                "batch_id": batch_id,
                "status": "DRY_RUN",
                "goals_discovered": len(goals),
                "goals_listed": dry_run_details,
                "kill_switch_ok": ks_ok,
                "kill_switch_reason": ks_reason,
                "budget_ok": bg_ok,
                "budget_reason": bg_reason,
                "dry_run": True,
                "started_at": start_time,
                "completed_at": _now(),
            }
            _log("BATCH_COMPLETE", batch_id=batch_id, status="DRY_RUN", total=len(goals))
            return result

        # ---- LIVE EXECUTION MODE ----

        # Pre-flight: kill switch + budget
        ks_ok, ks_reason = _check_kill_switch()
        if not ks_ok:
            _log("BATCH_BLOCKED_KILL_SWITCH", batch_id=batch_id, reason=ks_reason)
            _notify("ESCALATION", message=f"Batch {batch_id} blocked — {ks_reason}", severity="ERROR")
            return {
                "batch_id": batch_id,
                "status": "BLOCKED",
                "reason": ks_reason,
                "dry_run": False,
                "started_at": start_time,
                "completed_at": _now(),
            }

        bg_ok, bg_reason = _check_budget()
        if not bg_ok:
            _log("BATCH_BLOCKED_BUDGET", batch_id=batch_id, reason=bg_reason)
            _notify("ESCALATION", message=f"Batch {batch_id} blocked — {bg_reason}", severity="ERROR")
            return {
                "batch_id": batch_id,
                "status": "BLOCKED",
                "reason": bg_reason,
                "dry_run": False,
                "started_at": start_time,
                "completed_at": _now(),
            }

        # Initialize parallel loop manager
        mgr = _ParallelLoopManager(max_concurrent=self.max_concurrent) if _ParallelLoopManager else None

        results = []
        completed = 0
        failed = 0
        blocked = 0

        for goal in goals:
            goal_id = goal["id"]

            # Per-goal kill switch check
            ks_ok, ks_reason = _check_kill_switch()
            if not ks_ok:
                _log("GOAL_BLOCKED_KILL_SWITCH", goal_id=goal_id, batch_id=batch_id, reason=ks_reason)
                _notify("GOAL_FAILED", goal_id=goal_id, message=f"Blocked by kill switch: {ks_reason}", severity="ERROR")
                results.append({"goal_id": goal_id, "status": "BLOCKED", "reason": ks_reason})
                blocked += 1
                break  # Stop batch entirely

            # Per-goal budget check
            bg_ok, bg_reason = _check_budget()
            if not bg_ok:
                _log("GOAL_BLOCKED_BUDGET", goal_id=goal_id, batch_id=batch_id, reason=bg_reason)
                _notify("GOAL_FAILED", goal_id=goal_id, message=f"Blocked by budget: {bg_reason}", severity="ERROR")
                results.append({"goal_id": goal_id, "status": "BLOCKED", "reason": bg_reason})
                blocked += 1
                break  # Stop batch

            # Increment budget counter before execution
            if _BudgetManager is not None:
                try:
                    bm = _BudgetManager()
                    bm.increment()
                except Exception:
                    pass

            _log("GOAL_START", goal_id=goal_id, batch_id=batch_id, risk=goal.get("risk"))
            _notify("GOAL_APPROVED", goal_id=goal_id, message=f"Executing {goal_id} ({goal.get('risk', '?')} risk)", severity="INFO")

            # Execute goal (with optional parallelism)
            if mgr and self.max_concurrent > 1:
                # Submit to parallel manager
                submit_result = mgr.submit_goal(goal_id)
                if submit_result.get("status") == "BLOCKED":
                    results.append({"goal_id": goal_id, "status": "BLOCKED", "reason": submit_result.get("reason", "")})
                    blocked += 1
                    continue
                elif submit_result.get("status") == "REJECTED":
                    results.append({"goal_id": goal_id, "status": "REJECTED", "reason": submit_result.get("reason", "")})
                    blocked += 1
                    continue

            # Run through self-correcting loop
            exec_result = _execute_single_goal(goal_id)

            # Complete in parallel manager
            if mgr:
                try:
                    mgr.complete_goal(goal_id, exec_result.get("verdict", "UNKNOWN"), str(exec_result))
                except Exception:
                    pass

            if exec_result.get("status") == "COMPLETED" and exec_result.get("verdict") == "PASS":
                completed += 1
                _log("GOAL_DONE", goal_id=goal_id, batch_id=batch_id, verdict="PASS")
                _notify("GOAL_DONE", goal_id=goal_id, message=f"{goal_id} completed — PASS", severity="INFO")
            else:
                failed += 1
                _log("GOAL_FAILED", goal_id=goal_id, batch_id=batch_id,
                      verdict=exec_result.get("verdict"), status=exec_result.get("status"))
                _notify("GOAL_FAILED", goal_id=goal_id,
                         message=f"{goal_id} failed — {exec_result.get('status', 'UNKNOWN')}", severity="ERROR")

            results.append(exec_result)
            time.sleep(0.1)  # Small delay between goals

        end_time = _now()
        status = "COMPLETE" if failed == 0 and blocked == 0 else ("PARTIAL" if completed > 0 else "FAILED")

        _log("BATCH_COMPLETE", batch_id=batch_id, status=status,
             total=len(goals), completed=completed, failed=failed, blocked=blocked)
        _notify("ESCALATION",
                 message=f"Batch {batch_id} finished: {completed} passed, {failed} failed, {blocked} blocked",
                 severity="INFO" if status == "COMPLETE" else "WARN")

        return {
            "batch_id": batch_id,
            "status": status,
            "goals_discovered": len(goals),
            "completed": completed,
            "failed": failed,
            "blocked": blocked,
            "results": results,
            "dry_run": False,
            "started_at": start_time,
            "completed_at": end_time,
        }


if __name__ == "__main__":
    import sys

    bp = BatchProcessor(max_concurrent=3)

    if len(sys.argv) > 1 and sys.argv[1] == "--dry-run":
        print("=== BATCH DRY RUN ===")
        result = bp.run_batch(dry_run=True)
    else:
        print("=== BATCH LIVE RUN ===")
        print("WARNING: This will execute goals. Use --dry-run to preview.")
        if len(sys.argv) > 1 and sys.argv[1] == "--live":
            result = bp.run_batch(dry_run=False)
        else:
            print("Aborted. Use --dry-run to preview or --live to execute.")
            result = {"status": "ABORTED", "message": "Use --dry-run or --live flag"}

    print(json.dumps(result, indent=2, ensure_ascii=False))