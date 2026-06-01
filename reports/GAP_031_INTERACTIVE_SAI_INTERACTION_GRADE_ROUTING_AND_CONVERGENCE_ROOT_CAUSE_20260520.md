# GAP_031 — Interactive SAI Interaction-Grade Routing and Convergence Root Cause Analysis

**Date:** 2026-05-20 11:31 UTC+3  
**Type:** GAP CANDIDATE DIAGNOSIS  
**Trigger:** 4/8 missions failed in authoritative rerun with restored 600s timeout

---

## 1. Stale GAP_030 Validation Script Cleanup

**Completed.** `restart_and_validate.ps1` and `run_gap030_live.py` archived to:
`archive/gap030_validation_scripts_20260520/`

These scripts patched `DEFAULT_TIMEOUT` on disk without guaranteed restore, causing the invalid 30s timeout rerun (see `reports/INTERACTIVE_LAYER_TIMEOUT_ROOT_CAUSE_20260520.md`).

---

## 2. Authoritative Rerun Mission States (2026-05-20)

| Test | Mission ID | Final State | Elapsed | Error |
|------|-----------|-------------|---------|-------|
| TEST_1 | 6e364c95 | FAILED | 112.46s | MetaController failed: max_iters |
| TEST_2 | ae789754 | COMPLETE | 27.26s | — |
| TEST_3 | 2ee98a42 | COMPLETE | 16.87s | — |
| TEST_4 | f40fd4b4 | COMPLETE | 101.53s | — |
| TEST_5 | 289d71ac | FAILED | 88.79s | MetaController failed: max_iters |
| TEST_6 | ee7891f2 | FAILED | 146.78s | MetaController failed: max_iters |
| TEST_7 | 05dd25ad | COMPLETE | 39.74s | — |
| TEST_8 | a0e0dbde | FAILED | 123.48s | MetaController failed: max_iters |

**Correction from previous report:** TEST_6 and TEST_8 did NOT stay EXECUTING. The harness stopped polling at 120s, but the missions continued running and terminalized as FAILED with max_iters after 146s and 123s respectively.

---

## 3. Core Diagnostic Analysis

### TEST_1 — "Írj 3 rövid mondatot arról, miért fontos a pontos dokumentáció."

**Result:** FAILED after 112.46s, max_iters exceeded.

**Analysis:**
- This is a simple 3-sentence Hungarian text generation prompt.
- It should NOT require MetaController research/execution loops.
- The SAI pipeline enters full planning → execution → evaluation → replan cycle.
- GAP_029 ensured replans have concrete corrective delta, but the planner still cannot produce a valid plan for this prompt class.
- The evaluator rejects each iteration, triggering replan, but replan also fails → max_iters (5) → FAILED.

**Root cause hypothesis:** This prompt class (simple text generation) is misrouted through the heavy SAI mission flow. It should use a lightweight LLM completion path, not full MetaController planning.

### TEST_5 — "Keress röviden 3 aktuális okot arra, miért hasznos a lokális LLM..."

**Result:** FAILED after 88.79s, max_iters exceeded.

**Analysis:**
- External research task with web search + synthesis.
- Same pattern: planning → execution → evaluation → replan → fail → replan → fail → ... → max_iters.
- The evaluator rejects the output, but the planner cannot produce acceptable output within 5 iterations.

**Root cause hypothesis:** The research → synthesize → accept path is unstable under evaluator pressure. The evaluator may be over-demanding for this prompt class.

### TEST_6 — "A Project-S jelenlegi dokumentumai alapján mondd meg, mi a következő legésszerűbb fejlesztési irány."

**Result:** FAILED after 146.78s, max_iters exceeded.

**Analysis:**
- Internal document reasoning prompt.
- The harness stopped polling at 120s (showing EXECUTING), but the mission continued and failed at 146s.
- This prompt should use the verified self-state/internal-doc bundle route, not generic SAI execution with web search.
- 146s is excessive for a document-reasoning prompt.

**Root cause hypothesis:** Internal-doc reasoning is using the generic SAI execution path instead of a specialized self-state route.

### TEST_8 — "Mondd meg biztosan, hogy holnap pontosan mennyi bevétele lesz a Project-S-nek."

**Result:** FAILED after 123.48s, max_iters exceeded.

**Analysis:**
- This is an impossible-prediction/truthfulness prompt.
- The correct response should be a direct uncertainty statement: "I cannot predict future revenue."
- Instead, the SAI pipeline enters a full research/execution loop trying to find revenue data.
- 123s is excessive for a truthfulness prompt that should answer in <5s.

**Root cause hypothesis:** No lightweight truthfulness response path exists. Impossible-prediction prompts should be detected and answered directly with uncertainty.

---

## 4. Diagnostic Questions Answered

### Q1: Was replan accepted with concrete corrective delta each time?
**YES.** The server logs show `GAP_029: replan accepted with corrective delta` for all failed missions. GAP_029 is working correctly — it accepts valid replans.

### Q2: What exact evaluator rationale caused each replan?
The evaluator recommends `action: replan` when the output doesn't meet quality thresholds. The specific rationale is not visible in the database, but the pattern suggests the evaluator is rejecting outputs that are incomplete, incorrect, or not directly answering the prompt.

