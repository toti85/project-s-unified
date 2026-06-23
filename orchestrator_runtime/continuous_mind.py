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
import asyncio
import hashlib
import json
import logging
import os
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

try:
    from orchestrator_runtime.taste_model.mission_outcome_logger import log_outcome as _log_outcome
except Exception:
    _log_outcome = None  # type: ignore[assignment]

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
SKIP_STATUSES = DONE_STATUSES | {"PAUSED", "FAILED", "NEEDS_HUMAN"}  # AO8J_4: skip paused/failed goals
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
        # AO8J_4: skip DONE/PAUSED/FAILED/NEEDS_HUMAN goals
        if status in SKIP_STATUSES:
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


def _set_goal_status(goal_id: str, status: str, note: str = "") -> bool:
    """Set any status on a goal. Returns True on success."""
    if not GOAL_QUEUE_PATH.exists():
        return False
    try:
        data = _read_json(GOAL_QUEUE_PATH)
        goals = data if isinstance(data, list) else data.get("goals") or []
        for goal in goals:
            if isinstance(goal, dict) and goal.get("id") == goal_id:
                goal["status"] = status
                goal["status_changed_at"] = _now_iso()
                if note:
                    goal["status_note"] = note
                break
        tmp = GOAL_QUEUE_PATH.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
        tmp.replace(GOAL_QUEUE_PATH)
        return True
    except Exception as exc:
        log.error("Cannot set goal %s -> %s: %s", goal_id, status, exc)
        return False

def _mark_goal_done(goal_id: str) -> bool:
    """Mark a goal as DONE in goal_queue.json."""
    return _set_goal_status(goal_id, "DONE")

def _mark_goal_failed(goal_id: str, reason: str = "") -> bool:
    """Mark a goal as FAILED so _pick_next_goal skips it. AO8J_4."""
    return _set_goal_status(goal_id, "FAILED", note=reason)

def _mark_goal_paused(goal_id: str) -> bool:
    """Mark a goal as PAUSED (human review) so _pick_next_goal skips it. AO8J_4."""
    return _set_goal_status(goal_id, "PAUSED", note="Awaiting human review per PAUSE gateway decision")

# ── AO8J_4: Output identity check ────────────────────────────────────

def _check_output_identity(expected_run_id: str, expected_goal_id: str) -> str | None:
    """
    Read last_output.md and verify the embedded Run ID / Goal ID header
    matches expectations. Returns None if OK, or a description string if mismatch.
    """
    last_output_path = OUTBOX_DIR / "last_output.md"
    if not last_output_path.exists():
        return f"last_output.md not found (expected run_id={expected_run_id})"

    try:
        head = last_output_path.read_text(encoding="utf-8").split("\n")[:5]
    except OSError as exc:
        return f"cannot read last_output.md: {exc}"

    found_run_id = None
    found_goal_id = None
    for line in head:
        if line.startswith("Run ID:"):
            found_run_id = line.replace("Run ID:", "").strip()
        elif line.startswith("Goal ID:"):
            found_goal_id = line.replace("Goal ID:", "").strip()

    if found_run_id is None and found_goal_id is None:
        return "output has no Run ID / Goal ID header (pre-AO8J_4 format)"

    issues = []
    if found_run_id and found_run_id != expected_run_id:
        issues.append(f"Run ID mismatch: expected={expected_run_id} got={found_run_id}")
    if found_goal_id and found_goal_id != expected_goal_id:
        issues.append(f"Goal ID mismatch: expected={expected_goal_id} got={found_goal_id}")

    return "; ".join(issues) if issues else None


