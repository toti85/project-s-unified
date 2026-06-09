# AO5_T8 — CWI Integration Plan (Ghost Branch v0.2)

**Run ID:** AO5_T8_CWI_PLAN | **Iteration:** 1 | **Date:** 2026-06-09
**Status:** PLAN ONLY — No src/ modifications, No implementation
**Scope:** cognitive_workflow_integration.py integration into MS-AO5 governance pipeline

---

## 1. Hook Point Analysis

### 1.1 bridge_runner.py — Pre-Consumption Phase (PRIMARY CANDIDATE)

| Attribute | Value |
|-----------|-------|
| **File** | `orchestrator_runtime/governance/bridge_runner.py` |
| **Function** | `consume_executor_output()` |
| **Line** | ~215-329 |
| **Current responsibility** | Validates output_ready.json + last_output.md checksum, marks consumed, passes to verdict |
| **Why suitable** | This is the active governance pipeline entry point. All executor output flows through here. Pre-consume phase already has kill switch gate (line 239-249). Adding CWI analysis here would be advisory-only and non-blocking. |
| **Why not suitable** | bridge_runner.py is synchronous file validation. CWI requires async context. Would need to wrap in `asyncio.run()` or refactor to async. |

**Integration point:** After kill switch check (line 249), before output_ready.json validation (line 251).

```python
# Line 249-251: After kill switch, before output_ready check
# ── CWI ADVISORY PRE-ANALYSIS (non-blocking) ──
try:
    from core.cognitive_workflow_integration import get_cognitive_workflow_integration
    cwi = get_cognitive_workflow_integration()
    # Extract task description from goal_queue or run_id context
    cognitive_advisory = await cwi.process_task_cognitively(
        task_description=task_description_from_context,
        context={"integration": "bridge_runner_pre_consume", "run_id": run_id},
        user_id="ao5_system"
    )
    # Store advisory in run context (non-blocking, advisory-only)
    logger.info(f"CWI advisory for {run_id}: intent={cognitive_advisory.get('intent_analysis', {}).get('intent_type')}")
except Exception as e:
    logger.warning(f"CWI pre-analysis failed for {run_id}: {e} — continuing without cognitive advisory")
```

### 1.2 bridge_runner.py — Verdict Phase (SECONDARY CANDIDATE)

| Attribute | Value |
|-----------|-------|
| **File** | `orchestrator_runtime/governance/bridge_runner.py` |
| **Function** | `get_verdict_for_content()` |
| **Line** | ~334-379 |
| **Current responsibility** | Passes consumed content to self_correcting_loop for verdict |
| **Why suitable** | Post-execution analysis could provide cognitive insights about execution quality. |
| **Why not suitable** | This is post-execution. CWI is designed for pre-execution task analysis. Would be less valuable. |

### 1.3 filesystem_orchestrator.py — Execution Phase (TERTIARY CANDIDATE)

| Attribute | Value |
|-----------|-------|
| **File** | `src/orchestrator/filesystem_orchestrator.py` |
| **Function** | `OrchestratedRun.execute()` |
| **Line** | TBD (not in orchestrator_runtime/) |
| **Current responsibility** | Executes orchestrated runs with state machine |
| **Why suitable** | Direct integration point for task execution. |
| **Why not suitable** | This is in src/ — RISK_008 PREP ONLY constraint. Would require src/ modifications. Not suitable for first integration. |

### 1.4 CLI Entry Point — Task Input Phase (NOT RECOMMENDED)

| Attribute | Value |
|-----------|-------|
| **File** | `orchestrator_runtime/governance/bridge_runner.py` |
| **Function** | `_cli()` |
| **Line** | ~395-417 |
| **Current responsibility** | CLI wrapper for consume command |
| **Why suitable** | Early integration point for CLI-driven tasks. |
| **Why not suitable** | Only affects CLI users, not automated pipeline. Too narrow scope. |

---

## 2. Recommended Primary Hook Point

**Primary hook:** `bridge_runner.py` — `consume_executor_output()` — Pre-Consumption Phase (after kill switch, before output_ready validation)

**Why this is the safest first integration point:**

