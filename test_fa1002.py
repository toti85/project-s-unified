import sys
sys.path.insert(0, "src")

try:
    from orchestrator.filesystem_orchestrator import FilesystemOrchestrator, Goal
    from orchestrator.state_machine import StateMachine, RunState
    print("IMPORT_OK")
    
    orch = FilesystemOrchestrator()
    print(f"runs_dir: {orch.runs_dir}")
    print(f"exists: {orch.runs_dir.exists()}")
    
    goal_text = "Create JSON validator in sandbox with 3 tests."
    (orch.inbox / "goal.md").write_text(goal_text, encoding="utf-8")
    
    run_id = orch.create_run(Goal(text="JSON validator", raw=goal_text))
    print(f"run_id: {run_id}")
    
    prompt = orch.draft_prompt(run_id)
    print(f"prompt len: {len(prompt)}")
    
    orch.mark_in_progress(run_id)
    
    sm = StateMachine.load(run_id)
    print(f"state: {sm.current_state.value}")
    print(f"history: {len(sm.get_history())}")
    
    import os
    print(f"folder: {os.path.exists(str(orch.runs_dir / run_id))}")
    print("DONE")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()