def _archive_outbox_for_mismatch(run_id: str) -> None:
    """Move outbox files to archive with MISMATCH label. AO8J_4."""
    archive_dir = OUTBOX_DIR / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    for fname in ["last_output.md", "output_ready.json"]:
        src = OUTBOX_DIR / fname
        if src.exists():
            dst = archive_dir / f"{ts}_MISMATCH_{run_id}_{fname}"
            src.rename(dst)
            log.info("Archived mismatched outbox %s -> %s", src.name, dst.name)

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

    # If consume succeeded, route through bridge_runner.get_verdict_for_content()
    # (T47.11: fixes architectural gap — logs bridge_gateway_allow/deny to
    # governance/cycle_log.jsonl for CM-SAI direct runs, completing audit trail).
    if result.get("status") == "ACCEPTED" and "gateway_decision" not in result:
        try:
            from orchestrator_runtime.governance.bridge_runner import get_verdict_for_content
            last_output_path = OUTBOX_DIR / "last_output.md"
            content = (
                last_output_path.read_text(encoding="utf-8")
                if last_output_path.exists()
                else ""
            )
            # Pass goal_id as run_id so _evaluate_execution_gateway classifies correctly
            verdict = get_verdict_for_content(content=content, run_id=goal_id)
            result["gateway_decision"] = verdict.get("gateway_decision", "ALLOW")
            result["gateway_reason"] = verdict.get("reason", "")
            result["bridge_verdict"] = verdict
            log.info(
                "bridge_runner verdict for goal_id=%s: %s",
                goal_id, result["gateway_decision"],
            )
        except Exception as exc:
            # Never break consume flow — fall back to local classify
            log.warning("bridge_runner verdict call failed for %s: %s — fallback classify", goal_id, exc)
            try:
                from orchestrator_runtime.governance.risk_classifier import classify_execution_request
                classification = classify_execution_request(goal_id)
                result["gateway_decision"] = classification.get("gateway_decision", "ALLOW")
                result["gateway_reason"] = classification.get("reason", "")
            except Exception as exc2:
                log.warning("Gateway classification also failed for %s: %s — defaulting ALLOW", goal_id, exc2)
                result["gateway_decision"] = "ALLOW"

    return result

# ── SAI direct execution (T47.8) ───────────────────────────────────────────

