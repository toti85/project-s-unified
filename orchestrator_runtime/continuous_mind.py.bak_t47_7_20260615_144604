"""
Continuous Mind v0.1 — Project-S Heartbeat Loop

Sz autonomous execution cycle:
  1. Pick next pending goal from goal_queue.json
  2. Generate prompt via sz_prompt_generator
  3. Write prompt to cline_inbox/ (FA1_HANDOFF_V1 protocol)
  4. Poll cline_outbox/ for output_ready.json
  5. Consume via bridge_runner (T37/T38 gateway: ALLOW/PAUSE/DENY)
  6. ALLOW → SCL processes, goal marked DONE
     PAUSE → logged to active_loops/pause_queue.jsonl, awaits human
     DENY  → logged to active_loops/deny_log.jsonl, goal skipped
  7. Sleep heartbeat interval, repeat

Kill switch: active → loop halts immediately.
Budget: exhausted → loop halts and activates kill switch.
Dry-run: --dry-run → generates + prints prompt but never writes inbox.

Usage:
    python orchestrator_runtime/continuous_mind.py
    python orchestrator_runtime/continuous_mind.py --dry-run
    python orchestrator_runtime/continuous_mind.py --once            # single iteration
    python orchestrator_runtime/continuous_mind.py --heartbeat 30   # 30s interval
    python orchestrator_runtime/continuous_mind.py --max-cycles 5   # safety cap
    python orchestrator_runtime/continuous_mind.py --run-id GOAL_XY # consume only
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── Paths ─────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parents[1]
ORCHESTRATOR_ROOT = Path(__file__).resolve().parent

GOAL_QUEUE_PATH = ORCHESTRATOR_ROOT / "goal_queue.json"
INBOX_DIR = ORCHESTRATOR_ROOT / "cline_inbox"
OUTBOX_DIR = ORCHESTRATOR_ROOT / "cline_outbox"
ACTIVE_LOOPS_DIR = ORCHESTRATOR_ROOT / "active_loops"
GOVERNANCE_DIR = ORCHESTRATOR_ROOT / "governance"

CM_LOG_PATH = ACTIVE_LOOPS_DIR / "cm_v01_cycle_log.jsonl"
PAUSE_QUEUE_PATH = ACTIVE_LOOPS_DIR / "cm_v01_pause_queue.jsonl"
DENY_LOG_PATH = ACTIVE_LOOPS_DIR / "cm_v01_deny_log.jsonl"
STATE_PATH = ACTIVE_LOOPS_DIR / "cm_v01_state.json"

# ── Sys path for imports ───────────────────────────────────────────────
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

# ── Logging ───────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [CM] %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
log = logging.getLogger("continuous_mind")

# ── Constants ─────────────────────────────────────────────────────────

DEFAULT_HEARTBEAT_SECONDS = 60
DEFAULT_MAX_CYCLES = 100
DEFAULT_OUTPUT_WAIT_SECONDS = 600
DEFAULT_POLL_INTERVAL_SECONDS = 5

DONE_STATUSES = {"DONE", "COMPLETED", "CLOSED", "RESOLVED"}
SKIP_RATIONALE = "already completed"

# ── Governance imports (lazy, fail-gracefully) ─────────────────────────

def _load_kill_switch():
    try:
        from orchestrator_runtime.governance.kill_switch import KillSwitch
        return KillSwitch()
    except ImportError:
        return None

def _load_budget():
    try:
        from orchestrator_runtime.governance.budget_manager import BudgetManager
        return BudgetManager()
    except ImportError:
        return None

# ── File helpers ───────────────────────────────────────────────────────

def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def _write_json_atomic(path: Path, data: dict) -> None:
    ACTIVE_LOOPS_DIR.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
    tmp.replace(path)


def _append_jsonl(path: Path, entry: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

# ── Goal queue ────────────────────────────────────────────────────────

def _pick_next_goal() -> dict | None:
    """Return the highest-priority pending goal from goal_queue.json, or None."""
    if not GOAL_QUEUE_PATH.exists():
        log.warning("goal_queue.json not found at %s", GOAL_QUEUE_PATH)
        return None

    try:
        data = _read_json(GOAL_QUEUE_PATH)
    except Exception as exc:
        log.error("Cannot read goal_queue.json: %s", exc)
        return None

    goals = data if isinstance(data, list) else data.get("goals") or data.get("pending_goals") or []

    pending = []
    for goal in goals:
        if not isinstance(goal, dict):
            continue
        status = str(goal.get("status", "PENDING")).strip().upper()
        rationale = str(goal.get("rationale", "")).strip().lower()
        if status in DONE_STATUSES:
            continue
        if SKIP_RATIONALE in rationale:
            continue
        pending.append(goal)

    if not pending:
        return None

    # Sort by numeric priority field if present
    def _sort_key(g: dict) -> int:
        p = g.get("priority")
        try:
            return int(p)
        except (TypeError, ValueError):
            return 9999

    pending.sort(key=_sort_key)
    return pending[0]


def _mark_goal_done(goal_id: str) -> bool:
    """Mark a goal as DONE in goal_queue.json. Returns True on success."""
    if not GOAL_QUEUE_PATH.exists():
        return False
    try:
        data = _read_json(GOAL_QUEUE_PATH)
        goals = data if isinstance(data, list) else data.get("goals") or []
        for goal in goals:
            if isinstance(goal, dict) and goal.get("id") == goal_id:
                goal["status"] = "DONE"
                goal["done_at"] = _now_iso()
                break
        tmp = GOAL_QUEUE_PATH.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
        tmp.replace(GOAL_QUEUE_PATH)
        return True
    except Exception as exc:
        log.error("Cannot mark goal %s DONE: %s", goal_id, exc)
        return False

# ── Prompt generation ─────────────────────────────────────────────────

def _generate_prompt(goal: dict, mission_number: int) -> str:
    """
    Generate a Cline mission prompt for a given goal.
    Delegates to sz_prompt_generator internals when available,
    falls back to a minimal inline template.
    """
    try:
        from orchestrator_runtime.sz_prompt_generator import (
            parse_self_state,
            parse_goal_queue,
            recent_reports,
            read_last_output_head,
            build_context,
            choose_mission,
            materialize_template,
            slugify,
            next_mission_number,
        )

        state = parse_self_state()
        goals = parse_goal_queue()
        reports = recent_reports()
        last_output_head = read_last_output_head()
        mission = choose_mission(state, goals, reports)
        slug = slugify(mission["title"])
        context_lines = build_context(state, reports, last_output_head)

        lines = [
            f"AO5_T{mission_number}",
            "",
            f"Working directory: C:\\ProjectS-Unified",
            "",
            f"EXECUTION MODE: {mission['execution_mode']}",
            "",
            "CONTEXT:",
        ]
        lines.extend(context_lines)
        lines += [
            "",
            "TASK:",
        ]
        for phase in mission["phases"]:
            lines.append(phase)
        lines += ["", "OUTPUT FILES EXPECTED:"]
        for out in mission["outputs"]:
            materialized = (
                out.replace("<N>", str(mission_number))
                   .replace("<mission_id>", f"AO5_T{mission_number}")
                   .replace("<slug>", slug)
                   .replace("<date>", datetime.now(timezone.utc).strftime("%Y%m%d"))
            )
            lines.append(f"- {materialized}")
        lines += ["", "RETURN VALUES:"]
        for rv in mission["return_values"]:
            lines.append(f"- {rv}")
        lines += [
            "",
            "CRITICAL CONSTRAINTS:",
            "- No src/ modifications without Toti approval",
            "- No git push without Toti approval",
            "- All file ops in sandbox/ + reports/ + cline_outbox/",
            "",
            "RISK_010 REMINDER:",
            "- last_output.md FINAL first",
            "- checksum computed",
            "- output_ready.json LAST",
            "",
            "PROOF NOT JUST CODE:",
            "- Show evidence, not just intent",
            "- Prefer verification artifacts and concrete file references",
            "",
            f"GENERATOR META: reason={mission['reason']} generated_utc={datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            f"GENERATOR META: proposal={mission['summary']}",
        ]
        return "\n".join(lines)

    except ImportError as exc:
        log.warning("sz_prompt_generator not available (%s), using inline fallback", exc)

    # Inline fallback: minimal but functional
    goal_id = goal.get("id", "UNKNOWN")
    goal_title = goal.get("title", "Unnamed goal")
    ts = datetime.now(timezone.utc).strftime("%Y%m%d")

    return (
        f"AO5_T{mission_number}\n\n"
        f"Working directory: C:\\ProjectS-Unified\n\n"
        f"EXECUTION MODE: SURGICAL\n\n"
        f"GOAL: {goal_id} — {goal_title}\n\n"
        f"TASK:\n"
        f"Phase 1 — Understand the goal context, locate relevant files.\n"
        f"Phase 2 — Implement the minimum necessary change.\n"
        f"Phase 3 — Validate and write closeout report.\n\n"
        f"OUTPUT FILES EXPECTED:\n"
        f"- reports/MS_AO5_T{mission_number}_{goal_id}_{ts}.md\n"
        f"- orchestrator_runtime/cline_outbox/last_output.md\n"
        f"- orchestrator_runtime/cline_outbox/output_ready.json\n\n"
        f"CRITICAL CONSTRAINTS:\n"
        f"- No git push without Toti approval\n\n"
        f"RISK_010 REMINDER:\n"
        f"- last_output.md FINAL first\n"
        f"- checksum computed\n"
        f"- output_ready.json LAST\n"
    )

# ── Inbox write (FA1_HANDOFF_V1) ──────────────────────────────────────

def _write_inbox(prompt: str, run_id: str, iteration: int) -> None:
    """Write next_prompt.md then prompt_ready.json — FA1_HANDOFF_V1 order."""
    INBOX_DIR.mkdir(parents=True, exist_ok=True)

    prompt_path = INBOX_DIR / "next_prompt.md"
    prompt_path.write_text(prompt, encoding="utf-8")

    ready = {
        "run_id": run_id,
        "iteration": iteration,
        "status": "READY",
        "timestamp": _now_iso(),
        "next_prompt_file": "orchestrator_runtime/cline_inbox/next_prompt.md",
        "context": f"CM v0.1 heartbeat — {run_id}",
    }
    ready_path = INBOX_DIR / "prompt_ready.json"
    with open(ready_path, "w", encoding="utf-8") as fh:
        json.dump(ready, fh, indent=2, ensure_ascii=False)

    log.info("Inbox written: run_id=%s iteration=%d", run_id, iteration)

# ── Outbox poll ───────────────────────────────────────────────────────

def _wait_for_output(run_id: str, timeout: int, poll_interval: int) -> bool:
    """
    Poll cline_outbox/output_ready.json until:
      - consumed=false AND run_id matches → return True
      - timeout exceeded → return False
    """
    output_ready_path = OUTBOX_DIR / "output_ready.json"
    deadline = time.time() + timeout
    log.info("Waiting for output: run_id=%s timeout=%ds", run_id, timeout)

    while time.time() < deadline:
        if output_ready_path.exists():
            try:
                meta = _read_json(output_ready_path)
                if (
                    not meta.get("consumed", True)
                    and meta.get("run_id") == run_id
                    and meta.get("status") in ("ready", "READY")
                ):
                    log.info("Output ready detected for run_id=%s", run_id)
                    return True
            except Exception as exc:
                log.debug("output_ready.json parse error (will retry): %s", exc)
        time.sleep(poll_interval)

    log.warning("Timeout waiting for output: run_id=%s", run_id)
    return False

# ── Gateway consume ───────────────────────────────────────────────────

def _consume_via_gateway(run_id: str, goal_id: str, expected_iteration: int = 1) -> dict:
    """
    Consume executor output via bridge_runner, then resolve gateway decision.

    run_id  — FA1_HANDOFF_V1 file identifier (used for checksum/consume)
    goal_id — queue entry identifier (used for risk classification)

    Returns dict with at minimum:
      status: ACCEPTED | WAITING_FOR_EXECUTOR | REJECTED_* | BLOCKED_*
      gateway_decision: ALLOW | PAUSE | DENY
    """
    try:
        from orchestrator_runtime.governance.bridge_runner import consume_executor_output
        result = consume_executor_output(run_id, expected_iteration=expected_iteration)
    except Exception as exc:
        log.error("bridge_runner consume failed for %s: %s", run_id, exc)
        return {
            "status": "CONSUME_ERROR",
            "run_id": run_id,
            "gateway_decision": "DENY",
            "error": str(exc),
        }

    # If consume succeeded, classify the GOAL (not the run_id) for gateway decision.
    # The run_id encodes the goal_id but may not match queue keys directly.
    if result.get("status") == "ACCEPTED" and "gateway_decision" not in result:
        try:
            from orchestrator_runtime.governance.risk_classifier import classify_execution_request
            classification = classify_execution_request(goal_id)
            result["gateway_decision"] = classification.get("gateway_decision", "ALLOW")
            result["gateway_reason"] = classification.get("reason", "")
            log.info(
                "Gateway classification for goal_id=%s: %s",
                goal_id, result["gateway_decision"],
            )
        except Exception as exc:
            log.warning("Gateway classification failed for %s: %s — defaulting ALLOW", goal_id, exc)
            result["gateway_decision"] = "ALLOW"

    return result

# ── CM state ──────────────────────────────────────────────────────────

def _load_cm_state() -> dict:
    if STATE_PATH.exists():
        try:
            return _read_json(STATE_PATH)
        except Exception:
            pass
    return {
        "version": "0.1",
        "started": _now_iso(),
        "total_cycles": 0,
        "goals_completed": 0,
        "goals_paused": 0,
        "goals_denied": 0,
        "last_cycle_at": None,
        "last_run_id": None,
    }


def _save_cm_state(state: dict) -> None:
    _write_json_atomic(STATE_PATH, state)

# ── Core loop ─────────────────────────────────────────────────────────

def run_heartbeat(
    heartbeat: int = DEFAULT_HEARTBEAT_SECONDS,
    max_cycles: int = DEFAULT_MAX_CYCLES,
    output_wait: int = DEFAULT_OUTPUT_WAIT_SECONDS,
    dry_run: bool = False,
    once: bool = False,
) -> None:
    """Main continuous mind loop."""
    ks = _load_kill_switch()
    budget = _load_budget()

    cm_state = _load_cm_state()
    cm_state.setdefault("started", _now_iso())
    log.info(
        "CM v0.1 starting — heartbeat=%ds max_cycles=%d dry_run=%s",
        heartbeat, max_cycles, dry_run,
    )

    cycle = 0
    while cycle < max_cycles:
        # ── Kill switch check ──────────────────────────────────────
        if ks and ks.is_active():
            log.warning("Kill switch active — CM halting.")
            _append_jsonl(CM_LOG_PATH, {
                "event": "cm_kill_switch_halt",
                "cycle": cycle,
                "at": _now_iso(),
            })
            break

        # ── Budget check ───────────────────────────────────────────
        if budget:
            try:
                remaining = budget.remaining()
                if remaining <= 0:
                    log.warning("Budget exhausted (remaining=%s) — CM halting.", remaining)
                    if ks:
                        ks.activate("CM v0.1: budget exhausted")
                    _append_jsonl(CM_LOG_PATH, {
                        "event": "cm_budget_halt",
                        "cycle": cycle,
                        "remaining": remaining,
                        "at": _now_iso(),
                    })
                    break
            except Exception as exc:
                log.debug("Budget check failed (non-fatal): %s", exc)

        cycle += 1
        cm_state["total_cycles"] = cycle
        cm_state["last_cycle_at"] = _now_iso()

        log.info("── Cycle %d / %d ─────────────────────────────────", cycle, max_cycles)

        # ── Pick goal ──────────────────────────────────────────────
        goal = _pick_next_goal()
        if goal is None:
            log.info("No pending goals — idle cycle.")
            _append_jsonl(CM_LOG_PATH, {
                "event": "cm_idle",
                "cycle": cycle,
                "at": _now_iso(),
            })
            if once:
                break
            time.sleep(heartbeat)
            continue

        goal_id = goal.get("id", f"UNKNOWN_{cycle}")
        goal_title = goal.get("title", "Unnamed goal")
        log.info("Goal selected: %s — %s", goal_id, goal_title)

        # Mission number: scan existing reports + missions to find next T<N>
        try:
            from orchestrator_runtime.sz_prompt_generator import next_mission_number
            mission_num = next_mission_number()
        except Exception:
            # Fallback: read cm_state for rough estimate
            mission_num = cm_state.get("total_cycles", cycle) + 39  # post-T39 baseline

        run_id = goal_id  # use bare goal_id so gateway can look it up in goal_queue
        cm_state["last_run_id"] = run_id

        # ── Generate prompt ────────────────────────────────────────
        log.info("Generating prompt for run_id=%s", run_id)
        try:
            prompt = _generate_prompt(goal, mission_num)
        except Exception as exc:
            log.error("Prompt generation failed: %s", exc)
            _append_jsonl(CM_LOG_PATH, {
                "event": "cm_prompt_error",
                "cycle": cycle,
                "goal_id": goal_id,
                "error": str(exc),
                "at": _now_iso(),
            })
            if once:
                break
            time.sleep(heartbeat)
            continue

        if dry_run:
            log.info("DRY-RUN — prompt generated, NOT writing to inbox.")
            print("\n" + "=" * 70)
            print(f"DRY-RUN PROMPT (run_id={run_id})")
            print("=" * 70)
            print(prompt)
            print("=" * 70 + "\n")
            _append_jsonl(CM_LOG_PATH, {
                "event": "cm_dry_run",
                "cycle": cycle,
                "goal_id": goal_id,
                "run_id": run_id,
                "prompt_chars": len(prompt),
                "at": _now_iso(),
            })
            _save_cm_state(cm_state)
            break  # dry-run always exits after first prompt

        # ── Write inbox ────────────────────────────────────────────
        try:
            _write_inbox(prompt, run_id, iteration=1)
        except Exception as exc:
            log.error("Inbox write failed: %s", exc)
            _append_jsonl(CM_LOG_PATH, {
                "event": "cm_inbox_error",
                "cycle": cycle,
                "goal_id": goal_id,
                "run_id": run_id,
                "error": str(exc),
                "at": _now_iso(),
            })
            if once:
                break
            time.sleep(heartbeat)
            continue

        _append_jsonl(CM_LOG_PATH, {
            "event": "cm_inbox_written",
            "cycle": cycle,
            "goal_id": goal_id,
            "run_id": run_id,
            "at": _now_iso(),
        })

        # ── Wait for executor output ───────────────────────────────
        output_arrived = _wait_for_output(run_id, output_wait, DEFAULT_POLL_INTERVAL_SECONDS)

        if not output_arrived:
            log.warning("Output timeout for run_id=%s — skipping consume.", run_id)
            _append_jsonl(CM_LOG_PATH, {
                "event": "cm_output_timeout",
                "cycle": cycle,
                "goal_id": goal_id,
                "run_id": run_id,
                "at": _now_iso(),
            })
            if once:
                break
            time.sleep(heartbeat)
            continue

        # ── Gateway consume ────────────────────────────────────────
        result = _consume_via_gateway(run_id, goal_id, expected_iteration=cm_state.get("total_cycles", cycle))
        status = result.get("status", "UNKNOWN")
        gateway = result.get("gateway_decision", "UNKNOWN")

        log.info("Consume result: status=%s gateway=%s", status, gateway)

        _append_jsonl(CM_LOG_PATH, {
            "event": "cm_consume_result",
            "cycle": cycle,
            "goal_id": goal_id,
            "run_id": run_id,
            "status": status,
            "gateway_decision": gateway,
            "at": _now_iso(),
        })

        # ── Route by gateway decision ──────────────────────────────
        if status == "ACCEPTED" and gateway == "ALLOW":
            log.info("ALLOW — goal %s processed by SCL.", goal_id)
            _mark_goal_done(goal_id)
            cm_state["goals_completed"] = cm_state.get("goals_completed", 0) + 1
            _append_jsonl(CM_LOG_PATH, {
                "event": "cm_goal_completed",
                "cycle": cycle,
                "goal_id": goal_id,
                "run_id": run_id,
                "at": _now_iso(),
            })

        elif gateway == "PAUSE" or status in ("PENDING_HUMAN", "AWAIT_HUMAN"):
            log.warning("PAUSE — goal %s queued for human review.", goal_id)
            cm_state["goals_paused"] = cm_state.get("goals_paused", 0) + 1
            _append_jsonl(PAUSE_QUEUE_PATH, {
                "goal_id": goal_id,
                "run_id": run_id,
                "cycle": cycle,
                "consume_result": result,
                "queued_at": _now_iso(),
            })

        elif gateway == "DENY" or status == "BLOCKED_POLICY":
            log.warning("DENY — goal %s blocked by policy.", goal_id)
            cm_state["goals_denied"] = cm_state.get("goals_denied", 0) + 1
            _append_jsonl(DENY_LOG_PATH, {
                "goal_id": goal_id,
                "run_id": run_id,
                "cycle": cycle,
                "consume_result": result,
                "denied_at": _now_iso(),
            })
            # Mark denied goal so we don't retry it indefinitely
            _mark_goal_done(goal_id)

        else:
            log.info("Unhandled consume status=%s — continuing.", status)

        _save_cm_state(cm_state)

        if once:
            log.info("--once flag set — exiting after first cycle.")
            break

        log.info("Sleeping %ds before next cycle.", heartbeat)
        time.sleep(heartbeat)

    log.info(
        "CM v0.1 finished. cycles=%d completed=%d paused=%d denied=%d",
        cm_state.get("total_cycles", 0),
        cm_state.get("goals_completed", 0),
        cm_state.get("goals_paused", 0),
        cm_state.get("goals_denied", 0),
    )
    _save_cm_state(cm_state)


# ── Consume-only mode ─────────────────────────────────────────────────

def consume_only(run_id: str) -> None:
    """Manually consume a specific run_id via gateway. No inbox write."""
    log.info("Consume-only mode: run_id=%s", run_id)
    result = _consume_via_gateway(run_id, run_id)
    print(json.dumps(result, indent=2, ensure_ascii=False))


# ── CLI ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="continuous_mind",
        description="Continuous Mind v0.1 — Project-S autonomous heartbeat loop",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate and print prompt but do NOT write to inbox.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run exactly one cycle then exit.",
    )
    parser.add_argument(
        "--heartbeat",
        type=int,
        default=DEFAULT_HEARTBEAT_SECONDS,
        metavar="SECONDS",
        help=f"Sleep interval between cycles (default: {DEFAULT_HEARTBEAT_SECONDS}s).",
    )
    parser.add_argument(
        "--max-cycles",
        type=int,
        default=DEFAULT_MAX_CYCLES,
        metavar="N",
        help=f"Hard cap on total cycles (default: {DEFAULT_MAX_CYCLES}).",
    )
    parser.add_argument(
        "--output-wait",
        type=int,
        default=DEFAULT_OUTPUT_WAIT_SECONDS,
        metavar="SECONDS",
        help=f"Max seconds to wait for executor output (default: {DEFAULT_OUTPUT_WAIT_SECONDS}s).",
    )
    parser.add_argument(
        "--run-id",
        metavar="RUN_ID",
        help="Consume-only mode: consume a specific run_id from the outbox.",
    )

    args = parser.parse_args()

    if args.run_id:
        consume_only(args.run_id)
        return

    run_heartbeat(
        heartbeat=args.heartbeat,
        max_cycles=args.max_cycles,
        output_wait=args.output_wait,
        dry_run=args.dry_run,
        once=args.once,
    )


if __name__ == "__main__":
    main()
