"""
MS-AO1 Parallel Loop Manager — AO1.4 / GOAL_004
Manages multiple concurrent goal execution loops with conflict detection.

Rules:
  - Max 3 parallel loops
  - Conflict detection: two goals touching same file → serialize
  - Per-loop state in orchestrator_runtime/active_loops/<GOAL_ID>/state.json
  - Sandbox only

Usage:
    from orchestrator_runtime.governance.parallel_loop_manager import ParallelLoopManager
    mgr = ParallelLoopManager(max_concurrent=3)
    mgr.submit_goal("GOAL_004")
    mgr.check_conflicts(["GOAL_004", "GOAL_005"])
"""

import json
from pathlib import Path
from datetime import datetime, timezone

ACTIVE_LOOPS_DIR = Path(__file__).parent.parent / "active_loops"
GOAL_QUEUE_PATH = Path(__file__).parent.parent / "goal_queue.json"

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
    if path.exists():
        path.unlink()
    tmp.rename(path)


# File-touch mapping: which goals might touch which files
# In production, this would be inferred from goal descriptions or manifests
_FILE_TOUCH_MAP = {
    "GOAL_001": ["orchestrator_runtime/goal_queue.json"],
    "GOAL_002": ["orchestrator_runtime/governance/risk_classifier.py", "orchestrator_runtime/governance/approval_log.json"],
    "GOAL_003": ["orchestrator_runtime/governance/self_correcting_loop.py", "orchestrator_runtime/governance/approval_log.json"],
    "GOAL_004": ["orchestrator_runtime/governance/parallel_loop_manager.py", "orchestrator_runtime/active_loops/"],
    "GOAL_005": ["orchestrator_runtime/governance/self_state_updater.py", "orchestrator_runtime/governance/pending_self_state_updates.json", "orchestrator_runtime/governance/self_state_audit.json"],
    "GOAL_006": ["orchestrator_runtime/governance/"],
    "GOAL_007": ["reports/MS_AO1_PROGRESS_REPORT_20260527.md"],
    "GOAL_008": ["self_state.json"],  # read-only
}


