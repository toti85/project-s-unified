import sys
sys.path.insert(0, 'src')

try:
    from orchestrator.filesystem_orchestrator import FilesystemOrchestrator
    orch = FilesystemOrchestrator()
    
    output = orch.receive_output('FA1_002')
    print(f'Output received: {len(output) if output else 0} chars')
    
    verdict = orch.evaluate_output('FA1_002')
    print(f'Verdict: {verdict.status.value} confidence={verdict.confidence}')
    
    orch.issue_verdict('FA1_002', verdict=verdict)
    print('Verdict issued')
    
    archived = orch.archive_run('FA1_002')
    print(f'Archived: {archived}')
    print('DONE')
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()