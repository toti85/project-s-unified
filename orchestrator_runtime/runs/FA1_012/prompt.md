# MS-FA1 Auto Mode v1 Readiness Package - Cline Task Prompt

## 1. Goal Description
You are operating in AUTO MODE v1 READINESS assessment phase. Your task is to evaluate and document whether the Project-S MS-FA1 system is prepared for limited Auto Mode execution. This is a **documentation and assessment task only**. Do not implement new features, modify runtime code, or change system state. 

Review existing MS-FA1 evidence/reports located in the project root:
- `FA1.1_manual_loop`
- `FA1.2_semi_automated_loop`
- `FA1.2H_hardening`
- `FA1.3_AI_prompt_drafter_evaluator`
- `FA1.4_controlled_multi_iteration`
- `FA1.5_file_based_handoff_polling`
- `Hardening_001_AI_prompt_drafting`
- `Hardening_002_AI_verdict_evaluator`

Synthesize findings into three policy/operator/verdict documents that define safe boundaries, operational workflows, and readiness status for Auto Mode v1.

## 2. Allowed Directory
- `C:\ProjectS-Unified\orchestrator_runtime\sandbox`
- Subdirectories within sandbox (specifically `reports/`)
- Read-only access to project root for evidence review

## 3. Forbidden Paths & Operations
- `src/core/**`
- `interactive_layer/**`
- `self_state.json`
- `router/`, `server/`, `network/` configuration files
- Any path outside `C:\ProjectS-Unified\orchestrator_runtime\sandbox`
- File deletion or renaming
- Git operations (`commit`, `tag`, `push`, `pull`, `merge`, `rebase`)
- External network calls, API requests, or package installations
- Execution of runtime binaries or services

## 4. Required Deliverables
Create exactly three markdown files in the sandbox `reports/` directory:

1. `reports/MS_FA1_AUTO_MODE_V1_POLICY_20260524.md`
   - Allowed automated actions
   - Explicitly forbidden actions
   - `NEEDS_HUMAN` trigger conditions
   - `max_iterations` limit
   - Safety stop conditions
   - Sandbox/docs-only execution rules

2. `reports/MS_FA1_AUTO_MODE_V1_OPERATOR_EXAMPLE_20260524.md`
   - How to submit a high-level goal
   - How Project-S decomposes it into subtasks
   - How the prompt is routed to Cline
   - How output is returned
   - How verdict is generated
   - Stop/escalation conditions

3. `reports/MS_FA1_AUTO_MODE_V1_READINESS_VERDICT_20260524.md`
   - Verdict: `READY` / `PARTIAL` / `NOT READY`
   - Task categories allowed for Auto Mode v1
   - Task categories explicitly blocked
   - Recommended next steps

## 5. Test Instructions
After generating the deliverables, perform the following validation:
- Verify all three files exist in `C:\ProjectS-Unified\orchestrator_runtime\sandbox\reports\`
- Confirm each file contains all required sections from Section 4
- Run content checks: grep for `NEEDS_HUMAN`, `max_iterations`, `safety_stop`, `READY/PARTIAL/NOT_READY`, `docs-only`
- Verify zero modifications to forbidden paths
- Confirm no git state changes or external calls were attempted
- Output the final A-H checklist exactly as specified in Section 8

## 6. Output/Report Location
All deliverables must be written to:
`C:\ProjectS-Unified\orchestrator_runtime\sandbox\reports\`

## 7. Safety Constraints
- Work exclusively within the sandbox directory for all writes.
- Read-only access to project root for evidence review.
- Zero tolerance for production code, config, or state modifications.
- No external network, filesystem, or process execution outside sandbox.
- If any constraint is at risk of violation, halt immediately and report.
- Treat this as a pure documentation/assessment pipeline step.

## 8. Final Output Format
After completing all tasks and validations, return exactly this checklist:

A. Nagy cél részfeladatokra bontva? yes/no
B. Auto Mode policy elkészült? yes/no
C. Operator example elkészült? yes/no
D. Readiness verdict elkészült? yes/no
E. Auto Mode v1 státusz: READY / PARTIAL / NOT READY
F. Bármilyen production fájl módosult? yes/no
G. Safety violation count
H. Következő ajánlott lépés