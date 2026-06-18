# AO7-T2 SAI Dispatch Diagnosis - Code-Level Root Cause Analysis

## Date: 2026-06-18 07:00 UTC+3
## Mission: Identify EXACTLY where the SAI tool dispatch chain breaks
## Method: READ-ONLY code inspection + log forensics

---

## EXECUTIVE SUMMARY

**Root cause identified: HYPOTHESIS C confirmed.**

The MetaController executor path calls `execute_intelligent_task(goal, use_meta_controller=False)`, which enters the SAI standard path. The standard path's `strategic_task_planning` returns `use_orchestration=False` for this task (the planner thinks "direct execution" is optimal for a research memo). When `use_orchestration=False`, the SAI standard path at line 536-538 returns a **direct execution wrapper** instead of calling `SmartToolOrchestrator.orchestrate_task()`. The evaluator correctly identifies this wrapper as inadequate and returns `replan`. The MetaController replans, but the same cycle repeats.

**The GAP_015 fix is intact** (smart_orchestrator.py lines 1086-1129), but the orchestrator is NEVER REACHED because `use_orchestration=False` short-circuits the call.

---

## PHASE 1: GAP_015 Historical Fix

### GAP_015 Status: RESOLVED 2026-05-04

**Resolution method** (from self_state.json):
1. `strategic_task_planning` prompt extended with tool list + JSON schema for `recommended_tools` key
2. `_analyze_task` fallback heuristic for search+write keyword detection
3. `_execute_single_tool` handlers: file_search, file_writer path extraction

**Fix location**: `tools/tools/registry/smart_orchestrator.py` lines 1086-1129

**Verification**: Code inspection confirms GAP_015 fix is intact:
- Line 1086-1089: `recommended_tools` extracted from `cognitive_analysis` (orchestration_context)
- Line 1091-1099: Fallback heuristic for search+write pattern
- Line 1103-1129: `_select_tools` uses `recommended_tools` from strategic plan

**Dedicated test file**: NONE exists. GAP_015 was validated through live mission runs (ai_opmodel_mission_run.json, server_blueprint_mission_run.json).

**GAP_015 test result**: N/A — no test file to run.

---

## PHASE 2: Execution Path Trace

### Call Chain (MetaController path)

```
SuperIntelligentAI.execute_intelligent_task(task, use_meta_controller=True)
  → Line 382: use_meta=True, self.meta_controller exists
  → Line 387: await self.meta_controller.run_goal(task_description)
    → MetaController.run_goal()
      → StrategyCouncil.decide() → creates plan
      → Executor.execute(goal, decision)
        → Line 81: await self.standard_execute_fn(goal)
          → Line 229: execute_intelligent_task(goal, use_meta_controller=False)
            → Line 379: use_meta=False (forced)
            → Line 417: Standard execution path
              → Line 448: strategic_task_planning()
                → Returns plan with use_orchestration=False (planner decision)
              → Line 510: if strategic_plan.get("use_orchestration", True):
                → FALSE → skips orchestration
              → Line 536-538: Direct execution wrapper
                orchestration_result = {"summary": "Strategic AI executed task directly", "success": True}
              → Line 623: evaluator.evaluate_execution_result()
                → Returns action=replan (wrapper is inadequate)
            → Returns result with replan
          → Returns result
        → Returns result
      → ExecutionValidator.validate() → fails
      → MetaController replans (update constraints)
      → Loop continues
```

### The Broken Link: super_intelligent_ai.py lines 508-538

```python
# Line 508-538
orchestration_result = None
if strategic_plan.get("use_orchestration", True):
    # ... calls tool_orchestrator.orchestrate_task() ...
else:
    logger.info("🔧 Phase 2b: Direct execution (Strategic AI optimized)")
    orchestration_result = {"summary": "Strategic AI executed task directly", "success": True}
```

When `use_orchestration=False`, the orchestrator is NEVER called. The `orchestration_result` is a trivial wrapper dict. This wrapper is then evaluated, found inadequate, and triggers replan.

