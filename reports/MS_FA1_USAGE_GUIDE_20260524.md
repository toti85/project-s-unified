# MS-FA1 Usage Guide

**Date:** 2026-05-25
**Version:** FA1-UsageGuide-v1
**Audience:** Project-S operator (human)

---

## What MS-FA1 Is

MS-FA1 is a **controlled filesystem orchestration pipeline** that allows Project-S to coordinate Cline through file-based handoff signals. It is a manual-loop tool: a human reviews every step.

**What it does:**
- Project-S drafts a task goal and a ready-to-copy Cline prompt
- Human reviews the prompt
- Human copies the prompt to Cline
- Cline executes the task in a sandbox
- Cline writes output back to a designated outbox
- Project-S evaluates the output and issues a verdict
- Human reviews the verdict before the next iteration

**What it is NOT:**
- **NOT full autonomy** — human is in the loop at every step
- **NOT UI automation** — no browser or desktop automation
- **NOT automatic Cline triggering** — human copies prompts manually
- **NOT production auto-editing** — Phase 1 restricts Cline to sandbox only

---

## Folder Structure

```
C:\ProjectS-Unified\orchestrator_runtime\
├── inbox\
│   └── goal.md                  # Human/Project-S writes the goal here
├── cline_inbox\
│   ├── next_prompt.md           # Ready-to-copy prompt for Cline
│   └── prompt_ready.json        # Signal: prompt is ready (run_id, iteration, checksum)
├── cline_outbox\
│   ├── last_output.md           # Cline writes execution output here
│   └── output_ready.json        # Signal: output is ready (run_id, iteration, consumed flag)
├── runs\
│   ├── FA1_001\                 # One folder per run
│   │   ├── goal.md
│   │   ├── prompt.md
│   │   ├── output.md
│   │   ├── evidence.md
│   │   ├── state.json
│   │   └── verdict.json
│   └── ...
├── logs\                        # Execution logs
├── reports\                     # Generated reports
├── sandbox\                     # Isolated workspace for Cline
│   ├── md_lister.py
│   ├── test_md_lister.py
│   └── ...
├── config.json
├── verdict_schema.json
└── README.md
```

**Code lives at:** `src/orchestrator/` (handoff_watcher.py, state_machine.py, verdict_evaluator.py, etc.)

---

## How to Run a Task — Step by Step

### Step 1: Define the Goal

Write the task goal in `orchestrator_runtime/inbox/goal.md`.

Example:
```
Create a Python script that counts CSV data rows (excluding header) with 3 unit tests.
Work only in orchestrator_runtime/sandbox/.
```

### Step 2: Draft the Prompt

Project-S (or you manually) creates a ready-to-copy prompt in `orchestrator_runtime/cline_inbox/next_prompt.md`.

The prompt must include:
- Task description
- Allowed sandbox directory (`orchestrator_runtime/sandbox/`)
- Forbidden paths (no Project-S production files, no config, no server files)
- Required deliverables (script + tests)
- Test instructions
- Output location (`orchestrator_runtime/cline_outbox/last_output.md`)

### Step 3: Human Review

**Read `next_prompt.md` carefully before proceeding.**

Check:
- Does the task stay within sandbox?
- Are forbidden paths clearly stated?
- Are deliverables specific?
- Is the output location correct?

If anything is wrong, edit the prompt before continuing.

### Step 4: Copy Prompt to Cline

Copy the contents of `orchestrator_runtime/cline_inbox/next_prompt.md` into Cline.

Also reference `orchestrator_runtime/cline_inbox/CLINE_HANDOFF_INSTRUCTIONS.md` so Cline knows the full protocol.

### Step 5: Cline Executes

Cline:
1. Reads the prompt
2. Works **only** in `orchestrator_runtime/sandbox/`
3. Creates the deliverables (e.g., script + tests)
4. Runs the tests
5. Writes final report to `orchestrator_runtime/cline_outbox/last_output.md`
6. Creates `orchestrator_runtime/cline_outbox/output_ready.json` with:
   ```json
   {
     "run_id": "FA1_XXX",
     "iteration": 1,
     "timestamp": "ISO 8601",
     "status": "ready",
     "checksum": "first 16 chars of SHA-256 of last_output.md"
   }
   ```

### Step 6: Project-S Evaluates

Project-S reads `cline_outbox/last_output.md` and evaluates:
- Were all deliverables created?
- Did tests pass?
- Were safety rules followed?
- Were any files outside sandbox modified?

### Step 7: Verdict Issued

A verdict is written to `orchestrator_runtime/runs/FA1_XXX/verdict.json`:

```json
{
  "run_id": "FA1_XXX",
  "goal": "Task description",
  "status": "PASS",
  "confidence": 0.95,
  "summary": "Human-readable verdict",
  "evidence_files": ["paths/to/evidence"],
  "files_changed": ["paths/to/changed/files"],
  "tests_run": ["test_name: PASS"],
  "risks": [],
  "next_action": "Proceed to next task",
  "created_at": "ISO 8601"
}
```

### Step 8: Human Reviews Verdict

