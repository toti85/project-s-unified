# GAP_029 Fix Verdict: Replan Delta Validation

**Date:** 2026-05-18  
**Status:** RESOLVED (primary fix confirmed)  
**Fix Applied:** Option 1 — REPLAN must include concrete corrective delta

---

## 1. Executive Verdict

**GAP_029 is RESOLVED.** The primary fix — requiring concrete corrective delta for replan actions — successfully broke the non-converging replan loop that caused 5/8 tests to fail with `max_iters`.

### Before Fix (Original Run)
| Metric | Count |
|--------|-------|
| PASS | 2 |
| PARTIAL | 1 |
| FAIL | 5 |
| **Total** | **8** |

### After Fix (Rerun)
| Metric | Count |
|--------|-------|
| PASS | 4 |
| PARTIAL | 0 |
| FAIL | 4 |
| **Total** | **8** |

### Improvement Summary
- **TEST_4** (Diagnostic-style operator request): FAIL → **PASS** ✅
- **TEST_7** (Output-format compliance): PARTIAL → **PASS** ✅
- **TEST_1** (Direct simple answer): FAIL → FAIL (different reason)
- **TEST_5** (External research task): FAIL → FAIL (different reason)
- **TEST_6** (Internal-doc reasoning): FAIL → FAIL (different reason)
- **TEST_8** (Truthfulness/impossible prediction): FAIL → FAIL (different reason)

---

## 2. What Changed

### The Non-Converging Loop is Broken

**Before:** All 5 failed tests entered a blind replan loop where the evaluator returned `action: replan` without concrete corrective feedback, and the MetaController blindly re-ran the same plan 5 times until `max_iters`.

**After:** The vague replan is now downgraded. The 4 remaining failures no longer die from `max_iters` — they die from a different reason: "answer does not address user prompt." This means the replan loop was broken, but the output quality is still insufficient for these prompts.

### Key Insight

The GAP_029 fix successfully addressed the **systemic replan convergence failure**. The remaining 4 failures are a **different problem**: the LLM output quality for these specific prompt types is insufficient, not the replan mechanism.

---

## 3. Unit Test Results

**35/35 tests passed** in 0.12 seconds.

| Test Category | Count | Status |
|---------------|-------|--------|
| has_concrete_corrective_delta | 12 | All pass |
| normalize_evaluator_action | 12 | All pass |
| validate_replan_action | 3 | All pass |
| track_replan_count | 5 | All pass |
| Integration (full flow) | 3 | All pass |

---

## 4. Replan Count Tracking

**Fixed.** The `track_replan_count` function now correctly counts replan events from the mission events table and persists the verified count into mission metadata.

---

## 5. Files Changed

| File | Change |
|------|--------|
| `src/core/evaluator_gap029.py` | **NEW** — Replan delta validation module |
| `src/core/evaluator.py` | Modified `_handle_evaluation_result` to call `normalize_evaluator_action` |
| `tests/test_gap029_replan_delta_validation.py` | **NEW** — 35 unit tests |

---

## 6. Normalization Rule (Exact)

```
If action=replan AND (specific_issues OR proposed_change OR details) present:
    → Keep as replan (valid replan with corrective delta)

If action=replan AND no corrective delta AND confidence >= 0.8 AND goal_achieved=False:
    → Downgrade to fail (high-confidence inadequate output)

If action=replan AND no corrective delta AND (confidence < 0.8 OR goal_achieved=True):
    → Downgrade to continue (uncertain output, accept as-is)

If action != replan:
    → No change
```

---

## 7. GAP_029 Final Status

**RESOLVED.**

The non-converging vague-replan loop is gone. The 5 original `max_iters` failures are no longer caused by blind replan loops.

**Remaining 4 failures** (TEST_1, TEST_5, TEST_6, TEST_8) are due to a different issue: the LLM output quality for these prompt types is insufficient. This is NOT a GAP_029 issue — it is an output quality issue that should be addressed separately.

---

## 8. TEST_7 Status

**RESOLVED.** TEST_7 went from PARTIAL to PASS. The output-format compliance issue was likely a side effect of the replan loop — when the replan was downgraded to continue, the LLM had a better chance to produce a compliant output.

---

## 9. Can We Proceed?

**Yes, with caveats.**

The GAP_029 fix is confirmed working. The system no longer gets stuck in blind replan loops. However:

1. **4 tests still fail** — not from replan loops, but from insufficient output quality.
2. **The remaining failures need a different fix** — likely improving the evaluator's answer adequacy check (GAP_027) or the strategic planner's output quality.
3. **Broader Interactive Layer testing can proceed** — the replan convergence issue is resolved.

**Recommendation:** Proceed to broader Interactive Layer testing, but address the remaining 4 output quality failures before adding new features (file upload/download).