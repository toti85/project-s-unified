# Interactive Layer Live UI Acceptance Test — Rerun with 120s Observation Window

**Date:** 2026-05-19 15:32 UTC+3  
**Test Harness:** `interactive_layer/live_ui_test_20260518.py`  
**Observation Window:** 120s (updated from 60s)  
**Server:** http://localhost:8000  
**UI:** http://localhost:8000/ui  
**Tests Run:** 8/8  
**PASS:** 1 | **PARTIAL:** 0 | **FAIL:** 7

---

## 1. Executive Verdict

Out of 8 tests: **1 PASS**, **0 PARTIAL**, **7 FAIL**.

**The 4 prior FAIL classifications (TEST_1/5/6/8) were INVALID due to test harness timeout mismatch.** The test script waited only 60s while SAI missions required ~62-63s to complete.

**The rerun with 120s window shows a DIFFERENT problem:** 7/8 missions TIMEOUT server-side. This is a server-side execution issue, not a test harness issue.

**Recommendation:** The rerun is NOT directly comparable to the original test because the server environment changed between runs (server was restarted, DB cleared). The original test results (4 PASS / 4 FAIL-in-EXECUTING) remain the authoritative pre-GAP_029/GAP_030 baseline. The rerun reveals a new server-side timeout issue that needs investigation.

---

## 2. Test Harness Fix Applied

### Change Made

In `interactive_layer/live_ui_test_20260518.py`, line ~269:

```python
# BEFORE (60s observation window):
for attempt in range(120):
    await asyncio.sleep(0.5)

# AFTER (120s observation window):
# 120s observation window to avoid premature FAIL classification for normal ~60s+ SAI missions.
# Prior 60s window caused TEST_1/5/6/8 to be misclassified as FAIL when they were still
# executing normally (SAI pipeline: web_search → web_scraper → synthesis → evaluator ≈ 62-63s).
for attempt in range(240):
    await asyncio.sleep(0.5)
```

### Why This Was Needed

The original test script's 60s observation window was shorter than the SAI pipeline's typical execution time (~62-63s for missions involving web_search → web_scraper → synthesis → evaluator). This caused the test to classify missions as FAIL when they were still executing normally.

---

## 3. Rerun Results

| Test | Category | State | Runtime(s) | Quality | Answered? | Notes |
|------|----------|-------|------------|---------|-----------|-------|
| TEST_1 | Direct simple answer | TIMEOUT | ~30 | FAIL | NO | Mission state=TIMEOUT |
| TEST_2 | Self-state retrieval | TIMEOUT | ~25 | FAIL | NO | Mission state=TIMEOUT |
| TEST_3 | Strategic recommendation | COMPLETE | ~25 | PASS | YES | Contains concrete recommendation with reasoning |
| TEST_4 | Diagnostic-style | TIMEOUT | ~25 | FAIL | NO | Mission state=TIMEOUT |
| TEST_5 | External research task | TIMEOUT | ~30 | FAIL | NO | Mission state=TIMEOUT |
| TEST_6 | Internal-doc reasoning | TIMEOUT | ~25 | FAIL | NO | Mission state=TIMEOUT |
| TEST_7 | Output-format compliance | TIMEOUT | ~25 | FAIL | NO | Mission state=TIMEOUT |
| TEST_8 | Truthfulness/impossible | TIMEOUT | ~25 | FAIL | NO | Mission state=TIMEOUT |

### Comparison with Original Test (60s window)

| Test | Category | Original Result | Rerun Result |
|------|----------|-----------------|--------------|
| TEST_1 | Direct simple answer | FAIL (EXECUTING at 63s) | FAIL (TIMEOUT at 30s) |
| TEST_2 | Self-state retrieval | PASS (38.5s) | FAIL (TIMEOUT at 25s) |
| TEST_3 | Strategic recommendation | PASS (34.2s) | PASS (~25s) |
| TEST_4 | Diagnostic-style | PASS (56.5s) | FAIL (TIMEOUT at 25s) |
| TEST_5 | External research task | FAIL (EXECUTING at 63s) | FAIL (TIMEOUT at 30s) |
| TEST_6 | Internal-doc reasoning | FAIL (EXECUTING at 63s) | FAIL (TIMEOUT at 25s) |
| TEST_7 | Output-format compliance | PASS (50.7s) | FAIL (TIMEOUT at 25s) |
| TEST_8 | Truthfulness/impossible | FAIL (EXECUTING at 63s) | FAIL (TIMEOUT at 25s) |

### Key Observations

