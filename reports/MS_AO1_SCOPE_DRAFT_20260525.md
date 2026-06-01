# MS-AO1 Scope Draft — Full Autonomy Planning

**Date:** 2026-05-27
**Status:** PLANNING PHASE (not started)
**Prerequisite:** MS-FA1 COMPLETE (FA1_014 PASS, 2026-05-25)

---

## What MS-FA1 Delivered (Baseline)

MS-FA1 proved a **controlled filesystem orchestration loop**:

- Project-S can generate structured tasks
- Tasks are written to a sandbox filesystem
- Cline reads tasks, executes them, writes results back
- AI evaluator scores results with confidence
- Multi-iteration loops work with proper handoff protocol
- Output consumption with run_id validation prevents stale data bugs
- All within strict sandbox confinement

**Classification:** Controlled orchestration. Human-in-the-loop at every stage. NOT autonomy.

---

## What MS-AO1 Adds Over MS-FA1

| Dimension | MS-FA1 (Current) | MS-AO1 (Target) |
|-----------|-----------------|-----------------|
| Task generation | Manual goal input | Autonomous goal discovery from self_state.json gaps, Organism proposals, or operator backlog |
| Loop initiation | Manual `run-loop` command | Self-initiated when new goal detected (with governance gates) |
| Human approval | Required before every Cline handoff | Optional per-task risk classification (low-risk auto-approve, high-risk require approval) |
| Concurrency | Single sequential loop | Multiple parallel loops with resource awareness |
| Self-correction | Verdict recorded, no auto-retry | Auto-retry on FAIL with modified prompt (bounded attempts) |
| Scope | Sandbox-only filesystem tasks | Sandbox filesystem + bounded external actions (web research, server health checks) |
| State persistence | Run archived, lessons not auto-captured | Auto-update self_state.json with run outcomes, new gaps discovered |
| Stopping conditions | Manual stop or max iterations | Self-determined completion + operator override + anomaly detection |

**Core difference:** MS-FA1 = human pushes the loop. MS-AO1 = the system pushes the loop, human governs the boundaries.

---

## Proposed Milestones

### AO1.1 — Autonomous Goal Discovery
- System reads self_state.json known_gaps (ACTIVE status)
- System reads Organism top_proposals.md
- System generates prioritized goal queue without manual input
- Output: `orchestrator_runtime/goal_queue.json`
- Safety: goals are READ-ONLY suggestions until approved

### AO1.2 — Risk-Classified Auto-Approval
- Each goal classified: LOW / MEDIUM / HIGH risk
- LOW: sandbox-only, read-only, no production impact → auto-approve
- MEDIUM: sandbox writes, test creation → auto-approve with logging
- HIGH: any production file touch, config changes → require human approval
- Gate: `orchestrator_runtime/governance/risk_classifier.py`

### AO1.3 — Self-Correcting Loop
- On FAIL verdict: auto-generate revised prompt with evaluator feedback
- Retry up to N times (configurable, default 2)
- On repeated FAIL: escalate to human with full context
- Prevent infinite retry loops with hard budget limits

### AO1.4 — Parallel Loop Orchestration
- Multiple goals processed concurrently
- Resource awareness: rate limit AI calls, filesystem I/O
- Conflict detection: two goals modifying same file → serialize
- Output: `orchestrator_runtime/active_loops/` with per-loop state

### AO1.5 — Self-State Auto-Update
- After PASS: auto-update self_state.json (add milestone, update gap status)
- After FAIL: record failure in evidence log
- New gaps discovered during runs: auto-append to known_gaps
- Safety: all self_state.json writes logged to audit trail

### AO1.6 — Bounded External Actions
- Web research tasks (DDGS) in autonomous mode
- Server health checks (iLO read-only, WinRM status)
- No state-changing external actions without human approval
- All external actions logged with timestamps and results

---

## Risk / Safety Considerations

### Inherited from MS-FA1 (carry forward)
- RISK_001: MetaController dispatcher dormant bug — still dormant, observe-only
- Sandbox confinement — must remain strict
- No production file modifications without explicit approval
- API keys never printed or logged

### New MS-AO1 Risks

| Risk | Description | Mitigation |
|------|-------------|------------|
| AO1-R1 | Infinite autonomous loop | Hard iteration budget per goal (default 3). Global daily budget (default 20). Manual kill switch. |
| AO2-R2 | Auto-approval too permissive | Risk classifier must be conservative. Default: MEDIUM requires approval. Operator can relax. |
| AO1-R3 | Self-state corruption from auto-writes | All self_state.json writes are atomic (write temp, validate JSON, rename). Pre-write backup. |
| AO1-R4 | Goal queue explosion | Max queue size (default 10). Dedup by goal hash. Stale goals auto-expire (24h). |
| AO1-R5 | Rate limit exhaustion (OpenRouter) | Global rate limiter across all parallel loops. Backoff on 429. Daily token budget. |
| AO1-R6 | Cascading failures from auto-retry | Each retry must use a different strategy. Same strategy repeated = escalate to human. |

### Governance Principles (non-negotiable)
1. **Foundation.md elv:** meglévő modulokat összekötjük, nem helyettesítjük
2. **Governance first:** safety gates before capability expansion
3. **Evidence first, conclusion second:** all autonomous decisions logged
4. **Human override always available:** kill switch, pause, manual review
5. **No production changes without explicit approval:** sandbox remains the default boundary

---

## Open Questions Before Starting

1. **Auto-approval threshold:** What risk level should be auto-approved by default? (Conservative: none. Moderate: LOW only. Aggressive: LOW + MEDIUM.)
2. **Daily budget:** How many autonomous runs per day before requiring human check-in? (Proposed: 10-20.)
3. **Goal sources:** Should MS-AO1 only use self_state.json gaps, or also Organism proposals, or also external triggers (email, webhooks)?
4. **Self-state write authority:** Should the system be allowed to mark gaps as RESOLVED autonomously, or only add new evidence?
5. **Kill switch design:** File-based flag? CLI command? Both?
6. **First real test:** Should AO1.1 be tested with a known-safe goal (like generating a report) before attempting any gap resolution?
7. **Relationship to FEAT_001 CodeAgent:** MS-AO1 and CodeAgent overlap in self-modification capability. Should they be merged or kept separate?
8. **Operator notification:** How should the system notify the operator of autonomous activity? (File-based log? Email? UI?)

---

## What MS-AO1 is NOT

- NOT full AGI or unrestricted autonomy
- NOT production-deployable without human oversight
- NOT a replacement for the Interactive Layer
- NOT a system that modifies its own code without explicit governance approval
- NOT a system that makes financial decisions or interacts with external APIs beyond read-only research

---

## Estimated Effort

| Milestone | Complexity | Estimated Cline Sessions |
|-----------|-----------|-------------------------|
| AO1.1 Goal Discovery | Low | 1-2 |
| AO1.2 Risk Classifier | Medium | 2-3 |
| AO1.3 Self-Correcting Loop | Medium | 2-3 |
| AO1.4 Parallel Loops | High | 3-4 |
| AO1.5 Self-State Auto-Update | Medium | 2-3 |
| AO1.6 Bounded External Actions | Medium | 2-3 |
| **Total** | | **12-18 sessions** |

---

## Recommended Starting Point

Begin with AO1.1 (Goal Discovery) as a READ-ONLY phase. No autonomous execution yet — just prove the system can generate a valid, prioritized goal queue from existing self_state.json data. This is zero-risk and validates the foundation for everything else.

---

*Scope draft generated 2026-05-27. Awaiting operator review before any implementation begins.*