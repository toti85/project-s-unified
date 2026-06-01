# GAP_026 + GAP_027 Root Cause Analysis

**Date:** 2026-05-18
**Analysis Time:** 10:20 UTC+3
**Source Code:** ProjectS-Unified

---

## 1. Executive Summary

Two critical issues identified through live UI acceptance testing:

| GAP | Name | Root Cause | Fixable? |
|-----|------|------------|----------|
| GAP_026 | Self-referential Project-S state query returns wrapper, not answer | Planner guidance changes narrative but `use_orchestration=False` skips actual tool execution | YES — surgical fix possible |
| GAP_027 | Non-answer wrapper output satisfies success gates | Evaluator evaluates tool execution success, not answer adequacy; `deterministic=True` fallback accepts any non-crashing execution | YES — surgical fix possible |

---

## 2. GAP_026 — Self-Referential Routing Still Failing

### 2.1 Observed Behavior

**Prompt:** "Írj 5 rövid pontot arról, hogy mi a Project-S jelenlegi állapota."

**Before fix:** Planner chose "Conduct a web search..."
**After fix:** Planner chose "Utilize internal tools to gather current status information..."

**But:** The final output was still "STRATEGIC AI EXECUTION COMPLETE..." — a wrapper, not 5 bullet points.

### 2.2 Root Cause — Code Trace

#### Step 1: Strategic Planning (evaluator.py:strategic_task_planning)

The self-referential guidance IS injected into the prompt:
```python
self_ref_note = (
    "\n\n*** IMPORTANT SELF-REFERENTIAL ROUTING RULE ***\n"
    "This question is about Project-S itself (our own system).\n"
    "DO NOT use web_search, web_scraper, or web_analyzer.\n"
    "Use ONLY internal tools: file_reader, file_search, file_content_search,\n"
    "system_info, or your direct knowledge.\n"
    "*** END SELF-REFERENTIAL ROUTING RULE ***\n"
)
```

The planner (Qwen3 235B) receives this and changes its narrative from "web search" to "internal tools."

**BUT** the planner's JSON response includes:
```json
{
  "use_cognitive_core": false,
  "use_orchestration": false,
  "recommended_tools": [],
  "confidence": 0.9
}
```

#### Step 2: Execution Path (super_intelligent_ai.py:465-486)

```python
# PHASE 2: Conditional Tool Orchestration
if strategic_plan.get("use_orchestration", True):
    # Tool orchestration path — actual tools executed
    orchestration_result = await self.tool_orchestrator.orchestrate_task(...)
else:
    # DIRECT EXECUTION PATH — NO tools executed!
    logger.info("🔧 Phase 2b: Direct execution (Strategic AI optimized)")
    orchestration_result = {"summary": "Strategic AI executed task directly", "success": True}
```

**This is the root cause.** When the planner sets `use_orchestration=False`, the system takes the "Direct execution" path which:
1. Does NOT execute any tools
2. Returns a dummy dict: `{"summary": "Strategic AI executed task directly", "success": True}`
3. The planner's `recommended_tools` list is empty or ignored

#### Step 3: Output Generation (super_intelligent_ai.py:507-534)

```python
execution_output = f"""STRATEGIC AI EXECUTION COMPLETE

📋 TASK: {task_description}

🧠 STRATEGIC ANALYSIS (Qwen3 235B):
Strategy: {strategic_plan.get('strategy', 'standard_execution')}
...

✅ STATUS: {'SUCCESS' if evaluation_result.get('success', False) else 'OPTIMIZING'}
"""
```

This is the wrapper output the user sees. It contains:
- The task description (echoed back)
- The strategic plan summary
- The evaluation result
- **NOT the actual answer to the user's question**

### 2.3 Why the Self-Referential Guidance Only Changed Narrative

The planner receives the guidance and changes its TEXT response ("Utilize internal tools..."), but:
1. The planner still sets `use_orchestration=False` (because it thinks "direct execution" is optimal)
2. The `recommended_tools` list is empty or not populated
3. The execution path ignores the planner's intent when `use_orchestration=False`

**The guidance changes the planner's narrative but not its structural decision to skip orchestration.**

### 2.4 Minimal Surgical Fix

**Option A: Force orchestration when self-referential**

In `evaluator.py:strategic_task_planning()`, when self-ref detected, force `use_orchestration=True` and populate `recommended_tools`:

```python
if self_ref:
    strategic_prompt += (
        "\n\n*** MANDATORY EXECUTION MODE ***\n"
        "You MUST set use_orchestration=true and recommended_tools must include\n"
        "file_search or file_content_search or file_reader.\n"
        "Do NOT set use_orchestration=false for self-referential questions.\n"
        "*** END MANDATORY EXECUTION MODE ***\n"
    )
```

**Risk:** Low — adds stronger guidance to the planner prompt.

**Option B: Force orchestration in code**

In `super_intelligent_ai.py`, when self-ref patterns detected, override `use_orchestration`:

```python
# After strategic_plan is returned
if self_ref_detected and not strategic_plan.get("use_orchestration", True):
    strategic_plan["use_orchestration"] = True
    if not strategic_plan.get("recommended_tools"):
        strategic_plan["recommended_tools"] = ["file_search", "file_content_search"]
```

**Risk:** Low — code-level override, no prompt dependency.

**Recommended:** Option B — more reliable because it doesn't depend on the LLM following instructions.

---

## 3. GAP_027 — Non-Answer Wrapper Passes Success Gates

### 3.1 Observed Behavior

