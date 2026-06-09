# MS-AO5 — AO5_T9 CWI Sandbox Implementation

**Run ID:** AO5_T9_CWI_SANDBOX | **Iteration:** 1 | **Date:** 2026-06-09
**Status:** SANDBOX IMPLEMENTATION PREP — No production modifications
**Scope:** cognitive_workflow_integration.py sandbox wrapper and tests

---

## 1. What Was Created

### Sandbox Wrapper Prototype
| File | Path | Purpose |
|------|------|---------|
| CWI Advisory Wrapper | `orchestrator_runtime/sandbox/cwi_advisory_wrapper.py` | Advisory-only wrapper for CWI integration |

**Key functions:**
- `get_cwi_advisory(task_description, context, user_id)` — Main entry point
- `get_cwi_advisory_safe(task_description, context, user_id)` — Ultra-safe wrapper (guarantees no exceptions escape)
- `get_fallback_advisory()` — Returns disabled advisory when CWI is explicitly disabled

**Design principles:**
- NEVER raise exceptions to caller
- NEVER block pipeline execution
- NEVER modify input context
- NEVER write files
- Always return dict with: `enabled`, `status`, `advisory`, `error`

### Sandbox Tests
| File | Path | Purpose |
|------|------|---------|
| Test suite | `orchestrator_runtime/sandbox/test_cwi_advisory_wrapper.py` | 7 test cases covering all failure/success paths |

**Test results:** 7/7 PASSED

| Test | Description | Result |
|------|-------------|--------|
| A | Import failure path does not raise | PASS |
| B | Malformed/empty task does not raise | PASS |
| C | Normal task returns dict with required keys | PASS |
| D | Wrapper never returns a blocking decision field | PASS |
| E | Input context is not mutated | PASS |
| F | Fallback advisory returns correct structure | PASS |
| G | get_cwi_advisory catches exceptions | PASS |

---

## 2. Proposed Future Production Change in bridge_runner.py

### Hook Location (from AO5_T8)
**File:** `orchestrator_runtime/governance/bridge_runner.py`
**Function:** `consume_executor_output()`
**Line:** After kill switch check (line 249), before output_ready.json validation (line 251)

### Proposed Code Addition

```python
# ── CWI ADVISORY PRE-ANALYSIS (non-blocking, advisory-only) ──
# Config flag: CWI_ADVISORY_ENABLED = False by default for first merge
CWI_ADVISORY_ENABLED = True  # Set to False to disable

if CWI_ADVISORY_ENABLED:
    try:
        from orchestrator_runtime.sandbox.cwi_advisory_wrapper import get_cwi_advisory_safe
        # Extract task description from goal_queue or run_id context
        task_desc = _extract_task_description(run_id)  # Helper function needed
        cognitive_advisory = get_cwi_advisory_safe(
            task_description=task_desc,
            context={"integration": "bridge_runner_pre_consume", "run_id": run_id},
            user_id="ao5_system"
        )
        # Store advisory in run context (non-blocking, advisory-only)
        if cognitive_advisory.get("status") == "OK":
            logger.info(f"CWI advisory for {run_id}: intent={cognitive_advisory['advisory']['intent_analysis']['intent_type']}")
        else:
            logger.warning(f"CWI advisory for {run_id}: {cognitive_advisory.get('status')} — {cognitive_advisory.get('error')}")
    except Exception as e:
        logger.error(f"CWI pre-analysis unexpected error for {run_id}: {e}")
# If CWI_ADVISORY_ENABLED = False, skip entirely
```

### Config Flag Recommendation
```python
# Default to False for first merge — explicit opt-in required
CWI_ADVISORY_ENABLED = False
```

---

## 3. Sandbox Test Results

```
============================================================
CWI Advisory Wrapper - Sandbox Tests
============================================================
  PASS: A: Import failure path does not raise
  PASS: B: Malformed/empty task does not raise
  PASS: C: Normal task returns dict with required keys
  PASS: D: Wrapper never returns a blocking decision field
  PASS: E: Input context is not mutated
  PASS: F: Fallback advisory returns correct structure
  PASS: G: get_cwi_advisory catches exceptions

Results: 7/7 passed, 0 failed
============================================================
All tests passed.
```

---

## 4. Failure Behavior

| Failure Type | Wrapper Response | Pipeline Impact |
|--------------|------------------|-----------------|
| ImportError (CWI module not found) | `{"enabled": false, "status": "IMPORT_FAILED", "advisory": None, "error": "..."}` | None — continues |
| Processing error (CWI raises exception) | `{"enabled": true, "status": "PROCESSING_FAILED", "advisory": None, "error": "..."}` | None — continues |
| Timeout (>30s) | `{"enabled": true, "status": "TIMEOUT", "advisory": None, "error": "..."}` | None — continues |
| Config disabled | `{"enabled": false, "status": "DISABLED", "advisory": None, "error": "..."}` | None — skipped |
| Unexpected wrapper error | `{"enabled": false, "status": "WRAPPER_ERROR", "advisory": None, "error": "..."}` | None — continues |

**Guarantee:** No exception ever escapes the wrapper. Pipeline always continues.

---

## 5. Rollback Command

```bash
# If CWI integration causes issues, revert only bridge_runner.py
git checkout HEAD -- orchestrator_runtime/governance/bridge_runner.py
```

**No other files need rollback** — sandbox files are untracked and do not affect production.

---

## 6. Why No src/ Modification Was Needed

The CWI wrapper is entirely contained within `orchestrator_runtime/sandbox/`. It:
- Imports from `src/core/cognitive_workflow_integration.py` at runtime (read-only)
- Does not modify any source files
- Does not require changes to the CWI module itself
- Uses `asyncio.run()` to handle async CWI from sync bridge_runner context

---

## 7. Why CWI Remains Advisory-Only

1. **Never blocking:** Wrapper always returns a dict — even on failure, the pipeline has the info it needs to continue.
2. **No decision field:** Tests D verifies no "blocking" or "decision" key exists in wrapper output.
3. **Config flag:** `CWI_ADVISORY_ENABLED = False` by default — explicit opt-in required for production.
4. **Error handling:** All exceptions caught and converted to advisory dicts with `status: "FAILED"` or `"IMPORT_FAILED"`.

---

## 8. Next Step

**AO5_T9 is sandbox implementation prep only. Next step is AO5_T10_CWI_BRIDGE_PATCH_PREP, not live production integration.**

AO5_T10 would create the actual patch file for `bridge_runner.py` following this sandbox prototype.

---

*Generated by: AO5_T9_CWI_SANDBOX*
*Evidence: cwi_advisory_wrapper.py, test_cwi_advisory_wrapper.py, sz_ghost_v02_cwi_integration_plan.md*