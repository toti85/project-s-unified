# MS-FA1 Auto Mode v1 Policy

**Date:** 2026-05-26
**Version:** AutoMode-v1-Policy
**Status:** ACTIVE

---

## 1. Allowed Automated Actions

Auto Mode v1 permits the following actions **without human intervention**:

| Action | Scope | Conditions |
|--------|-------|------------|
| Goal reading | `inbox/goal.md` | File must exist and be non-empty |
| Run creation | `runs/FA1_XXX/` | Auto-generated run ID |
| Prompt drafting | `cline_inbox/next_prompt.md` | AI or deterministic template |
| Handoff signal | `cline_inbox/prompt_ready.json` | Must include run_id, iteration, checksum |
| Output polling | `cline_outbox/output_ready.json` | Validates run_id, iteration, consumed flag |
| Output evaluation | Heuristic or AI | Conservative PASS threshold |
| Verdict issuance | `runs/FA1_XXX/verdict.json` | Must match verdict schema |
| Run archiving | `runs/FA1_XXX/` → archived | Only on PASS verdict |
| Sandbox file creation | `sandbox/**` | Any file type within sandbox |
| Sandbox file modification | `sandbox/**` | Only files previously created in sandbox |
| Sandbox test execution | `sandbox/**` | pytest or unittest only |

## 2. Explicitly Forbidden Actions

The following actions are **never** permitted in Auto Mode v1:

| Action | Reason |
|--------|--------|
| Modifying `src/core/**` | Production code protection |
| Modifying `interactive_layer/**` | Interactive layer protection |
| Modifying `self_state.json` | State integrity protection |
| Modifying `router/`, `server/`, `network/` configs | Infrastructure protection |
| Modifying any file outside `orchestrator_runtime/sandbox/**` | Sandbox containment |
| File deletion or renaming | Data preservation |
| Git operations (commit, tag, push, pull, merge, rebase) | Version control integrity |
| External network calls | Network isolation |
| API requests outside OpenRouter | API scope limitation |
| Package installations | Dependency freeze |
| Runtime binary execution | Process isolation |
| Modifying orchestrator source code | Self-modification prevention |
| Modifying `.env.local` or API keys | Secret protection |

## 3. NEEDS_HUMAN Trigger Conditions

Auto Mode v1 **must** escalate to `NEEDS_HUMAN` when:

| Condition | Description |
|-----------|-------------|
| Production file change detected | Any file outside sandbox modified |
| Path escape attempt | Cline output references paths outside sandbox |
| Missing tests | Deliverable claims tests but none found |
| Test failures | Any test in output shows FAILED or ERROR |
| Ambiguous output | Output too short (<50 chars) or unclear |
| Confidence below threshold | Evaluator confidence < 0.5 |
| Safety policy violation | Any forbidden action detected |
| External network reference | Output mentions API calls or network access |
| Config change reference | Output mentions modifying config files |
| Verdict schema invalid | AI returns malformed verdict JSON |
| Run state machine error | Invalid state transition |
| max_iterations exceeded | Loop count exceeds configured limit |

## 4. max_iterations Limit

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `max_iterations` | 2 | Conservative limit for v1 |
| Config location | `orchestrator_runtime/config.json` | Centralized config |
| Override | CLI `--max-iterations` flag | Operator control |
| Behavior on exceed | STOP verdict, no auto-retry | Safety stop |

## 5. Safety Stop Conditions

Auto Mode v1 **immediately stops** on:

| Condition | Action |
|-----------|--------|
| STOP verdict issued | Halt loop, archive run, notify operator |
| State machine error | Halt loop, log error, require human |
| Filesystem write failure | Halt loop, log error, require human |
| Timeout exceeded | WAITING_FOR_CLINE, no false PASS |
| Stale output detected | Reject output, continue waiting |
| Consumed output re-read | Reject, continue waiting |
| Run ID mismatch | Reject output, continue waiting |
| Iteration mismatch | Reject output, continue waiting |
| Checksum mismatch | Warning only, continue evaluation |

## 6. Sandbox/Docs-Only Execution Rules

| Rule | Enforcement |
|------|-------------|
| All writes to `sandbox/**` only | CLI + HandoffWatcher validation |
| Read-only access to project root | No write permissions outside sandbox |
| No production code modifications | Forbidden paths list |
| No config modifications | Forbidden paths list |
| No state modifications | Forbidden paths list |
| Documentation assessment only | Task type restriction for v1 |
| Pure documentation pipeline | No runtime behavior changes |

---

**Document End**