class ParallelLoopManager:
    def __init__(self, max_concurrent=3):
        self.max_concurrent = max_concurrent
        ACTIVE_LOOPS_DIR.mkdir(parents=True, exist_ok=True)

    def get_active_count(self):
        """Count currently active loops."""
        if not ACTIVE_LOOPS_DIR.exists():
            return 0
        count = 0
        for state_file in ACTIVE_LOOPS_DIR.glob("*/state.json"):
            state = _load_json(state_file, {})
            if state.get("status") == "ACTIVE":
                count += 1
        return count

    def can_submit(self):
        """Check if we can submit a new goal without exceeding max_concurrent."""
        return self.get_active_count() < self.max_concurrent

    def submit_goal(self, goal_id, files_touched=None):
        """
        Submit a goal for parallel execution.

        Args:
            goal_id: Goal identifier
            files_touched: List of files this goal may touch (optional, uses default map)

        Returns:
            dict with submission result
        """
        # AO2.3: check kill switch
        if _KILL_SWITCH is not None and _KILL_SWITCH.is_active():
            ks_status = _KILL_SWITCH.status()
            return {
                "goal_id": goal_id,
                "status": "BLOCKED",
                "reason": f"Kill switch active: {ks_status.get('reason', '')}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        # AO2.3: check budget
        if _BUDGET is not None and not _BUDGET.can_run():
            return {
                "goal_id": goal_id,
                "status": "BLOCKED",
                "reason": f"Daily budget exhausted. Remaining: {_BUDGET.remaining()}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        if not self.can_submit():
            return {
                "goal_id": goal_id,
                "status": "REJECTED",
                "reason": f"Max concurrent loops ({self.max_concurrent}) reached. Current active: {self.get_active_count()}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        # Use provided files or default mapping
        if files_touched is None:
            files_touched = _FILE_TOUCH_MAP.get(goal_id, [])

        loop_dir = ACTIVE_LOOPS_DIR / goal_id
        loop_dir.mkdir(parents=True, exist_ok=True)

        state = {
            "goal_id": goal_id,
            "status": "ACTIVE",
            "files_touched": files_touched,
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
            "verdict": None,
            "retry_count": 0,
        }

        _save_json(loop_dir / "state.json", state)

        return {
            "goal_id": goal_id,
            "status": "SUBMITTED",
            "active_loops": self.get_active_count(),
            "max_concurrent": self.max_concurrent,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def complete_goal(self, goal_id, verdict, feedback=""):
        """Mark a goal as completed in its loop state."""
        state_file = ACTIVE_LOOPS_DIR / goal_id / "state.json"
        if not state_file.exists():
            return {"goal_id": goal_id, "status": "ERROR", "reason": "No active loop found."}

        state = _load_json(state_file, {})
        state["status"] = "COMPLETED"
        state["verdict"] = verdict
        state["feedback"] = feedback
        state["completed_at"] = datetime.now(timezone.utc).isoformat()
        _save_json(state_file, state)

        return {
            "goal_id": goal_id,
            "status": "COMPLETED",
            "verdict": verdict,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _get_files_for_goal(self, goal_id):
        """Get files touched by a goal, checking both static map and goal_queue.json."""
        # Check static map first
        if goal_id in _FILE_TOUCH_MAP:
            return _FILE_TOUCH_MAP[goal_id]
        # Check goal_queue.json for 'touches' field
        queue = _load_json(GOAL_QUEUE_PATH, {"goals": []})
        for goal in queue.get("goals", []):
            if goal.get("id") == goal_id:
                touches = goal.get("touches", [])
                if touches:
                    return touches
        return []

    def check_conflicts(self, goal_ids):
        """
        Check if any two goals in the list touch the same files.

        Returns:
            dict with conflicts list and serialization recommendation
        """
        conflicts = []
        for i in range(len(goal_ids)):
            for j in range(i + 1, len(goal_ids)):
                gid_a = goal_ids[i]
                gid_b = goal_ids[j]
                files_a = set(self._get_files_for_goal(gid_a))
                files_b = set(self._get_files_for_goal(gid_b))
                shared = files_a & files_b
                if shared:
                    conflicts.append({
                        "goal_a": gid_a,
                        "goal_b": gid_b,
                        "shared_files": list(shared),
                        "recommendation": "SERIALIZE",
                    })

        return {
            "goal_ids_checked": goal_ids,
            "conflicts": conflicts,
            "has_conflicts": len(conflicts) > 0,
            "recommendation": "SERIALIZE" if conflicts else "PARALLEL_OK",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_all_active(self):
        """Return all active loop states."""
        active = []
        if not ACTIVE_LOOPS_DIR.exists():
            return active
        for state_file in ACTIVE_LOOPS_DIR.glob("*/state.json"):
            state = _load_json(state_file, {})
            active.append(state)
        return active

    def get_serialization_order(self, goal_ids):
        """
        Given a list of goal IDs, return an execution order that serializes
        conflicting goals and groups non-conflicting ones for parallel execution.

        Returns:
            list of batches, where each batch is a list of goal_ids that can run in parallel
        """
        if not goal_ids:
            return []

        batches = []
        assigned_files = set()
        remaining = list(goal_ids)

        while remaining:
            batch = []
            for gid in list(remaining):
                files = set(self._get_files_for_goal(gid))
                if not (files & assigned_files):
                    batch.append(gid)
                    assigned_files |= files
            if not batch:
                # Force-assign remaining to avoid infinite loop
                batch = [remaining[0]]
                assigned_files |= set(self._get_files_for_goal(remaining[0]))
            remaining = [g for g in remaining if g not in batch]
            batches.append(batch)

        return batches


if __name__ == "__main__":
    import sys

    mgr = ParallelLoopManager(max_concurrent=3)

    if len(sys.argv) > 1 and sys.argv[1] == "check-conflicts" and len(sys.argv) > 2:
        goal_ids = sys.argv[2:]
        conflicts = mgr.check_conflicts(goal_ids)
        print("Conflict check:")
        print(json.dumps(conflicts, indent=2))
        order = mgr.get_serialization_order(goal_ids)
        print(f"\nSerialization order ({len(order)} batches):")
        for i, batch in enumerate(order):
            print(f"  Batch {i+1}: {batch}")
    else:
        # Demo: check conflicts between all goals
        all_goals = [f"GOAL_{i:03d}" for i in range(1, 9)]
        conflicts = mgr.check_conflicts(all_goals)
        print("Conflict check:")
        print(json.dumps(conflicts, indent=2))

        # Demo: serialization order
        order = mgr.get_serialization_order(all_goals)
        print(f"\nSerialization order ({len(order)} batches):")
        for i, batch in enumerate(order):
            print(f"  Batch {i+1}: {batch}")
