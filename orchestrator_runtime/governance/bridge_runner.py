"""
MS-AO3 Bridge Runner — Project-S consumes Copilot/executor output from cline_outbox/

Follows FA1_HANDOFF_V1 protocol. Reads output_ready.json + last_output.md from
orchestrator_runtime/cline_outbox/, validates checksum, marks consumed, passes
content to self_correcting_loop for verdict.

RISK_008 CONSTRAINT: This module does NOT simulate any end-to-end executor flow.
It only consumes output that already exists on disk. If no output exists, it
returns WAITING_FOR_EXECUTOR — never a false PASS.

HIGH RISK GATE: Before SCL verdict, checks risk_classifier. If goal is HIGH risk
with auto_approve=false, returns PENDING_HUMAN verdict instead of proceeding to SCL.

KILL SWITCH: Pre-consume check blocks all processing if kill switch is active.

Usage (Python):
    from orchestrator_runtime.governance.bridge_runner import consume_executor_output
    result = consume_executor_output("AO3_HARD_T1", expected_iteration=1)

Usage (CLI):
    python orchestrator_runtime/governance/bridge_runner.py consume --run-id AO3_T2_001 --iteration 1

Returns dict with keys:
    status: ACCEPTED | WAITING_FOR_EXECUTOR | REJECTED_CHECKSUM | REJECTED_RUN_ID | REJECTED_CONSUMED | BLOCKED_KILL_SWITCH
    content: (if ACCEPTED) the output markdown content
    run_id: the run_id processed
    iteration: the iteration processed
"""

# ── Path fix for subprocess imports ────────────────────────────────────
import sys
from pathlib import Path
# Add project root so orchestrator_runtime package is importable
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))
# Add src/ so core.* modules are importable (CWI dependency)
sys.path.insert(0, str(project_root / "src"))

import argparse
import hashlib
import json
import logging
import os
import time
from datetime import datetime, timezone


# ── Path management (overridable for testing) ─────────────────────────

_DEFAULT_OUTBOX = Path(__file__).parent.parent / "cline_outbox"
_DEFAULT_CYCLE_LOG = Path(__file__).parent / "cycle_log.jsonl"

# Mutable state — tests call set_test_paths() to redirect these
_test_outbox: Path | None = None
_test_cycle_log: Path | None = None


def _outbox() -> Path:
    return _test_outbox if _test_outbox is not None else _DEFAULT_OUTBOX


def _cycle_log() -> Path:
    return _test_cycle_log if _test_cycle_log is not None else _DEFAULT_CYCLE_LOG


def _output_ready() -> Path:
    return _outbox() / "output_ready.json"


def _last_output() -> Path:
    return _outbox() / "last_output.md"


def set_test_paths(outbox_dir: Path, cycle_log_path: Path | None = None):
    """Override paths for unit testing with real on-disk fixtures."""
    global _test_outbox, _test_cycle_log
    _test_outbox = outbox_dir
    _test_cycle_log = cycle_log_path


def reset_test_paths():
    """Restore production paths after testing."""
    global _test_outbox, _test_cycle_log
    _test_outbox = None
    _test_cycle_log = None


# ── Status constants ──────────────────────────────────────────────────

STATUS_ACCEPTED = "ACCEPTED"
STATUS_WAITING_FOR_EXECUTOR = "WAITING_FOR_EXECUTOR"
STATUS_REJECTED_CHECKSUM = "REJECTED_CHECKSUM"
STATUS_REJECTED_RUN_ID = "REJECTED_RUN_ID"
STATUS_REJECTED_CONSUMED = "REJECTED_CONSUMED"
STATUS_BLOCKED_KILL_SWITCH = "BLOCKED_KILL_SWITCH"

# ── CWI Advisory Feature Flag ─────────────────────────────────────────
# Default False: CWI remains disabled until explicit opt-in.
# Can be enabled via env var: $env:CWI_ADVISORY = "true"
CWI_ADVISORY_ENABLED = (
    os.environ.get("CWI_ADVISORY", "false").lower() == "true"
)

# ── Overseer Advisory Feature Flag ────────────────────────────────────
# Default False: OverseerAgent remains disabled until explicit opt-in.
# Can be enabled via env var: $env:OVERSEER_ADVISORY = "true"
OVERSEER_ADVISORY_ENABLED = (
    os.environ.get("OVERSEER_ADVISORY", "false").lower() == "true"
)

# ── Notification (lazy) ───────────────────────────────────────────────