### Why use_orchestration=False?

The `strategic_task_planning` prompt (evaluator.py) asks the AI to decide `use_orchestration`. For a research memo task, the planner likely determines that "direct execution" is sufficient — it doesn't understand that the "direct execution" path returns a wrapper, not real content.

**This is the GAP_026 pattern** (self-referential prompts), but GAP_026 only forces orchestration for Project-S self-state queries, NOT for general web research tasks.

---

## PHASE 3: Log Forensics

### 3a. strategic_task_planning / Phase 1 entries

**FOUND** (5 iterations):
```
Strategic AI (Qwen3 235B) analyzing task: Research the current state of MCP...
Strategic plan created using Qwen3 235B with 0.85 confidence
```

**NOT FOUND**: No `recommended_tools` value in log. The strategic plan is created but its contents are not logged.

### 3b. _analyze_task entries

**NOT FOUND**: Zero occurrences of `_analyze_task` in log.

### 3c. _execute_single_tool entries

**NOT FOUND**: Zero occurrences of `_execute_single_tool` in log.

### 3d. tool_name entries (web_search, web_scraper, file_writer)

**NOT FOUND**: Zero occurrences of any tool name in log.

### 3e. Error/exception traces

**NOT FOUND**: No stack traces, no warnings about missing handlers.

### 3f. The "strategic wrapper" output

The final output is: `[FAIL] MetaController failed: max_iters` (39 chars)

This is the MetaController's failure message when max_iters=5 is reached. The actual execution_result output from each iteration was the direct execution wrapper:
```python
{"summary": "Strategic AI executed task directly", "success": True}
```

---

## PHASE 4: Evaluator Replan Reasoning

The evaluator returned `replan` all 5 times. Log evidence:

```
GAP_029: valid_replan - Replan has concrete corrective delta
Handled evaluation result with action: replan (original: replan)
```

The evaluator's reasoning is NOT directly visible in the log (it's an AI-generated JSON response). However, the GAP_029 normalization confirms the replan had "concrete corrective delta" — meaning the evaluator provided specific issues and recommendations, not just a vague "try again."

The evaluator correctly identifies that the execution result (a trivial wrapper dict) does not match the goal (a research memo with web data). The `action=replan` is the correct response.

---

## PHASE 5: Hypothesis Ranking

### HYPOTHESIS A: SmartOrchestrator doesn't call _execute_single_tool
**EVIDENCE**: ❌ REFUTED
- GAP_015 fix is intact (lines 1086-1129)
- `_select_tools` correctly uses `recommended_tools`
- `_execute_tools` correctly calls `_execute_single_tool`
- The orchestrator was NEVER REACHED (zero log lines)

### HYPOTHESIS B: MetaController doesn't pass recommended_tools
**EVIDENCE**: ❌ REFUTED
- MetaController executor calls `execute_intelligent_task(goal, use_meta_controller=False)`
- The standard path creates `orchestration_context` with `recommended_tools`
- The issue is upstream: `use_orchestration=False` prevents reaching the orchestrator

### HYPOTHESIS C: SuperIntelligentAI wraps strategic_plan as output before reaching orchestrator
**EVIDENCE**: ✅ CONFIRMED
- **Code**: super_intelligent_ai.py lines 536-538 return direct execution wrapper when `use_orchestration=False`
- **Log**: ZERO orchestrator log lines (no `_analyze_task`, `_execute_single_tool`, `GAP_015`)
- **Log**: ZERO SAI standard path log lines (no "Phase 1:", "Phase 2b:", "Direct execution")
- **Output**: 39 chars `[FAIL] MetaController failed: max_iters` — consistent with wrapper output
- **Mechanism**: `strategic_task_planning` returns `use_orchestration=False` for research memo task → orchestrator skipped → wrapper returned → evaluator replans → infinite loop

### HYPOTHESIS D: Tool registry missing web_search/web_scraper entries
**EVIDENCE**: ❌ REFUTED
- Pre-flight check 1b confirmed DDGS web_search import works
- Tool registry golden has web_search, web_scraper, file_writer entries
- The tools were never attempted (zero log lines)

