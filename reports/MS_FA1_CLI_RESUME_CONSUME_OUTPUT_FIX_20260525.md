# MS-FA1 CLI Resume/Consume-Output Fix

**Date:** 2026-05-26
**Version:** FA1-ResumeFix
**Status:** COMPLETE
**Verdict:** PASS

---

## Problem

After Cline completed FA1_012 and wrote `last_output.md` and `output_ready.json`, running `run-loop --auto` created a new run (FA1_013) instead of consuming the existing output. This broke the operator workflow.

## Root Causes

1. `run-loop` did not check for unconsumed `output_ready.json` before starting a new run
2. No `consume-output` command existed for explicit output consumption
3. No `resume` command existed for continuing from current state
4. `StateMachine.load()` used `__new__` without setting `_runs_dir`, causing `AttributeError` on state persistence

## Fixes Applied

### 1. `consume-output` Command

**New CLI command:** `python -m orchestrator.cli consume-output --run-id FA1_012`

**Process:**
1. Read `output_ready.json` from `cline_outbox/`
2. Verify `run_id` matches
3. Verify not already consumed
4. Read `last_output.md`
5. Save output to `runs/{run_id}/output.md`
6. Transition state machine to `CLINE_OUTPUT_RECEIVED`
7. Evaluate output (AI or heuristic)
8. Issue verdict
9. Archive if PASS
10. Set `consumed=true` in `output_ready.json`

### 2. `resume` Command

**New CLI command:** `python -m orchestrator.cli resume --run-id FA1_012`

**Process:**
1. Load state machine for run
2. If `IN_PROGRESS` or `WAITING_FOR_CLINE`: check for unconsumed output, consume if found, otherwise wait
3. If `EVALUATING_OUTPUT`: evaluate saved output
4. If `VERDICT_ISSUED` or `ARCHIVED`: report existing verdict

### 3. `run-loop` Unconsumed Output Detection

**Before:** Silently started new run, clearing outbox first.

**After:** Checks for unconsumed `output_ready.json` before clearing outbox. If found:
```
BLOCKED: Unconsumed output exists for run_id FA1_012.

Options:
  1. Consume it: python -m orchestrator.cli consume-output --run-id FA1_012
  2. Resume it: python -m orchestrator.cli resume --run-id FA1_012
  3. Clear outbox manually and re-run
```
Exits safely with code 1.

### 4. `StateMachine.load()` Bug Fix

**File:** `src/orchestrator/state_machine.py`

**Bug:** `load()` used `__new__` to skip `__init__`, but forgot to set `_runs_dir`.

**Fix:** Added `sm._runs_dir = runs_dir or RUNS_DIR` in `load()`.

### 5. FA1_013 Marked Accidental

**File:** `orchestrator_runtime/runs/FA1_013/ACCIDENTAL_NEW_RUN.md`

FA1_013 was created accidentally and must NOT be counted as Auto Mode validation.

---

## FA1_012 Consume-Output Result

```
============================================================
Consume Output: FA1_012
============================================================

Output received: 2079 chars

Output saved to: C:\ProjectS-Unified\orchestrator_runtime\runs\FA1_012\output.md
Evaluating output...
  Verdict: PASS
  Confidence: 1.00
  Summary: Heuristic evaluation: PASS (confidence 1.00)

Verdict issued for FA1_012
Run archived.
Output marked as consumed.

COMPLETE: FA1_012 verdict = PASS
```

**Result:** PASS — FA1_012 consumed, evaluated, verdict issued, archived, consumed=true.

---

## Files Modified

| File | Change |
|------|--------|
| `src/orchestrator/cli.py` | Added `consume-output`, `resume`, unconsumed output detection, `_has_unconsumed_output()` |
| `src/orchestrator/state_machine.py` | Fixed `load()` to set `_runs_dir` |
| `orchestrator_runtime/runs/FA1_013/ACCIDENTAL_NEW_RUN.md` | NEW — marks FA1_013 as accidental |
| `reports/MS_FA1_CLI_RESUME_CONSUME_OUTPUT_FIX_20260525.md` | NEW — this report |

---

## CLI Commands Summary

| Command | Description |
|---------|-------------|
| `--help` | Show help |
| `list-runs` | List all runs |
| `status` | Show latest run status + verdict |
| `check-env` | Check OpenRouter env setup |
| `consume-output --run-id X` | Consume Cline output for existing run |
| `resume --run-id X` | Resume existing run from current state |
| `run-loop --auto --max-iterations N` | Execute a run loop (blocks if unconsumed output exists) |

---

## Report Answers

| Question | Answer |
|----------|--------|
| A. consume-output command added? | **YES** |
| B. resume command added? | **YES** |
| C. run-loop prevents accidental new run? | **YES** — Blocks with clear instructions when unconsumed output exists |
| D. FA1_013 marked accidental/incomplete? | **YES** — `ACCIDENTAL_NEW_RUN.md` created |
| E. FA1_012 consumed/evaluated? | **YES** |
| F. FA1_012 final verdict | **PASS** (confidence: 1.00, heuristic evaluator) |
| G. tests pass? | **24/24** (sandbox tests) |
| H. ready to continue Auto Mode v1 validation? | **YES** — CLI workflow fixed, FA1_012 validated |

---

**Document End**