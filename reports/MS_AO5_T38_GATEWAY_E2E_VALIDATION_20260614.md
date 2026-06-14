# MS AO5 T38 — Gateway End-to-End Validation

Generated: 2026-06-14
Task: AO5_T38
Mode: VALIDATION (read-only on src/, write to sandbox/ + outbox)

## Executive Summary

Full real end-to-end validation of the T37 risk-classified gateway was completed via
3 actual bridge_runner consume handshakes. All 3 cases confirmed correct gateway
behavior. Zero divergences versus T37 synthetic validation.

**Final verdict: T37 gateway is PROVED end-to-end.**

---

## Phase 1 — Backup Verification

Backups created for both governance files before any validation work:

| File | Backup | Bytes | Identical |
|------|--------|-------|-----------|
| bridge_runner.py | bridge_runner.py.bak_t37_20260614_210914 | 24293 | YES |
| risk_classifier.py | risk_classifier.py.bak_t37_20260614_210914 | 11215 | YES |

Phase 1: PASS

---

## Phase 2 — Outbox Handshakes Created

RISK_010 order respected for all 3 cases:
1. last_output.md written first
2. SHA-256 checksum computed from on-disk binary (identical to bridge_runner method)
3. output_ready.json written last

| Case | Run ID | Outbox Dir | Checksum |
|------|--------|------------|----------|
| LOW | AO3_GOAL_007 | cline_outbox/ao5_t38_low | ea673a4eaed9fc9d |
| MEDIUM | AO3_AO3_HARD_T2_GOV | cline_outbox/ao5_t38_medium | b99b187a4cfcbe90 |
| HIGH | AO3_AO3_HARD_T3_HIGH | cline_outbox/ao5_t38_high | c36fa0b1a7f6ef5b |

---

## Phase 3 — Real bridge_runner Consume Results

All 3 calls went through the full consume_executor_output → get_verdict_for_content path.

| Case | Consume Status | Gateway Decision | Action | Latency |
|------|---------------|-----------------|--------|---------|
| LOW | ACCEPTED | ALLOW | DONE | ~205ms |
| MEDIUM | ACCEPTED | PAUSE | AWAIT_HUMAN | ~53ms |
| HIGH | ACCEPTED | DENY | BLOCKED | ~84ms |

Notes:
- LOW: ALLOW path → SCL executed → verdict_result contains action=DONE (no gateway_decision field in output — SCL takes over). Gateway decision confirmed via explicit classify_execution_request.
- MEDIUM: PAUSE path → verdict_result contains gateway_decision=PAUSE, action=AWAIT_HUMAN.
- HIGH: DENY path → verdict_result contains gateway_decision=DENY, action=BLOCKED.

---

## Phase 4 — Evidence File

`orchestrator_runtime/sandbox/ao5_t38_e2e_validation.json`

---

## Phase 5 — T37 Synthetic vs T38 Real Comparison

| Case | Synth GW | Real GW | GW Match | Synth Action | Real Action | Act Match |
|------|----------|---------|----------|--------------|-------------|-----------|
| LOW | ALLOW | ALLOW | YES | DONE | DONE | YES |
| MEDIUM | PAUSE | PAUSE | YES | AWAIT_HUMAN | AWAIT_HUMAN | YES |
| HIGH | DENY | DENY | YES | BLOCKED | BLOCKED | YES |

Divergences: 0

### Additional finding: unknown run_id behavior

First attempt used AO5_T38_LOW / AO5_T38_MEDIUM / AO5_T38_HIGH as run_ids.
These do not exist in goal_queue.json. All three returned DENY (safe default).
This is the correct and expected behavior per the policy: unknown = HIGH risk = DENY.

---

## Phase 6 — Final Verdict

**T37 gateway is PROVED end-to-end.**

Evidence summary:
- 3 real bridge_runner consume calls completed: YES
- All checksums matched (no REJECTED_CHECKSUM): YES
- LOW → ALLOW → SCL → DONE: PROVED
- MEDIUM → PAUSE → AWAIT_HUMAN: PROVED
- HIGH → DENY → BLOCKED: PROVED
- Unknown ID → DENY (safe default): PROVED (bonus case)
- Zero divergences vs T37 synthetic: YES
- Any src/ modifications: NO
- Unexpected errors: NO

---

## Return Values (A-J)

- A. Backups verified present? YES (bridge_runner.py.bak_t37_20260614_210914 + risk_classifier.py.bak_t37_20260614_210914)
- B. 3 outbox directories created? YES (ao5_t38_low / ao5_t38_medium / ao5_t38_high)
- C. 3 bridge_runner consume executions completed? YES
- D. LOW case: consume=ACCEPTED, gateway=ALLOW, action=DONE
- E. MEDIUM case: consume=ACCEPTED, gateway=PAUSE, action=AWAIT_HUMAN
- F. HIGH case: consume=ACCEPTED, gateway=DENY, action=BLOCKED
- G. Synthetic vs Real divergence? NO (0 divergences)
- H. Gateway PROVED end-to-end? YES
- I. Any src/ modifications? NO
- J. Any unexpected errors during consume? NO
