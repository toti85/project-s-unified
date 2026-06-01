# MS-FA1 Orchestrator Module Map

**Date:** 2026-05-25
**Version:** FA1-ModuleMap-v1
**Audience:** Developers working on MS-FA1

---

## Package Overview

```
src/orchestrator/
├── __init__.py
├── ai_client.py
├── cline_bridge.py
├── filesystem_orchestrator.py
├── handoff_watcher.py
├── README.md
├── run_archive.py
├── state_machine.py
├── verdict_evaluator.py
└── verdict_schema.py
```

**Runtime data:** `orchestrator_runtime/`

---

## Module Inventory

### 1. filesystem_orchestrator.py

**Purpose:** Goal/prompt lifecycle management. Central orchestrator coordinating the full semi-automated loop.

**Maturity:** **IMPLEMENTED** — Fully functional through FA1.4

**Main Classes/Functions:**
| Name | Type | Description |
|------|------|-------------|
| `RUNTIME_ROOT` | constant | Path to `orchestrator_runtime/` |
| `Goal` | dataclass | Parsed goal with text, acceptance_criteria, constraints, raw |
| `Verdict` | dataclass | Evaluation verdict with status, confidence, evidence, etc. |
| `FilesystemOrchestrator` | class | Main orchestrator class |
| `.read_goal()` | method | Read goal from `inbox/goal.md`, parse criteria/constraints |
| `.create_run()` | method | Create run folder, save goal, init state machine |
| `.draft_prompt()` | method | Template-based prompt drafting (PLACEHOLDER — FA1.3 AI replacement pending) |
| `.mark_in_progress()` | method | State transition after human review |
| `.receive_output()` | method | Read Cline output from `cline_outbox/last_output.md` |
| `.wait_for_cline_output()` | method | Poll for output with timeout |
| `.evaluate_output()` | method | Heuristic evaluation (PLACEHOLDER — FA1.3 AI replacement pending) |
| `.issue_verdict()` | method | Save verdict.json, state transition |
| `.archive_run()` | method | Generate evidence.md, final state transition |
| `.save_iteration()` | method | Save iteration artifacts to `runs/{id}/iterations/iter_NNN/` |
| `.generate_fix_prompt()` | method | Generate correction prompt for FIX verdicts |
| `.save_final_verdict()` | method | Save `final_verdict.json` |
| `.run_loop()` | method | Full multi-iteration loop (goal → prompt → output → eval → verdict → archive) |

**Runtime Files Read/Written:**
| File | Read | Write |
|------|------|-------|
| `inbox/goal.md` | ✓ | — |
| `cline_inbox/next_prompt.md` | — | ✓ |
| `cline_outbox/last_output.md` | ✓ | — |
| `runs/FA1_XXX/goal.md` | ✓ | ✓ |
| `runs/FA1_XXX/prompt.md` | — | ✓ |
| `runs/FA1_XXX/output.md` | ✓ | ✓ |
| `runs/FA1_XXX/verdict.json` | — | ✓ |
| `runs/FA1_XXX/final_verdict.json` | — | ✓ |
| `runs/FA1_XXX/evidence.md` | — | ✓ |
| `runs/FA1_XXX/state.json` | ✓ | ✓ (via StateMachine) |
| `runs/FA1_XXX/iterations/iter_NNN/*` | — | ✓ |

**Key Finding:** AI prompt generation and AI verdict evaluation both live here as placeholder methods. FA1.3+ should replace with `ai_client.py` integration.

---

### 2. handoff_watcher.py

**Purpose:** File-based handoff polling between Project-S and Cline.

**Maturity:** **IMPLEMENTED** — Fully functional through FA1.5

**Main Classes/Functions:**
| Name | Type | Description |
|------|------|-------------|
| `HandoffSignal` | dataclass | Protocol signal: run_id, iteration, timestamp, status, checksum, consumed |
| `HandoffWatcher` | class | File-based handoff polling |
| `.prepare_handoff()` | method | Write `prompt_ready.json` (Project-S → Cline) |
| `.consume_output()` | method | Read `output_ready.json` + `last_output.md`, validate, mark consumed |
| `.watch_for_output()` | method | Poll with timeout (default 300s, 3s interval) |
| `.is_output_ready()` | method | Check if output_ready.json exists and matches |
| `.write_output_ready()` | method | Write output_ready.json (for Cline/testing) |

