"""
MS-AO3 Orchestrator Bridge — AO3.1/AO3.2/AO3.3

Connects the FA1 run-loop with the AO2 governance pipeline.
Uses FA1_HANDOFF_V1 protocol (next_prompt.md + prompt_ready.json).

Usage:
    from orchestrator_runtime.governance.orchestrator_bridge import OrchestratorBridge
    bridge = OrchestratorBridge()
    result = bridge.run_autonomous_cycle(dry_run=False, goal_ids=["GOAL_007"])
"""

import json
import sys
import os
import time
import hashlib
from pathlib import Path
from datetime import datetime, timezone

# Ensure orchestrator_runtime is importable when run as __main__
_bridge_dir = Path(__file__).resolve().parent
_runtime_dir = _bridge_dir.parent
if str(_runtime_dir) not in sys.path:
    sys.path.insert(0, str(_runtime_dir))

# --- paths ---
GOAL_QUEUE_PATH = Path(__file__).parent.parent / "goal_queue.json"
CLINE_INBOX = Path(__file__).parent.parent / "cline_inbox"
CLINE_OUTBOX = Path(__file__).parent.parent / "cline_outbox"
CYCLE_LOG_PATH = Path(__file__).parent / "cycle_log.jsonl"

# FA1_HANDOFF_V1 canonical paths
NEXT_PROMPT_PATH = CLINE_INBOX / "next_prompt.md"
PROMPT_READY_PATH = CLINE_INBOX / "prompt_ready.json"
OUTPUT_READY_PATH = CLINE_OUTBOX / "output_ready.json"
LAST_OUTPUT_PATH = CLINE_OUTBOX / "last_output.md"

# Deprecated: task.json (legacy AO3 protocol)
TASK_JSON_PATH = CLINE_INBOX / "task.json"

# Configurable handoff timeout
HANDOFF_TIMEOUT = int(os.environ.get("HANDOFF_TIMEOUT", "600"))  # 10 minutes

# --- governance imports ---
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
    from orchestrator_runtime.governance.self_correcting_loop import SelfCorrectingLoop
    _SelfCorrectingLoop = SelfCorrectingLoop
except ImportError:
    _SelfCorrectingLoop = None

try:
    from orchestrator_runtime.governance.risk_classifier import classify_goal, load_goal_queue
except ImportError:
    classify_goal = None
    load_goal_queue = None


def _now():
    return datetime.now(timezone.utc).isoformat()


def _atomic_write(path, content, is_json=False):
    """Atomic write: write to tmp, validate, rename."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    data = json.dumps(content, indent=2, ensure_ascii=False) if is_json else content
    tmp.write_text(data, encoding="utf-8")
    if p.exists():
        p.unlink()
    tmp.rename(p)


def _atomic_append_jsonl(path, record):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    lines = []
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            lines = f.readlines()
    lines.append(json.dumps(record, ensure_ascii=False) + "\n")
    with open(tmp, "w", encoding="utf-8") as f:
        f.writelines(lines)
    if p.exists():
        p.unlink()
    tmp.rename(p)


def _log(event_type, **kwargs):
    record = {"timestamp": _now(), "event": event_type}
    record.update(kwargs)
    _atomic_append_jsonl(CYCLE_LOG_PATH, record)


def _notify(event_type, goal_id=None, message="", severity=None):
    if _Notifier is None:
        return
    try:
        n = _Notifier()
        n.notify(event_type, goal_id=goal_id, message=message, severity=severity)
    except Exception:
        pass


def _check_kill_switch():
    if _KillSwitch is None:
        return True, "KillSwitch unavailable"
    ks = _KillSwitch()
    if ks.is_active():
        return False, ks.status().get("reason", "")
    return True, ""


def _check_budget():
    if _BudgetManager is None:
        return True, "BudgetManager unavailable"
    bm = _BudgetManager()
    if not bm.can_run():
        return False, f"Budget exhausted. Remaining: {bm.remaining()}"
    return True, ""


def _increment_budget():
    if _BudgetManager is not None:
        try:
            _BudgetManager().increment()
        except Exception:
            pass


def _generate_fa1_handoff(goal):
    """
    Generate FA1_HANDOFF_V1 handoff files.

    Returns (next_prompt_md, prompt_ready_dict, run_id).
    """
    goal_id = goal.get("id", "GOAL_XXX")
    title = goal.get("title", "")
    risk = goal.get("risk", "LOW")
    rationale = goal.get("rationale", "")
    sandbox_dir = str(Path(__file__).parent.parent / "sandbox")
    forbidden_paths = goal.get("forbidden_paths", ["src/", "config/", "self_state.json"])

    # Canonical run_id: AO3_<goal_id>
    run_id = f"AO3_{goal_id}"

    # 1. next_prompt.md — human/AI-readable task prompt
    forbidden_list = "\n".join(f"- {p}" for p in forbidden_paths)
    prompt_md = f"""# Task: {goal_id} — {title}

