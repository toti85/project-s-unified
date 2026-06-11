# AO5_T16 CWI Export Surface Repair — PARTIAL PASS

**Date:** 2026-06-11
**Status:** PARTIAL PASS (cognitive exports OK, CWI blocked by orchestration gap)
**Run ID:** AO5_T16_CWI_EXPORT_REPAIR

## What Changed
Modified `src/core/cognitive/__init__.py` to export all 9 symbols required by `cognitive_workflow_integration.py`.

## Backup Path
`src/core/cognitive/__init__.py.bak_t16`

## Import Test Results
- **SYNTAX_OK:** ✅
- **EXPORTS_OK:** ✅ All 9 symbols importable from `core.cognitive`
- **CWI_IMPORT_OK:** ❌ ImportError — `WorkflowRegistry` not exported from `core.orchestration`
- **Registry smoke:** ✅ `cognitive_registry` is `CognitiveRegistry` instance
- **CognitiveCore regression:** ✅ (included in EXPORTS_OK)

## CWI Import Failure Root Cause
`cognitive_workflow_integration.py` line 41 imports:
```python
from core.orchestration import WorkflowRegistry, LangGraphWorkflowEngine, WorkflowResult, workflow_registry
```

`core/orchestration/__init__.py` only exports `WORKFLOW_ENGINE_AVAILABLE`. The `workflow_engine.py` module exists but its symbols are not re-exported by `__init__.py`.

**This is a separate issue from the cognitive export surface repair.** The cognitive package now correctly exports all required symbols. The orchestration gap is a pre-existing issue.

## Files Modified
- `src/core/cognitive/__init__.py` — export shim with 9 symbols

## Rollback Command
```bash
git restore -- src/core/cognitive/__init__.py
```

## Verdict
**PARTIAL PASS** — Cognitive export surface repaired. CWI import blocked by separate orchestration gap (out of scope for T16).

## Next Steps
- Orchestration export gap needs separate fix
- CWI cannot fully import until `core.orchestration` exports `WorkflowRegistry`, `LangGraphWorkflowEngine`, `WorkflowResult`, `workflow_registry`