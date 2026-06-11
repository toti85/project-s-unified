# AO5_T17 Orchestration Export Surface Repair — PARTIAL PASS

**Date:** 2026-06-11
**Status:** PARTIAL PASS (orchestration exports OK, CWI blocked by decision_routing gap)
**Run ID:** AO5_T17_ORCH_EXPORT_REPAIR

## What Changed
Modified `src/core/orchestration/__init__.py` to export required orchestration symbols:
- WorkflowRegistry (from base_workflow)
- WorkflowResult (from base_workflow)
- workflow_registry (from base_workflow)
- LangGraphWorkflowEngine (from langgraph_engine)
- WORKFLOW_ENGINE_AVAILABLE (preserved from workflow_engine)

## Backup Path
`src/core/orchestration/__init__.py.bak_t17`

## Definitions Found Where
- `WorkflowRegistry`, `WorkflowResult`, `workflow_registry` → `src/core/orchestration/base_workflow.py`
- `LangGraphWorkflowEngine` → `src/core/orchestration/langgraph_engine.py`
- `WORKFLOW_ENGINE_AVAILABLE` → `src/core/orchestration/workflow_engine.py`

## Import Test Results
- **SYNTAX_OK:** ✅
- **ORCH_EXPORTS_OK:** ✅ All 5 symbols importable from `core.orchestration`
- **CWI_IMPORT_OK:** ❌ ImportError — `DecisionRouterRegistry` not exported from `integrations.decision_routing`
- **WORKFLOW_ENGINE_AVAILABLE regression:** ✅ True

## CWI Import Failure Root Cause
`cognitive_workflow_integration.py` line 42 imports:
```python
from integrations.decision_routing import DecisionRouterRegistry, AdvancedDecisionRouter, router_registry
```

`integrations/decision_routing/__init__.py` does not export `DecisionRouterRegistry`.

**This is a separate issue from the orchestration export surface repair.** The orchestration package now correctly exports all required symbols. The decision_routing gap is a pre-existing issue in a different package.

## Files Modified
- `src/core/orchestration/__init__.py` — export shim with 5 symbols

## Rollback Command
```bash
git restore -- src/core/orchestration/__init__.py
```

## Verdict
**PARTIAL PASS** — Orchestration export surface repaired. CWI import blocked by decision_routing gap (different package, out of scope for T17).

## CWI Import Chain Status
1. ✅ `core.cognitive` — 9 symbols exported (T16)
2. ✅ `core.orchestration` — 5 symbols exported (T17)
3. ❌ `integrations.decision_routing` — missing `DecisionRouterRegistry` (next mission)