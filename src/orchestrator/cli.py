"""
cli.py — MS-FA1 Orchestrator CLI Entrypoint

Usage:
    python -m orchestrator.cli --help
    python -m orchestrator.cli list-runs
    python -m orchestrator.cli status
    python -m orchestrator.cli check-env
    python -m orchestrator.cli consume-output --run-id FA1_012
    python -m orchestrator.cli resume --run-id FA1_012
    python -m orchestrator.cli run-loop --auto --max-iterations 2

This module provides a command-line interface to the MS-FA1 filesystem
orchestration pipeline. It reuses existing orchestrator modules and does
NOT implement any new orchestration logic.

Safety:
    - No automatic Cline invocation
    - No UI automation
    - Stops safely if Cline output is not available
    - Prints clear operator instructions
    - Clears stale outbox before starting new run
    - Detects unconsumed output before creating new runs
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="orchestrator.cli",
        description="MS-FA1 Filesystem Orchestration Pipeline CLI",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # list-runs
    subparsers.add_parser("list-runs", help="List all runs")

    # status
    subparsers.add_parser("status", help="Show status of the latest run")

    # check-env
    subparsers.add_parser("check-env", help="Check OpenRouter env setup (no key printed)")

    # consume-output
    consume_parser = subparsers.add_parser("consume-output", help="Consume Cline output for an existing run")
    consume_parser.add_argument(
        "--run-id",
        required=True,
        help="Run ID to consume output for (e.g., FA1_012)",
    )

    # resume
    resume_parser = subparsers.add_parser("resume", help="Resume an existing run from current state")
    resume_parser.add_argument(
        "--run-id",
        required=True,
        help="Run ID to resume (e.g., FA1_012)",
    )
    resume_parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Seconds to wait for Cline output (default: 30)",
    )

    # run-loop
    loop_parser = subparsers.add_parser("run-loop", help="Execute a run loop")
    loop_parser.add_argument(
        "--auto",
        action="store_true",
        default=False,
        help="Auto mode: skip human review for sandbox tasks",
    )
    loop_parser.add_argument(
        "--max-iterations",
        type=int,
        default=2,
        help="Maximum iterations (default: 2)",
    )
    loop_parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Seconds to wait for Cline output per iteration (default: 30)",
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if args.command == "check-env":
        cmd_check_env()
    elif args.command == "consume-output":
        cmd_consume_output(run_id=args.run_id)
    elif args.command == "resume":
        cmd_resume(run_id=args.run_id, timeout=args.timeout)
    elif args.command == "list-runs":
        cmd_list_runs()
    elif args.command == "status":
        cmd_status()
    elif args.command == "run-loop":
        cmd_run_loop(auto=args.auto, max_iterations=args.max_iterations, timeout=args.timeout)
    else:
        parser.print_help()
        sys.exit(1)


def cmd_check_env() -> None:
    """Check OpenRouter environment setup. Never prints the actual key."""
    from pathlib import Path
    import os

    project_root = Path(__file__).resolve().parent.parent
    env_local = project_root / ".env.local"

    print("MS-FA1 OpenRouter Environment Check")
    print("=" * 40)
    print()

    # 1. .env.local exists?
    print(f".env.local exists: {'yes' if env_local.exists() else 'no'}")

    # 2. OPENROUTER_API_KEY loaded?
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if key:
        print("OPENROUTER_API_KEY (env): yes")
    elif env_local.exists():
        # Check if key is in .env.local without printing it
        found = False
        for line in env_local.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("#") or not line:
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                if k.strip() == "OPENROUTER_API_KEY" and v.strip():
                    found = True
                    break
        print(f"OPENROUTER_API_KEY (.env.local): {'yes' if found else 'no'}")
    else:
        print("OPENROUTER_API_KEY (.env.local): no (file missing)")

    # 3. Config loaded?
    # project_root is src/, so orchestrator_runtime is at project_root.parent
    config_path = project_root.parent / "orchestrator_runtime" / "config.json"
    if config_path.exists():
        import json
        config = json.loads(config_path.read_text(encoding="utf-8"))
        prompt_cfg = config.get("prompt_drafter", {})
        eval_cfg = config.get("verdict_evaluator", {})
        print(f"prompt_drafter enabled: {prompt_cfg.get('enabled', 'N/A')}")
        print(f"prompt_drafter model: {prompt_cfg.get('model', 'N/A')}")
        print(f"verdict_evaluator enabled: {eval_cfg.get('enabled', 'N/A')}")
        print(f"verdict_evaluator model: {eval_cfg.get('model', 'N/A')}")
    else:
        print("config.json: not found")

    print()
    print("NOTE: API key value is never printed.")


def cmd_consume_output(run_id: str) -> None:
    """Consume Cline output for an existing run."""
    from .filesystem_orchestrator import FilesystemOrchestrator
    from .handoff_watcher import HandoffWatcher

    orchestrator = FilesystemOrchestrator()
    watcher = HandoffWatcher()

    print("=" * 60)
    print(f"Consume Output: {run_id}")
    print("=" * 60)
    print()

    # Step 1: Read output_ready.json
    output_ready_path = orchestrator.cline_outbox / "output_ready.json"
    if not output_ready_path.exists():
        print("ERROR: No output_ready.json found in cline_outbox.")
        sys.exit(1)

    signal_data = json.loads(output_ready_path.read_text(encoding="utf-8"))

    # Step 2: Verify run_id matches
    signal_run_id = signal_data.get("run_id", "")
    if signal_run_id != run_id:
        print(f"ERROR: Run ID mismatch. Expected {run_id}, got {signal_run_id}.")
        sys.exit(1)

    # Step 3: Verify not already consumed
    if signal_data.get("consumed", False):
        print(f"INFO: Output for {run_id} already consumed.")
        # Check if verdict exists
        verdict_path = orchestrator.runs_dir / run_id / "verdict.json"
        if verdict_path.exists():
            verdict = json.loads(verdict_path.read_text(encoding="utf-8"))
            print(f"Existing verdict: {verdict.get('status', 'N/A')}")
        return

    # Step 4: Read last_output.md
    last_output_path = orchestrator.cline_outbox / "last_output.md"
    if not last_output_path.exists():
        print("ERROR: No last_output.md found in cline_outbox.")
        sys.exit(1)

    output_text = last_output_path.read_text(encoding="utf-8")
    print(f"Output received: {len(output_text)} chars")
    print()

    # Step 5: Save output to run folder
    run_dir = orchestrator.runs_dir / run_id
    if not run_dir.exists():
        print(f"ERROR: Run folder {run_dir} does not exist.")
        sys.exit(1)

    (run_dir / "output.md").write_text(output_text, encoding="utf-8")
    print(f"Output saved to: {run_dir / 'output.md'}")

    # Step 6: Transition state machine to CLINE_OUTPUT_RECEIVED then EVALUATING_OUTPUT
    print("Evaluating output...")
    try:
        orchestrator._load_state_machine(run_id)
        from .state_machine import RunState
        sm = orchestrator._state_machine
        if sm.current_state != RunState.CLINE_OUTPUT_RECEIVED:
            sm.transition(RunState.CLINE_OUTPUT_RECEIVED, "Cline output consumed")
    except Exception:
        pass  # State transition best-effort
    verdict = orchestrator.evaluate_output(run_id)
    print(f"  Verdict: {verdict.status.value}")
    print(f"  Confidence: {verdict.confidence:.2f}")
    print(f"  Summary: {verdict.summary[:100]}")
    print()

    # Step 7: Issue verdict
    orchestrator.issue_verdict(run_id, verdict=verdict)
    print(f"Verdict issued for {run_id}")

    # Step 8: Archive if PASS
    if verdict.status.value == "PASS":
        orchestrator.archive_run(run_id)
        print("Run archived.")
    else:
        print(f"Run status: {verdict.status.value}")
        print(f"Next action: {verdict.next_action}")

    # Step 9: Mark consumed
    signal_data["consumed"] = True
    signal_data["status"] = "consumed"
    output_ready_path.write_text(json.dumps(signal_data, indent=2), encoding="utf-8")
    print("Output marked as consumed.")
    print()
    print(f"COMPLETE: {run_id} verdict = {verdict.status.value}")


def cmd_resume(run_id: str, timeout: int) -> None:
    """Resume an existing run from current state."""
    from .filesystem_orchestrator import FilesystemOrchestrator
    from .handoff_watcher import HandoffWatcher
    from .state_machine import StateMachine, RunState

    orchestrator = FilesystemOrchestrator()
    watcher = HandoffWatcher()

    print("=" * 60)
    print(f"Resume Run: {run_id}")
    print("=" * 60)
    print()

    # Step 1: Load state machine
    run_dir = orchestrator.runs_dir / run_id
    if not run_dir.exists():
        print(f"ERROR: Run folder {run_dir} does not exist.")
        sys.exit(1)

    try:
        sm = StateMachine.load(run_id, runs_dir=orchestrator.runs_dir)
        current_state = sm.current_state
        print(f"Current state: {current_state.value}")
    except Exception as e:
        print(f"Could not load state machine: {e}")
        print("Assuming WAITING_FOR_CLINE state.")
        current_state = RunState.WAITING_FOR_CLINE

    # Step 2: Handle based on state
    if current_state in (RunState.WAITING_FOR_CLINE, RunState.IN_PROGRESS):
        # Check if output already exists
        output_ready_path = orchestrator.cline_outbox / "output_ready.json"
        if output_ready_path.exists():
            signal_data = json.loads(output_ready_path.read_text(encoding="utf-8"))
            if signal_data.get("run_id") == run_id and not signal_data.get("consumed", False):
                print(f"Unconsumed output found for {run_id}. Consuming...")
                cmd_consume_output(run_id)
                return

        # Wait for output
        print(f"Waiting for Cline output (timeout: {timeout}s)...")
        iteration = signal_data.get("iteration", 1) if output_ready_path.exists() else 1
        output = watcher.watch_for_output(run_id, iteration, timeout=timeout, poll_interval=2.0)

        if output:
            print("Output received. Consuming...")
            (run_dir / "output.md").write_text(output, encoding="utf-8")

            # Evaluate
            verdict = orchestrator.evaluate_output(run_id)
            print(f"  Verdict: {verdict.status.value}")
            print(f"  Confidence: {verdict.confidence:.2f}")

            orchestrator.issue_verdict(run_id, verdict=verdict)

            if verdict.status.value == "PASS":
                orchestrator.archive_run(run_id)
                print("Run archived.")
            else:
                print(f"Run status: {verdict.status.value}")
        else:
            print("WAITING_FOR_CLINE: No output received within timeout.")
    elif current_state == RunState.EVALUATING_OUTPUT:
        # Output should already be in run folder
        output_path = run_dir / "output.md"
        if output_path.exists():
            print("Output already saved. Evaluating...")
            verdict = orchestrator.evaluate_output(run_id)
            print(f"  Verdict: {verdict.status.value}")
            orchestrator.issue_verdict(run_id, verdict=verdict)
            if verdict.status.value == "PASS":
                orchestrator.archive_run(run_id)
                print("Run archived.")
        else:
            print("ERROR: No output.md in run folder.")
    elif current_state in (RunState.VERDICT_ISSUED, RunState.ARCHIVED):
        print(f"Run already complete (state: {current_state.value}).")
        verdict_path = run_dir / "verdict.json"
        if verdict_path.exists():
            verdict = json.loads(verdict_path.read_text(encoding="utf-8"))
            print(f"Verdict: {verdict.get('status', 'N/A')}")
    else:
        print(f"Cannot resume from state: {current_state.value}")


def _has_unconsumed_output(outbox: Path) -> Optional[dict]:
    """Check if unconsumed output_ready.json exists. Returns signal data or None."""
    output_ready = outbox / "output_ready.json"
    if not output_ready.exists():
        return None
    try:
        data = json.loads(output_ready.read_text(encoding="utf-8"))
        if not data.get("consumed", False):
            return data
    except (json.JSONDecodeError, ValueError):
        pass
    return None


def _clear_stale_outbox(outbox: Path) -> None:
    """Clear stale outbox files before starting a new run."""
    last_output = outbox / "last_output.md"
    output_ready = outbox / "output_ready.json"
    if last_output.exists():
        last_output.unlink()
    if output_ready.exists():
        output_ready.unlink()


def cmd_list_runs() -> None:
    """List all runs."""
    from .run_archive import list_runs

    runs = list_runs()
    if not runs:
        print("No runs found.")
        return

    print(f"{'Run ID':<12} {'Status':<15} {'Goal (truncated)'}")
    print("-" * 70)
    for run in runs:
        run_id = run.get("run_id", "unknown")
        status = run.get("status", "unknown")
        goal = run.get("goal", "")[:40]
        print(f"{run_id:<12} {status:<15} {goal}")

    print(f"\nTotal: {len(runs)} run(s)")


def cmd_status() -> None:
    """Show status of the latest run."""
    from .run_archive import list_runs, get_run_status
    from .filesystem_orchestrator import RUNTIME_ROOT

    runs = list_runs()
    if not runs:
        print("No runs found.")
        return

    # Get the latest run (highest number)
    latest = sorted(runs, key=lambda r: r.get("run_id", ""))[-1]
    run_id = latest.get("run_id", "")

    status = get_run_status(run_id)
    print(f"Latest run: {run_id}")
    print(f"Status: {status or 'unknown'}")

    # Load verdict directly from runs/{run_id}/verdict.json
    runs_dir = RUNTIME_ROOT / "runs"
    verdict_path = runs_dir / run_id / "verdict.json"
    if verdict_path.exists():
        verdict = json.loads(verdict_path.read_text(encoding="utf-8"))
        print(f"Verdict: {verdict.get('status', 'N/A')}")
        print(f"Confidence: {verdict.get('confidence', 'N/A')}")
        print(f"Summary: {verdict.get('summary', 'N/A')[:100]}")
    else:
        print("No verdict yet.")


def cmd_run_loop(auto: bool, max_iterations: int, timeout: int) -> None:
    """Execute a run loop."""
    from .filesystem_orchestrator import FilesystemOrchestrator, Goal
    from .handoff_watcher import HandoffWatcher

    orchestrator = FilesystemOrchestrator()
    watcher = HandoffWatcher()

    # Step 0: Check for unconsumed output BEFORE clearing outbox
    unconsumed = _has_unconsumed_output(orchestrator.cline_outbox)
    if unconsumed:
        existing_run_id = unconsumed.get("run_id", "unknown")
        print(f"BLOCKED: Unconsumed output exists for run_id {existing_run_id}.")
        print()
        print(f"Options:")
        print(f"  1. Consume it: python -m orchestrator.cli consume-output --run-id {existing_run_id}")
        print(f"  2. Resume it: python -m orchestrator.cli resume --run-id {existing_run_id}")
        print(f"  3. Clear outbox manually and re-run")
        sys.exit(1)

    # Step 1: Clear stale outbox to prevent consuming old output
    _clear_stale_outbox(orchestrator.cline_outbox)

    # Step 2: Read goal
    print("=" * 60)
    print("MS-FA1 Run Loop")
    print("=" * 60)
    print()

    goal = orchestrator.read_goal()
    if not goal:
        # Check if goal.md exists but is empty
        goal_path = orchestrator.inbox / "goal.md"
        if goal_path.exists():
            print("ERROR: inbox/goal.md exists but is empty.")
        else:
            print("ERROR: No goal found in inbox/goal.md")
            print()
            print("To start a run:")
            print(f"  1. Write your goal to: {goal_path}")
            print("  2. Run: python -m orchestrator.cli run-loop --auto")
        sys.exit(1)

    print(f"Goal: {goal.text[:80]}...")
    print(f"Acceptance criteria: {len(goal.acceptance_criteria)}")
    print(f"Constraints: {len(goal.constraints)}")
    print()

    # Step 3: Create run
    run_id = orchestrator.create_run(goal)
    print(f"Run ID: {run_id}")
    print()

    # Step 4: Draft prompt
    print("Drafting prompt...")
    prompt = orchestrator.draft_prompt(run_id, auto_mode=auto)
    print(f"Prompt drafted ({len(prompt)} chars)")
    print(f"  -> {orchestrator.cline_inbox / 'next_prompt.md'}")
    print()

    # Step 5: Prepare handoff signal
    print("Preparing handoff signal...")
    handoff_path = watcher.prepare_handoff(run_id, 1, prompt)
    print(f"  -> {handoff_path}")
    print()

    # Step 6: Wait for Cline output (with timeout)
    print(f"Waiting for Cline output (timeout: {timeout}s)...")
    print()
    print("INSTRUCTIONS FOR OPERATOR:")
    print("  1. Copy the prompt from:")
    print(f"     {orchestrator.cline_inbox / 'next_prompt.md'}")
    print("  2. Paste it into Cline")
    print("  3. Cline should write output to:")
    print(f"     {orchestrator.cline_outbox / 'last_output.md'}")
    print("  4. Cline should also create:")
    print(f"     {orchestrator.cline_outbox / 'output_ready.json'}")
    print()

    output = watcher.watch_for_output(run_id, 1, timeout=timeout, poll_interval=2.0)

    if output:
        print("Cline output received!")
        print(f"  Length: {len(output)} chars")
        print()

        # Save output to run folder for evaluation
        (orchestrator.runs_dir / run_id / "output.md").write_text(output, encoding="utf-8")

        # Evaluate
        print("Evaluating output...")
        verdict = orchestrator.evaluate_output(run_id)
        print(f"  Verdict: {verdict.status.value}")
        print(f"  Confidence: {verdict.confidence:.2f}")
        print(f"  Summary: {verdict.summary[:100]}")
        print()

        # Issue verdict
        orchestrator.issue_verdict(run_id, verdict=verdict)

        # Archive if PASS
        if verdict.status.value == "PASS":
            orchestrator.archive_run(run_id)
            print("Run archived.")
        else:
            print(f"Run status: {verdict.status.value}")
            print(f"Next action: {verdict.next_action}")
    else:
        print("WAITING_FOR_CLINE: No output received within timeout.")
        print()
        print("The prompt has been prepared. Next steps:")
        print(f"  1. Copy prompt from: {orchestrator.cline_inbox / 'next_prompt.md'}")
        print("  2. Paste into Cline and execute")
        print("  3. After Cline writes output, run:")
        print(f"     python -m orchestrator.cli consume-output --run-id {run_id}")
        print()
        print("Or resume with:")
        print(f"  python -m orchestrator.cli resume --run-id {run_id}")


if __name__ == "__main__":
    main()