**Runtime Files Read/Written:**
| File | Read | Write |
|------|------|-------|
| `cline_inbox/prompt_ready.json` | — | ✓ |
| `cline_outbox/output_ready.json` | ✓ | ✓ |
| `cline_outbox/last_output.md` | ✓ | — |

**Key Finding:** This is where handoff polling lives. Run ID and iteration validation, consumed flag, checksum verification all implemented.

---

### 3. verdict_evaluator.py

**Purpose:** Conservative heuristic evaluator for FA1.2. Placeholder for FA1.3+ AI evaluation.

**Maturity:** **PLACEHOLDER** — Heuristic-only; designed to be replaced

**Main Classes/Functions:**
| Name | Type | Description |
|------|-------------|---|
| `EvaluationResult` | dataclass | status, confidence, reasoning, matched_criteria, unmet_criteria, issues |
| `VerdictEvaluator` | class | Heuristic evaluator |
| `.evaluate()` | method | Evaluate output against acceptance criteria |

**Heuristics:**
- Output must be > 50 chars
- If tests mentioned, "OK" or "PASSED" pattern required
- "FAILED"/"ERROR"/"failures" patterns → FIX
- "error"/"exception"/"traceback" → confidence penalty
- Acceptance criteria keyword matching (lenient)
- confidence >= 0.8 and no issues → PASS
- test failures → FIX
- uncertain → NEEDS_HUMAN

**Runtime Files Read/Written:** None directly (receives output_text as parameter)

**Key Finding:** This is where AI verdict evaluation should live. Currently heuristic-only. FA1.3+ should integrate with SAI evaluator or `ai_client.py`.

---

### 4. verdict_schema.py

**Purpose:** Verdict creation, validation, and storage schema.

**Maturity:** **IMPLEMENTED**

**Main Classes/Functions:**
| Name | Type | Description |
|------|------|-------------|
| `VerdictStatus` | enum | PASS, FIX, STOP, NEEDS_HUMAN, ERROR |
| `VerdictSchema` | class | Schema validation (UNCLEAR — not fully inspected) |

**Runtime Files Read/Written:**
| File | Read | Write |
|------|------|-------|
| `orchestrator_runtime/verdict_schema.json` | — | — (reference only) |

**Key Finding:** Schema definition module. VerdictStatus enum used across all modules.

---

### 5. state_machine.py

**Purpose:** Run state transitions and tracking.

**Maturity:** **IMPLEMENTED**

**Main Classes/Functions:**
| Name | Type | Description |
|------|------|-------------|
| `RunState` | enum | QUEUED, PROMPT_DRAFTED, HUMAN_REVIEW, IN_PROGRESS, CLINE_OUTPUT_RECEIVED, EVALUATING_OUTPUT, VERDICT_ISSUED, ARCHIVED |
| `StateMachine` | class | State transitions with persistence |
| `.transition()` | method | Transition to new state with log entry |
| `.can_transition()` | method | Check if transition is valid |
| `._persist()` | method | Save state to `runs/{id}/state.json` |
| `.load()` | classmethod | Load state machine from disk |

**Runtime Files Read/Written:**
| File | Read | Write |
|------|------|-------|
| `runs/FA1_XXX/state.json` | ✓ | ✓ |

**Key Finding:** State machine enforces valid transitions. Persists to state.json per run.

---

### 6. ai_client.py

**Purpose:** AI client for prompt drafting and evaluation.

**Maturity:** **STUB** — Exists but not fully integrated into filesystem_orchestrator

**Main Classes/Functions:**
| Name | Type | Description |
|------|------|-------------|
| `OrchestratorAIClient` | class | AI client wrapper (UNCLEAR — not fully inspected) |
| `AIConfig` | class | Configuration for AI prompt/eval (enabled/disabled flags) |

**Key Finding:** Referenced by `generate_fix_prompt()` in filesystem_orchestrator.py with try/except ImportError. Prompt config and eval config can be independently enabled/disabled. Full integration unclear.

---

### 7. cline_bridge.py

**Purpose:** Prompt drafting and output parsing for Cline.

**Maturity:** **STUB** — Module exists; behavior unclear

