# MS-AO2 Scope Draft — Autonomous Operations Activation

**Date:** 2026-05-27
**Status:** PLANNING PHASE (not started)
**Prerequisite:** MS-AO1 COMPLETE (8/8 goals, 6-component governance pipeline, 2026-05-27)

---

## What MS-AO1 Delivered (Baseline)

MS-AO1 proved a **complete governance infrastructure** for controlled autonomous goal processing:

- Goal queue with risk classification (LOW/MEDIUM/HIGH)
- Risk classifier with relaxed threshold (MEDIUM+sandbox_only=APPROVED)
- Self-correcting loop with bounded retries (max 2) and escalation
- Parallel loop manager with conflict detection and serialization
- Self-state updater (read-only, pending updates, human approval required)
- Full approval/audit logging

**Classification:** Governance infrastructure. NOT full autonomy. All 8 goals processed with 0 failures, 0 escalations.

---

## What MS-AO2 Adds Over MS-AO1

| Dimension | MS-AO1 (Current) | MS-AO2 (Target) |
|-----------|-----------------|-----------------|
| Self-state updates | Pending only, human approval required | **Live writes** with atomic method, human-approved activation |
| Operator notification | File-based logs only | **Active notification system** (file-based flags + optional email/UI) |
| Goal execution | Manual trigger per goal | **Semi-autonomous** — system proposes, operator approves batch |
| Kill switch | None | **File-based kill switch** + CLI pause command |
| Daily budget | None | **Configurable daily budget** (default: 10 goals/day) |
| Evidence capture | Manual reports | **Auto-capture** run outcomes to pending self-state updates |

**Core difference:** MS-AO1 = infrastructure built, manual operation. MS-AO2 = activate the infrastructure with safety guards.

---

## Proposed Milestones

### AO2.1 — Activate Self-State Live Writes

- Enable `self_state_updater.py` to apply pending updates to `self_state.json`
- Atomic write method: backup → temp → validate JSON → rename
- Pre-write backup always created
- Post-write validation: JSON parseable, milestone count correct, no data loss
- Every write logged to `self_state_audit.json` with `self_state_modified: true`
- Safety: only milestone updates and evidence additions (no gap status changes without explicit approval)

### AO2.2 — Operator Notification System

- File-based notification flags in `orchestrator_runtime/notifications/`
- Notification types: goal_completed, goal_failed, escalation_required, budget_warning
- Optional email notification (configurable, disabled by default)
- Notification digest: daily summary of autonomous activity
- Operator can acknowledge/clear notifications via CLI

### AO2.3 — Kill Switch + Daily Budget

- File-based kill switch: `orchestrator_runtime/.kill_switch` — if exists, all autonomous processing stops
- CLI command: `python -m orchestrator.cli kill-switch toggle`
- Daily budget: max N goals per day (default: 10)
- Budget tracking in `orchestrator_runtime/governance/daily_budget.json`
- Budget reset at midnight UTC
- Budget exhaustion → pause + notification, not error

### AO2.4 — Semi-Autonomous Batch Processing

- System proposes next batch of goals from goal_queue.json
- Operator approves batch (not individual goals)
- Batch size configurable (default: 3 goals per batch)
- Each goal in batch still goes through risk classifier + self-correcting loop
- Batch failure (any goal escalates) → pause batch, notify operator

---

## Risk / Safety Considerations

### Inherited from MS-AO1 (carry forward)
- Sandbox confinement must remain strict
- No production file modifications without explicit approval
- API keys never printed or logged

### New MS-AO2 Risks

| Risk | Description | Mitigation |
|------|-------------|------------|
| AO2-R1 | Self-state corruption from live writes | Atomic write (backup → temp → validate → rename). Pre-write backup. Post-write validation. |
| AO2-R2 | Kill switch not noticed in time | File-based check before EVERY goal submission. CLI status command. |
| AO2-R3 | Daily budget too permissive | Default: 10 goals/day. Operator can adjust. Budget exhaustion = pause, not error. |
| AO2-R4 | Notification fatigue | Digest mode (daily summary). Configurable thresholds. |
| AO2-R5 | Batch cascade failure | Any escalation pauses entire batch. Operator must review before continuing. |

### Governance Principles (non-negotiable)
1. **Foundation.md elv:** meglévő modulokat összekötjük, nem helyettesítjük
2. **Governance first:** safety gates before capability expansion
3. **Evidence first, conclusion second:** all autonomous decisions logged
4. **Human override always available:** kill switch, pause, manual review
5. **No production changes without explicit approval:** sandbox remains the default boundary

---

## What MS-AO2 is NOT

- NOT full autonomy — operator still approves batches
- NOT self-modifying code — governance infrastructure only
- NOT production-deployable without human oversight
- NOT a replacement for the Interactive Layer
- NOT a system that makes financial decisions

---

## Estimated Effort

| Milestone | Complexity | Estimated Cline Sessions |
|-----------|-----------|-------------------------|
| AO2.1 Self-State Live Writes | Medium | 2-3 |
| AO2.2 Operator Notifications | Low-Medium | 1-2 |
| AO2.3 Kill Switch + Budget | Low | 1-2 |
| AO2.4 Batch Processing | Medium | 2-3 |
| **Total** | | **6-10 sessions** |

---

## Recommended Starting Point

Begin with AO2.3 (Kill Switch + Daily Budget) — safety infrastructure before activation. Then AO2.1 (Self-State Live Writes) to activate the pending update mechanism. AO2.2 and AO2.4 can follow in parallel.

---

*Scope draft generated 2026-05-27. Awaiting operator review before any implementation begins.*