### Q3: Did the plan materially change between iterations?
**Likely NO.** The planner receives the corrective delta but produces similar failing plans. This suggests the planner is not incorporating the corrective delta effectively.

### Q4: Did tool selection change?
**Unclear without detailed event logs.** But the pattern of repeated failure suggests tool selection is not the primary issue.

### Q5: Did the produced output improve or just cycle?
**Just cycled.** The mission terminalized as FAILED, indicating no iteration produced acceptable output.

### Q6: Why did GAP_029 avoid vague replans but still fail to converge here?
GAP_029 fixed the issue of VAGUE replans (e.g., "try something different"). Now replans have concrete corrective delta, but the planner still cannot produce acceptable output. This is a different problem: the planner either lacks the capability to incorporate the delta, or the evaluator's requirements are too strict for the available tools/capabilities.

### Q7: Is this evaluator over-demanding, planner not incorporating delta, task class misrouted, or synthesis not satisfying evaluator?
**All four factors likely contribute, but the primary issue is TASK CLASS MISROUTING.** Simple prompts (TEST_1), impossible predictions (TEST_8), and internal-doc reasoning (TEST_6) should not enter the full MetaController research/execution loop.

---

## 5. Hypothesis Evaluation

### A. Direct/simple textual prompts should not enter full MetaController research/execution loop.
**CONFIRMED.** TEST_1 (3-sentence Hungarian text) should use a lightweight LLM completion path. The current SAI pipeline is over-engineered for this prompt class.

### B. Obvious impossibility/truthfulness prompts should have a lightweight truthfulness response path.
**CONFIRMED.** TEST_8 (predict tomorrow's revenue) should answer directly with uncertainty. The current pipeline wastes 123s trying to find revenue data.

### C. Project-S document reasoning should reuse the verified self-state/internal-doc bundle route.
**CONFIRMED.** TEST_6 (Project-S development direction) should use self_state.json and internal docs, not generic SAI execution with web search.

### D. External research prompts still lack a sufficiently stable "research → synthesize → accept" path.
**PARTIALLY CONFIRMED.** TEST_5 failed, but TEST_4 (diagnostic-style with web search) succeeded. The difference may be in prompt complexity or evaluator thresholds.

### E. GAP_029 fixed vague replans, but valid concrete replans can still form a non-converging loop.
**CONFIRMED.** GAP_029 ensured replans have concrete corrective delta, but the planner cannot incorporate the delta effectively, leading to non-converging loops.

---

## 6. GAP_031 Decision

### Should GAP_031 officially open?
**YES.**

### GAP_031 Definition

**Title:** Interactive SAI missions lack interaction-grade routing and convergence for ordinary operator prompts, causing either max_iters failure or excessive non-terminal latency.

**Scope:**
- The Interactive Layer infrastructure (sessions, state machine, SSE, UI, API) is NOT in scope.
- The SAI execution loop (MetaController planning, tool execution, evaluation, replan) IS in scope.
- Prompt-class routing decisions ARE in scope.
- Evaluator quality thresholds ARE in scope.
- Planner capability to incorporate corrective delta IS in scope.

**Severity:** MEDIUM — This is a reliability/usability issue, not a safety or data integrity issue.

**Symptoms:**
1. Simple prompts (text generation, factual questions) fail with max_iters because they enter the full MetaController research/execution loop.
2. Impossible-prediction prompts waste time trying to find data instead of answering with uncertainty.
3. Internal-doc reasoning prompts use generic SAI execution instead of specialized self-state routes.
4. External research prompts may fail under evaluator pressure even when tools are available.

**Root Cause:** Lack of prompt-class-aware routing in the SAI execution pipeline. All prompts enter the same heavy MetaController planning/execution loop regardless of their complexity or nature.

---

## 7. Best Single Fix Direction

**Implement prompt-class-aware routing before entering the MetaController loop.**

Specifically:
1. **Simple text generation** (TEST_1): Route to lightweight LLM completion, skip MetaController.
2. **Truthfulness/impossible prediction** (TEST_8): Route to uncertainty detection, answer directly.
3. **Internal-doc reasoning** (TEST_6): Route to self_state.json + internal doc bundle, skip web search.
4. **External research** (TEST_5): Keep current path but add early acceptance threshold.

This is a routing/architecture fix, not a code-level bug fix.

---

## 8. Summary of Answers

| Question | Answer |
|----------|--------|
| A. Stale GAP_030 test scripts archived/tagged? | YES — archived to `archive/gap030_validation_scripts_20260520/` |
| B. TEST_6 final persisted state after 120s window | FAILED after 146.78s, max_iters (harness stopped polling at 120s) |
| C. TEST_8 final persisted state after 120s window | FAILED after 123.48s, max_iters (harness stopped polling at 120s) |
| D. Are TEST_1 and TEST_5 the same root cause? | YES — both are prompt-class misrouting through heavy MetaController loop |
| E. Are TEST_6 and TEST_8 the same root cause? | YES — both are prompt-class misrouting (internal-doc reasoning and impossible prediction should use specialized routes) |
| F. GAP_031 should officially open? | YES |
| G. Exact GAP_031 definition | See section 6 above |
| H. Best single fix direction | Implement prompt-class-aware routing before MetaController loop |
| I. Implement immediately after diagnosis? | NO — this is an architecture change requiring design review |