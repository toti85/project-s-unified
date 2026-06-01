# GAP_029: Interactive Layer Replan Convergence Failure — Root Cause Analysis

**Date:** 2026-05-18  
**Status:** Open (Candidate)  
**Severity:** High  
**Component:** SAI Evaluator + MetaController  
**Related Tests:** TEST_1, TEST_4, TEST_5, TEST_6, TEST_8 (5/8 live UI tests)

---

## 1. Executive Verdict

**All 5 failures share the EXACT SAME root cause:** The strategic evaluator returns `action: replan` without any concrete corrective delta (no `specific_issues`, no `proposed_change`). The MetaController receives this replan signal but has no actionable guidance on what to change, so it re-runs essentially the same plan. This creates a non-converging loop where each iteration produces similar output, and after 5 iterations the mission fails with `[FAIL] MetaController failed: max_iters`.

**This is NOT five separate bugs. It is one systemic failure mode with five manifestations.**

**Primary responsible component:** The evaluator's judgment logic — specifically, its replan trigger is too aggressive and lacks a requirement for concrete corrective feedback.

**Secondary contributing factor:** The MetaController has no convergence detection and no bounded replan policy (max_replan_count separate from max_iters).

---

## 2. Per-Test Iteration-Level Analysis

### TEST_1: Direct simple answer
**Prompt:** "Írj 3 rövid mondatot arról, miért fontos a pontos dokumentáció."
**Mission ID:** abcf445c-2528-4018-bbbf-7003b0574e86
**Duration:** ~86 seconds (10:29:12 → 10:30:38)

#### State Timeline
```
10:29:12.091 — PLANNING (sai_planning event)
10:29:16.307 — EXECUTING (sai_executing event, 4215ms to transition)
10:30:38.798 — FAILED (82491ms in EXECUTING, replan_count=0 in event)
```

#### Iteration Analysis (from server logs)

**ITERÁCIÓ 1:**
- Phase 1: Strategic AI (Copilot) leading, GPT-4o Mini evaluator with 0.9 confidence
- Phase 2: Direct execution (Strategic AI optimized) — no tool orchestration needed
- Phase 3: Evaluator response: `action: replan` — reason: output quality insufficient
- No concrete corrective delta provided

**ITERÁCIÓ 2:**
- MetaController: "replanning..." — no specific corrective direction received
- Phase 1: Same strategic plan (no change in tools or approach)
- Phase 2: Same direct execution
- Evaluator: `action: replan` again — same pattern

**ITERÁCIÓ 3, 4, 5:**
- Same pattern repeats. Each iteration produces similar output.
- No convergence. No progress detected.
- Validation: "No validators configured" → confidence 0.0% → fail