def _execute_via_sai(goal_id: str, prompt: str, cycle: int) -> dict:
    """
    Run a goal directly through SAI (no human inbox handoff).
    Calls sai_pre_execution_gate, executes SAI, writes to outbox.
    Returns dict with: success, run_id, checksum, error.
    Set CM_SAI_DIRECT_MODE=1 to enable this path in the CM cycle.
    """
    try:
        from orchestrator_runtime.governance.sai_gateway_adapter import (
            sai_pre_execution_gate,
            write_sai_output_to_outbox,
            build_sai_handoff_content,
        )
    except ImportError as exc:
        return {"success": False, "reason": f"sai_gateway_adapter import failed: {exc}"}

    try:
        mission_id = f"CM_CYCLE_{cycle}_{goal_id}"

        # Pre-execution gate
        gate = sai_pre_execution_gate(mission_id, goal_id=goal_id)
        if not gate["allowed"]:
            return {
                "success": False,
                "reason": f"Gate denied: {gate.get('reason', 'unknown')}",
                "gate": gate,
            }

        # Import and run SAI
        from src.core.super_intelligent_ai import SuperIntelligentAI
        ai = SuperIntelligentAI(use_meta_controller=False)

        sai_result = asyncio.run(
            asyncio.wait_for(
                ai.execute_intelligent_task(prompt),
                timeout=120,
            )
        )

        # Build handoff content and write to outbox with goal_id as run_id
        content = build_sai_handoff_content(mission_id, sai_result)
        write_result = write_sai_output_to_outbox(
            mission_id,
            content,
            iteration=cycle,
            goal_id=goal_id,
        )

        return {
            "success": write_result.get("success", False),
            "run_id": write_result.get("run_id", goal_id),
            "checksum": write_result.get("checksum"),
            "sai_success": sai_result.get("success"),
            "error": write_result.get("error"),
        }

    except asyncio.TimeoutError:
        return {"success": False, "reason": "SAI timeout after 120s"}
    except Exception as exc:
        return {"success": False, "reason": f"SAI execution error: {exc}"}

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

        # ── Continue CLI executor mode (CM_CONTINUE_MODE=1) ────────
        # Set CM_CONTINUE_MODE=1 to route auto_approve LOW/MEDIUM goals
        # through the Continue CLI executor (cn) instead of SAI or inbox.
        # Existing SAI mode and inbox fallback remain unchanged when flag is absent.
        use_continue = (
            goal.get("auto_approve", False)
            and goal.get("risk", "HIGH") in ("LOW", "MEDIUM")
            and os.environ.get("CM_CONTINUE_MODE", "").lower() in ("1", "true", "yes")
        )

        # ── SAI direct mode (CM_SAI_DIRECT_MODE=1) ────────────────
        # Set CM_SAI_DIRECT_MODE=1 to enable direct SAI execution
        # for auto_approve LOW/MEDIUM goals (skips inbox handoff).
        use_sai_direct = (
            goal.get("auto_approve", False)
            and goal.get("risk", "HIGH") in ("LOW", "MEDIUM")
            and os.environ.get("CM_SAI_DIRECT_MODE", "").lower() in ("1", "true", "yes")
            and not use_continue  # Continue takes priority if both are set
        )

        if use_continue:
            log.info("Continue CLI mode for goal %s (auto_approve+%s)", goal_id, goal.get("risk"))

            # ── Watchdog check before proceeding ────────────────────
            try:
                from orchestrator_runtime.governance.continue_watchdog import decide
                wd = decide(outbox_dir=OUTBOX_DIR)
            except Exception as exc:
                log.warning("continue_watchdog not available (%s) — allowing", exc)
                wd = {"allow_continue": True, "reason": "WATCHDOG_UNAVAILABLE", "evidence": []}

            if not wd["allow_continue"]:
                log.warning("Watchdog blocked goal %s: %s — %s", goal_id, wd["reason"], wd.get("evidence"))
                _append_jsonl(CM_LOG_PATH, {
                    "event": "cm_watchdog_block",
                    "cycle": cycle,
                    "goal_id": goal_id,
                    "reason": wd["reason"],
                    "evidence": wd.get("evidence", []),
                    "at": _now_iso(),
                })
                _save_cm_state(cm_state)
                if once:
                    break
                time.sleep(heartbeat)
                continue

            _append_jsonl(CM_LOG_PATH, {
                "event": "cm_continue_start",
                "cycle": cycle,
                "goal_id": goal_id,
                "at": _now_iso(),
            })

            try:
                from orchestrator_runtime.governance.continue_executor_adapter import run_and_write
                continue_result = run_and_write(
                    prompt=prompt,
                    run_id=run_id,
                    iteration=cycle,
                    metadata={"goal_id": goal_id},
                )
            except Exception as exc:
                log.error("Continue run_and_write failed: %s", exc)
                _append_jsonl(CM_LOG_PATH, {
                    "event": "cm_continue_error",
                    "cycle": cycle,
                    "goal_id": goal_id,
                    "error": str(exc),
                    "at": _now_iso(),
                })
                if once:
                    break
                time.sleep(heartbeat)
                continue

            run = continue_result.get("run") or {}
            outbox = continue_result.get("outbox") or {}
            overall = continue_result.get("overall", "UNKNOWN")
            run_ok = overall == "OK" and run.get("status") == "OK"
            _append_jsonl(CM_LOG_PATH, {
                "event": "cm_continue_result",
                "cycle": cycle,
                "goal_id": goal_id,
                "run_id": run_id,
                "run_status": run.get("status"),
                "outbox_status": outbox.get("status"),
                "checksum": outbox.get("checksum"),
                "overall": overall,
                "reason": continue_result.get("reason"),
                "at": _now_iso(),
            })

            # ── AO8J_2: empty output — log failure, do NOT mark DONE, do NOT consume ──
            if overall == "EMPTY_OUTPUT":
                log.warning("Continue EMPTY_OUTPUT for goal %s: %s", goal_id, continue_result.get("reason", "unknown"))
                _append_jsonl(CM_LOG_PATH, {
                    "event": "cm_continue_empty_output",
                    "cycle": cycle,
                    "goal_id": goal_id,
                    "run_id": run_id,
                    "reason": continue_result.get("reason"),
                    "at": _now_iso(),
                })
                _save_cm_state(cm_state)
                if once:
                    break
                time.sleep(heartbeat)
                continue

            # ── AO8J_4: Pre-consume run_id mismatch guard ──────────────
            if run_ok:
                # Read last_output.md and verify it contains expected run_id/goal_id
                _mismatch = _check_output_identity(run_id, goal_id)
                if _mismatch:
                    log.warning("Run ID mismatch for goal %s: %s", goal_id, _mismatch)
                    _append_jsonl(CM_LOG_PATH, {
                        "event": "cm_mismatch_error",
                        "cycle": cycle,
                        "goal_id": goal_id,
                        "run_id": run_id,
                        "mismatch": _mismatch,
                        "at": _now_iso(),
                    })
                    # Archive the mismatched outbox
                    _archive_outbox_for_mismatch(run_id)
                    # Mark goal as FAILED so it won't be retried forever
                    _mark_goal_failed(goal_id, f"MISMATCH: {_mismatch}")
                    cm_state["goals_failed"] = cm_state.get("goals_failed", 0) + 1
                    _save_cm_state(cm_state)
                    if once:
                        break
                    time.sleep(heartbeat)
                    continue

                # Bridge consume the Continue output
                result = _consume_via_gateway(run_id, goal_id, expected_iteration=cycle)
                status = result.get("status", "UNKNOWN")
                gateway = result.get("gateway_decision", "UNKNOWN")

                log.info("Continue consume result: status=%s gateway=%s", status, gateway)
                _append_jsonl(CM_LOG_PATH, {
                    "event": "cm_consume_result",
                    "cycle": cycle,
                    "goal_id": goal_id,
                    "run_id": run_id,
                    "status": status,
                    "gateway_decision": gateway,
                    "via": "continue",
                    "at": _now_iso(),
                })

                # Taste Model logging
                if _log_outcome:
                    try:
                        _continue_log_status = (
                            "completed" if (status == "ACCEPTED" and gateway == "ALLOW") else
                            "blocked" if gateway == "DENY" else
                            "partial" if gateway == "PAUSE" else
                            "failed"
                        )
                        _log_outcome(
                            mission_id=goal_id.upper(),
                            date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                            claimed_status=_continue_log_status,
                            actual_status=_continue_log_status,
                            model_used="continue_cli_qwen3.6",
                            runtime_validated=(status == "ACCEPTED" and gateway == "ALLOW"),
                            value_immediate=3,
                            patterns=["cm_continue", f"cm_{status.lower()}", f"gw_{gateway.lower()}"],
                            notes=f"CM-Continue cycle {cycle}: {goal_id} status={status} gw={gateway}",
                        )
                    except Exception as exc:
                        log.warning("log_outcome failed (continue): %s", exc)

                if status == "ACCEPTED" and gateway == "ALLOW":
                    log.info("Continue ALLOW — goal %s completed.", goal_id)
                    _mark_goal_done(goal_id)
                    cm_state["goals_completed"] = cm_state.get("goals_completed", 0) + 1
                    _append_jsonl(CM_LOG_PATH, {
                        "event": "cm_goal_completed",
                        "cycle": cycle,
                        "goal_id": goal_id,
                        "run_id": run_id,
                        "via": "continue",
                        "at": _now_iso(),
                    })
                elif gateway == "PAUSE" or status in ("PENDING_HUMAN", "AWAIT_HUMAN"):
                    log.warning("Continue PAUSE — goal %s queued for human review.", goal_id)
                    cm_state["goals_paused"] = cm_state.get("goals_paused", 0) + 1
                    _append_jsonl(PAUSE_QUEUE_PATH, {
                        "goal_id": goal_id, "run_id": run_id, "cycle": cycle,
                        "consume_result": result, "queued_at": _now_iso(),
                    })
                    _append_jsonl(CM_LOG_PATH, {
                        "event": "cm_goal_blocked",
                        "cycle": cycle,
                        "goal_id": goal_id,
                        "run_id": run_id,
                        "reason": gateway,
                        "via": "continue",
                        "at": _now_iso(),
                    })
                    # AO8J_4: Mark PAUSED so _pick_next_goal skips it on next cycle
                    _mark_goal_paused(goal_id)
                elif gateway == "DENY" or status == "BLOCKED_POLICY":
                    log.warning("Continue DENY — goal %s blocked by policy.", goal_id)
                    cm_state["goals_denied"] = cm_state.get("goals_denied", 0) + 1
                    _append_jsonl(DENY_LOG_PATH, {
                        "goal_id": goal_id, "run_id": run_id, "cycle": cycle,
                        "consume_result": result, "denied_at": _now_iso(),
                    })
                    _append_jsonl(CM_LOG_PATH, {
                        "event": "cm_goal_blocked",
                        "cycle": cycle,
                        "goal_id": goal_id,
                        "run_id": run_id,
                        "reason": "DENY",
                        "via": "continue",
                        "at": _now_iso(),
                    })
                    _mark_goal_done(goal_id)
                else:
                    log.info("Continue consume unhandled status=%s — continuing.", status)
            else:
                log.warning("Continue execution failed: %s", run.get("error", "(no error field)"))

            _save_cm_state(cm_state)
            if once:
                log.info("--once flag set — exiting after Continue cycle.")
                break
            log.info("Sleeping %ds before next cycle.", heartbeat)
            time.sleep(heartbeat)
            continue  # skip inbox-write + polling below

        if use_sai_direct:
            log.info("SAI direct mode for goal %s (auto_approve+%s)", goal_id, goal.get("risk"))
            _append_jsonl(CM_LOG_PATH, {
                "event": "cm_sai_direct_start",
                "cycle": cycle,
                "goal_id": goal_id,
                "at": _now_iso(),
            })

            # ── Compute Arbiter V0: executor recommendation ────────
            try:
                from orchestrator_runtime.compute_arbiter import recommend_executor as _recommend_executor
                _arbiter_rec = _recommend_executor(
                    task_text=prompt,
                    risk_level=goal.get("risk", "UNKNOWN"),
                )
            except Exception as _arb_exc:
                log.warning("Compute Arbiter import/call failed (%s) — proceeding with SAI default.", _arb_exc)
                _arbiter_rec = {
                    "primary_executor": "sai",
                    "routing_enabled": False,
                    "confidence": 0.5,
                    "blocked": False,
                    "blocked_reason": None,
                    "warning": None,
                    "recommendation": "Arbiter unavailable — SAI default used.",
                }

            log.info(
                "Compute Arbiter: executor=%s confidence=%.2f blocked=%s",
                _arbiter_rec.get("primary_executor"),
                _arbiter_rec.get("confidence", 0.0),
                _arbiter_rec.get("blocked"),
            )
            _append_jsonl(CM_LOG_PATH, {
                "event": "cm_arbiter_recommendation",
                "cycle": cycle,
                "goal_id": goal_id,
                "primary_executor": _arbiter_rec.get("primary_executor"),
                "confidence": _arbiter_rec.get("confidence"),
                "blocked": _arbiter_rec.get("blocked"),
                "blocked_reason": _arbiter_rec.get("blocked_reason"),
                "warning": _arbiter_rec.get("warning"),
                "recommendation": _arbiter_rec.get("recommendation"),
                "at": _now_iso(),
            })

            # Guard 1: Arbiter recommends non-SAI executor (not possible in V0, but defensive)
            if _arbiter_rec.get("primary_executor") != "sai":
                _reason = f"Arbiter recommended non-SAI executor: {_arbiter_rec.get('primary_executor')}. V0 only supports SAI."
                log.error("Compute Arbiter: %s — halting cycle.", _reason)
                _append_jsonl(CM_LOG_PATH, {
                    "event": "cm_arbiter_halted",
                    "cycle": cycle,
                    "goal_id": goal_id,
                    "reason": _reason,
                    "at": _now_iso(),
                })
                _save_cm_state(cm_state)
                if once:
                    break
                time.sleep(heartbeat)
                continue

            # Guard 2: Blocked (HIGH risk or explicit block)
            if _arbiter_rec.get("blocked"):
                _reason = _arbiter_rec.get("blocked_reason", "Arbiter blocked execution.")
                log.warning("Compute Arbiter: goal %s blocked — %s", goal_id, _reason)
                _append_jsonl(CM_LOG_PATH, {
                    "event": "cm_arbiter_blocked",
                    "cycle": cycle,
                    "goal_id": goal_id,
                    "reason": _reason,
                    "at": _now_iso(),
                })
                _save_cm_state(cm_state)
                if once:
                    break
                time.sleep(heartbeat)
                continue

            # Guard 3: Very low confidence
            if _arbiter_rec.get("confidence", 1.0) < 0.3:
                _reason = f"Arbiter confidence too low ({_arbiter_rec.get('confidence'):.2f} < 0.30). Human review recommended."
                log.warning("Compute Arbiter: %s — halting cycle for goal %s.", _reason, goal_id)
                _append_jsonl(CM_LOG_PATH, {
                    "event": "cm_arbiter_low_confidence",
                    "cycle": cycle,
                    "goal_id": goal_id,
                    "confidence": _arbiter_rec.get("confidence"),
                    "reason": _reason,
                    "at": _now_iso(),
                })
                _save_cm_state(cm_state)
                if once:
                    break
                time.sleep(heartbeat)
                continue

            if _arbiter_rec.get("warning"):
                log.warning("Compute Arbiter warning for %s: %s", goal_id, _arbiter_rec["warning"])
            # ── End Compute Arbiter V0 ─────────────────────────────

            sai_exec = _execute_via_sai(goal_id, prompt, cycle)

            _append_jsonl(CM_LOG_PATH, {
                "event": "cm_sai_direct_result",
                "cycle": cycle,
                "goal_id": goal_id,
                "success": sai_exec.get("success"),
                "sai_success": sai_exec.get("sai_success"),
                "run_id": sai_exec.get("run_id"),
                "reason": sai_exec.get("reason", ""),
                "at": _now_iso(),
            })

            if sai_exec["success"]:
                run_id = sai_exec["run_id"]
                result = _consume_via_gateway(run_id, goal_id, expected_iteration=cycle)
                status = result.get("status", "UNKNOWN")
                gateway = result.get("gateway_decision", "UNKNOWN")

                log.info("SAI consume result: status=%s gateway=%s", status, gateway)
                _append_jsonl(CM_LOG_PATH, {
                    "event": "cm_consume_result",
                    "cycle": cycle,
                    "goal_id": goal_id,
                    "run_id": run_id,
                    "status": status,
                    "gateway_decision": gateway,
                    "via": "sai_direct",
                    "at": _now_iso(),
                })
                if _log_outcome:
                    try:
                        _sai_log_status = (
                            "completed" if (status == "ACCEPTED" and gateway == "ALLOW") else
                            "blocked" if gateway == "DENY" else
                            "partial" if gateway == "PAUSE" else
                            "failed"
                        )
                        _log_outcome(
                            mission_id=goal_id.upper(),
                            date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                            claimed_status=_sai_log_status,
                            actual_status=_sai_log_status,
                            model_used="continuous_mind_sai",
                            runtime_validated=(status == "ACCEPTED" and gateway == "ALLOW"),
                            value_immediate=3,
                            patterns=["cm_sai_direct", f"cm_{status.lower()}", f"gw_{gateway.lower()}"],
                            notes=f"CM-SAI cycle {cycle}: {goal_id} status={status} gw={gateway}",
                        )
                    except Exception as exc:
                        log.warning("log_outcome failed (sai consume): %s", exc)

                if status == "ACCEPTED" and gateway == "ALLOW":
                    log.info("SAI ALLOW — goal %s completed.", goal_id)
                    _mark_goal_done(goal_id)
                    cm_state["goals_completed"] = cm_state.get("goals_completed", 0) + 1
                    _append_jsonl(CM_LOG_PATH, {
                        "event": "cm_goal_completed",
                        "cycle": cycle,
                        "goal_id": goal_id,
                        "run_id": run_id,
                        "via": "sai_direct",
                        "at": _now_iso(),
                    })
                elif gateway == "PAUSE" or status in ("PENDING_HUMAN", "AWAIT_HUMAN"):
                    log.warning("SAI PAUSE — goal %s queued for human review.", goal_id)
                    cm_state["goals_paused"] = cm_state.get("goals_paused", 0) + 1
                    _append_jsonl(PAUSE_QUEUE_PATH, {
                        "goal_id": goal_id, "run_id": run_id, "cycle": cycle,
                        "consume_result": result, "queued_at": _now_iso(),
                    })
                elif gateway == "DENY" or status == "BLOCKED_POLICY":
                    log.warning("SAI DENY — goal %s blocked by policy.", goal_id)
                    cm_state["goals_denied"] = cm_state.get("goals_denied", 0) + 1
                    _append_jsonl(DENY_LOG_PATH, {
                        "goal_id": goal_id, "run_id": run_id, "cycle": cycle,
                        "consume_result": result, "denied_at": _now_iso(),
                    })
                    _mark_goal_done(goal_id)
                else:
                    log.info("SAI consume unhandled status=%s — continuing.", status)
            else:
                log.warning("SAI direct execution failed: %s", sai_exec.get("reason"))
                # SAI failed — skip to next cycle (inbox fallback not used in T47.8)

            _save_cm_state(cm_state)
            if once:
                log.info("--once flag set — exiting after SAI direct cycle.")
                break
            log.info("Sleeping %ds before next cycle.", heartbeat)
            time.sleep(heartbeat)
            continue  # skip inbox-write + polling below

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
            if _log_outcome:
                try:
                    _log_outcome(
                        mission_id=goal_id.upper(),
                        date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                        claimed_status="failed",
                        actual_status="failed",
                        model_used="continuous_mind_v01",
                        runtime_validated=False,
                        value_immediate=3,
                        patterns=["cm_cycle", "cm_output_timeout"],
                        notes=f"CM cycle {cycle}: output timeout for {goal_id}",
                    )
                except Exception as exc:
                    log.warning("log_outcome failed (cm_timeout): %s", exc)
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
        if _log_outcome:
            try:
                _cm_log_status = (
                    "completed" if (status == "ACCEPTED" and gateway == "ALLOW") else
                    "blocked" if gateway == "DENY" else
                    "partial" if gateway == "PAUSE" else
                    "failed"
                )
                _log_outcome(
                    mission_id=goal_id.upper(),
                    date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    claimed_status=_cm_log_status,
                    actual_status=_cm_log_status,
                    model_used="continuous_mind_v01",
                    runtime_validated=(status == "ACCEPTED" and gateway == "ALLOW"),
                    value_immediate=3,
                    patterns=["cm_cycle", f"cm_{status.lower()}", f"gw_{gateway.lower()}"],
                    notes=f"CM cycle {cycle}: {goal_id} status={status} gw={gateway}",
                )
            except Exception as exc:
                log.warning("log_outcome failed (cm_consume): %s", exc)

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
            # AO8J_4: Mark PAUSED so _pick_next_goal skips it
            _mark_goal_paused(goal_id)

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