1. **Non-blocking:** Can be implemented as advisory-only. If CWI fails, pipeline continues normally.
2. **Already has gate pattern:** Kill switch gate (line 239-249) demonstrates the pattern for optional pre-processing.
3. **Centralized:** All executor output flows through here — no need to modify multiple entry points.
4. **Governance-aligned:** This is the active MS-AO5 governance pipeline. Integration here ensures all runs get cognitive advisory.
5. **Easy rollback:** Single function modification. Can be disabled by removing the try/except block.
6. **No src/ modifications:** Entirely within orchestrator_runtime/, compliant with RISK_008.

---

## 3. Wrapper Contract

### 3.1 Interface

```python
async def process_task_cognitively(
    task_description: str,
    context: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Returns:
    {
        "success": bool,
        "intent_analysis": {
            "intent_type": str,      # e.g., "file_search", "web_research", "general"
            "confidence": float,     # 0.0-1.0
            "operation": str,        # e.g., "search", "write", "analyze"
            "parameters": Dict,
            "suggested_approach": str
        },
        "task_decomposition": {
            "subtasks": List[Dict],  # [{id, description, priority, complexity}]
            "total_complexity": int, # 1-5 scale
            "execution_strategy": str
        },
        "semantic_reasoning": {
            "strategy": str,         # e.g., "sequential_execution"
            "confidence": float,
            "explanation": str,
            "similar_patterns": List[str]
        },
        "processing_context": {
            "user_id": str,
            "session_id": str,
            "task_type": str
        }
    }
    """
```

### 3.2 Advisory-Only Mode (First Integration)

**Mode:** Advisory-only — CWI result is NEVER blocking.

**Behavior:**
- CWI analysis runs in background (non-blocking)
- Results stored in `context` dict, passed to verdict phase
- If CWI fails (import error, processing error, timeout), pipeline continues with `cognitive_advisory = None`
- CWI results are logged but do not affect verdict

**Fallback:**
```python
# Default when CWI unavailable
cognitive_advisory = {
    "success": False,
    "error": "CWI not available",
    "intent_analysis": {"intent_type": "unknown", "confidence": 0.0},
    "task_decomposition": {"subtasks": [], "total_complexity": 0},
    "semantic_reasoning": {"strategy": "default", "confidence": 0.0}
}
```

### 3.3 Error Handling

| Error Type | Handling |
|------------|----------|
| ImportError (CWI module not found) | Log warning, continue with `cognitive_advisory = None` |
| Processing error (CWI raises exception) | Log error, continue with default advisory |
| Timeout (>30s) | Log timeout, continue with partial advisory |
| AI provider error (OpenRouter 429) | Log error, continue with intent analysis from cached patterns |

---

## 4. Risk Classification

| Risk Type | Level | Details |
|-----------|-------|---------|
| **Import risk** | LOW | All 4 dependency modules are ACTIVE (core.cognitive, core.orchestration, integrations.decision_routing, core.state) |
| **Runtime risk** | MEDIUM | CWI requires async context. Would need `asyncio.run()` wrapper or refactor bridge_runner to async. |
| **False-positive risk** | LOW | Advisory-only mode means CWI cannot cause false PASS/FAIL verdicts. |
| **Latency/performance risk** | MEDIUM | CWI adds ~1-2 AI calls (intent analysis + task decomposition). Could add 5-15s per run. |
| **Rollback risk** | LOW | Single function modification. Can be disabled by removing try/except block. |
| **RISK_001 interaction** | NONE | CWI is advisory-only, never triggers autonomous action. |
| **RISK_008 interaction** | LOW | Integration is in orchestrator_runtime/, not src/. Compliant with PREP ONLY constraint. |
| **RISK_010 interaction** | LOW | CWI analysis runs before checksum computation, does not modify last_output.md. |

---

## 5. Sandbox Test Plan

### 5.1 Test 1: Happy Path — Simple Handoff

**Goal:** Verify CWI provides cognitive advisory for a simple task.

**Setup:**
```python
# Create test task in goal_queue.json
{
    "id": "AO5_T8_TEST_001",
    "title": "File search task",
    "description": "Search for files containing 'import os' in src/",
    "risk": "LOW",
    "auto_approve": true
}
```

