# MS-FA1: Filesystem Automation Pipeline Design

**Date:** 2026-05-24  
**Version:** FA1.0 (Design + Scaffold)  
**Status:** Phase 0 Complete  
**Model Policy:** Quality-First (OpenRouter Qwen3.6 baseline)

---

## 1. Goal

Create a safe, filesystem-based automation pipeline that allows Project-S to draft tasks and Cline to execute them in a controlled loop. This is **not** full autonomy, **not** UI automation, and **not** production auto-editing.

The pipeline enables:
- Project-S drafts a goal/spec into `inbox/goal.md`
- Project-S drafts a ready-to-copy Cline prompt into `cline_inbox/next_prompt.md`
- Human copies prompt to Cline
- Cline executes, writes output to `cline_outbox/last_output.md`
- Project-S evaluates, produces verdict, logs run
- Human reviews before next iteration

---

## 2. Non-Goals

- **NOT autonomy:** No automatic triggering of Cline from Project-S
- **NOT UI automation:** No browser/desktop automation
- **NOT production auto-editing:** No automatic modifications to Project-S production files in Phase 1
- **NOT model switching:** OpenRouter Qwen3.6 remains Cline baseline; local models tested later via parity/fallback
- **NOT CI/CD integration:** This is a manual-loop pipeline for now

---

## 3. Folder Structure

```
C:\ProjectS-Automation\
├── inbox\
│   └── goal.md              # Human/Project-S writes the goal here
├── cline_inbox\
│   └── next_prompt.md       # Ready-to-copy prompt for Cline
├── cline_outbox\
│   └── last_output.md       # Cline writes execution output here
├── runs\                    # One folder per run: runs/FA1_001/, runs/FA1_002/, etc.
│   └── FA1_001\
│       ├── state.md         # Run state machine log
│       ├── verdict.json     # Verdict for this run
│       └── notes.md         # Human/evaluator notes
├── logs\                    # Execution logs, timestamps, model versions
├── reports\                 # Generated reports (design, audit, summary)
├── sandbox\                 # Isolated workspace for Cline to work in
│   └── SANDBOX_TASK_001.md  # First sandbox task spec
├── verdict_schema.json      # JSON schema for verdicts
└── README.md                # Pipeline documentation
```

---

## 4. Run State Machine

Each run progresses through the following states:

```
[QUEUED] → [PROMPT_DRAFTED] → [HUMAN_REVIEW] → [IN_PROGRESS]
     → [EVALUATING] → [VERDICT_ISSUED] → [ARCHIVED]
```

| State | Description | Actor |
|-------|-------------|-------|
| `QUEUED` | Goal defined, awaiting prompt draft | Human/Project-S |
| `PROMPT_DRAFTED` | Cline prompt written to `cline_inbox/next_prompt.md` | Project-S |
| `HUMAN_REVIEW` | Human reviews prompt before sending to Cline | Human |
| `IN_PROGRESS` | Cline is executing the task | Cline |
| `EVALUATING` | Project-S evaluates Cline's output | Project-S |
| `VERDICT_ISSUED` | Verdict written, run complete | Project-S |
| `ARCHIVED` | Run folder archived, ready for next | Human |

State transitions are logged in `runs/{run_id}/state.md`.

---

## 5. Verdict Schema

See `verdict_schema.json` for the full JSON schema.

| Field | Type | Description |
|-------|------|-------------|
| `run_id` | string | Unique run identifier (e.g., `FA1_001`) |
| `goal` | string | What was the task trying to achieve |
| `status` | enum | `PASS` / `FIX` / `STOP` / `NEEDS_HUMAN` / `ERROR` |
| `confidence` | float (0-1) | Evaluator confidence in the verdict |
| `summary` | string | Human-readable verdict summary |
| `evidence_files` | string[] | Paths to files that support the verdict |
| `files_changed` | string[] | Files modified during this run |
| `tests_run` | string[] | Tests executed and their outcomes |
| `risks` | string[] | Identified risks or concerns |
| `next_action` | string | Recommended next step |
| `created_at` | ISO 8601 | Timestamp of verdict |

### Status Definitions

