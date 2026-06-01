# MS-AO4 T5 — Live Budget Exhaustion Test (PREP) — 2026-06-01

## Deliverables Checklist

| Item | Answer |
|------|--------|
| A. budget_config.json set to limit=2? | **YES** |
| B. 3 goal output files created with real checksums? | **YES** |
| C. batch_processor budget check confirmed/added? | **YES** — already present (lines 374-381) |
| D. did you execute or simulate? | **NO** |

## Budget Configuration

**budget_config.json:**
```json
{
  "daily_limit": 2
}
```

**daily_budget.json (reset):**
```json
{
  "date": "2026-06-01",
  "count": 0,
  "limit": 2
}
```

## 3 LOW Risk Goal Output Files

| Goal ID | Output File | Checksum |
|---------|-------------|----------|
| AO4_T5_GOAL_A | `orchestrator_runtime/cline_outbox/last_output_AO4_T5_GOAL_A.md` | `4c41369ad43f47c8` |
| AO4_T5_GOAL_B | `orchestrator_runtime/cline_outbox/last_output_AO4_T5_GOAL_B.md` | `e9ced198393f41ae` |
| AO4_T5_GOAL_C | `orchestrator_runtime/cline_outbox/last_output_AO4_T5_GOAL_C.md` | `2a2fa9fde89ec18f` |

## Batch Processor Budget Check (Confirmed)

The `batch_processor.py` already has per-goal budget integration:

**Lines 374-381 — Per-goal budget check:**
```python
# Per-goal budget check
bg_ok, bg_reason = _check_budget()
if not bg_ok:
    _log("GOAL_BLOCKED_BUDGET", goal_id=goal_id, batch_id=batch_id, reason=bg_reason)
    _notify("GOAL_FAILED", goal_id=goal_id, message=f"Blocked by budget: {bg_reason}", severity="ERROR")
    results.append({"goal_id": goal_id, "status": "BLOCKED", "reason": bg_reason})
    blocked += 1
    break  # Stop batch
```

**Lines 384-389 — Budget increment before execution:**
```python
if _BudgetManager is not None:
    try:
        bm = _BudgetManager()
        bm.increment()
    except Exception:
        pass
```

**Expected test flow (live execution):**
1. Goal A: budget count 0→1, runs OK
2. Goal B: budget count 1→2, runs OK
3. Goal C: budget check fails (count=2 >= limit=2) → BLOCKED_BUDGET

## What Was NOT Done (RISK_008 Compliance)

- **NO** batch execution performed
- **NO** simulation of any end-to-end flow
- **NO** src/ modifications
- **NO** self_state.json modifications

## Next Step (Real T5 Test)

1. Add 3 goals to goal_queue.json (AO4_T5_GOAL_A/B/C)
2. Run: `python orchestrator_runtime/governance/batch_processor.py --dry-run`
3. Verify dry_run shows 3 goals, budget_ok=True
4. Run: `python orchestrator_runtime/governance/batch_processor.py --live`
5. Verify Goal C blocked with BLOCKED_BUDGET
6. Reset budget_config.json to daily_limit: 10