**Execution:**
1. Run bridge_runner consume for AO5_T8_TEST_001
2. Verify CWI advisory is generated
3. Verify intent_type = "file_search"
4. Verify pipeline continues to verdict

**Expected:**
- CWI advisory: `{"intent_type": "file_search", "confidence": >0.8}`
- Verdict: PASS/FAIL based on content, not CWI
- No pipeline blocking

### 5.2 Test 2: Malformed/Unknown Task

**Goal:** Verify CWI does not block on unknown task types.

**Setup:**
```python
{
    "id": "AO5_T8_TEST_002",
    "title": "Unknown task",
    "description": "Perform quantum entanglement analysis on cosmic microwave background",
    "risk": "LOW",
    "auto_approve": true
}
```

**Execution:**
1. Run bridge_runner consume for AO5_T8_TEST_002
2. Verify CWI handles gracefully
3. Verify intent_type = "general" or similar fallback
4. Verify pipeline continues

**Expected:**
- CWI advisory: `{"intent_type": "general", "confidence": ~0.5}`
- No exception raised
- Pipeline continues normally

### 5.3 Test 3: CWI Failure Path

**Goal:** Verify pipeline continues when CWI import or processing fails.

**Setup:**
```python
# Temporarily rename CWI module to simulate missing module
# src/core/cognitive_workflow_integration.py → cognitive_workflow_integration.py.bak
```

**Execution:**
1. Run bridge_runner consume for any test task
2. Verify ImportError is caught
3. Verify `cognitive_advisory = None` or default advisory
4. Verify pipeline continues to verdict

**Expected:**
- Log warning: "CWI pre-analysis failed — continuing without cognitive advisory"
- No exception propagated
- Pipeline continues normally
- Verdict based on content, not CWI

---

## 6. Rollback Plan

### 6.1 Files Changed in Implementation

| File | Change |
|------|--------|
| `orchestrator_runtime/governance/bridge_runner.py` | Add CWI pre-analysis block in `consume_executor_output()` |

### 6.2 Disable CWI

**Option 1: Config flag (recommended)**
```python
# Add to bridge_runner.py or config
CWI_ENABLED = True  # Set to False to disable

def consume_executor_output(...):
    if not CWI_ENABLED:
        # Skip CWI analysis
        pass
    # ... rest of function
```

**Option 2: Remove integration block**
```bash
# Revert to previous version
git checkout HEAD -- orchestrator_runtime/governance/bridge_runner.py
```

### 6.3 Expected Git Restore Command

```bash
git checkout HEAD -- orchestrator_runtime/governance/bridge_runner.py
```

### 6.4 Rollback Verification

1. Run bridge_runner consume for test run
2. Verify no CWI-related log messages
3. Verify pipeline continues normally
4. Verify verdict is based on content only

---

## 7. 24h Observation Criteria

After implementation, monitor for 24 hours:

| Metric | Baseline | Alert Threshold | Action |
|--------|----------|-----------------|--------|
| **bridge_runner verdicts** | Normal distribution | >20% REJECTED_CHECKSUM | Disable CWI, investigate |
| **approval_log** | Normal rate | >50% PENDING_HUMAN | Review CWI advisory impact |
| **cycle_log** | Normal rate | >2x normal duration | Check CWI latency |
| **Latency** | ~5-10s per run | >30s per run | Disable CWI, optimize |
| **REJECTED_CHECKSUM recurrence** | 0% | >5% | CWI modifying last_output.md (RISK_010 violation) |
| **False BLOCK** | 0% | >0% | CWI blocking pipeline (should be advisory-only) |
| **False PASS** | Normal rate | >20% increase | CWI advisory affecting verdict |
| **CWI exceptions** | 0% | >10% of runs | CWI module issue, disable |

---

## 8. Implementation Phase Boundary

**AO5_T8 is plan only. Next step is AO5_T8_IMPL_PREP or AO5_T9_CWI_SANDBOX_IMPLEMENTATION, not live production integration.**

---

*Generated by: AO5_T8_CWI_PLAN Ghost Branch v0.2 Integration Plan*
*Evidence: bridge_runner.py, sz_ghost_v02_cwi_evolution.md, MS_AO5_AO5_T7_GHOST_V02_PREP_20260610.md*