| Status | Meaning |
|--------|---------|
| `PASS` | Task completed successfully, all criteria met |
| `FIX` | Task mostly complete, minor fixes needed (auto-retry OK) |
| `STOP` | Task failed fundamentally, stop pipeline |
| `NEEDS_HUMAN` | Human judgment required to proceed |
| `ERROR` | Unexpected error in pipeline execution |

---

## 6. Safety Policy

### Rule 1: Sandbox-First
Cline may only modify files under `C:\ProjectS-Automation\sandbox\` until Phase FA1.1 passes all acceptance criteria.

### Rule 2: No Production Files
No files in `C:\ProjectS-Unified\` production directories may be modified by Cline during sandbox tasks.

### Rule 3: No Config Changes
No router/server/config changes without explicit human approval in the run notes.

### Rule 4: No Network Calls
Sandbox tasks must not require external network access.

### Rule 5: Human-in-the-Loop
Every prompt must be reviewed by a human before being sent to Cline.

### Rule 6: Verdict Required
Every run must produce a verdict before the next run starts.

### Rule 7: Confidence Threshold
- `confidence >= 0.8`: Auto-approve next iteration
- `confidence 0.5-0.8`: Human review recommended
- `confidence < 0.5`: Human review required

---

## 7. First Sandbox Task

**Task:** SANDBOX_TASK_001 — Markdown File Lister

Create a small Python helper script inside the sandbox that:
- Lists all markdown files in a given folder
- Includes 3 unit tests
- Runs successfully with `pytest` or `unittest`

**Constraints:**
- Work only in `C:\ProjectS-Automation\sandbox\`
- No Project-S production files modified
- No config changes
- No network calls

---

## 8. Model Policy v1

| Role | Model | Rationale |
|------|-------|-----------|
| **Cline execution baseline** | OpenRouter Qwen3.6 | Proven quality with Project-S tasks |
| **Prompt drafting** | Best available strategic model / current Project-S | Quality-first approach |
| **Evaluation** | Best available evaluator model | Independent verdict quality |
| **Local Qwen3.6** | Parity/fallback tests (Phase FA2+) | Not forced in v1 |
| **Local Qwen2.5-Coder** | Parity/fallback tests (Phase FA2+) | Not forced in v1 |

**Decision:** Do NOT switch Cline to local model yet. Keep OpenRouter Qwen3.6 as baseline. Local models will be evaluated for parity in later phases.

---

## 9. Acceptance Criteria for Phase FA1.1

Phase FA1.1 (Manual Loop with Sandbox Task 001) is complete when:

- [x] Design document created
- [ ] Folder scaffold created
- [ ] Verdict schema created
- [ ] Sandbox task spec created
- [ ] Ready-to-copy Cline prompt created
- [ ] Human reviews and copies prompt to Cline
- [ ] Cline executes task in sandbox only
- [ ] Tests pass
- [ ] Cline writes output to `cline_outbox/last_output.md`
- [ ] Project-S evaluates output
- [ ] Verdict issued (expected: PASS or FIX)
- [ ] Run archived in `runs/FA1_001/`
- [ ] No production files modified
- [ ] Safety policy violations: 0

---

## Appendix A: Pipeline Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    MS-FA1 Pipeline Flow                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Human ──→ inbox/goal.md                                    │
│       ──→ reviews cline_inbox/next_prompt.md                │
│       ──→ reviews verdict                                   │
│                                                              │
│  Project-S ──→ cline_inbox/next_prompt.md                   │
│            ──→ evaluates cline_outbox/last_output.md         │
│            ──→ runs/FA1_XXX/verdict.json                     │
│                                                              │
│  Cline ──→ reads prompt (manual copy by human)              │
│        ──→ works in sandbox/ only                           │
│        ──→ writes cline_outbox/last_output.md               │
│                                                              │
│  Boundary Rules:                                             │
│  • Cline ≠ production files (Phase 1)                       │
│  • Every run ≠ verdict required                             │
│  • Confidence threshold ≠ auto-approve gate                 │
│                                                              │
└─────────────────────────────────────────────────────────────┤
```

---

## Appendix B: Run ID Convention

Format: `{PHASE}_{SEQ:3d}`

Examples:
- `FA1_001` — First run of FA1 phase
- `FA1_002` — Second run of FA1 phase
- `FA2_001` — First run of FA2 phase

---

**Document End**