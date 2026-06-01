import sys
sys.path.insert(0, 'src')

try:
    from orchestrator.filesystem_orchestrator import FilesystemOrchestrator, Goal
    from orchestrator.state_machine import StateMachine

    orch = FilesystemOrchestrator()

    # Create run
    goal_text = "Create CSV row counter in sandbox with 3 unit tests."
    (orch.inbox / "goal.md").write_text(goal_text, encoding="utf-8")
    run_id = orch.create_run(Goal(text="CSV row counter", raw=goal_text))
    print(f"run_id: {run_id}")

    # Draft prompt (auto mode - skips HUMAN_REVIEW)
    prompt = orch.draft_prompt(run_id, auto_mode=True)
    print(f"prompt len: {len(prompt)}")

    # Check state (should be IN_PROGRESS, not HUMAN_REVIEW)
    sm = StateMachine.load(run_id)
    print(f"state after draft: {sm.current_state.value}")

    # Receive output
    output = orch.receive_output(run_id)
    print(f"output received: {len(output) if output else 0} chars")

    # Evaluate
    verdict = orch.evaluate_output(run_id)
    print(f"verdict: {verdict.status.value} confidence={verdict.confidence}")

    # Issue verdict
    orch.issue_verdict(run_id, verdict=verdict)
    print("verdict issued")

    # Archive
    archived = orch.archive_run(run_id)
    print(f"archived: {archived}")

    # Final state
    sm2 = StateMachine.load(run_id)
    print(f"final state: {sm2.current_state.value}")
    print(f"history: {len(sm2.get_history())} transitions")
    print("DONE")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()