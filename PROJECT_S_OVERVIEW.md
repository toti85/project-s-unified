# Project-S — Overview & Operating Guide

*Status snapshot for any AI agent (Claude, ChatGPT, Copilot, Cline, DeepSeek, Qwen) joining the work.*
*Last updated: 2026-05-23T10:00:00Z*
*Phase: production_stable — Interactive Layer v1 fully validated (GAP_026-031), MS-OQ1-E Direct Structure validated (12.9/15), DL380 staging proof achieved*
---

## 0. What this document is

This is a single-pass orientation file. Any AI reading it should understand:

1. What Project-S **is** (not what it aspires to be)
2. What state the system is in **today**
3. How the team works (multi-AI orchestration, roles)
4. What the current focus is (bounty hunting)
5. What infrastructure already exists vs what's planned
6. How to behave when asked to contribute

If you only read one section, read sections 1, 3, and 7.

---

## 1. What Project-S actually is

Project-S is a controlled autonomous AI system with a persistent file-based self-model. Not a chatbot wrapper. Not an agent framework clone. Not a "self-improving AI" in the marketing sense.

Concretely it is:

**A Python codebase** at `C:\ProjectS-Unified\` (~346 .py files, unified from two prior parallel codebases). The active execution path is **SuperIntelligentAI** (SAI) at `src/core/super_intelligent_ai.py`, which runs a three-phase pipeline (Strategic Planning → Tool Orchestration → Evaluation) with **MetaController** orchestrating multi-iteration goal execution via `use_meta_controller=True`.

**A persistent self-model** at `self_state.json` (~90KB JSON), structured as identity + current_state + model_policy + decisions_made (42+ entries) + milestones (31+ entries) + known_risks (7) + gaps_summary (31 gaps: 30 RESOLVED + 1 ACCEPTED). This is updated manually after every meaningful work session by an AI assistant under human supervision — it's a manually-curated record, **not** an auto-derived state. The "self-knowledge" is in the file system, not in the model weights.

**A Witness layer** that logs every task execution to `memory/intelligence/meta_evidence.jsonl` (403,000+ records). This is the audit trail. The hook fires after every SAI task completion and records source, tools used, success/failed status, and timestamps. The naming convention is messy (top-level `source` is hardcoded "agent_loop" for historical reasons, actual source is in `result.source`) but the data is intact.

**15 real tools** registered in `tools/tools/registry/` — file ops (search, content search, write), web ops (DDGS search, page fetch, scraper), browser automation (Playwright), system tools, PDF generator, Roblox Studio integration. The orchestrator (`smart_orchestrator.py`) supports multi-tool sequencing with output piping (GAP_015) and an **LLM synthesis step** (GAP_019): web_search + web_scraper output is synthesized by Qwen3.6-35B-A3B into a structured decision memo before file_writer writes the output.

**Browser automation capability — VERIFIED (2026-05-14):**
Browser automation is no longer only registered; it has been live-verified in the canonical SAI path. The Phase 1 planner now selects `browser_automation` after the GAP_021 tool-manifest fix. Live mission evidence: Chromium launched via Playwright/CDP, 3 real URLs visited (playwright.dev, github.com/browser-use/browser-use, docs.agentql.com/home), browser execution completed in 94.30s, final memo written (3505 bytes), verdict PASS 9/9. The only newly discovered residue is GAP_022 (evaluator JSON serialization for browser_use AgentHistoryList, low-priority, non-blocking).

**A Foundation document** at `PROJECT_S_FOUNDATION.md` (immutable, 2026-04-26 v1.0) that sets the principles: "Governance First, Autonomy Later" — controlled autonomy takes priority over open-ended self-direction.

What Project-S is NOT:
- It does NOT learn from past runs in the ML sense. Models are stateless API calls; the meta_evidence.jsonl is logged but never used for fine-tuning. The "learning" is human-curated pattern documentation, not model parameter updates.
- It does NOT self-develop. The FEAT_001 CodeAgent concept exists but is deferred. All code changes today are written by Cline, Copilot, or Continue agents under human direction.
- It is NOT a single agent. It's a Doer (SAI + MetaController via use_meta_controller=True) plus external agents (Cline, Copilot, Continue) plus several AI models routed via OpenRouter and direct APIs.

---

## 2. Current system state

**Phase:** production_stable

**Gaps:** 31 total. 30 RESOLVED. 1 ACCEPTED (GAP_007). 0 ACTIVE.

**Interactive Layer v1 — FULLY VALIDATED (2026-05-20):**
Interactive Layer v1 (`interactive_layer/` package) hardened through GAP_026–GAP_031. Control-flow (GAP_026–030) + interaction-grade prompt routing (GAP_031) all resolved. See GAP_031 section below for routing detail. Acceptance matrix: **8/8 PASS** (all route classes, all prompt types).

**MS-OQ1-E Direct Structure — VALIDATED (2026-05-23):**
Message-OQ1-E Direct Structure pattern validated at 12.9/15 (80% >= 12% threshold). Direct lightweight response routing confirmed for simple factual prompts without MetaController overhead.

**DL380 Server — STAGING PROOF ACHIEVED (2026-05-18):**
SHAYANSKA-DL380 (serial CZ3733LABY) proved Project-S can be reproduced outside the DEV laptop environment. Code transferred to `C:\ProjectS\project-s-code`, Python 3.12.9, Git, runtime dependencies installed, Interactive Layer starts, `/health` returns HTTP 200, OpenRouter/Qwen3 235B SAI calls reached live execution path. Server-side development intentionally paused. DEV master remains canonical. Final clean resync later after DEV-side hardening. NOT production.

**Most recent significant fixes (2026-05-14):**
- GAP_017: `WebSearchTool` replaced Google HTML scraper with DDGS (DuckDuckGo) backend — no API key required, bot-detection resistant
- GAP_018: False-success status after failed web search chain — covered by GAP_017 fix
- GAP_019: LLM synthesis step added to `smart_orchestrator.py` — web_search + web_scraper output synthesized by Qwen3.6 into structured decision memo (max_tokens=8000)
- GAP_020: SAI/MetaController truthfulness fix — 5 false-success paths patched (evaluator nested key, backup exception, execution history, has_output stub rejection, replan blocking); 40 regression tests
- GAP_021: Strategic planner browser_automation visibility — Phase 1 planning prompt now includes TOOL MANIFEST with explicit browser_automation selection guidance; 6 tests pass, live mission PASS 9/9

**Server Phase milestone (2026-05-15):**
- iLO script recovered from `project_s/infrastructure/ilo_controller.py`
- Read-only connectivity test: PASS (connect, get_system_info, get_power_state, get_health_summary)
- Server model: ProLiant DL380 Gen9, BIOS P89 v3.40 (08/29/2024)
- Redirect workaround exercised 3 times, essential for connectivity
- No state-changing commands issued

**Fresh-DB Interactive Layer user/session fix:**
`interactive_layer/main.py` — `get_or_create_user()` called before `create_mission()` in `/api/chat`. A fresh Interactive Layer database no longer fails session/mission creation due to missing user FK state. Already present in DEV master.

**Earlier significant fixes (2026-05-03 → 2026-05-04):**
- GAP_010: AgentLoop tool pipeline 6-layer fix
- GAP_015: Multi-tool sequencing with output piping in `smart_orchestrator.py`
- GAP_016: Evaluator context overflow truncation

- GAP_022: RESOLVED (2026-05-14) — Evaluator JSON serialization fix. `_sanitize_for_json()` recursive helper added to `src/core/evaluator.py`. Both `execution_result` and `context` sanitized before `json.dumps()`. 16 focused tests pass.

**GAP_023 (RESOLVED — 2026-05-14): browser_automation now receives a browser-scoped subtask in mixed pipelines.**
Fix: Added explicit `elif tool_name == "browser_automation":` branch in `_execute_single_tool` (smart_orchestrator.py). Detects mixed pipeline via `"Context from previous tools:"` separator; constructs scoped subtask (original mission capped 800 chars + browser-only role + strict constraints: no file write, no report generation). Dedicated browser missions pass through unchanged. Verified live: planner selected `['web_search', 'browser_automation', 'file_writer']`, scope isolation fired in both MetaController iterations (`1418 chars` vs `5452 chars`), browser navigated real pages without writing files. 9/9 unit tests + 23/23 total pass. Residual known issue: MetaController `timeout=120s` too short for full browser+synthesis pipelines (pre-existing; GAP_024 candidate).

**Architectural decisions (current):**
- AgentLoop ARCHIVED 2026-05-03. SAI is the sole active Doer pipeline.
- **MetaController** is active via SAI's `use_meta_controller=True` path in all live external missions. The *standalone MetaController dispatcher* remains dormant (RISK_001 applies there only).
- External observation hook in SAI — Witness layer's meta_evidence stream active.
- WorkflowEngine (LangGraph, 947 lines) present but unused.

**Model policy (2026-05-14, updated):**
- Synthesis (strategic memos): `qwen/qwen3.6-35b-a3b` — **verified runtime default** (code fix applied 2026-05-14, live-verified PASS 5/5 42.7s; explicit `_synthesis_model_override` still wins when set)
- Cognitive Phase 1: `qwen/qwen3-235b-a22b`
- Evaluator: `deepseek/deepseek-chat`
- max_tokens for synthesis: 8000

**Known risks (7 active, all documented):**
- RISK_001: MetaController *standalone dispatcher* can deadlock if reactivated — does NOT apply to SAI-integrated path
- RISK_005: "Production ready" audits historically unreliable; verify every claim with live test
- RISK_006: AgentLoop reactivation requires Phase 2 `_analyze_task` fix
- RISK_007: `web_analyzer` parameter mismatch (minor, non-blocking)
- (3 others, see self_state.json `known_risks`)

**One minor TODO:** TODO_001 — `MetaController.observe()` top-level `source` parameter (currently hardcoded "agent_loop"). 1-line fix, low priority.

**All gaps resolved:** 30 RESOLVED, 1 ACCEPTED, 0 ACTIVE. The system has no open gap items.

---

## 2b. Interactive Layer Interaction-Grade Routing — GAP_031 RESOLVED (2026-05-20)

**Root cause:** Ordinary prompt classes were misrouted into the heavy MetaController research/execution loop, causing: simple direct prompts to max_iters fail; internal-doc prompts to take 120s+ and fail; impossible-certainty prompts to agent-loop instead of giving truthful uncertainty; external research prompts to fall back into a generic loop.

**Fix:** Hybrid prompt-class-aware routing layer implemented in `interactive_layer/prompt_router.py`.

**Route taxonomy (6 classes):**

| Route Class | When used | Handler |
|---|---|---|
| `DIRECT_LIGHTWEIGHT_RESPONSE` | Simple factual / short-answer prompts | Direct LLM call, no MetaController |
| `TRUTHFUL_UNCERTAINTY_RESPONSE` | Impossible or unknowable certainty requested | Fixed truthful-uncertainty response |
| `INTERNAL_PROJECT_DOC_REASONING` | Questions about Project-S state, docs, gaps | File-grounded reasoning, no MetaController |
| `EXTERNAL_RESEARCH_SYNTHESIS` | "Find / search / research" prompts with web intent | DDGS web search → numbered synthesis |
| `FULL_AGENTIC_META_CONTROLLER` | Complex strategic / multi-step missions | Full SAI + MetaController pipeline |
| `CLARIFICATION_NEEDED` | Ambiguous / under-specified prompt | Clarification response |

**Hungarian normalization:** V1 requirement — accent-stripped prompt normalization for reliable pattern matching.

**Route metadata:** `route_type`, `route_confidence`, `route_rationale`, `route_matched_rules`, `route_llm_used`, `route_llm_model` — all persisted into mission records.

**EXTERNAL_RESEARCH_SYNTHESIS handler:** DDGS web search (30s timeout, up to 8 results), Hungarian→English query derivation, synthesized numbered-point answer. Truthful static fallback if DDGS returns no results. Always `COMPLETE` — never falls back to MetaController.

**Evidence:**
- Phase 1 (DIRECT/INTERNAL/TRUTHFUL): 22/22 unit tests PASS, 7/8 live acceptance
- Phase 2 (EXTERNAL_RESEARCH_SYNTHESIS): 31/31 unit tests PASS
- TEST_5 focused live: `route=EXTERNAL_RESEARCH_SYNTHESIS`, `state=COMPLETE`, `elapsed=4.4s`, 8 real web results
- **Full acceptance matrix: 8 PASS / 0 PARTIAL / 0 FAIL**

**Strategic implication:** Project-S now behaves more like a governed operator layer than a raw agent loop. It distinguishes: lightweight direct answers, truthful uncertainty, internal-doc reasoning, bounded external research, and full agentic missions.

---

## 3. How the team works — multi-AI orchestration

This is the operational reality, not aspirational design.

**Roles by AI:**

**Claude** (this conversation, claude.ai web/mobile) — strategic analysis, architecture reasoning, decision support, complex synthesis, code review at the system level. Used for sessions that involve weighing options, surfacing risks, writing prompts for other AIs. Anthropic API also accessible.

**ChatGPT** — secondary analysis, alternative framing, cross-validation of Claude's recommendations. Used in parallel for hard decisions. Sometimes catches things Claude misses (e.g., program-specific severity rubric corrections in bounty submissions).

**GitHub Copilot** (in VS Code) — direct in-editor code assistance, autocomplete, small refactors, file generation tasks where context is one or two files. Good at structured outputs (markdown templates, JSON updates).

**Cline** (VS Code extension via OpenRouter) — agentic coding tasks that require multi-step file operations, terminal commands, longer-running edits. Has its own session context and can plan multi-step tasks. Heavy lifter for non-trivial code work. Uses OpenRouter to access multiple models (Qwen3 235B, Claude Sonnet 4.5, DeepSeek V3, Qwen 2.5 Coder 32B).

**Continue** (VS Code extension via OpenRouter) — alternative to Cline, also configured with OpenRouter, used for quick file-level questions and edits.

**DeepSeek** — used historically for cross-validation, code review, alternative perspectives. Less active recently but available via OpenRouter.

**Qwen3 235B** — primary cognitive engine inside SAI Phase 1 (Strategic Planning). Routed through OpenRouter. Generates strategic_plan with recommended_tools list. **Note:** the newly-released **Qwen3.6-35B-A3B** (May 2026, MoE architecture, 35B total / 3B active, runs on 13-24GB VRAM locally, SWE-bench 73.4%) is a candidate for local replacement on the Tesla M60 GPU, but not yet integrated — see section 8.

**Operational pattern:**

1. Strategic decision needed → Claude session (with full context loaded via project files or pasted state)
2. Claude writes a prompt for Cline or Copilot describing the concrete task
3. Cline/Copilot executes the prompt in VS Code, returns a structured report
4. Claude reviews the report, decides next step, writes next prompt OR closes the loop
5. After significant changes, self_state.json is updated (by Cline/Copilot under Claude's prompt direction)

**The human role:** operator. Reviews Claude's recommendations, makes final calls on contested decisions, executes the AI-prompted tasks in VS Code, copies outputs back to Claude. Does not write code directly except for very small tweaks. Does not architect the system independently; rather, evaluates and approves architectural proposals from Claude/ChatGPT.

**This is genuinely how it works.** It's not "human delegates to one AI"; it's "human moderates 4-6 AIs that have different strengths and different access patterns."

---

## 4. Current focus: external research missions and SAI reliability

Project-S has reached production_stable and confirmed **external research capability** on 2026-05-14 (see section 10). The current Project-S core focus is:

**1. External research mission execution:**
SAI + MetaController complete full external research tasks: web_search → web_scraper → LLM synthesis → file_writer. Live missions completed: B2 local model research memo, 30-day opportunity scan. Synthesis quality verified with Qwen3.6-35B-A3B (13744 bytes, 10/10 sections).

**2. SAI reliability and truthfulness:**
GAP_020 fix established the truthfulness gate (40 regression tests, 4/4 live scenarios). The next priority is ensuring additional mission types produce accurate success/partial/failure signals in the Witness trail.

**3. Evidence-grounded execution:**
Every mission result is logged to `meta_evidence.jsonl` via the Witness hook. `self_state.json` is updated manually after each session. The evidence trail is ground truth — not claimed status.

**4. Next capability priorities:**
- **Interactive output quality diagnosis** from the remaining 4 failed UI prompts in the post-GAP_029 live test rerun
- Continue higher-value external missions with verified browser automation capability

**Note — bounty hunting as a separate external workflow:**
Security bug bounty work (`C:\audits\`) is an *application* of the Witness methodology to EVM Solidity contracts, operated independently of Project-S system development. It is intentionally **not** a current Project-S core focus. Track record: 17 audits Jan–May 2026, 0 paid findings. See Section 5 for audit knowledge base details.

---

## 5. The audit knowledge base

This is **separate** from Project-S system development. It lives in its own directory and follows its own update cadence.

**Location:** `C:\audits\`

**Core files:**
- `BOUNTY_HUNTING_PLAYBOOK.md` — master document, all 17 audits with strategies, lessons learned, anti-patterns
- `learning.jsonl` — 24 patterns (append-only), structured for programmatic access. Categories: submission_strategy, submission_quality, audit_workflow, review_process, operational_security, audit_methodology, tooling, platform_specific
- `PATTERNS_CHEATSHEET.md` — condensed reference card, checklist format, ~14KB
- `_core/TARGET_TRIAGE_WORKFLOW.md` — 6-phase operational pipeline (Phase 0: target selection → Phase 5: triage management), each phase references relevant patterns

**Per-audit structure (TV system):**

Every active audit has its own directory under `C:\audits\<target>\` with five files:
- `TARGET.md` — program details, scope, reward tiers, deployed addresses, audit PDFs
- `THREAT_VECTORS.md` — TV list with status (OPEN → TESTING → AMBIGUOUS → CLOSED | SUBMIT)
- `STATUS.md` — current phase, progress metrics, blockers, next actions
- `DECISIONS.md` — timestamped decision log
- `TEST_LOG.md` — test runs and results

This methodology was developed in earlier audit sessions (Uniswap v4, Jupiter Lend, Symbiotic) and refined through application. The TV system enables clear PIVOT decisions (5+ TVs CLOSED in sequence = target is well-defended, move on) and prevents the "I'll just look a bit more" trap.

**The two memory systems are intentionally separate:**
- `self_state.json` = Project-S system development knowledge
- `audits/learning.jsonl` + per-target files = bounty hunting knowledge

Merging them would dilute both. They share methodology (evidence-based, append-only logging) but not content.

---

## 6. The current workflow (as of 2026-05-14)

**Home dev machine (primary) — full SAI + MetaController + synthesis pipeline active:**

1. **External research missions** via `interactive_task.py` → SAI → MetaController → SmartToolOrchestrator → synthesis → file_writer
2. **Bounty audit recon** — SAI multi-tool pipeline: `file_search` → `file_content_search` → `file_writer` (30-50× faster than manual grep for large codebases)
3. **Code changes** — Cline (agentic, multi-step) or Copilot (in-editor, single-file)
4. **Strategic decisions** — Claude (this AI) for architecture, ChatGPT for cross-validation
5. **self_state.json updates** — after every significant session, via Copilot/Cline under Claude's prompt direction

**Work machine (secondary) — manual audit workflow with Copilot in VS Code:**

1. Browse HackenProof for small-to-mid targets (Solidity, EVM, continuous bounty, 50-200 contracts)
2. Apply the 6-phase TARGET_TRIAGE_WORKFLOW for each candidate
3. Create per-target directory and TV files
4. Run recon manually (Copilot grep on patterns: `delegatecall`, `assembly`, `.call{value:`, `unchecked`, `block.timestamp`, `selfdestruct`, `tx.origin`, `ecrecover`)
5. Apply pre-submission checklist (prior disclosure, live bytecode verification, severity calibration, anti-patterns)
6. Submit through platform UI; log outcomes to `learning.jsonl`

---

## 7. How to behave if you're an AI joining this work

**If asked to help on Project-S system development:**

Read `self_state.json` first if available. Check the `current_state` block for `active_focus` and `next_concrete_step`. Verify against `gaps_summary` whether the request relates to a known gap or a new issue. **Do not assume the system is more capable than the documented state.** The 16 RESOLVED gaps include many cases where AI assistants (including past Claude sessions) overestimated functionality and had to be corrected.

If asked to make code changes:
- Static check (`python -c "import ast; ..."`) before committing any change
- Live verification (run the relevant test or script) before claiming success
- Update `self_state.json` after meaningful changes (milestone, decision, or gap status change)
- Append to `meta_evidence.jsonl` only via the Witness hook, not manually

**If asked to help on a bounty audit:**

Read `C:\audits\PATTERNS_CHEATSHEET.md` first. Read `_core/TARGET_TRIAGE_WORKFLOW.md` for current phase. Then read the target's `TARGET.md` and `STATUS.md` for specifics.

Apply the pre-submission checklist religiously. The most expensive mistake pattern is `severity_calibration_post_verification` — overclaiming impact without verifying all code paths. The second most expensive is `live_deployment_verification_required` — claiming live impact without on-chain bytecode verification (lost the DPSC-432 submission this way).

Never click external links in target repo GitHub issues (phishing risk, see `phishing_in_bounty_target_repos` pattern).

**If asked for a strategic decision:**

Provide options with explicit tradeoffs. Don't recommend new feature development unless the existing system is clearly insufficient for the stated goal. The system has a documented tendency to expand scope when the harder task is application. Surface this tradeoff explicitly.

When uncertainty exists, recommend verification over speculation. The Witness methodology applies: evidence first, conclusion second.

**If asked to write to self_state.json:**

Read the current state first. Verify counts (milestones, decisions, gaps) before incrementing. Maintain atomic writes (full read, modify, full write, validate). Never partial-update. The file is human-readable and reviewed; consistency matters.

**General behavior:**

- This work has been running for 6+ months across 17 audits and dozens of system development sessions. Assume there is more context than you can see. Ask before making significant changes if uncertain.
- The operator runs multiple AIs in parallel. Conflicting advice happens. Make your reasoning explicit so it can be compared.
- Outcomes matter more than process. The system is production_stable; the goal now is paid findings. Help with that goal, not with rebuilding the system.

---

## 8. Future features (deferred, not active)

These exist as documented ideas. **None are in active development.** They may become relevant if the application phase produces specific demands.

**FEAT_001 — CodeAgent (Project-S self-developing module).** Vision: Project-S writes its own code via Cline-like agent integration into SAI. Deferred until after revenue is established and concrete need emerges. Listed in `self_state.json` `future_features`.

**Qwen3.6-35B-A3B synthesis integration.** MoE model (May 2026): 35B total params / 3B active per token, Apache 2.0. Now used as **default synthesis model** (strategic memos, research reports) via OpenRouter — confirmed by A/B comparison on 2026-05-14 (wins 7/8 dimensions vs gpt-4o-mini). `max_tokens=8000` required for full-length memos. **Local integration** on Tesla M60 16GB VRAM: still a future option (120-190 token/sec with quantization, drastic cost reduction), but current OpenRouter usage is fine. Caveats for local: CUDA 13.2 driver bug on small quants, verbosity (6× tokens vs competitors). **Status for local: deferred. OpenRouter synthesis: ACTIVE.**

**Organism overnight scanner.** Original Idea Log entry (IDEA_022): proactive system that scans repos, prioritizes targets, proposes audits. Requires local LLM (now feasible with Qwen3.6). Deferred.

**Server migration (DL380 Gen9 → full production).** Hardware exists, RDP not yet configured, planned for "after revenue stabilizes." Currently no urgency.

**MetaController standalone dispatcher reactivation.** The *standalone dispatcher* is dormant since 2026-02-19 (RISK_001). The SAI-integrated path (`use_meta_controller=True`) is already active. Full standalone reactivation would require RISK_001 audit. Currently not needed.

---

## 9. Quick reference

**Active files to read first:**
- `C:\ProjectS-Unified\self_state.json` — system state
- `C:\ProjectS-Unified\PROJECT_S_FOUNDATION.md` — principles
- `C:\audits\PATTERNS_CHEATSHEET.md` — audit checklist
- `C:\audits\_core\TARGET_TRIAGE_WORKFLOW.md` — audit pipeline

**Active code paths:**
- SAI (sole Doer): `src/core/super_intelligent_ai.py`
- MetaController (via SAI): `src/core/meta/meta_controller.py` — active via `use_meta_controller=True`
- Smart Orchestrator (+ synthesis): `tools/tools/registry/smart_orchestrator.py`
- Witness hook: triggered after every SAI task, writes to `memory/intelligence/meta_evidence.jsonl`

**Archived/dormant (don't touch unless reactivating):**
- AgentLoop: `src/core/agent/agent_loop.py` (ARCHIVED 2026-05-03)
- MetaController *standalone dispatcher*: dormant (RISK_001) — the SAI-integrated path is active
- WorkflowEngine: present but unused

**Active external accounts:**
- HackenProof, Cantina, Immunefi, Code4rena — bounty platforms (profiles exist, point-building phase on HackenProof)
- OpenRouter — multi-model API access
- GitHub — repo hosting, audit target source

**Workspace separation:**
- `C:\ProjectS-Unified\` — system development (home dev machine primarily)
- `C:\audits\` — bounty audit work (cross-machine, more portable)
- `C:\bounty_reports\` — historical submissions (Citrea archive etc.)
- `C:\1225\project_s_super_core\` — legacy audit work, source for BOUNTY_HUNTING_PLAYBOOK

---

## 10. Final note

This system was built across roughly 6 months by one operator working in parallel with multiple AI assistants. It is not a polished product. It is not a generalizable framework. It is a working setup that lets a small operation do security audit work with structured discipline and a persistent memory across sessions.

The honest assessment as of 2026-05-14: the **infrastructure works** (15 tools, synthesis pipeline, 20 gaps resolved), the **external research pipeline works** (B2 + 30-day scan confirmed), the **audit methodology works**, the **revenue does not yet work**. The bet for the next 1-3 months is disciplined application — external research missions + bounty audits — target by target.

Until then: less building, more shipping.

---

## 10. 2026-05-14 External Mission Milestone

This section summarizes the confirmed capability additions from the 2026-05-14 session.

**Pipeline verified (end-to-end):** `interactive_task.py → SAI(use_meta_controller=True) → MetaController.run_goal() → SmartToolOrchestrator → web_search(DDGS) → web_scraper → LLM synthesis(Qwen3.6) → file_writer`

**Completed missions:**
1. B2 local model research memo (`B2_LOCAL_MODEL_SYNTHESIS_20260514.md`, 3353 bytes, 7/7 sections)
2. 30-day non-bounty opportunity scan — gpt-4o-mini baseline (`PROJECT_S_30_DAY_OPPORTUNITY_SCAN_GPT4OMINI_20260514.md`)
3. 30-day opportunity scan — Qwen3.6 full (`PROJECT_S_30_DAY_OPPORTUNITY_SCAN_QWEN36_FULL_20260514.md`, 13744 bytes, 10/10 sections)
4. **Browser automation external mission rerun** (`PROJECT_S_BROWSER_EXTERNAL_MISSION_RERUN_20260514.md`, 3505 bytes, 9/9 sections, verdict PASS)

**Fixes shipped:**
- GAP_017: DDGS web search (26 tests)
- GAP_018: False-success on empty web results
- GAP_019: LLM synthesis step (11 tests, max_tokens=8000)
- GAP_020: SAI/MetaController truthfulness gate (40 regression tests, 4/4 live scenarios)
- GAP_021: Strategic planner browser_automation visibility — TOOL MANIFEST injected into Phase 1 prompt (6 tests, live mission PASS 9/9)

**Model comparison verdict:** Qwen3.6-35B-A3B is the synthesis default. gpt-4o-mini is the fallback. See `reports/PROJECT_S_30_DAY_OPPORTUNITY_SCAN_QWEN36_FULL_VERDICT_20260514.md`.

**New capability state:**
| Capability | Status |
|------------|--------|
| web_search (DDGS) | VERIFIED |
| web_scraper | VERIFIED |
| LLM synthesis (GAP_019) | VERIFIED |
| browser_automation | **VERIFIED** — Phase 1 planner selects it, live mission: 3 URLs, 94.30s, PASS |
| file_writer | VERIFIED |

---

## 11. MS-OQ1-E Direct Structure Milestone (2026-05-23)

**Score:** 12.9/15 (80% >= 12% threshold) — **PASS**

**Finding:** Direct lightweight response routing validated for simple factual prompts. Prompts classified as `DIRECT_LIGHTWEIGHT_RESPONSE` bypass the heavy MetaController research/execution loop, using direct LLM calls instead. This confirms the GAP_031 routing layer correctly handles the most common prompt class without unnecessary overhead.

**Evidence:** `reports/MS_OQ1_E_DIRECT_STRUCTURE_FINAL_VALIDATION_20260523.md`

---

## 12. MS-FA1 Filesystem Automation Pipeline Milestone (2026-05-24)

**Classification:** Controlled filesystem orchestration — NOT full autonomy (MS-AO1)

**Status:** COMPLETE through Phase 1.5

**What MS-FA1 is:** A controlled, human-in-the-loop filesystem protocol that allows Project-S to coordinate Cline through file-based handoff signals. Project-S drafts tasks and prompts into defined inbox folders; a human reviews and copies the prompt to Cline; Cline executes in a sandbox and writes output to an outbox; Project-S evaluates and issues a verdict. No UI automation, no auto-triggering, no production file modifications.

**Completed phase chain:**

| Phase | Title | Verdict |
|-------|-------|---------|
| FA1.1 | Manual Filesystem Loop | PASS |
| FA1.2 | Semi-Automated Loop | PASS |
| FA1.2H | Hardening | PASS |
| FA1.3 | AI Prompt Drafter + AI Evaluator | PASS |
| FA1.4 | Controlled Multi-Iteration Loop | PASS |
| FA1.5 | File-Based Cline Handoff Polling | PASS |

**Evidence (6 runs, all PASS):**

| Run | Task | Result |
|-----|------|--------|
| FA1_001 | Manual sandbox loop | PASS |
| FA1_002 | Semi-auto JSON validator | PASS |
| FA1_003 | Hardening CSV row counter | PASS |
| FA1_004 | AI prompt/evaluator INI parser | PASS |
| FA1_005 | Multi-iteration TXT word counter | PASS |
| FA1_006 | Handoff polling YAML key counter | PASS |

**Test results:** 25/25 unit tests PASS
**Safety violations:** 0

**Key artifacts:**
- Design: `reports/MS_FA1_FILESYSTEM_AUTOMATION_PIPELINE_DESIGN_20260524.md`
- Handoff protocol: `src/orchestrator/handoff_watcher.py`
- Cline instructions: `orchestrator_runtime/cline_inbox/CLINE_HANDOFF_INSTRUCTIONS.md`
- Verdict: `reports/MS_FA1_PHASE_1_5_FILE_BASED_HANDOFF_POLLING_VERDICT_20260524.md`

**Strategic meaning:** Project-S can now coordinate Cline through a controlled filesystem protocol with run ID validation, consumed flags, timeout safety, and human-in-the-loop at every step. This is a foundation for future automation phases but does NOT constitute full autonomy.

---

*End of overview.*
*Any AI joining the work: if this document is more than 30 days old, ask for an updated version before assuming current state. The pace of change has been high.*
