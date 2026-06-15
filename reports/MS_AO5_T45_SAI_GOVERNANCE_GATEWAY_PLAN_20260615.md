# AO5_T45 — SAI Governance Gateway Plan
**Mission:** AO5_T45_SAI_GOVERNANCE_GATEWAY_PLAN  
**Date:** 2026-06-15  
**Mode:** PLAN + SURGICAL PREP ONLY — no code modified  
**Executor:** copilot (GitHub Copilot / Claude Sonnet 4.6)

---

## A. SAI Entrypoint Found?

**YES — two entrypoints identified:**

| Entrypoint | Path | Role |
|---|---|---|
| Primary executor | `interactive_layer/sai_runner.py` | Async background task; calls `SuperIntelligentAI` |
| Core AI class | `src/core/super_intelligent_ai.py` (47240 bytes) | `class SuperIntelligentAI` at line 133 |

`sai_runner._run_sai_mission(mission_id, session_id, prompt, ...)` is the callable boundary.  
It imports `from src.core.super_intelligent_ai import SuperIntelligentAI` lazily inside the function.

---

## B. Bridge / Gateway Integration Point

### Current output flow (SAI)

```
sai_runner._run_sai_mission()
  └─ SuperIntelligentAI(use_meta_controller=True).execute(prompt)
       └─ result dict  →  _db_update_result(mission_id, output)
                       →  _db_log_event(...)
                       →  transition_mission_state(..., "COMPLETE")
```

**SAI output goes ONLY to the interactive_layer database (`_db_update_result`).  
It does NOT write to `cline_outbox/last_output.md` or `output_ready.json`.  
It does NOT call `bridge_runner.consume_executor_output()`.  
It does NOT pass through `risk_classifier`.**

### Current governance flow (CM / Cline executor)

```
continuous_mind.run_heartbeat()
  └─ _write_inbox(run_id)              ← writes cline_inbox/next_prompt.md
  └─ _wait_for_output(run_id, 600s)    ← polls cline_outbox/output_ready.json
  └─ _consume_via_gateway(run_id, goal_id, expected_iteration)
       └─ bridge_runner.consume_executor_output(run_id, expected_iteration)
            ├─ KillSwitch check        ← gate 0
            ├─ output_ready.json read  ← FA1_HANDOFF_V1
            ├─ checksum validation     ← tamper detection
            └─ gateway classification  ← risk_classifier → ALLOW/PAUSE/DENY
```

### The gap

SAI execution is a parallel track that **completely bypasses** every governance gate:

| Control | CM/Cline path | SAI path |
|---|---|---|
| Kill switch | ✓ enforced | ✗ not checked |
| Risk pre-classification | ✓ before any execution | ✗ absent |
| FA1_HANDOFF_V1 checksum | ✓ verified on consume | ✗ no file written |
| Gateway ALLOW/PAUSE/DENY | ✓ enforced post-consume | ✗ absent |
| Budget manager | ✓ via bridge_runner | ✗ not invoked |
| Cycle log | ✓ logged | ✗ not logged to CM log |

---

## C. Risk Controls Already Available

All the needed controls already exist and are tested:

| Control | File | Function | Status |
|---|---|---|---|
| Risk classification | `orchestrator_runtime/governance/risk_classifier.py` | `classify_execution_request(goal_id)` | ✓ battle-tested T37/T38 |
| Gateway decision | `orchestrator_runtime/governance/bridge_runner.py` | `_evaluate_execution_gateway(run_id)` | ✓ ALLOW/PAUSE/DENY proven |
| Kill switch | `orchestrator_runtime/governance/kill_switch.py` | `KillSwitch().is_active()` | ✓ integrated in bridge_runner |
| FA1_HANDOFF_V1 consume | `orchestrator_runtime/governance/bridge_runner.py` | `consume_executor_output(run_id, expected_iteration)` | ✓ checksum + consumed flag |
| Budget manager | `orchestrator_runtime/governance/budget_manager.py` | — | ✓ exists |
| Goal queue | `orchestrator_runtime/goal_queue.json` | 8 pending goals, LOW/MEDIUM/HIGH classified | ✓ |

The pattern is proven: classify → gate → execute → consume → log.  
What's missing is applying this pattern to the SAI path.

---

## D. Missing Controls

### D1 — Pre-execution SAI gateway (highest priority)
`sai_runner._run_sai_mission()` has no pre-execution call to `risk_classifier`.  
A SAI execution request with unknown or HIGH risk proceeds to `SuperIntelligentAI` unconditionally.

**Required:** Before `ai = SuperIntelligentAI(...)`, call `classify_execution_request(goal_id)`.  
If DENY → raise / return without executing.  
If PAUSE → log and wait for explicit approval flag.  
If ALLOW → proceed.

### D2 — FA1_HANDOFF_V1 adapter (medium priority)
SAI output goes to `_db_update_result`. It never writes `last_output.md` or `output_ready.json`.  
CM's `_wait_for_output()` polls `cline_outbox/output_ready.json` — SAI output is invisible to CM.

