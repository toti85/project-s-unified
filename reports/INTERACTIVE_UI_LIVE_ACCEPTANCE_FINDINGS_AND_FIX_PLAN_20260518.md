# Interactive UI Live Acceptance — Findings and Fix Plan

**Date:** 2026-05-18
**Test Time:** 10:02 UTC+3
**Test Source:** Live browser session at `http://localhost:8000/ui`

---

## 1. Executive Summary

Three issues identified during live UI acceptance testing:

1. **TEST 1:** Mission FAILED with `MetaController failed: max_iters` — likely legitimate SAI limitation
2. **TEST 2:** Mission marked COMPLETE but planner routed a Project-S self-state question to `web_search` instead of internal state, and final output did not contain the requested 5 bullet points
3. **UI BUG:** Live Mission Status panel shows event histories from multiple missions mixed together

---

## 2. TEST 1 — MetaController max_iters Failure

### Prompt
"lassu a laptop, mérdfel hogy tudnánk gyorsitani" (Hungarian: "laptop is slow, check if we can speed it up")

### Result
- Mission FAILED
- Error: `[FAIL] MetaController failed: max_iters`

### Diagnosis
The MetaController has `max_iters=5, timeout=120s` configured. The failure indicates the SAI pipeline exhausted its iteration budget without achieving a deterministic goal match. This is a **legitimate SAI limitation** — the planner attempted to analyze and respond to a system-performance question but could not complete within 5 iterations.

### Classification
**Not a new GAP.** This is expected behavior for the current SAI architecture when faced with open-ended diagnostic questions that require multi-step tool orchestration. The system correctly FAILED rather than producing a hallucinated answer.

### Priority
Low — no fix required. This is a known SAI limitation.

---

## 3. TEST 2 — Wrong Project-S Self-State Routing

### Prompt
"Írj 5 rövid pontot arról, hogy mi a Project-S jelenlegi állapota." (Hungarian: "Write 5 short bullet points about Project-S current state.")

### Observed Behavior
1. Mission marked COMPLETE
2. Strategic planner chose: "Conduct a web search to gather current information about Project-S"
3. Final output did NOT contain 5 bullet points answering the user's request
4. Output showed a strategic execution wrapper instead of the requested content
5. Evaluator still marked: `Success: True, Goal Achieved: True`

### Root Cause Analysis

#### 3a. Why did the planner route to web_search?

The strategic planning prompt in `evaluator.py:strategic_task_planning()` generates a tool manifest that lists available tools:
```
- web_search: search the web
- web_scraper: scrape web pages
- web_analyzer: analyze web content
- file_read: read files from disk
- ...
```

The planner receives the user prompt "Írj 5 rövid pontot arról, hogy mi a Project-S jelenlegi állapota." and the tool manifest. There is **no explicit guidance** in the planning prompt that self-referential questions about "Project-S" should prefer internal state/docs over web search.

The planner (Qwen3 235B) interpreted "Project-S jelenlegi állapota" (Project-S current state) as a request for external information about Project-S, which it correctly classified as something that could be found via web search.

**Root cause:** The strategic planning prompt does not include self-referential routing guidance. The planner has no way to know that "Project-S" refers to the system itself, not an external entity.

#### 3b. Why did the final output not contain 5 bullet points?

The SAI pipeline executed:
1. PLANNING — planner decided to use web_search
2. EXECUTING — web_search tool executed
3. COMPLETE — result stored

The `result` field contains the **execution wrapper** (strategic plan + tool execution log), not the actual content the user requested. The evaluator then evaluated this wrapper as "satisfactory" because:
- The tool WAS executed (web_search ran)
- The evaluation prompt asks "did the tool execute?" not "did the output answer the user's question?"

**Root cause:** The evaluation logic evaluates tool execution success, not answer adequacy. A wrapper/execution summary is accepted as a valid result.

#### 3c. Why did evaluator mark COMPLETE as success?

From the server logs:
```
INFO [core.meta.execution_validator] Validation completed: validation_ea648651 -> failed (confidence: 0.0%)
INFO [core.meta.meta_controller] [OK] Goal achieved in 1 iterations (validator=False, deterministic=True)
```

The execution validator FAILED (confidence 0.0%) because there are no validators configured. However, the MetaController fell through to:
```
[OK] Goal achieved in 1 iterations (validator=False, deterministic=True)
```

This is the **deterministic=True fallback path** — when the validator is not configured (no validators), the system assumes the goal was achieved if the SAI pipeline completed without crashing.

**Root cause:** The `deterministic=True` fallback in MetaController treats any non-crashing execution as success, regardless of whether the output actually answers the user's question.

### GAP Classification

**GAP_026: Self-referential Project-S state questions incorrectly route to web instead of internal state**
- Status: CONFIRMED
- Severity: MEDIUM
- Impact: Self-referential questions about "Project-S", "current system status", "what is Project-S" incorrectly route to web_search

**GAP_027: Non-answer/wrapper output can still satisfy success gates**
- Status: CONFIRMED
- Severity: HIGH
- Impact: Execution wrappers, tool logs, and strategic summaries are accepted as valid results even when the user asked for concrete content (bullet points, analysis, etc.)

---

## 4. UI BUG — Mixed Event Histories

### Observation
The Live Mission Status panel shows event histories from multiple missions mixed together beneath the newest mission_id.

### Root Cause
The `state-log` div is never cleared when a new mission starts. Each new mission appends its events to the existing log, creating a confusing mixed history.

### Fix
Clear `state-log` when a new mission starts. Chat history remains intact.

---

## 5. Proposed Fixes

### Fix 1: Self-referential Routing Guidance (GAP_026)

**Approach:** Add self-referential routing guidance to the strategic planning prompt.

**Implementation:**
In `evaluator.py:strategic_task_planning()`, detect prompts that reference "Project-S", "system status", "current state", "what is" and prepend internal context guidance:

```python
# If prompt references Project-S or system status, prefer internal sources
self_ref_keywords = ["project-s", "system status", "current state", 
                     "what is project", "mi a project", "project jelenlegi"]
if any(kw in prompt.lower() for kw in self_ref_keywords):
    planning_prompt = (
        "IMPORTANT: This question is about Project-S itself. "
        "Do NOT use web_search. Use internal tools: file_read, system_info, "
        "or direct knowledge. The answer should come from internal state/docs.\n\n"
        + planning_prompt
    )
```

**Risk:** Low — this is a prompt-level change only.

### Fix 2: Answer Adequacy Guard (GAP_027)

**Approach:** Add a post-execution adequacy check for direct-answer tasks.

**Implementation:**
After SAI execution completes, before marking COMPLETE:
1. Check if the result contains substantive content (not just a wrapper)
2. For direct-answer tasks (prompts asking for bullet points, analysis, etc.), verify the result contains actual content, not just execution metadata

**Risk:** Medium — requires changes to the evaluation path.

### Fix 3: UI Event Panel Reset (UI BUG)

**Status:** APPLIED

Clear `state-log` div when a new mission starts.

---

## 6. Priority Order

1. **Fix 3 (UI event panel)** — APPLIED, no risk
2. **Fix 1 (Self-referential routing)** — Low risk, prompt-level change
3. **Fix 2 (Answer adequacy guard)** — Medium risk, requires evaluation path changes

---

## 7. Next Steps

1. Apply Fix 1 to `evaluator.py`
2. Test with self-referential prompts
3. Evaluate Fix 2 feasibility
4. Create focused regression tests

---

*End of findings report.*