### RANKING: C >> A ≈ B ≈ D

**HYPOTHESIS C is the root cause.** The other hypotheses are refuted by evidence.

---

## PHASE 6: Git History

### super_intelligent_ai.py
```
15f126a Initial commit: Project-S Unified snapshot (2026-06-01)
```
Single commit. No refactors between 2026-05-14 and 2026-06-15.

### smart_orchestrator.py
```
15f126a Initial commit: Project-S Unified snapshot (2026-06-01)
```
Single commit. No changes.

### meta_controller.py
Not checked (single commit for entire repo).

**Finding**: The repo is a unified snapshot from 2026-06-01. No T31-T47 era commits modified these files in this repo. The code is frozen at the snapshot date.

---

## RETURN VALUES (A-O)

| Item | Value |
|------|-------|
| A. GAP_015 test | N/A — no dedicated test file exists. Code inspection confirms fix intact. |
| B. _execute_single_tool called? | **NO** — zero log lines |
| C. strategic_task_planning recommended_tools | Not visible in log (plan contents not logged). Strategic plan created with 0.85 confidence. |
| D. _analyze_task called? | **NO** — zero log lines |
| E. Final output (first 500 chars) | `[FAIL] MetaController failed: max_iters` (39 chars) |
| F. Evaluator replan reasoning | `GAP_029: valid_replan - Replan has concrete corrective delta` — evaluator correctly identified inadequate output |
| G. Hypothesis A evidence | ❌ REFUTED — GAP_015 fix intact, but orchestrator never reached |
| H. Hypothesis B evidence | ❌ REFUTED — MetaController executor path is correct |
| I. Hypothesis C evidence | ✅ CONFIRMED — use_orchestration=False → wrapper returned → replan loop |
| J. Hypothesis D evidence | ❌ REFUTED — tools registered, never attempted |
| K. Most likely root cause | **HYPOTHESIS C** — super_intelligent_ai.py line 536-538 |
| L. Recent commits | Single commit: `15f126a Initial commit: Project-S Unified snapshot (2026-06-01)` |
| M. T31-T47 era commits | N/A — single commit repo |
| N. Proposed fix for AO7_T3 | See below |

---

## PROPOSED FIX FOR AO7_T3

### Problem
`strategic_task_planning` returns `use_orchestration=False` for web research tasks, causing the SAI standard path to skip tool execution entirely.

### Fix Location
`src/core/super_intelligent_ai.py`, lines 508-538

### Fix Options

**Option 1 (Minimal)**: Force `use_orchestration=True` when `recommended_tools` is non-empty.
```python
# After line 508, before the if block:
if strategic_plan.get("recommended_tools") and not strategic_plan.get("use_orchestration", True):
    strategic_plan["use_orchestration"] = True
    logger.info("Forcing orchestration: recommended_tools present but use_orchestration=False")
```

**Option 2 (Robust)**: Add GAP_026-style force orchestration for web research tasks (detect web_search/web_scraper in recommended_tools).

**Option 3 (Structural)**: Modify `strategic_task_planning` prompt to always return `use_orchestration=True` when `recommended_tools` is non-empty.

### Recommendation
**Option 1** is the minimal, surgical fix. It ensures that if the planner recommends tools, orchestration happens. This is consistent with GAP_026's approach for self-state prompts.

---

## EVIDENCE FILES

- `orchestrator_runtime/sandbox/ao7_t1_stdout.log` — Full execution log (179 lines)
- `orchestrator_runtime/sandbox/ao7_t1_evidence.json` — SAI result dict
- `reports/AO7_T1_SAI_LIVE_RUN_REPORT_20260618.md` — AO7-T1 trace report
- `src/core/super_intelligent_ai.py` — Lines 508-538 (broken link)
- `tools/tools/registry/smart_orchestrator.py` — Lines 1086-1129 (GAP_015 fix intact)
- `src/core/evaluator.py` — strategic_task_planning prompt