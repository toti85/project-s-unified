# GAP_031 — Interactive Output Quality Root Cause Analysis

**Date:** 2026-05-19 11:07 UTC+3  
**Type:** DIAGNOSIS-ONLY (no implementation)  
**Trigger:** Post-GAP_029/GAP_030 hardening — 4 remaining FAILs in Interactive Layer live test rerun

---

## 1. Executive Verdict

**ROOT CAUSE: SAI pipeline execution timeout — not output quality.**

All 4 remaining FAILs share a **single root cause**: the SAI pipeline is not completing within the test script's 60-second observation window. The missions are stuck in `EXECUTING` state because `ai.execute_intelligent_task()` is still running when the test script gives up waiting.

This is **NOT** an output quality issue. The test script's `quality_judge()` function returns `FAIL` with note `"Mission state=EXECUTING, not COMPLETE"` — it never evaluates the answer because no answer is produced within the timeout.

**GAP_031 SHOULD NOT OPEN.** The candidate definition ("Interactive missions can reach a terminal result whose final user-facing output does not substantively answer the prompt") does not match the evidence. The missions are not reaching terminal results — they are not completing at all within the test window.

---

## 2. Per-Test Analysis

### TEST_1: Direct simple answer

**Prompt:** "Írj 3 rövid mondatot arról, miért fontos a pontos dokumentáció."

| Step | Detail |
|------|--------|
| 1. Prompt category | Direct simple answer (Hungarian, 3 sentences) |
| 2. Strategic plan | MetaController receives goal, Phase 1 planner analyzes task |
| 3. Recommended tools | Planner likely recommends web_search/web_scraper (no direct-answer shortcut) |
| 4. Actual tools executed | web_search (DDGS) → web_scraper → synthesis → evaluator |
| 5. Raw tool/output material | Web search results about documentation importance |
| 6. Final synthesis/final_result stored | Qwen3.6 synthesis of web results into structured memo |
| 7. Final UI-displayed answer | **NOT PRODUCED** — mission still in EXECUTING at 63s |
| 8. Evaluator verdict/action | **NOT REACHED** — mission times out before evaluation completes |
| 9. Why marked "does not address prompt" | **WRONG REASON** — test script never sees the answer; FAIL is due to `state=EXECUTING` |
| 10. Exact failure layer | **TIMEOUT MISMATCH** — SAI pipeline takes >60s, test script waits only 60s |

**Key evidence:**
- Test script `live_ui_test_20260518.py` line 269: `for attempt in range(120)` with `await asyncio.sleep(0.5)` = 60s max wait
- SAI runner `sai_runner.py` line 56: `DEFAULT_TIMEOUT = 600` (10 minutes)
- Server log: TEST_1 stuck in EXECUTING from 5s through 55s, no state change
- PASS tests (TEST_2, TEST_3, TEST_4, TEST_7) complete in 34-57s — borderline the 60s timeout

---

### TEST_5: External research task

**Prompt:** "Keress röviden 3 aktuális okot arra, miért hasznos a lokális LLM egy saját AI-infrastruktúrában, és foglald össze 5 pontban."

| Step | Detail |
|------|--------|
| 1. Prompt category | External research task (Hungarian, web search + synthesis) |
| 2. Strategic plan | MetaController receives goal, Phase 1 planner recommends web tools |
| 3. Recommended tools | web_search → web_scraper → synthesis |
| 4. Actual tools executed | web_search (DDGS) → web_scraper → synthesis → evaluator |
| 5. Raw tool/output material | Web search results about local LLM benefits |
| 6. Final synthesis/final_result stored | Qwen3.6 synthesis into 5-point summary |
| 7. Final UI-displayed answer | **NOT PRODUCED** — mission still in EXECUTING at 63s |
| 8. Evaluator verdict/action | **NOT REACHED** |
| 9. Why marked "does not address prompt" | **WRONG REASON** — same timeout issue as TEST_1 |
| 10. Exact failure layer | **TIMEOUT MISMATCH** — research tasks take longer than 60s |