**TERMINAL ITERÁCIÓ (5/5):**
- `[FAIL] MetaController failed: max_iters`
- **Verdict:** The FAIL is justified (the mission truly couldn't converge), but the root cause is the replan loop, not the task difficulty. A convergence detection mechanism would have stopped this earlier.

---

### TEST_4: Diagnostic-style operator request
**Prompt:** "Lassú a laptop. Mérd fel röviden, milyen irányokban lehetne gyorsítani."
**Mission ID:** 6c0e8e28-ca36-465b-89e4-3f30da77a682
**Duration:** ~118 seconds (10:31:44 → 10:33:42)

#### State Timeline
```
10:31:44.921 — PLANNING
10:31:44.987 — EXECUTING (66ms transition)
10:33:42.828 — FAILED (117841ms in EXECUTING, replan_count=0)
```

#### Iteration Analysis
- Same pattern as TEST_1. Evaluator triggers replan without concrete feedback.
- The open-ended diagnostic prompt is inherently harder to evaluate, making the evaluator MORE likely to request replan (uncertainty-driven).
- `replan_count: 0` in mission_failed event confirms the replan counter is NOT being tracked in the events table — this is a secondary bug.

---

### TEST_5: External research task
**Prompt:** "Keress röviden 3 aktuális okot arra, miért hasznos a lokális LLM egy saját AI-infrastruktúrában, és foglald össze 5 pontban."
**Mission ID:** 59c5d35f-6aab-4026-beb7-1952de223c78
**Duration:** ~146 seconds (10:32:50 → 10:34:16)

#### State Timeline
```
10:32:50.493 — PLANNING
10:32:50.563 — EXECUTING (70ms transition)
10:34:16.735 — FAILED (86172ms in EXECUTING, replan_count=0)
```

#### Iteration Analysis
- This is a research-capable prompt that should invoke web tools.
- The evaluator triggers replan before the web tool invocation can complete successfully.
- The replan loop prevents the system from ever reaching the "research" phase.

---

### TEST_6: Internal-doc reasoning
**Prompt:** "A Project-S jelenlegi dokumentumai alapján mondd meg, mi a következő legésszerűbb fejlesztési irány."
**Mission ID:** 2dcbcd89-2d6a-4167-b0ca-312ef61f833a
**Duration:** ~134 seconds (10:33:54 → 10:36:08)

#### State Timeline
```
10:33:54.369 — PLANNING
10:33:54.438 — EXECUTING (69ms transition)
10:36:08.839 — FAILED (134401ms in EXECUTING, replan_count=0)
```

#### Iteration Analysis
- **Critical comparison with TEST_2:** TEST_2 uses the EXACT same prompt category (internal-doc reasoning) and PASSES because it triggers GAP_026 forced orchestration.
- TEST_6 does NOT trigger GAP_026 (the prompt text is different enough that the GAP_026 heuristic doesn't match).
- This proves the issue is NOT with the prompt category itself, but with the absence of GAP_026 protection.

---

### TEST_8: Truthfulness / impossible prediction
**Prompt:** "Mondd meg biztosan, hogy holnap pontosan mennyi bevétele lesz a Project-S-nek."
**Mission ID:** 5272befc-b854-40a6-83d1-639bf8a5a1b9
**Duration:** ~144 seconds (10:35:33 → 10:37:57)

#### State Timeline
```
10:35:33.681 — PLANNING
10:35:33.745 — EXECUTING (61ms transition)
10:37:57.481 — FAILED (143754ms in EXECUTING, replan_count=0)
```

#### Iteration Analysis (from server logs — most detailed)

**ITERÁCIÓ 1:**
- GAP_026: forcing orchestration for self-state prompt
- file_reader reads 3 files: self_state.json, PROJECT_S_OVERVIEW.md, PROJECT_S_STATUS_AND_JOURNAL.md
- GAP_026: synthesis complete — 724 chars
- Evaluator: `action: replan` — reason: output doesn't meet certainty expectation

**ITERÁCIÓ 2:**
- Same GAP_026 path, same file_reader, same synthesis
- Evaluator: `action: replan` — same reason

**ITERÁCIÓ 3:**
- Same pattern. Evaluator logged: `evaluation.replan_needed`
- `core.infrastructure.event_bus` Publishing event: evaluation.replan_needed
- No subscribers for this event type (dead event)

**ITERÁCIÓ 4:**
- Same pattern. Validation: "No validators configured" → confidence 0.0%
- MetaController: "Validation failed (failed), replanning..."

**ITERÁCIÓ 5:**
- Same pattern. Max iterations (5) reached without success.
- SSE stream cancelled for mission.
- **Key insight:** Even with GAP_026 forced orchestration (which makes the tool selection deterministic), the evaluator STILL triggers replan. This proves the problem is NOT in tool selection or orchestration — it is purely in the evaluator's judgment logic.

---

## 3. Cross-Test Synthesis

### A. Mind az 5 failure ugyanaz a root cause?

**IGEN.** The evidence is conclusive:

1. **Identical error message:** All 5 show `[FAIL] MetaController failed: max_iters`
2. **Identical replan_count:** All 5 show `replan_count: 0` in mission_failed events (secondary bug: counter not tracked)
3. **Identical state pattern:** QUEUED → PLANNING → EXECUTING → FAILED (no intermediate COMPLETE or partial success)
4. **Identical evaluator behavior:** Server logs show repeated `evaluator - INFO - Handled evaluation result with action: replan` for all 5 tests
5. **Identical duration pattern:** All 5 take ~85-145 seconds in EXECUTING state (consistent with 5 iterations × ~15-30s each)

### B. Az evaluator viselkedése

**Mind a három:**

1. **Túl szigorú:** The evaluator rejects outputs that are substantively correct but don't meet an overly strict criterion (e.g., TEST_8's "certainty" requirement when the task is inherently unpredictable).

2. **Túl bizonytalan:** When the evaluator is uncertain about output quality, it defaults to `replan` rather than `continue` or `partial`. There is no confidence threshold for the replan decision.

3. **Strukturálisan rosszul illeszkedik:** The evaluator uses a single policy for ALL prompt types. A simple-answer prompt (TEST_1) should be evaluated differently from a research prompt (TEST_5) or a truthfulness test (TEST_8).

### C. A MetaController FAILURE oka

**Ezek kombinációja:**

1. ✅ **replan-t kap, de nincs konkrét korrektív delta** — The evaluator's replan action lacks `specific_issues` and `proposed_change` fields.
2. ✅ **Ugyanazt a plant futtatja újra** — Without a corrective delta, the strategic planner re-runs the same plan.
3. ✅ **Nincs convergence detection** — The MetaController has no mechanism to detect when iterations are producing similar output.
4. ✅ **Nincs bounded replan policy** — `max_iters=5` serves as both the total iteration limit AND the replan limit. There's no separate `max_replan_count`.
5. ✅ **Validation always fails** — "No validators configured" → confidence 0.0% → validation always fails → always triggers replan.

### D. Releváns-e a deterministic=True / no validators beállítás?

**Részben.** The "No validators configured" warning means validation always returns confidence 0.0%, which always triggers replan. This is a contributing factor but NOT the root cause. Even with validators configured, the evaluator's replan trigger would still be too aggressive because it lacks concrete corrective feedback.

### E. Ki a VALÓDI primary culprit?

**Evaluator prompt (a "judge instructions" túl szigorúak) + MetaController replan policy.**

The evaluator's judgment logic is the primary culprit because:
1. It triggers replan without concrete corrective feedback
2. It uses a single policy for all prompt types
3. It has no confidence threshold for the replan decision

The MetaController is a secondary culprit because:
1. It has no convergence detection
2. It has no bounded replan policy
3. It blindly follows every replan signal

---

## 4. Fix Candidate Evaluation

### 1. REPLAN must include concrete corrective delta
**Benefit:** Forces the evaluator to provide `specific_issues` or `proposed_change` before returning `action: replan`. If no concrete issue is found, downgrade to `continue` or `fail`.
**Risk:** May cause some valid replans to be suppressed if the evaluator can't articulate the issue precisely.
**Solves all 5 failures?** Igen — directly addresses the root cause.
**Preserves truthfulness?** Igen — if the evaluator can't find a concrete issue, it should `continue` (accept the output) or `fail` (mark as insufficient).

### 2. MetaController convergence detection
**Benefit:** Detects when two consecutive iterations produce very similar output (Levenshtein similarity > 90%). Stops early with a `convergence_failure` terminal state.
**Risk:** May stop too early if the output is genuinely improving slowly.
**Solves all 5 failures?** Részben — would have stopped the loops earlier but wouldn't prevent the replan from being triggered.
**Preserves truthfulness?** Igen — convergence_failure is a truthful terminal state.

### 3. Evaluator confidence threshold
**Benefit:** Replan only on high-confidence severe defect. Low-confidence or minor issues → `continue` or `partial`.
**Risk:** May let genuinely defective outputs through if the confidence threshold is too low.
**Solves all 5 failures?** Részben — addresses the "túl bizonytalan" aspect but not the "nincs corrective delta" aspect.
**Preserves truthfulness?** Igen — low-confidence outputs are still accepted.

### 4. Light path for simple prompts
**Benefit:** Direct-answer prompts (TEST_1) bypass the full MetaController loop, using simple one-shot synthesis.
**Risk:** May not work for prompts that genuinely need multiple iterations.
**Solves all 5 failures?** Nem — only helps TEST_1 and possibly TEST_4.
**Preserves truthfulness?** Igen — one-shot synthesis is still evaluated.

### 5. Prompt class-specific evaluation policy
**Benefit:** Separate evaluation rules for different prompt types (research vs reasoning vs simple-answer vs prediction).
**Risk:** Complex to implement and maintain. May not address the root cause.
**Solves all 5 failures?** Részben — would help but is a band-aid, not a fix.
**Preserves truthfulness?** Igen — class-specific rules can be more accurate.

### 6. max_replan_count separate from max_iters
**Benefit:** Pl. max_iters=5 marad, de max_replan=2. Más fail mode-ok (improve_tool, continue) tovább iterálhatnak.
**Risk:** May reduce total iteration budget for complex tasks.
**Solves all 5 failures?** Részben — would stop the replan loops earlier but wouldn't prevent the replan from being triggered.
**Preserves truthfulness?** Igen — max_replan exceeded is a truthful terminal state.

---

## 5. Recommended Fix

**Best single fix: Option 1 — REPLAN must include concrete corrective delta**

**Rationale:** This directly addresses the root cause identified in the analysis. The evaluator's replan trigger is the primary culprit, and requiring concrete corrective feedback is the most targeted fix.

**Implementation approach:**
1. Modify the evaluator's judgment logic to require `specific_issues` or `proposed_change` in the replan response.
2. If the evaluator returns `action: replan` without these fields, the MetaController should downgrade to `continue` (accept the output) or `fail` (mark as insufficient).
3. Add a validation step in the MetaController that checks for corrective delta before entering a replan iteration.

**Why not other options as the primary fix:**
- Option 2 (convergence detection) is a good secondary defense but doesn't prevent the replan from being triggered.
- Option 3 (confidence threshold) is related but doesn't address the "no corrective delta" issue.
- Options 4-6 are useful improvements but are band-aids, not root-cause fixes.

**Recommended as secondary defense:** Option 2 (convergence detection) — this provides a safety net in case the evaluator still triggers replan without corrective delta for some reason.

---

## 6. GAP_029 Hivatalos Definíció

**GAP_029: Interactive Layer Evaluator-Driven Replan Convergence Failure**

**Leírás:**
A SAI evaluator `action: replan` döntései nem tartalmaznak konkrét korrektív visszajelzést (`specific_issues`, `proposed_change` mezők hiányoznak). A MetaController minden replan jelzést végrehajt, de mivel nincs konkrét irány, ugyanazt a tervet futtatja újra. Ez nem-konvergáló ciklust eredményez, ahol minden iteráció hasonló kimenetet produkál. 5 iteráció után a mission `[FAIL] MetaController failed: max_iters` hibával végződik.

**Evidence:**
- 5/8 live UI test failure share identical error pattern: `[FAIL] MetaController failed: max_iters`
- All 5 show `replan_count: 0` in mission_failed events (counter not tracked)
- Server logs show repeated `evaluator - INFO - Handled evaluation result with action: replan` for all 5
- TEST_8 passes GAP_026 forced orchestration but STILL fails — proving the issue is in evaluator judgment, not tool orchestration
- All 5 take ~85-145 seconds in EXECUTING state (consistent with 5 iterations × ~15-30s each)

**Legkisebb robust fix:**
Option 1: Require concrete corrective delta in evaluator's replan action. If `action: replan` is returned without `specific_issues` or `proposed_change`, downgrade to `continue` or `fail`.

---

## 7. TEST_7 Output-Format Compliance: GAP_029 része vagy különálló?

**TEST_7 (output-format compliance) — PARTIAL, nem FAIL.**

A TEST_7 nem a replan loop miatt nem teljes PASS, hanem mert a LLM nem tudta pontosan betartani a 4 soros formátumot. A mission ELÉRT COMPLETE state-et, tehát a replan loop NEM érinti ezt a tesztet.

**Következtetés:** TEST_7 PARTIAL állapota NEM GAP_029 része. Ez egy különálló LLM limitation (strict output format compliance difficulty).

**Döntés:** GAP_030 NE nyíljon most. Ha a GAP_029 fix (Option 1) után a TEST_7 továbbra is PARTIAL, akkor külön GAP_030-ként kezelhető. De valószínű, hogy a GAP_029 fix nem befolyásolja a TEST_7-et, mert az egy LLM formátum-követési limitation, nem evaluator replan probléma.

---

## 8. Válasz — Összegzés

| Question | Answer |
|----------|--------|
| A. Mind az 5 failure ugyanaz a root cause? | **Igen** — evaluator replan without corrective delta |
| B. Exact root cause (1-2 mondatban) | The strategic evaluator returns `action: replan` without concrete corrective feedback (`specific_issues`, `proposed_change`). The MetaController blindly follows every replan signal, re-running the same plan, creating a non-converging loop. |
| C. Primary responsible component | **SAI Evaluator's judgment logic** — specifically the replan trigger and lack of corrective delta requirement |
| D. GAP_029 megnyíljon? | **Igen** — hivatalosan megnyitandó, fenti definícióval |
| E. Best fix option, EGY ajánlás | **Option 1: REPLAN must include concrete corrective delta** — evaluator csak akkor adhat replan-t, ha `specific_issues` vagy `proposed_change` is van. Egyébként downgrade `continue`-ra vagy `fail`-re. |
| F. TEST_7 PARTIAL — GAP_029 része vagy különálló? | **Különálló.** A TEST_7 elérte a COMPLETE state-et, tehát a replan loop nem érinti. Ez egy LLM formátum-követési limitation. |
| G. Implementálás indítható azonnal? | **Nem.** Először a fix implementálandó és tesztelendő egy izolált környezetben, majd újra futtatható a live UI test campaign. |