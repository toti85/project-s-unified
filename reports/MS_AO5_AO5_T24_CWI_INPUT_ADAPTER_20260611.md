# AO5_T24 CWI Input Adapter — PASS

**Date:** 2026-06-11
**Status:** PASS
**Run ID:** AO5_T24_CWI_INPUT_ADAPTER

## Root Cause
CWI's `process_task_cognitively()` returns:
```
{success, results, cognitive_analysis, learning_insights, execution_metrics, timestamp}
```

The wrapper validated for flat keys:
```
{success, intent_analysis, task_decomposition, semantic_reasoning, processing_context}
```

These keys exist inside `cognitive_analysis`, not at the top level. Result: `KeyError: Missing required key in advisory: intent_analysis`.

## Fix Applied
Added T24 adapter in `cwi_advisory_wrapper.py` that promotes `cognitive_analysis` sub-keys to top level:
```python
advisory = dict(raw_advisory)
ca = raw_advisory.get("cognitive_analysis")
if isinstance(ca, dict):
    for key in ("intent_analysis", "task_decomposition", "semantic_reasoning", "processing_context"):
        if key in ca and key not in advisory:
            advisory[key] = ca[key]
```

## Files Modified
- `orchestrator_runtime/sandbox/cwi_advisory_wrapper.py` — adapter layer

## Backup
- `orchestrator_runtime/sandbox/cwi_advisory_wrapper.py.bak_t24`

## Rollback Command
```bash
git restore -- orchestrator_runtime/sandbox/cwi_advisory_wrapper.py
```

## Manual Test Results
- **Verdict:** ACCEPTED
- **CWI_status:** OK
- **CWI_output_first_200:** Contains real cognitive evidence (success, workflow_execution, intent_analysis)
- **CWI_latency_ms:** 38791.92 (first run includes import overhead)
- **Total latency:** 11.89ms (consume phase)

## Observation Entry
```json
{
  "cwi_enabled": true,
  "cwi_status": "OK",
  "cwi_output_first_200": "{'success': True, 'results': {'workflow_execution': WorkflowResult(status=<WorkflowStatus.COMPLETED: 'completed'>, ...",
  "cwi_latency_ms": 38791.92,
  "verdict": "ACCEPTED"
}
```

## Verdict
**PASS** — CWI adapter resolves shape mismatch. Real cognitive evidence in telemetry.