## Context
- **Goal ID:** {goal_id}
- **Run ID:** {run_id}
- **Risk Level:** {risk}
- **Rationale:** {rationale}

## Instructions
Execute this goal. Work ONLY in the allowed sandbox directory.

## Allowed Paths
- **Sandbox:** {sandbox_dir}

## Forbidden Paths
{forbidden_list}

## Output Requirements
1. Write report to: `{sandbox_dir}/reports/{goal_id}_report.md`
2. Write final output to: `orchestrator_runtime/cline_outbox/last_output.md`
3. Signal completion by creating: `orchestrator_runtime/cline_outbox/output_ready.json`

## output_ready.json Format
```json
{{
  "run_id": "{run_id}",
  "iteration": 1,
  "timestamp": "ISO 8601 timestamp",
  "status": "ready",
  "checksum": "first 16 chars of SHA-256 of last_output.md content"
}}
```

## Safety Constraints
- Do NOT modify src/, config/, or self_state.json
- Do NOT make external network calls unless explicitly authorized
- All output must be written to the sandbox directory
- If you encounter an error you cannot resolve, write an error report and signal completion
"""

    # 2. prompt_ready.json — structured metadata
    checksum = hashlib.sha256(prompt_md.encode("utf-8")).hexdigest()[:16]
    prompt_ready = {
        "run_id": run_id,
        "goal_id": goal_id,
        "iteration": 1,
        "timestamp": _now(),
        "status": "ready",
        "checksum": checksum,
        "consumed": False,
        "protocol": "FA1_HANDOFF_V1",
        "source": "AO3_BRIDGE",
        "risk": risk,
        "sandbox_dir": sandbox_dir,
        "forbidden_paths": forbidden_paths,
        "expected_output_path": str(LAST_OUTPUT_PATH),
        "expected_signal_path": str(OUTPUT_READY_PATH),
    }

    return prompt_md, prompt_ready, run_id


def _write_fa1_handoff(prompt_md, prompt_ready, dry_run=False):
    """Write FA1 handoff files atomically."""
    if dry_run:
        return

    # Write next_prompt.md
    _atomic_write(NEXT_PROMPT_PATH, prompt_md)
    _log("NEXT_PROMPT_WRITTEN", run_id=prompt_ready["run_id"])

    # Write prompt_ready.json
    _atomic_write(PROMPT_READY_PATH, prompt_ready, is_json=True)
    _log("PROMPT_READY_WRITTEN", run_id=prompt_ready["run_id"])

    # Write deprecated task.json as legacy mirror
    _write_deprecated_task_json(prompt_ready, prompt_md)


def _write_deprecated_task_json(prompt_ready, prompt_md):
    """Write task.json as deprecated legacy mirror."""
    task_data = {
        "deprecated": True,
        "canonical_protocol": "FA1_HANDOFF_V1",
        "note": "This file is deprecated. Use next_prompt.md + prompt_ready.json instead.",
        "goal_id": prompt_ready["goal_id"],
        "run_id": prompt_ready["run_id"],
        "task_id": prompt_ready["run_id"],
        "title": prompt_ready.get("goal_id", ""),
        "risk": prompt_ready["risk"],
        "prompt": prompt_md,
        "sandbox_dir": prompt_ready["sandbox_dir"],
        "forbidden_paths": prompt_ready["forbidden_paths"],
        "generated_at": prompt_ready["timestamp"],
    }
    _atomic_write(TASK_JSON_PATH, task_data, is_json=True)
    _log("TASK_JSON_DEPRECATED_MIRROR", run_id=prompt_ready["run_id"])


class OrchestratorBridge:
    def __init__(self, max_retries=2):
        self.max_retries = max_retries

    def run_autonomous_cycle(self, dry_run=False, goal_ids=None):
        cycle_id = f"CYCLE_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        start_time = _now()

        _log("CYCLE_START", cycle_id=cycle_id, dry_run=dry_run, goal_ids=goal_ids)
        _notify("ESCALATION", message=f"Cycle {cycle_id} started (dry_run={dry_run})", severity="INFO")

        result = {
            "cycle_id": cycle_id,
            "dry_run": dry_run,
            "started_at": start_time,
            "steps": [],
        }

        # Step 1: Kill switch
        ks_ok, ks_reason = _check_kill_switch()
        result["steps"].append({"step": "kill_switch_check", "ok": ks_ok, "reason": ks_reason})
        _log("KILL_SWITCH_CHECK", cycle_id=cycle_id, ok=ks_ok)
        if not ks_ok:
            result["status"] = "ABORTED"
            result["abort_reason"] = ks_reason
            result["completed_at"] = _now()
            _log("CYCLE_ABORTED", cycle_id=cycle_id, reason=ks_reason)
            return result

        # Step 2: Budget
        bg_ok, bg_reason = _check_budget()
        result["steps"].append({"step": "budget_check", "ok": bg_ok, "reason": bg_reason})
        _log("BUDGET_CHECK", cycle_id=cycle_id, ok=bg_ok)
        if not bg_ok:
            result["status"] = "ABORTED"
            result["abort_reason"] = bg_reason
            result["completed_at"] = _now()
            _log("CYCLE_ABORTED", cycle_id=cycle_id, reason=bg_reason)
            return result

        # Step 3: Goal discovery
        goals = self._get_goals(goal_ids)
        result["steps"].append({"step": "goal_discovery", "count": len(goals), "goal_ids": [g["id"] for g in goals]})
        _log("GOALS_DISCOVERED", cycle_id=cycle_id, count=len(goals))

        if not goals:
            result["status"] = "EMPTY"
            result["completed_at"] = _now()
            return result

        # Step 4: Generate FA1 handoff + write files
        goal = goals[0]
        goal_id = goal["id"]
        prompt_md, prompt_ready, run_id = _generate_fa1_handoff(goal)

        _write_fa1_handoff(prompt_md, prompt_ready, dry_run=dry_run)

        result["steps"].append({
            "step": "fa1_handoff",
            "goal_id": goal_id,
            "run_id": run_id,
            "prompt_length": len(prompt_md),
            "protocol": "FA1_HANDOFF_V1",
            "files_written": not dry_run,
        })
        _log("FA1_HANDOFF_WRITTEN", cycle_id=cycle_id, run_id=run_id, goal_id=goal_id)

        # Step 5: HandoffWatcher (skip in dry_run)
        if dry_run:
            result["steps"].append({"step": "handoff_watcher", "status": "SKIPPED_DRY_RUN"})
        else:
            ready, output_data = self._wait_for_output_ready(timeout=HANDOFF_TIMEOUT)
            result["steps"].append({"step": "handoff_watcher", "ready": ready, "output_data": output_data})
            _log("HANDOFF_WATCHER", cycle_id=cycle_id, ready=ready)

            if not ready:
                # Timeout escalation
                result["steps"].append({
                    "step": "handoff_timeout",
                    "status": "TIMEOUT",
                    "escalation": "NEEDS_HUMAN",
                    "timeout_seconds": HANDOFF_TIMEOUT,
                })
                _log("HANDOFF_TIMEOUT", cycle_id=cycle_id, timeout=HANDOFF_TIMEOUT)
                _notify("ESCALATION", message=f"Handoff timeout after {HANDOFF_TIMEOUT}s — manual intervention needed", severity="ERROR")
            elif ready and _SelfCorrectingLoop is not None:
                # Step 6: Consume output + self-correcting loop
                success, output_md, output_ready = self._consume_output()

                # Validate run_id in output
                output_run_id = output_ready.get("run_id") if output_ready else None
                if output_run_id and output_run_id != run_id:
                    _log("RUN_ID_MISMATCH", expected=run_id, got=output_run_id)

                scl = _SelfCorrectingLoop(max_retries=self.max_retries)
                verdict = "PASS" if success and len(output_md) > 50 else "FAIL"
                feedback = output_md[:500] if output_md else "No output"
                scl_result = scl.process_goal(goal_id, verdict, feedback)

                result["steps"].append({
                    "step": "output_verification",
                    "success": success,
                    "verdict": verdict,
                    "scl_action": scl_result.get("action"),
                    "run_id_matched": output_run_id == run_id if output_run_id else False,
                })
                _log("OUTPUT_VERIFICATION", cycle_id=cycle_id, verdict=verdict)

                if verdict == "PASS":
                    _increment_budget()
                    _notify("GOAL_DONE", goal_id=goal_id, message=f"PASS — {feedback[:100]}")
                else:
                    _notify("GOAL_FAILED", goal_id=goal_id, message=f"FAIL — {feedback[:100]}", severity="ERROR")

                result["verdict"] = verdict
                result["scl_result"] = scl_result
            elif not dry_run and ready:
                result["steps"].append({"step": "output_verification", "status": "SCL_UNAVAILABLE"})

        result["status"] = "DRY_RUN_COMPLETE" if dry_run else "COMPLETE"
        result["completed_at"] = _now()
        _log("CYCLE_COMPLETE", cycle_id=cycle_id, status=result["status"])
        _notify("ESCALATION", message=f"Cycle {cycle_id}: {result['status']}")

        return