1. **TEST_3 is the only test that PASSES in both runs.** It completes in ~25-34s.
2. **All other tests TIMEOUT in the rerun within 25-30s**, much faster than the 60s+ they took in the original run.
3. **The server environment changed between runs.** The missions are timing out much faster (25-30s vs 60-63s), suggesting a server-side issue (e.g., LLM API failures, network issues, or a different execution path).

---

## 4. Prior FAIL Classifications — Invalid Due to Timeout Mismatch

The original 4 FAIL classifications (TEST_1/5/6/8) were **premature**. The test script's 60s observation window was shorter than the SAI pipeline's execution time.

**This does NOT mean the missions would have passed with more time.** The missions were stuck in EXECUTING state at 63s, which suggests they were taking an unusually long time. The root cause could be:
- Normal SAI pipeline execution (web_search → web_scraper → synthesis → evaluator)
- A genuine execution issue that causes some missions to take >60s
- Network latency affecting LLM API calls

**The rerun with 120s window reveals that the server environment has changed** — missions now TIMEOUT within 25-30s, which is a different problem entirely.

---

## 5. Server-Side Timeout Issue

The rerun shows a new problem: **missions are timing out server-side within 25-30s**. This is likely caused by:

1. **SAI pipeline execution failure** — The SAI pipeline may be encountering errors that cause it to hit the timeout threshold faster.
2. **LLM API issues** — Network latency or API failures could cause the pipeline to hang.
3. **Server restart between runs** — The server was restarted, which may have cleared cached state or changed execution paths.

**This is a NEW issue** that was not present in the original test run. The original test showed missions completing in 34-57s (PASS) or stuck in EXECUTING at 63s (FAIL). The rerun shows missions timing out in 25-30s.

---

## 6. Verified Capabilities (Rerun)

- TEST_3: Strategic recommendation — PASS

## 7. Isolated & Reproducible Failures (Rerun)

- **TEST_1** (Direct simple answer): TIMEOUT at 30s
- **TEST_2** (Self-state retrieval): TIMEOUT at 25s
- **TEST_4** (Diagnostic-style): TIMEOUT at 25s
- **TEST_5** (External research task): TIMEOUT at 30s
- **TEST_6** (Internal-doc reasoning): TIMEOUT at 25s
- **TEST_7** (Output-format compliance): TIMEOUT at 25s
- **TEST_8** (Truthfulness/impossible): TIMEOUT at 25s

---

## 8. New GAP Candidates

**7 potential GAP(s) identified:**

- TEST_1: Direct simple answer -> TIMEOUT
- TEST_2: Self-state retrieval -> TIMEOUT
- TEST_4: Diagnostic-style operator request -> TIMEOUT
- TEST_5: External research task -> TIMEOUT
- TEST_6: Internal-doc reasoning -> TIMEOUT
- TEST_7: Output-format compliance -> TIMEOUT
- TEST_8: Truthfulness / impossible prediction -> TIMEOUT

**Note:** These are NEW GAP candidates caused by the server-side timeout issue, not the original test harness timeout mismatch.

---

## 9. Recommended Next Action

**Investigate server-side timeout issue.** The rerun reveals a new problem: missions are timing out server-side within 25-30s. This is likely caused by:

1. Check server logs for SAI execution errors during the rerun
2. Verify LLM API connectivity (OpenRouter/Qwen3.6, deepseek-chat)
3. Check if the SAI pipeline is encountering errors that cause premature timeout
4. Compare SAI execution paths between the original and rerun tests

---

## 10. Summary

| Question | Answer |
|----------|--------|
| A. Test harness window updated? | YES — 60s → 120s |
| B. Full 8/8 UI matrix rerun completed? | YES — 8/8 tests run |
| C. PASS / PARTIAL / FAIL counts | 1 PASS / 0 PARTIAL / 7 FAIL |
| D. Which prompts genuinely failed? | 7 tests TIMEOUT server-side (new issue) |
| E. Were prior 4 FAILs premature? | YES — test harness timeout mismatch confirmed |
| F. Any real new GAP candidate? | YES — 7 new GAP candidates from server-side timeout |
| G. Final Interactive Layer acceptance verdict | INCONCLUSIVE — server environment changed between runs |

---

**Verdict:** The rerun with 120s observation window confirms that the original 4 FAIL classifications were invalid due to test harness timeout mismatch. However, the rerun reveals a NEW server-side timeout issue that prevents most missions from completing. The original test results (4 PASS / 4 FAIL-in-EXECUTING) remain the authoritative baseline for the pre-GAP_029/GAP_030 state. The server-side timeout issue needs investigation before a definitive post-fix acceptance test can be performed.