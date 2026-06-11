# AO5_T19 CWI Runtime Smoke Test — PARTIAL PASS

**Date:** 2026-06-11
**Status:** PARTIAL PASS
**Run ID:** AO5_T19_CWI_RUNTIME_SMOKE

## Public Entrypoints Found
- `CognitiveWorkflowIntegration.__init__(config)` — constructor
- `process_task_cognitively(task_description, context, user_id)` — async main entry point
- `_initialize_components()` — internal initialization
- `_perform_cognitive_analysis()` — internal cognitive analysis
- `_select_and_configure_workflow()` — internal workflow selection
- `_execute_cognitive_workflow()` — internal workflow execution
- `_post_process_and_learn()` — internal post-processing

## Import Result
- **CWI_IMPORT_OK:** ✅

## Instantiation Result
- **CWI_INSTANCE_OK:** ✅ `CognitiveWorkflowIntegration`

## Minimal Task Result
- **Task:** "count words in a text file"
- **Executed:** ✅ (no crash, returned structured result)
- **Latency:** 213.41ms
- **Result:**
```json
{
  "success": false,
  "error": "'NoneType' object has no attribute 'make_decision'",
  "execution_id": "exec_1781130229",
  "timestamp": "2026-06-11T01:23:49.219061"
}
```

## Error Analysis
The `make_decision` error occurs because `self.decision_router` is `None`.
The `router_registry.get_router("advanced_router")` call in `_initialize_components()` returns `None` because the AdvancedDecisionRouter is not registered under that key.

This is a runtime registration issue, not an import/export issue. The export surface is repaired.

## Registry State
- **EnhancedCognitiveProcessor:** ✅ registered as "enhanced_cognitive_processor"
- **AdvancedIntentAnalyzer:** ✅ registered as "advanced_intent_analyzer"
- **SemanticReasoningEngine:** ✅ registered as "semantic_reasoning_engine"

All 3 cognitive components are properly registered and instantiated.

## Warnings/Dependency Fallback
- LangChainDeprecationWarning: pydantic v1 shim (from langgraph, not our code)

## Verdict
**PARTIAL PASS** — Import ✅ + Instantiate ✅ + Processing returns structured result ✅ but processing blocked by unregistered decision router (runtime registration issue, not export surface).

## Files Modified
- **NONE** — verification only