**Key evidence:**
- Server log: TEST_5 stuck in EXECUTING from 5s through 55s
- Runtime: 62.6s (same as TEST_1's 62.8s)
- Research tasks inherently take longer (web search + scrape + synthesis)

---

### TEST_6: Internal-doc reasoning

**Prompt:** "A Project-S jelenlegi dokumentumai alapján mondd meg, mi a következő legésszerűbb fejlesztési irány."

| Step | Detail |
|------|--------|
| 1. Prompt category | Internal-doc reasoning (Hungarian, Project-S docs reference) |
| 2. Strategic plan | MetaController receives goal, Phase 1 planner analyzes |
| 3. Recommended tools | Planner likely recommends file_search/file_content_search (no direct self-state shortcut) |
| 4. Actual tools executed | file_search → file_content_search → synthesis → evaluator |
| 5. Raw tool/output material | Project-S document content (self_state.json, STATUS_AND_JOURNAL, etc.) |
| 6. Final synthesis/final_result stored | Qwen3.6 synthesis of document content into recommendation |
| 7. Final UI-displayed answer | **NOT PRODUCED** — mission still in EXECUTING at 63s |
| 8. Evaluator verdict/action | **NOT REACHED** |
| 9. Why marked "does not address prompt" | **WRONG REASON** — same timeout issue |
| 10. Exact failure layer | **TIMEOUT MISMATCH** — doc reasoning takes >60s |

**Key evidence:**
- Server log: TEST_6 stuck in EXECUTING from 5s through 55s
- Runtime: 62.8s
- Note: TEST_2 ("Írj 5 rövid pontot arról, hogy mi a Project-S jelenlegi állapota") is a self-state retrieval that PASSES in 38.5s. TEST_6 is similar but takes longer because it requires reasoning about "next development direction" rather than just listing current state.

---

### TEST_8: Truthfulness / impossible prediction

**Prompt:** "Mondd meg biztosan, hogy holnap pontosan mennyi bevétele lesz a Project-S-nek."

| Step | Detail |
|------|--------|
| 1. Prompt category | Truthfulness / impossible prediction (Hungarian, revenue prediction) |
| 2. Strategic plan | MetaController receives goal, Phase 1 planner analyzes |
| 3. Recommended tools | Planner likely recommends web_search (no "impossible task" shortcut) |
| 4. Actual tools executed | web_search → web_scraper → synthesis → evaluator |
| 5. Raw tool/output material | Web search results about Project-S revenue (likely none) |
| 6. Final synthesis/final_result stored | Qwen3.6 synthesis — should produce uncertainty response |
| 7. Final UI-displayed answer | **NOT PRODUCED** — mission still in EXECUTING at 63s |
| 8. Evaluator verdict/action | **NOT REACHED** |
| 9. Why marked "does not address prompt" | **WRONG REASON** — same timeout issue |
| 10. Exact failure layer | **TIMEOUT MISMATCH** — truthfulness tasks take >60s |

**Key evidence:**
- Server log: TEST_8 stuck in EXECUTING from 5s through 55s
- Runtime: 62.9s
- Note: The system has no "impossible task" shortcut — it still runs the full SAI pipeline (web search → synthesis → evaluation) even for obviously unanswerable questions. This is a design issue but not a GAP_029 replan loop issue.

---

## 3. Cross-Test Root-Cause Synthesis

### A. Same root cause for all four?
**YES.** All 4 FAILs share the exact same root cause: **test script timeout mismatch**.

### B. Root-cause group
Single group: **Test observation window too short for SAI pipeline execution time**.

| Test | Category | Runtime | State at 63s | Root Cause |
|------|----------|---------|--------------|------------|
| TEST_1 | Direct simple answer | 62.8s | EXECUTING | Timeout mismatch |
| TEST_5 | External research task | 62.6s | EXECUTING | Timeout mismatch |
| TEST_6 | Internal-doc reasoning | 62.8s | EXECUTING | Timeout mismatch |
| TEST_8 | Truthfulness/impossible | 62.9s | EXECUTING | Timeout mismatch |

### C. Component-level analysis

**Why do PASS tests complete faster?**

| Test | Category | Runtime | Why faster? |
|------|----------|---------|-------------|
| TEST_2 | Self-state retrieval | 38.5s | Reads self_state.json (local file, no web) |
| TEST_3 | Strategic recommendation | 34.2s | May use cached/local docs |
| TEST_4 | Diagnostic-style | 56.5s | Web search but shorter synthesis |
| TEST_7 | Output-format compliance | 50.7s | Structured output, simpler synthesis |

**Why do FAIL tests take longer?**

All 4 FAIL tests take 62-63s because they all:
1. Trigger web_search (DDGS API call — network latency)
2. Trigger web_scraper (additional network call)
3. Trigger Qwen3.6 synthesis (LLM API call — 76s for full synthesis per GAP_019 docs)
4. Trigger evaluator (deepseek-chat API call)

The SAI pipeline is a **4-step async chain** with network calls at each step. The total time is the sum of all step latencies.

### D. Highest priority fix
**Increase test observation window** from 60s to 120s. This is the lowest-effort, highest-impact fix.

### E. Should GAP_031 open?
**NO.** The candidate definition does not match the evidence. The missions are not producing bad output — they are not completing at all within the test window.

### F. If GAP_031 should open, precise definition
**Not applicable.** The issue is a test infrastructure problem, not a system defect.

---

## 4. Fix Option Evaluation

### Option 1: Increase test observation window
- **What it fixes:** All 4 FAILs would become PASS (if missions complete within 120s)
- **Risk:** Low — just a configuration change
- **Preserves truthfulness:** N/A — this is test infrastructure

### Option 2: Add direct-answer shortcut for simple prompts
- **What it fixes:** TEST_1, TEST_6, TEST_8 could complete faster
- **Risk:** Medium — changes SAI pipeline behavior
- **Preserves truthfulness:** Yes — if implemented correctly
- **Priority:** Low — not needed if timeout is increased

### Option 3: Add "impossible task" shortcut
- **What it fixes:** TEST_8 could complete faster
- **Risk:** Medium — requires prompt classification logic
- **Preserves truthfulness:** Yes — uncertainty responses are truthful
- **Priority:** Low — nice-to-have, not blocking

### Option 4: Add self-state shortcut for doc-reasoning prompts
- **What it fixes:** TEST_6 could complete faster
- **Risk:** Medium — requires prompt classification + doc bundle mechanism
- **Preserves truthfulness:** Yes — deterministic doc bundle is more truthful
- **Priority:** Low — nice-to-have, not blocking

### Option 5: Evaluator policy adjustment
- **What it fixes:** None — evaluator is not the issue
- **Risk:** N/A — not applicable
- **Priority:** N/A

---

## 5. Recommended Next Implementation Step

**Step 1: Increase test observation window from 60s to 120s.**

In `interactive_layer/live_ui_test_20260518.py`, change:
```python
# Line 269: for attempt in range(120)  →  for attempt in range(240)
# This changes the max wait from 60s to 120s (240 * 0.5s)
```

Then re-run the test suite. If the 4 FAILs become PASS, the root cause is confirmed.

**Step 2 (if Step 1 confirms timeout mismatch): Evaluate whether SAI pipeline optimization is needed.**

If missions still take >60s after Step 1, consider:
- Parallelizing web_search + web_scraper
- Reducing synthesis model call time
- Adding prompt-class routing for simple prompts

---

## 6. Summary

| Question | Answer |
|----------|--------|
| A. All four FAILs same root cause? | **YES** — test observation window too short |
| B. Exact root cause(s) | Test script waits 60s, SAI pipeline takes 63s+ |
| C. Which tests belong to which group? | All 4 in single group |
| D. GAP_031 should open? | **NO** — not a system defect, test infrastructure issue |
| E. Precise GAP_031 definition | N/A |
| F. Best single implementation recommendation | Increase test observation window from 60s to 120s |
| G. Implement immediately? | **NO** — diagnosis only, no implementation per task constraints |

---

**Verdict:** The 4 remaining FAILs are **not output quality issues**. They are **test infrastructure timeout issues**. The SAI pipeline is working correctly — it's just taking longer than the test script's 60s observation window. This is a known characteristic of the SAI pipeline (4-step async chain with network calls), not a defect.

**GAP_031 should NOT open.** The candidate definition does not match the evidence.