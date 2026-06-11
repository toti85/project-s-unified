# AO5_T20 Decision Router Bootstrap Fix — PARTIAL PASS

**Date:** 2026-06-11
**Status:** PARTIAL PASS
**Run ID:** AO5_T20_ROUTER_BOOTSTRAP_FIX

## Root Cause
`router_registry.get_router("advanced_router")` returned `None` because no code ever called `router_registry.register_router()`. The `AdvancedDecisionRouter` class existed and was exported, but was never instantiated and registered in the global `router_registry`.

## Exact Fix Applied
Added bootstrap registration in `src/integrations/decision_routing/__init__.py`:
```python
# Bootstrap: register AdvancedDecisionRouter in the global registry
if ADVANCED_DECISION_ROUTER_AVAILABLE:
    _router_instance = AdvancedDecisionRouter()
    router_registry.register_router(_router_instance, is_default=True)
```

## Why Architecture-Safe
- Uses existing `register_router()` API
- Registers under default name `"advanced_router"` (matches CWI lookup)
- No monkeypatching, no bypass, no fake router
- Import side-effect: registration happens when package is imported

## Files Modified
- `src/integrations/decision_routing/__init__.py` — added 3 lines of bootstrap registration

## Rollback Command
```bash
git restore -- src/integrations/decision_routing/__init__.py
```

## Router Verification
- **ROUTER_OK:** ✅ `True AdvancedDecisionRouter`

## Runtime Smoke Result
- **Previous error:** `'NoneType' object has no attribute 'make_decision'` — FIXED
- **Current error:** `'NoneType' object has no attribute 'execute'` — NEW BLOCKER
- **Latency:** 92.31ms
- **Result:**
```json
{
  "success": false,
  "error": "'NoneType' object has no attribute 'execute'",
  "execution_id": "exec_1781131011",
  "timestamp": "2026-06-11T01:36:51.633920"
}
```

## Cognitive Evidence
- Intent analysis: ✅ executed (intent detected: FILE_OPERATION)
- Router usage: ✅ executed (no more make_decision error)
- Workflow selection: ⚠️ partial (workflow selected but engine not registered)
- Semantic reasoning: ✅ executed (reasoning performed)

## Next Blocker
`workflow_registry.get_workflow("langgraph_engine")` returns `None`. The LangGraphWorkflowEngine is not registered in the workflow registry. This is a separate runtime registration issue (similar pattern to the router fix).

## Verdict
**PARTIAL PASS** — Router bootstrap fixed. CWI progresses past decision routing stage. Next blocker: workflow engine not registered in workflow_registry.