# MS-AO3 Scope Draft — 2026-05-27

## Production Readiness Requirements

### AO3.1: FA1 Orchestrator + AO2 Governance Integration
- Bridge runner script for Project-S to consume Copilot output from cline_outbox/
- Full pipeline consumption validation (currently NOT_VALIDATED)
- End-to-end handoff protocol with governance gates
- Status: Protocol unification COMPLETE, integration NOT_VALIDATED

### AO3.2: End-to-End Autonomous Run with Real Goal
- Real goal processed through full governance stack
- Kill switch + budget checks before each goal
- Batch processing with dry_run validation
- Status: 1 of 7 hardening tests validated (TEST_1)
- RISK_008 ACTIVE: Cline simulated PASS reflex requires human coordination

### AO3.3: Monitoring Dashboard
- Real-time batch run status
- Kill switch state visualization
- Budget consumption tracking
- Notification history viewer
- Status: NOT STARTED

## Risks and Open Questions

### Active Risks
- **RISK_008**: Cline simulated PASS reflex — all e2e tests must be human-coordinated
- **RISK_001**: MetaController dispatcher sync bug (DORMANT but monitored)

### Open Questions
1. DL380 OS: Windows Server or Proxmox migration?
2. meta_evidence.jsonl (104.7 MB) migration decision pending
3. Bridge runner: who triggers executor — human or automated?
4. Monitoring dashboard: CLI-only or web-based?

### Dependencies
- MS-AO2 COMPLETE (governance stack operational)
- MS-FA1 COMPLETE (filesystem automation pipeline)
- FA1 handoff protocol v1 validated
- 6 remaining hardening tests (TEST_2-7) need real executor

## Milestones to Complete MS-AO3
1. Bridge runner script (Project-S consumes Copilot output)
2. 6 hardening tests with real executor (human-coordinated)
3. Full pipeline consumption validation
4. Monitoring dashboard MVP