The output "STRATEGIC AI EXECUTION COMPLETE... STATUS: SUCCESS" was accepted as a valid answer to "Write 5 bullet points about Project-S current state."

### 3.2 Root Cause — Code Trace

#### Gate 1: Evaluator (evaluator.py:evaluate_execution_result)

The evaluator is called with:
```python
await self.evaluator.evaluate_execution_result(
    original_goal=task_description,
    tool_used="strategic_ai_orchestration",
    tool_params={"strategic_plan": strategic_plan},
    execution_result={
        "strategic_plan": strategic_plan,
        "cognitive_result": cognitive_result,
        "orchestration_result": orchestration_result  # {"summary": "Strategic AI executed task directly", "success": True}
    },
    context={"strategic_execution": True}
)
```

The evaluation prompt asks:
```
TOOL EXECUTED: strategic_ai_orchestration
EXECUTION RESULT: {"strategic_plan": {...}, "orchestration_result": {"summary": "Strategic AI executed task directly", "success": True}}
```

The AI evaluator evaluates: "Did the tool execute?" — YES, the tool WAS executed (it's the strategic AI itself). The execution result is a valid dict. The AI returns `goal_achieved=True`.

**The evaluator evaluates tool execution success, not answer adequacy.**

#### Gate 2: MetaController Fallback (meta_controller.py)

From logs:
```
INFO [core.meta.execution_validator] Validation completed: validation_e09370a9 -> failed (confidence: 0.0%)
INFO [core.meta.meta_controller] [OK] Goal achieved in 4 iterations (validator=False, deterministic=True)
```

The execution validator FAILED (0.0% confidence) because no validators are configured. But the MetaController falls through to:
```python
[OK] Goal achieved in 1 iterations (validator=False, deterministic=True)
```

This is the `deterministic=True` fallback path. When no validators are configured, ANY non-crashing execution is marked as success.

**This is the second root cause.** The `deterministic=True` fallback treats any non-crashing execution as success.

### 3.3 Why the Wrapper Output is Accepted

1. The evaluator evaluates "did the tool execute?" — YES
2. The execution result is a valid dict — YES
3. The AI evaluator returns `goal_achieved=True` — because the execution didn't crash
4. The validator fails (0.0%) — but no validators are configured
5. The `deterministic=True` fallback accepts the result — because it didn't crash

**The system has no content-adequacy gate.** It only checks:
- Did the tool execute? (yes)
- Did it crash? (no)
- Did the AI evaluator say it was OK? (yes, because the execution was valid)

### 3.4 Minimal Surgical Fix

**Option A: Add content-adequacy check in evaluation prompt**

In `evaluator.py:_build_evaluation_prompt()`, add a check for direct-answer tasks:

```python
# For direct-answer prompts (bullet points, analysis, etc.)
if "bullet point" in original_goal.lower() or "5" in original_goal or "list" in original_goal.lower():
    evaluation_prompt += (
        "\n\nCRITICAL: The user asked for CONCRETE CONTENT (bullet points, analysis, etc.).\n"
        "The execution result must contain the actual requested content, not just an execution wrapper.\n"
        "If the result is only a strategic plan summary or execution log without the actual content,\n"
        "mark goal_achieved=false and action=replan.\n"
    )
```

**Risk:** Low — adds content-adequacy check to evaluation prompt.

**Option B: Fix deterministic fallback**

In `meta_controller.py`, change the fallback to require at least some content in the result:

```python
if not validator.passed and deterministic:
    # Check if result has substantive content
    if result and (result.get("result") or result.get("output")):
        result_text = str(result.get("result", result.get("output", "")))
        if len(result_text) > 50 and "STRATEGIC AI EXECUTION COMPLETE" not in result_text:
            # Has substantive content, not just a wrapper
            return {"success": True, "iterations": self.iteration_count}
    # Otherwise, mark as failed
    return {"success": False, "reason": "No validators, result lacks substantive content"}
```

**Risk:** Medium — changes core success logic.

**Recommended:** Option A — adds content-adequacy check to evaluation prompt without changing core logic.

---

## 4. GAP_028 — UnicodeEncodeError in Logging

### 4.1 Observed Behavior

```
UnicodeEncodeError: 'charmap' codec can't encode character '\xcd' in position 87
```

The character `\xcd` is "Í" from the Hungarian prompt "Írj 5 rövid pontot..."

### 4.2 Root Cause

The Windows console uses cp1251 encoding by default. When the logger tries to write Hungarian characters to the console, cp1251 cannot encode them.

**Location:** `src/utils/performance_monitor.py:54` — the logger uses the default Windows encoding.

### 4.3 Fix

Set UTF-8 encoding before any logging:
```python
import sys
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
```

Or set in `PYTHONIOENCODING=utf-8` environment variable.

**Risk:** None — standard Python UTF-8 encoding setup.

---

## 5. Fix Priority Order

1. **GAP_028 (Unicode)** — Trivial fix, no risk, enables clean logging for Hungarian
2. **GAP_026 (Self-referential routing)** — Force orchestration in code (Option B)
3. **GAP_027 (Content adequacy)** — Add content check to evaluation prompt (Option A)

---

## 6. Can These Be Fixed Surgically?

| GAP | Fixable surgically? | Risk | Effort |
|-----|---------------------|------|--------|
| GAP_026 | YES — code-level override in super_intelligent_ai.py | Low | 10 lines |
| GAP_027 | YES — prompt-level addition in evaluator.py | Low | 10 lines |
| GAP_028 | YES — sys.stdout/stderr encoding | None | 5 lines |

---

*End of root cause analysis.*