# AO3_T2_001 — Operator Runbook

## Purpose
This runbook guides the human operator through the **Level 2 validation** of the bridge_runner.py. This is a REAL end-to-end test with a real external executor (Copilot), NOT a simulation. This is the RISK_008 mitigation.

## Pre-Conditions
- [ ] `orchestrator_runtime/cline_inbox/next_prompt.md` exists (task prompt for Copilot)
- [ ] `orchestrator_runtime/cline_inbox/prompt_ready.json` exists (checksum: 94b6381798e44e93)
- [ ] `orchestrator_runtime/cline_outbox/output_ready.json` has NO AO3_T2_001 entry (clean state)
- [ ] `orchestrator_runtime/governance/bridge_runner.py` exists with CLI entry point

## Step 1 — Hand Task to Copilot (External Executor)

1. Open a **NEW browser tab or VS Code Copilot chat** (separate from Cline session).
2. Copy the contents of `orchestrator_runtime/cline_inbox/next_prompt.md` and send it to Copilot.
3. Let Copilot execute the task. Copilot will:
   - Create `orchestrator_runtime/sandbox/ao3_t2_sum.py`
   - Run it (expected output: 5050)
   - Write `orchestrator_runtime/cline_outbox/last_output.md`
   - Compute SHA-256 checksum of last_output.md
   - Write `orchestrator_runtime/cline_outbox/output_ready.json` with consumed=false

## Step 2 — Verify Copilot Output (Before Consume)

After Copilot finishes, verify these files exist:

```powershell
# Check last_output.md exists
Test-Path orchestrator_runtime\cline_outbox\last_output.md

# Check output_ready.json exists and has correct run_id
Get-Content orchestrator_runtime\cline_outbox\output_ready.json
```

Expected in output_ready.json:
- `"run_id": "AO3_T2_001"`
- `"iteration": 1`
- `"consumed": false`
- `"checksum"`: 16 hex chars

## Step 3 — Run Bridge Consume

```powershell
cd C:\ProjectS-Unified
$env:PYTHONPATH="C:\ProjectS-Unified\src"
python orchestrator_runtime/governance/bridge_runner.py consume --run-id AO3_T2_001 --iteration 1 --verdict
```

Expected output: JSON with `"status": "ACCEPTED"` and `"overall": "VERDICT_ISSUED"`.
Exit code: 0 (success)

## Step 4 — Filesystem Inspection (Manual Validation)

### 4a. Check consumed flag flipped
```powershell
Get-Content orchestrator_runtime\cline_outbox\output_ready.json
```
Verify: `"consumed": true` and `"consumed_at"` timestamp present.

### 4b. Check cycle_log.jsonl
```powershell
Get-Content orchestrator_runtime\governance\cycle_log.jsonl | Select-String "AO3_T2_001"
```
Verify: Entries for `bridge_consumed` and `verdict` events.

### 4c. Check notification feed
```powershell
Get-Content orchestrator_runtime\governance\feed.jsonl | Select-String "AO3_T2_001"
```
Verify: Notification entries for `BRIDGE_CONSUMED` and/or `GOAL_DONE`/`GOAL_FAILED`.

### 4d. Check approval_log.json
```powershell
Get-Content orchestrator_runtime\governance\approval_log.json | Select-String "AO3_T2_001"
```
Verify: Goal recorded with PASS or FAIL verdict.

## Step 5 — Verdict

### PASS Criteria (ALL must be true):
- [ ] CLI returned `"status": "ACCEPTED"` (exit code 0)
- [ ] `output_ready.json` → `consumed` is now `true`
- [ ] Checksum was accepted (not REJECTED_CHECKSUM)
- [ ] `cycle_log.jsonl` has `bridge_consumed` entry for AO3_T2_001
- [ ] `feed.jsonl` has notification for AO3_T2_001
- [ ] `approval_log.json` has verdict entry for AO3_T2_001

### If Checksum Mismatch (REJECTED_CHECKSUM):
This is GOOD — it means the guard works. Debug:
1. Recompute checksum manually: `python -c "import hashlib; print(hashlib.sha256(open('orchestrator_runtime/cline_outbox/last_output.md','rb').read()).hexdigest()[:16])"`
2. Compare to what Copilot wrote in output_ready.json
3. Fix the mismatch (Copilot may have written wrong checksum, or file may have been modified)
4. Retry

### If REJECTED_CONSUMED:
The output was already consumed. Reset by setting `"consumed": false` in output_ready.json and retry.

## Expected Result
If all PASS criteria met: **AO3_HARD_T2 = PASS (real, not simulated)**

This is the first time a real external executor's output has been consumed through the bridge runner with full governance stack validation.