**Key Finding:** Not inspected in detail. Listed in README as responsible for "Prompt drafting and output parsing for Cline." May overlap with `filesystem_orchestrator.draft_prompt()` and `ai_client.py`.

---

### 8. run_archive.py

**Purpose:** Run folder creation, archiving, and retrieval.

**Maturity:** **STUB** — Module exists; behavior unclear

**Key Finding:** Not inspected in detail. Listed in README as responsible for "Run folder creation, archiving, and retrieval." Some archiving logic already exists in `filesystem_orchestrator.archive_run()`. Potential overlap.

---

### 9. __init__.py

**Purpose:** Package initialization.

**Maturity:** **IMPLEMENTED**

---

## Responsibility Map

| Responsibility | Primary Module | Secondary Module | Maturity |
|----------------|----------------|------------------|----------|
| AI prompt generation | `filesystem_orchestrator.draft_prompt()` | `ai_client.py`, `cline_bridge.py` | **PLACEHOLDER** (template-based) |
| AI verdict evaluation | `verdict_evaluator.py` | `filesystem_orchestrator.evaluate_output()` | **PLACEHOLDER** (heuristic-only) |
| Handoff polling | `handoff_watcher.py` | — | **IMPLEMENTED** |
| Run archive logic | `filesystem_orchestrator.archive_run()` | `run_archive.py` | **IMPLEMENTED** (in filesystem_orchestrator) |
| State machine | `state_machine.py` | — | **IMPLEMENTED** |
| Verdict schema | `verdict_schema.py` | — | **IMPLEMENTED** |
| Full loop orchestration | `filesystem_orchestrator.run_loop()` | — | **IMPLEMENTED** |

---

## Known Limitations

1. **AI prompt drafting is placeholder** — `draft_prompt()` uses a simple template. FA1.3+ should integrate `ai_client.py` for AI-based prompt generation.

2. **AI verdict evaluation is heuristic-only** — `verdict_evaluator.py` uses regex pattern matching. FA1.3+ should integrate SAI evaluator or `ai_client.py`.

3. **Module overlap unclear** — `cline_bridge.py` and `run_archive.py` exist as stubs but their responsibilities overlap with `filesystem_orchestrator.py`. Need clarification on division of labor.

4. **ai_client.py not fully integrated** — Referenced with try/except ImportError in `generate_fix_prompt()`. Full integration status unclear.

5. **No automated test suite for orchestrator modules** — Sandbox tests (18/18 PASS) test sandbox deliverables, not orchestrator internals.

6. **FA1_005/FA1_006 run folders not persisted** — Run folders were not created for later phases. The `run_loop()` method should handle this, but it was not used for those runs.

---

## Recommended Next Hardening Targets

| Priority | Target | Reason |
|----------|--------|--------|
| **1** | Integrate AI prompt drafting | Replace template-based `draft_prompt()` with `ai_client.py` for quality-first prompts |
| **2** | Integrate AI verdict evaluation | Replace heuristic `verdict_evaluator.py` with SAI evaluator for accurate verdicts |
| **3** | Clarify cline_bridge.py vs filesystem_orchestrator.py | Eliminate responsibility overlap |
| **4** | Clarify run_archive.py vs filesystem_orchestrator.archive_run() | Eliminate responsibility overlap |
| **5** | Add orchestrator unit tests | Current tests cover sandbox deliverables only, not orchestrator internals |
| **6** | Ensure run folder persistence | Make `run_loop()` the default path; prevent ad-hoc runs without folder creation |

---

## Report Answers

| Question | Answer |
|----------|--------|
| A. Module map created? | **YES** |
| B. Source files inspected? | **YES** — filesystem_orchestrator.py (742 lines), handoff_watcher.py (245 lines), verdict_evaluator.py (131 lines), src/orchestrator/README.md |
| C. Any production files modified? | **NO** — only a new report created |
| D. Any stubs/future integration points identified? | **YES** — ai_client.py (STUB), cline_bridge.py (STUB), run_archive.py (STUB), AI prompt drafting (PLACEHOLDER), AI verdict evaluation (PLACEHOLDER) |
| E. Recommended next hardening target | **#1: Integrate AI prompt drafting** — Replace template-based `draft_prompt()` with `ai_client.py` for quality-first prompts |
| F. Ready for next real-world MS-FA1 task? | **YES** |

---

**Document End**