try:
    from orchestrator_runtime.governance.notifier import Notifier
    _NOTIFIER = Notifier()
except ImportError:
    _NOTIFIER = None


def _notify(event_type: str, message: str = ""):
    if _NOTIFIER is not None:
        try:
            _NOTIFIER.notify(event_type=event_type, message=message)
        except Exception:
            pass


# ── Helpers ───────────────────────────────────────────────────────────

def _log_cycle(entry: dict):
    entry["logged_at"] = datetime.now(timezone.utc).isoformat()
    with open(_cycle_log(), "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def compute_checksum(file_path: Path) -> str:
    """SHA-256 of file contents, first 16 hex chars."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def _atomic_write_output_ready(data: dict):
    path = _output_ready()
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    tmp.replace(path)


# ── HIGH risk gate ────────────────────────────────────────────────────

def _check_high_risk_gate(run_id: str) -> dict | None:
    """
    Check if run_id corresponds to a HIGH risk goal that requires human approval.
    Returns verdict dict if gate blocks, None if proceed to SCL.
    """
    # Check goal_queue.json
    goal_queue_path = Path(__file__).parent.parent.parent / "goal_queue.json"
    if goal_queue_path.exists():
        try:
            with open(goal_queue_path, "r", encoding="utf-8-sig") as f:
                queue = json.load(f)
            for goal in queue.get("goals", []):
                if goal.get("id") == run_id:
                    if goal.get("risk") == "HIGH" and not goal.get("auto_approve", False):
                        return {
                            "status": "PENDING_HUMAN",
                            "reason": f"HIGH risk goal '{goal.get('title', run_id)}' requires human approval before verdict",
                            "goal_id": run_id,
                            "action": "AWAIT_HUMAN",
                        }
        except (json.JSONDecodeError, IOError):
            pass

    # Check governance/hardening/ directory
    hardening_dir = Path(__file__).parent / "hardening"
    if hardening_dir.exists():
        for f in hardening_dir.glob("*.json"):
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    goal = json.load(fh)
                if goal.get("id") == run_id:
                    if goal.get("risk") == "HIGH" and not goal.get("auto_approve", False):
                        return {
                            "status": "PENDING_HUMAN",
                            "reason": f"HIGH risk goal '{goal.get('title', run_id)}' requires human approval before verdict",
                            "goal_id": run_id,
                            "action": "AWAIT_HUMAN",
                        }
            except (json.JSONDecodeError, IOError):
                pass

    return None


# ── Retry count tracking ──────────────────────────────────────────────

_RETRY_STATE_PATH = Path(__file__).parent / "retry_state.json"


def _get_retry_count(run_id: str) -> int:
    """Get current retry count for a run_id from persistent state."""
    if _RETRY_STATE_PATH.exists():
        try:
            with open(_RETRY_STATE_PATH, "r", encoding="utf-8") as f:
                state = json.load(f)
            return state.get(run_id, 0)
        except (json.JSONDecodeError, IOError):
            pass
    return 0


def _increment_retry_count(run_id: str):
    """Increment and persist retry count for a run_id."""
    state = {}
    if _RETRY_STATE_PATH.exists():
        try:
            with open(_RETRY_STATE_PATH, "r", encoding="utf-8") as f:
                state = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    state[run_id] = state.get(run_id, 0) + 1
    tmp = _RETRY_STATE_PATH.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    tmp.replace(_RETRY_STATE_PATH)


# ── Main function ─────────────────────────────────────────────────────

def consume_executor_output(run_id: str, expected_iteration: int) -> dict:
    """
    Consume executor output from cline_outbox/ following FA1_HANDOFF_V1.

    0. Kill switch active?          else BLOCKED_KILL_SWITCH (pre-consume gate)
    1. output_ready.json exists?   else WAITING_FOR_EXECUTOR
    2. run_id matches?             else REJECTED_RUN_ID
    3. iteration matches?          else REJECTED_RUN_ID
    4. not already consumed?       else REJECTED_CONSUMED
    5. last_output.md exists?      else WAITING_FOR_EXECUTOR
    6. checksum matches?           else REJECTED_CHECKSUM
    7. mark consumed=True, return ACCEPTED + content

    RISK_008: Missing output → WAITING_FOR_EXECUTOR, never a false PASS.
    """
    base = {
        "status": None,
        "content": None,
        "run_id": run_id,
        "iteration": expected_iteration,
        "error": None,
    }

    # ── KILL SWITCH pre-consume gate ──
    try:
        from orchestrator_runtime.governance.kill_switch import KillSwitch
        ks = KillSwitch()
        if ks.is_active():
            base["status"] = STATUS_BLOCKED_KILL_SWITCH
            base["error"] = "Kill switch is active — all consumption blocked"
            _log_cycle({"event": "bridge_kill_switch_blocked", "run_id": run_id})
            _notify("KILL_SWITCH_BLOCKED", f"Kill switch blocked consumption for {run_id}")
            return base
    except ImportError:
        pass  # Kill switch not available, proceed

    # ── CWI ADVISORY pre-consume hook (advisory-only, feature-flagged) ──
    # Only runs if CWI_ADVISORY_ENABLED is True.
    # Never raises, never blocks, never changes verdict or checksum logic.
    _cwi_start = time.perf_counter() if CWI_ADVISORY_ENABLED else None
    _cwi_advisory_status = "SKIPPED"
    _cwi_advisory_output = ""
    if CWI_ADVISORY_ENABLED:
        try:
            from orchestrator_runtime.sandbox.cwi_advisory_wrapper import get_cwi_advisory_safe
            # Extract task description from goal_queue if available
            task_desc = ""
            try:
                gq_path = Path(__file__).parent.parent.parent / "goal_queue.json"
                if gq_path.exists():
                    with open(gq_path, "r", encoding="utf-8-sig") as gf:
                        gq = json.load(gf)
                    for g in gq.get("goals", []):
                        if g.get("id") == run_id:
                            task_desc = g.get("description", g.get("title", run_id))
                            break
            except Exception:
                pass
            if not task_desc:
                task_desc = run_id  # Fallback to run_id
            _cwi_result = get_cwi_advisory_safe(
                task_description=task_desc,
                context={"integration": "bridge_runner_pre_consume", "run_id": run_id},
                user_id="ao5_system"
            )
            if _cwi_result.get("status") == "OK":
                _cwi_advisory_status = "OK"
                _adv = _cwi_result.get("advisory", {})
                _intent = _adv.get("intent_analysis", {}).get("intent_type", "unknown") if isinstance(_adv, dict) else str(_adv)[:100]
                _cwi_advisory_output = str(_adv)[:200]
                logger = logging.getLogger(__name__)
                logger.info(f"CWI advisory for {run_id}: intent={_intent}")
            else:
                _cwi_advisory_status = "ERROR"
                _cwi_advisory_output = str(_cwi_result.get("error", "unknown"))[:200]
                logger = logging.getLogger(__name__)
                logger.warning(f"CWI advisory for {run_id}: {_cwi_advisory_status} — {_cwi_advisory_output}")
        except Exception as _e:
            _cwi_advisory_status = "ERROR"
            _cwi_advisory_output = str(_e)[:200]
            logger = logging.getLogger(__name__)
            logger.error(f"CWI pre-analysis unexpected error for {run_id}: {_e}")
    _cwi_latency_ms = round((time.perf_counter() - _cwi_start) * 1000, 2) if _cwi_start else 0
    # If CWI_ADVISORY_ENABLED is False, skip entirely — no behavior change

    # ── OVERSEER ADVISORY pre-consume hook (advisory-only, feature-flagged) ──
    # Only runs if OVERSEER_ADVISORY_ENABLED is True.
    # Never raises, never blocks, never changes verdict or checksum logic.
    _overseer_start = time.perf_counter() if OVERSEER_ADVISORY_ENABLED else None
    _overseer_advisory_status = "SKIPPED"
    _overseer_advisory_output = ""
    if OVERSEER_ADVISORY_ENABLED:
        try:
            import asyncio
            from core.agents.overseer_agent import OverseerAgent
            from core.infrastructure.event_bus import EventBus
            _event_bus = EventBus()
            _overseer = OverseerAgent(_event_bus, memory_db_path=":memory:")
            _health = asyncio.run(_overseer.get_system_health())
            _overseer_advisory_status = "OK"
            _overseer_advisory_output = str(_health)[:200]
            logger = logging.getLogger(__name__)
            logger.info(f"Overseer advisory for {run_id}: health={_health}")
        except Exception as _e:
            _overseer_advisory_status = "ERROR"
            _overseer_advisory_output = str(_e)[:200]
            logger = logging.getLogger(__name__)
            logger.error(f"Overseer advisory error for {run_id}: {_e}")
    _overseer_latency_ms = round((time.perf_counter() - _overseer_start) * 1000, 2) if _overseer_start else 0
    # If OVERSEER_ADVISORY_ENABLED is False, skip entirely — no behavior change

    # ── Telemetry: append to overseer_observation.jsonl (ALL verdicts) ──
    _total_start = time.perf_counter()

    def _write_telemetry(errors=None):
        """Write telemetry line for ANY verdict (not just ACCEPTED)."""
        try:
            _lat = round((time.perf_counter() - _total_start) * 1000, 2)
            _obs_path = Path(__file__).parent / "overseer_observation.jsonl"
            _obs_line = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "run_id": run_id,
                "iteration": expected_iteration,
                # Overseer advisory fields
                "overseer_enabled": OVERSEER_ADVISORY_ENABLED,
                "overseer_status": _overseer_advisory_status,
                "overseer_output_first_200": _overseer_advisory_output,
                "overseer_latency_ms": _overseer_latency_ms,
                # CWI advisory fields
                "cwi_enabled": CWI_ADVISORY_ENABLED,
                "cwi_status": _cwi_advisory_status,
                "cwi_output_first_200": _cwi_advisory_output,
                "cwi_latency_ms": _cwi_latency_ms,
                # Totals
                "latency_ms_total": _lat,
                "verdict": base["status"],
                "errors": errors or []
            }
            with open(_obs_path, "a", encoding="utf-8") as _f:
                _f.write(json.dumps(_obs_line, ensure_ascii=False) + "\n")
        except Exception:
            pass  # Telemetry failure must never block consumption

    ready_path = _output_ready()
    if not ready_path.exists():
        base["status"] = STATUS_WAITING_FOR_EXECUTOR
        base["error"] = "output_ready.json not found"
        _log_cycle({"event": "bridge_wait", "run_id": run_id, "reason": "no_output_ready"})
        _notify("BRIDGE_WAIT", f"Waiting for executor output: {run_id}")
        _write_telemetry()
        return base

    try:
        with open(ready_path, "r", encoding="utf-8-sig") as f:
            ready = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        base["status"] = STATUS_WAITING_FOR_EXECUTOR
        base["error"] = f"Cannot read output_ready.json: {e}"
        _log_cycle({"event": "bridge_error", "run_id": run_id, "error": str(e)})
        _write_telemetry([str(e)])
        return base

    # run_id
    if ready.get("run_id") != run_id:
        base["status"] = STATUS_REJECTED_RUN_ID
        base["error"] = f"run_id mismatch: expected {run_id}, got {ready.get('run_id')}"
        _log_cycle({"event": "bridge_reject_run_id", "expected": run_id, "got": ready.get("run_id")})
        _notify("BRIDGE_REJECT", f"Run ID mismatch for {run_id}")
        _write_telemetry()
        return base

    # iteration
    if ready.get("iteration") != expected_iteration:
        base["status"] = STATUS_REJECTED_RUN_ID
        base["error"] = f"iteration mismatch: expected {expected_iteration}, got {ready.get('iteration')}"
        _log_cycle({"event": "bridge_reject_iteration", "expected": expected_iteration, "got": ready.get("iteration")})
        _notify("BRIDGE_REJECT", f"Iteration mismatch for {run_id}")
        _write_telemetry()
        return base

    # already consumed?
    if ready.get("consumed", False):
        base["status"] = STATUS_REJECTED_CONSUMED
        base["error"] = "Output already consumed (no double-consume)"
        _log_cycle({"event": "bridge_reject_consumed", "run_id": run_id})
        _write_telemetry()
        return base

    # last_output.md
    output_path = _last_output()
    if not output_path.exists():
        base["status"] = STATUS_WAITING_FOR_EXECUTOR
        base["error"] = "last_output.md not found"
        _log_cycle({"event": "bridge_wait", "run_id": run_id, "reason": "no_last_output"})
        _write_telemetry()
        return base

    try:
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
    except IOError as e:
        base["status"] = STATUS_WAITING_FOR_EXECUTOR
        base["error"] = f"Cannot read last_output.md: {e}"
        _log_cycle({"event": "bridge_error", "run_id": run_id, "error": str(e)})
        _write_telemetry([str(e)])
        return base

    # checksum
    actual = compute_checksum(output_path)
    expected = ready.get("checksum", "")
    if actual != expected:
        base["status"] = STATUS_REJECTED_CHECKSUM
        base["error"] = f"Checksum mismatch: expected {expected}, got {actual}"
        _log_cycle({"event": "bridge_reject_checksum", "run_id": run_id,
                     "expected": expected, "actual": actual})
        _notify("BRIDGE_REJECT", f"Checksum mismatch for {run_id}")
        _write_telemetry()
        return base

    # ── All checks passed ──
    ready["consumed"] = True
    ready["consumed_at"] = datetime.now(timezone.utc).isoformat()
    _atomic_write_output_ready(ready)


    base["status"] = STATUS_ACCEPTED
    base["content"] = content
    _log_cycle({"event": "bridge_consumed", "run_id": run_id,
                "iteration": expected_iteration, "checksum": actual})
    _notify("BRIDGE_CONSUMED", f"Consumed output for {run_id} iter {expected_iteration}")

    _write_telemetry()

    return base


# ── Verdict integration ───────────────────────────────────────────────

def get_verdict_for_content(content: str, run_id: str) -> dict:
    """
    Pass consumed content to self_correcting_loop for verdict.

    HIGH RISK GATE: Before SCL, checks if run_id is a HIGH risk goal.
    If so, returns PENDING_HUMAN instead of proceeding to SCL.
    """
    # HIGH risk gate check
    gate_result = _check_high_risk_gate(run_id)
    if gate_result is not None:
        _log_cycle({"event": "bridge_high_risk_gate", "run_id": run_id,
                     "gate_result": gate_result})
        _notify("HIGH_RISK_GATE", f"HIGH risk goal {run_id} blocked — requires human approval")
        return gate_result

    # Determine PASS/FAIL from content
    verdict_status = "FAIL" if (
        not content or
        not content.strip() or
        "FAILED" in content.upper() or
        "ERROR:" in content or
        "could not be completed" in content.lower()
    ) else "PASS"

    # Get current retry count for this run_id
    retry_count = _get_retry_count(run_id)

    # Proceed to SCL
    try:
        from orchestrator_runtime.governance.self_correcting_loop import SelfCorrectingLoop
        loop = SelfCorrectingLoop()
        verdict_result = loop.process_goal(
            goal_id=run_id,
            verdict=verdict_status,
            feedback=content[:2000],
            retry_count=retry_count,
        )
        # If FAIL, increment retry count for next time
        if verdict_result.get("status") == "FAIL":
            _increment_retry_count(run_id)
        _log_cycle({"event": "verdict", "run_id": run_id, "result": verdict_result})
        return verdict_result
    except ImportError:
        _log_cycle({"event": "verdict_error", "run_id": run_id,
                     "error": "self_correcting_loop not available"})
        return {"error": "self_correcting_loop not available"}


def consume_and_verdict(run_id: str, expected_iteration: int) -> dict:
    """Convenience: consume + verdict in one call."""
    consume_result = consume_executor_output(run_id, expected_iteration)
    if consume_result["status"] != STATUS_ACCEPTED:
        return {"consumption": consume_result, "verdict": None,
                "overall": consume_result["status"]}
    verdict = get_verdict_for_content(consume_result["content"], run_id)
    return {"consumption": consume_result, "verdict": verdict,
            "overall": "VERDICT_ISSUED"}


# ── CLI Entry Point ───────────────────────────────────────────────────

def _cli():
    """CLI wrapper: python bridge_runner.py consume --run-id X --iteration Y"""
    parser = argparse.ArgumentParser(description="Bridge Runner CLI")
    sub = parser.add_subparsers(dest="command")
    consume_p = sub.add_parser("consume", help="Consume executor output")
    consume_p.add_argument("--run-id", required=True, help="Run ID to consume")
    consume_p.add_argument("--iteration", required=True, type=int, help="Expected iteration")
    consume_p.add_argument("--verdict", action="store_true",
                           help="Also pass to self_correcting_loop for verdict")
    args = parser.parse_args()

    if args.command == "consume":
        result = consume_executor_output(args.run_id, args.iteration)
        if args.verdict and result["status"] == STATUS_ACCEPTED:
            verdict = get_verdict_for_content(result["content"], args.run_id)
            result["verdict"] = verdict
        # UTF-8 stdout to avoid cp1251 encode errors on Windows
        output = json.dumps(result, indent=4, ensure_ascii=False, default=str) + "\n"
        sys.stdout.buffer.write(output.encode("utf-8"))
        sys.exit(0 if result["status"] == STATUS_ACCEPTED else 1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    _cli()