# MS_AO8J_4 — Run ID Content Mismatch Fix

**Date:** 2026-06-23  
**Author:** Cline (AO8J_4)  
**Status:** COMPLETE  

---

## A. Mismatch Root Cause Confirmed

**Root cause:** When the gateway returned `PAUSE` for cycle N, the goal remained `PENDING` (not marked as PAUSED or FAILED). On the next cycle, `_pick_next_goal()` picked the same goal again. The Continue CLI executor re-ran the prompt. However, the produced `last_output.md` had content from the **old** run (carried over from a prior execution, run_id mismatch), while `output_ready.json` had the new `run_id`. The CM consumed without verifying the content matched the expected `run_id`.  

**Evidence from cycle log:**
- Cycle AO8J_LOOP_TEST_16: gateway decision = PAUSE — goal left PENDING  
- Cycle AO8J_LOOP_TEST_17: Continue executed again same goal, produced empty output  
- `output_ready.json`: `run_id = AO8J_RERUN_CLEAN_01`  
- `last_output.md` content: referenced `AO8J_RERUN_CLEAN_03` / `AO5_T64`  
- Gateway returned PAUSE → infinite retry loop  

---

## B. Run ID Header Enforced (Patch 1)

**File:** `orchestrator_runtime/governance/continue_executor_adapter.py`  

Before writing `last_output.md`, a header is prepended:

```
Run ID: <run_id>
Goal ID: <goal_id>

<original content>
```

This ensures every output file carries its own identity for verification. The `metadata` dict now flows `goal_id` through to `write_continue_output_to_outbox()`.

---

## C. Pre-Consume Mismatch Guard Implemented (Patch 2)

**File:** `orchestrator_runtime/continuous_mind.py`  

New function: `_check_output_identity(expected_run_id, expected_goal_id)`  
- Reads first 5 lines of `last_output.md`  
- Parses `Run ID:` and `Goal ID:` lines  
- If either mismatches or the header is missing entirely (pre-AO8J_4 format), returns a description string  
- If match, returns `None`  

In the Continue consume path, before `_consume_via_gateway()`:
```python
_mismatch = _check_output_identity(run_id, goal_id)
if _mismatch:
    log.warning("Run ID mismatch for goal %s: %s", goal_id, _mismatch)
    _archive_outbox_for_mismatch(run_id)
    _mark_goal_failed(goal_id, f"MISMATCH: {_mismatch}")
    continue  # skip to next cycle
```

Additional helpers:  
- `_archive_outbox_for_mismatch()` — moves outbox files to `archive/{ts}_MISMATCH_{run_id}_{file}`  
- `_mark_goal_failed()` — sets `status: "FAILED"` on the goal so it's never retried  

---

## D. PAUSE Handling Fixed (Patch 3)

**File:** `orchestrator_runtime/continuous_mind.py`  

Two changes:  

1. **`SKIP_STATUSES` constant** extended:
```python
SKIP_STATUSES = DONE_STATUSES | {"PAUSED", "FAILED", "NEEDS_HUMAN"}
```
Used in `_pick_next_goal()` to filter out non-pending goals.

2. **PAUSE branch now marks goal as PAUSED:**
```python
elif gateway == "PAUSE" or status in ("PENDING_HUMAN", "AWAIT_HUMAN"):
    _mark_goal_paused(goal_id)  # AO8J_4: NEW
```
This sets `status: "PAUSED"` with note `"Awaiting human review per PAUSE gateway decision"`.

Both PAUSE and FAILED statuses are now in `SKIP_STATUSES`, so the next cycle will skip them and move to the next pending goal (or idle safely).

---

## E. Tests Pass

**Test file:** `orchestrator_runtime/sandbox/test_ao8j_4_patches.py`

| Test | Description | Result |
|------|-------------|--------|
| 1 | Matching run_id/goal_id passes | PASS |
| 2 | Mismatched Run ID detected | PASS |
| 3 | Pre-AO8J_4 format (no header) detected | PASS |
| 4 | `_pick_next_goal` skips PAUSED/FAILED goals | PASS |
| 5 | `_set_goal_status` works | PASS |
| 6 | Continue adapter injects Run ID / Goal ID header | PASS |

All 6 tests pass.

---

## F. Ready for Clean Rerun

After fix deployment:
1. Kill any running CM process
2. Clear stale `output_ready.json` / `last_output.md` from `cline_outbox/`
3. Set goal `AO8J_RERUN_CLEAN_01` status back to `PENDING` in `goal_queue.json`
4. Launch with `CM_CONTINUE_MODE=1`
5. The mismatch guard will reject any pre-AO8J_4 output (marked FAILED)
6. A fresh Continue execution will produce `last_output.md` with proper Run ID header
7. If gateway returns PAUSE → goal marked PAUSED, not retried
8. Next cycle picks a different pending goal or idles cleanly

---

## G. Source Modifications

**NO** — `src/` directory was NOT modified.

---

## H. Self State Modifications

**NO** — `self_state.json` was NOT modified.

---

## I. Git Status

Files modified by this fix:

- `orchestrator_runtime/continuous_mind.py` — patches B, C, D  
- `orchestrator_runtime/governance/continue_executor_adapter.py` — patch B  
- `orchestrator_runtime/sandbox/test_ao8j_4_patches.py` — test file (new, in sandbox/)  

No other source or config files touched.