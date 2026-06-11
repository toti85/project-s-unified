# AO5_T21 Workflow Registry Bootstrap Fix — PARTIAL PASS

**Date:** 2026-06-11
**Status:** PARTIAL PASS
**Run ID:** AO5_T21_WORKFLOW_BOOTSTRAP_FIX

## Root Cause
`workflow_registry.get_workflow("langgraph_engine")` returned `None` because no code ever called `workflow_registry.register_workflow()`. The `LangGraphWorkflowEngine` class existed and was exported, but was never instantiated and registered in the global `workflow_registry`.

## Exact Fix Applied
Added bootstrap registration in `src/core/orchestration/__init__.py`:
```python
# Bootstrap: register LangGraphWorkflowEngine in the global registry
_engine_instance = LangGraphWorkflowEngine()
workflow_registry.register_workflow(_engine_instance, is_default=True)
```

## Why Architecture-Safe
- Uses existing `register_workflow()` API
- Registers under default name `"langgraph_engine"` (matches CWI lookup)
- No monkeypatching, no bypass, no fake workflow
- Import side-effect: registration happens when package is imported

## Files Modified
- `src/core/orchestration/__init__.py` — added 3 lines of bootstrap registration

## Rollback Command
```bash
git restore -- src/core/orchestration/__init__.py
```

## Workflow Verification
- **WORKFLOW_OK:** ✅ `True LangGraphWorkflowEngine`

## Runtime Smoke Result
- **Previous error:** `'NoneType' object has no attribute 'execute'` — FIXED
- **Current error:** `'WorkflowResult' object has no attribute 'get'` — NEW BLOCKER
- **Latency:** 165.08ms
- **Result:**
```json
{
  "success": false,
  "error": "'WorkflowResult' object has no attribute 'get'",
  "execution_id": "exec_1781131563",
  "timestamp": "2026-06-11T01:46:03.916082"
}
```

## Cognitive Evidence
- Intent analysis: ✅ executed (intent detected: FILE_OPERATION)
- Router usage: ✅ executed (decision routing works)
- Semantic reasoning: ✅ executed
- Workflow selection: ✅ executed (workflow found and attempted)
- Workflow execution: ⚠️ partial (graph execution attempted, fallback used, type mismatch in result handling)

## Next Blocker
`'WorkflowResult' object has no attribute 'get'` — CWI code expects a dict from workflow execution but receives a `WorkflowResult` object. This is a type compatibility issue in the CWI post-processing stage, not a bootstrap/registration issue.

## Verdict
**PARTIAL PASS** — Workflow engine bootstrap fixed. CWI progresses past workflow selection and attempts execution. Next blocker: WorkflowResult type compatibility in CWI post-processing.