Read the verdict. If satisfied, archive the run and proceed. If not, decide whether to:
- Request a fix (create a new prompt with corrections)
- Escalate to NEEDS_HUMAN
- Stop the run

---

## Handoff Protocol Signals

### prompt_ready.json

**Location:** `orchestrator_runtime/cline_inbox/prompt_ready.json`

**Purpose:** Signals that a prompt is ready for Cline to consume.

**Format:**
```json
{
  "run_id": "FA1_XXX",
  "iteration": 1,
  "timestamp": "ISO 8601",
  "status": "ready",
  "checksum": "first 16 chars of SHA-256 of next_prompt.md"
}
```

**Rules:**
- Created when prompt is drafted
- `status` changes to `"consumed"` after Cline reads it
- Prevents re-processing of the same prompt

### output_ready.json

**Location:** `orchestrator_runtime/cline_outbox/output_ready.json`

**Purpose:** Signals that Cline's output is ready for Project-S to evaluate.

**Format:**
```json
{
  "run_id": "FA1_XXX",
  "iteration": 1,
  "timestamp": "ISO 8601",
  "status": "ready",
  "checksum": "first 16 chars of SHA-256 of last_output.md",
  "consumed": false
}
```

**Rules:**
- Created by Cline after writing `last_output.md`
- `consumed` flag set to `true` after Project-S reads it
- Prevents re-evaluation of the same output
- Run ID and iteration must match or the output is rejected

---

## Verdict Statuses

| Status | Meaning | Action |
|--------|---------|--------|
| **PASS** | Task completed successfully, all criteria met | Archive run, proceed to next task |
| **FIX** | Task mostly complete, minor fixes needed | Create fix prompt, retry |
| **STOP** | Task failed fundamentally | Stop pipeline, investigate root cause |
| **NEEDS_HUMAN** | Human judgment required | Human must decide next action |
| **ERROR** | Unexpected error in pipeline | Investigate error, fix pipeline |

---

## When NEEDS_HUMAN Triggers

Use `NEEDS_HUMAN` when:
- The task requires a decision only a human can make
- Safety policy ambiguity exists
- Confidence is below 0.5
- The output quality is unclear
- External factors (network, permissions) block completion

---

## Safety Rules — What NOT to Do

| Rule | Explanation |
|------|-------------|
| **No production files** | Cline may not modify files in `src/core/`, `interactive_layer/`, or other Project-S production paths during Phase 1 |
| **No config changes** | No router, server, or environment config changes without explicit human approval |
| **No network calls** | Sandbox tasks must not require external network access |
| **No autonomy claims** | MS-FA1 is controlled orchestration, not full autonomy |
| **Human review required** | Every prompt must be reviewed before sending to Cline |
| **Verdict required** | Every run must produce a verdict before the next run starts |
| **Sandbox-only (Phase 1)** | Cline works only in `orchestrator_runtime/sandbox/` |

---

## How to Run a Safe Sandbox Task

1. **Define goal** in `inbox/goal.md`
2. **Draft prompt** in `cline_inbox/next_prompt.md` with explicit sandbox-only constraint
3. **Review prompt** — verify sandbox path, forbidden paths, deliverables
4. **Copy to Cline** — include CLINE_HANDOFF_INSTRUCTIONS.md reference
5. **Wait for output** — Cline writes to `cline_outbox/last_output.md`
6. **Evaluate** — check deliverables, tests, safety compliance
7. **Issue verdict** — write to `runs/FA1_XXX/verdict.json`
8. **Review verdict** — human approves before next iteration

---

## Run ID Convention

Format: `{PHASE}_{SEQ:3d}`

Examples:
- `FA1_001` — First run of FA1 phase
- `FA1_007` — Next run after FA1_006
- `FA2_001` — First run of FA2 phase

---

## Quick Reference

| Action | File/Path |
|--------|-----------|
| Write goal | `orchestrator_runtime/inbox/goal.md` |
| Read prompt | `orchestrator_runtime/cline_inbox/next_prompt.md` |
| Cline instructions | `orchestrator_runtime/cline_inbox/CLINE_HANDOFF_INSTRUCTIONS.md` |
| Cline output | `orchestrator_runtime/cline_outbox/last_output.md` |
| Run artifacts | `orchestrator_runtime/runs/FA1_XXX/` |
| Verdict schema | `orchestrator_runtime/verdict_schema.json` |
| Design doc | `reports/MS_FA1_FILESYSTEM_AUTOMATION_PIPELINE_DESIGN_20260524.md` |
| Evidence index | `reports/MS_FA1_EVIDENCE_INDEX_20260524.md` |

---

## Report Answers

| Question | Answer |
|----------|--------|
| A. Usage guide created? | **YES** |
| B. Source files inspected? | `src/orchestrator/README.md`, `orchestrator_runtime/README.md`, `CLINE_HANDOFF_INSTRUCTIONS.md`, `MS_FA1_EVIDENCE_INDEX_20260524.md` |
| C. Any production files modified? | **NO** — only a new report created |
| D. Any unclear commands found? | **NO** — all commands derived from existing documentation |
| E. Ready for next real-world MS-FA1 task? | **YES** |

---

**Document End**