# MS-FA1 Auto Mode v1 Operator Example

**Date:** 2026-05-26
**Version:** AutoMode-v1-Operator
**Status:** ACTIVE

---

## 1. How to Submit a High-Level Goal

**Step 1:** Write the goal to `inbox/goal.md`:

```markdown
Create a CSV counter helper in sandbox

- [ ] Create csv_counter.py
- [ ] Include 3 unit tests
```

**Step 2:** Run the CLI:

```bash
cd C:\ProjectS-Unified\src
python -m orchestrator.cli run-loop --auto --max-iterations 2
```

## 2. How Project-S Decomposes the Goal

**Input:** `inbox/goal.md` with acceptance criteria

**Process:**
1. `FilesystemOrchestrator.read_goal()` parses the markdown
2. Extracts text, acceptance criteria (lines starting with `- [ ]`), and constraints
3. Creates a new run folder: `runs/FA1_XXX/`
4. Saves goal text to `runs/FA1_XXX/goal.md`

**Example decomposition:**
```
Goal text: "Create a CSV counter helper in sandbox"
Acceptance criteria: ["Create csv_counter.py", "Include 3 unit tests"]
Constraints: []
```

## 3. How the Prompt is Routed to Cline

**Step 1: Prompt Drafting**

`FilesystemOrchestrator.draft_prompt(run_id, auto_mode=True)`:
- If AI enabled: calls `OrchestratorAIClient.draft_cline_prompt()`
- If AI disabled or fails: uses `_deterministic_prompt()`
- Validates prompt contains required safety sections

**Step 2: Write Prompt**

Prompt written to:
- `cline_inbox/next_prompt.md` — Full prompt text

**Step 3: Handoff Signal**

`HandoffWatcher.prepare_handoff(run_id, iteration, prompt)`:
- Writes `cline_inbox/prompt_ready.json` with:
  - `run_id`: "FA1_012"
  - `iteration`: 1
  - `timestamp`: ISO 8601
  - `checksum`: SHA-256 first 16 chars
  - `consumed`: false

**Step 4: Operator Action**

Operator copies `next_prompt.md` to Cline and executes.

## 4. How Output is Returned

**Cline writes:**
- `cline_outbox/last_output.md` — Execution output
- `cline_outbox/output_ready.json` — Signal with run_id, iteration, checksum

**Orchestrator polls:**
- `HandoffWatcher.watch_for_output(run_id, iteration, timeout)`
- Validates:
  - `run_id` matches current run
  - `iteration` matches expected
  - `consumed` is false
  - `output_ready.json` exists
  - Checksum matches (warning only)
- Sets `consumed=true` after reading
- Returns output text

## 5. How Verdict is Generated

**Step 1: Evaluate Output**

`FilesystemOrchestrator.evaluate_output(run_id)`:
- Loads goal, prompt, output from run folder
- If AI enabled: calls `OrchestratorAIClient.evaluate_cline_output()`
- If AI fails: falls back to `_heuristic_evaluate()`
- Returns `Verdict` object

**Step 2: Issue Verdict**

`FilesystemOrchestrator.issue_verdict(run_id, verdict)`:
- Saves verdict to `runs/FA1_XXX/verdict.json`
- Updates state machine

**Step 3: Archive or Continue**

- If `PASS`: `archive_run(run_id)` — run complete
- If `FIX` and iterations < max: generate fix prompt, repeat
- If `STOP` or `NEEDS_HUMAN`: halt, notify operator

## 6. Stop/Escalation Conditions

| Condition | Action |
|-----------|--------|
| `PASS` verdict | Archive run, complete |
| `FIX` verdict + iterations < max | Generate fix prompt, retry |
| `FIX` verdict + iterations >= max | STOP, notify operator |
| `STOP` verdict | Halt immediately, archive |
| `NEEDS_HUMAN` verdict | Halt, wait for operator |
| `ERROR` verdict | Halt, log error, require human |
| Timeout waiting for output | WAITING_FOR_CLINE, no false PASS |
| Stale output detected | Reject, continue waiting |
| Safety violation detected | STOP, notify operator |

---

**Document End**