**Required:** An `sai_outbox_adapter` that, after `_db_update_result`, also writes:
1. `cline_outbox/last_output.md` — SAI output content
2. `cline_outbox/output_ready.json` — with `run_id`, checksum, `consumed=false`

This makes SAI output consumable by the existing `consume_executor_output()` path.

### D3 — Kill switch pre-SAI gate (medium priority)
`bridge_runner.consume_executor_output()` checks the kill switch before any consume.  
`sai_runner` does not check it before launching SAI.

**Required:** Add `KillSwitch().is_active()` check at the top of `_run_sai_mission()`.

### D4 — SAI goal registration in goal_queue (low priority)
`classify_execution_request(goal_id)` looks up `goal_id` in `goal_queue.json`.  
SAI missions have their own `mission_id` (UUID from `interactive_layer/database.py`),  
not entries in `goal_queue.json`. If SAI's `mission_id` isn't in the queue, the classifier  
returns `DENY` (safe default) even for legitimately approved SAI work.

**Required:** Either (a) add SAI missions to `goal_queue.json` before execution,  
or (b) add a secondary classification path for SAI-native `mission_id` format.

---

## E. Recommended T46 Implementation Scope

**Scope: Minimal surgical additions — no changes to existing gateway or SAI core.**

### T46 target: `orchestrator_runtime/governance/sai_gateway_adapter.py` (new file)

```python
# sai_gateway_adapter.py — governance wrapper for SAI execution
# Pre-execution: classify → gate (ALLOW/PAUSE/DENY)
# Post-execution: write FA1_HANDOFF_V1 files so CM can consume
# Kill switch: check before any SAI launch
# Pure stdlib + reuse existing governance modules

def sai_pre_execution_gate(goal_id: str) -> dict:
    """Classify SAI execution request. Returns gateway_decision."""
    # 1. KillSwitch check
    # 2. classify_execution_request(goal_id) → ALLOW/PAUSE/DENY
    # 3. Return dict with gateway_decision

def write_sai_output_to_outbox(run_id: str, output: str) -> str:
    """Write SAI result to FA1_HANDOFF_V1 format. Returns checksum."""
    # 1. Write cline_outbox/last_output.md
    # 2. Compute SHA256 checksum (first 16 hex chars)
    # 3. Write cline_outbox/output_ready.json (consumed=false)
    # RISK_010: last_output.md FIRST, checksum computed, output_ready.json LAST
```

### Integration point in `sai_runner._run_sai_mission()` (3-line addition)

```python
# At start of _run_sai_mission, before ai = SuperIntelligentAI(...)
from orchestrator_runtime.governance.sai_gateway_adapter import sai_pre_execution_gate
gate = sai_pre_execution_gate(mission_id)
if gate["gateway_decision"] != "ALLOW":
    transition_mission_state(mission_id, MissionStateUpdate(state="FAILED"))
    _db_log_event(mission_id, "sai_gateway_blocked", gate)
    return
```

### After SAI completes (1-line addition after `_db_update_result`)

```python
from orchestrator_runtime.governance.sai_gateway_adapter import write_sai_output_to_outbox
write_sai_output_to_outbox(mission_id, output)
```

### Files to create/modify in T46

| File | Action | Scope |
|---|---|---|
| `orchestrator_runtime/governance/sai_gateway_adapter.py` | **CREATE** | ~80 lines, stdlib only |
| `interactive_layer/sai_runner.py` | **MODIFY** | 3 lines pre-gate + 1 line post-write |
| `orchestrator_runtime/goal_queue.json` | OPTIONAL | Add SAI goal entries if needed |

### Files to NOT touch in T46

- `bridge_runner.py` — already correct, no changes needed
- `risk_classifier.py` — already correct, no changes needed
- `continuous_mind.py` — no changes needed (will benefit automatically)
- `src/` — no modifications
- `self_state.json` — no modifications

---

## F. Any Code Modified?

**NO — zero files were modified in T45.**

This is a read-only planning mission. Evidence:

```
git diff -- .    →  (empty)
```

All findings above are from file inspection only.

---

## Execution Path Diagram (As-Is vs. To-Be)

### As-Is (T45 baseline)

```
CM heartbeat → classify → ALLOW → write inbox → poll outbox → consume → gateway → ALLOW/PAUSE/DENY
SAI runner   → SuperIntelligentAI → db.update_result → (END — no governance)
```

### To-Be (after T46)

```
CM heartbeat → classify → ALLOW → write inbox → poll outbox → consume → gateway → ALLOW/PAUSE/DENY
SAI runner   → [sai_pre_execution_gate: kill_switch + classify → ALLOW]
             → SuperIntelligentAI → db.update_result
             → [write_sai_output_to_outbox → last_output.md + output_ready.json]
             → (optionally: CM can now consume SAI output via existing path)
```

The To-Be adds governance without breaking either the SAI path or the CM path.
