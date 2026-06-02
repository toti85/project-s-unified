# MS-AO4 AO4.2 — External Goal Triggers (File Watcher + Webhook) — 2026-06-01

## Deliverables Checklist

| Item | Answer |
|------|--------|
| A. file_watcher.py created? | **YES** |
| B. webhook_receiver.py created? | **YES** |
| C. unit tests pass? | **6/6** |
| D. rate limiting implemented? | **YES** |
| E. kill switch integrated? | **YES** |
| F. HIGH risk → pending_human_approval? | **YES** |
| G. any src/ modifications? | **NO** |
| H. any self_state.json modifications? | **NO** |

---

## Components Created

### file_watcher.py

**Path:** `orchestrator_runtime/governance/file_watcher.py`

**Features:**
- Watches `goal_queue.json` for changes via SHA-256 hash comparison
- Filters auto-approvable goals (LOW + auto_approve, MEDIUM + sandbox_only)
- Passes to `risk_classifier.py` for validation
- Writes approved goals to `trigger_queue.json`
- Rate limit: max 5 new goals per minute (flood protection)
- Kill switch check before processing any trigger
- Logs all events to `trigger_log.jsonl`
- `start(dry_run=True)` — detects changes but doesn't write trigger_queue
- `start(dry_run=False)` — full processing

### webhook_receiver.py

**Path:** `orchestrator_runtime/governance/webhook_receiver.py`

**Features:**
- Simple HTTP server (port 8765, localhost only)
- `POST /goal` — accepts JSON goal submission
- Validates required fields: `id`, `title`, `risk`
- HIGH risk → `pending_human_approval.json` (NOT auto-processed)
- LOW/MEDIUM + sandbox_only → `trigger_queue.json`
- Rate limit: max 10 requests per minute per IP
- Kill switch check on every request
- Logs all requests to `trigger_log.jsonl`
- `GET /health` — health check endpoint

---

## Unit Test Results (6/6 PASS)

```
test_01_detects_new_goal              PASSED  — File watcher detects new goal added to goal_queue.json
test_02_rate_limit_blocks_flood       PASSED  — File watcher rate limit blocks flood (6 goals → 5 accepted, 1 blocked)
test_03_respects_kill_switch          PASSED  — File watcher respects kill switch (0 goals processed)
test_04_accepts_valid_low_goal        PASSED  — Webhook accepts valid LOW goal → trigger_queue entry
test_05_rejects_high_goal_to_pending  PASSED  — Webhook rejects HIGH goal → pending_human_approval entry
test_06_rate_limit_blocks_flood       PASSED  — Webhook rate limit blocks flood (11 requests → 1 rate limited)
```

**Test location:** `orchestrator_runtime/sandbox/test_ao4_triggers.py`
**All tests use real on-disk fixtures, no mocks.**

---

## Rate Limiting

| Component | Limit | Enforcement |
|-----------|-------|-------------|
| File Watcher | 5 goals/minute | Based on `goal_approved` events in trigger_log.jsonl |
| Webhook | 10 requests/minute/IP | In-memory timestamp tracking per IP |

---

## Kill Switch Integration

- **File Watcher:** Checks kill switch before processing any goals. If active, returns 0 processed and logs `kill_switch_active` event.
- **Webhook:** Checks kill switch on every `POST /goal` request. If active, returns HTTP 503 with kill switch reason.

---

## HIGH Risk Handling

HIGH risk goals are **NEVER** auto-processed:
- Written to `pending_human_approval.json` with status `PENDING_HUMAN_APPROVAL`
- NOT added to `trigger_queue.json`
- HTTP 202 response with reason: "HIGH risk goals require human approval"

---

## Safety Compliance

- No src/ modifications: **YES** ✓
- No self_state.json modifications: **YES** ✓
- Sandbox + orchestrator_runtime only: **YES** ✓
- localhost only for webhook: **YES** ✓
- No end-to-end simulation: **YES** ✓
- No fake trigger events: **YES** ✓

---

## File Inventory

| File | Purpose |
|------|---------|
| `orchestrator_runtime/governance/file_watcher.py` | File watcher for goal_queue.json changes |
| `orchestrator_runtime/governance/webhook_receiver.py` | HTTP webhook receiver for goal submissions |
| `orchestrator_runtime/sandbox/test_ao4_triggers.py` | Unit tests (6 tests) |
| `orchestrator_runtime/governance/trigger_queue.json` | Approved goals queue (created at runtime) |
| `orchestrator_runtime/governance/pending_human_approval.json` | HIGH risk goals pending approval (created at runtime) |
| `orchestrator_runtime/governance/trigger_log.jsonl` | Event log (created at runtime) |