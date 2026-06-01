# Cline Prompt: Auto Mode v1 Validation Run

## 1. Goal Description
Execute an Auto Mode v1 validation run to verify the functionality of the AI prompt drafting module and the AI evaluation module. The run must confirm that prompts are generated correctly, evaluation metrics are computed accurately, and all outputs are deterministic and reproducible within an isolated environment.

## 2. Allowed Directory
`C:\ProjectS-Unified\orchestrator_runtime\sandbox`
All file operations, script executions, temporary data storage, and artifact generation must be strictly confined to this directory and its subdirectories.

## 3. Forbidden Paths
- Any path outside `C:\ProjectS-Unified\orchestrator_runtime\sandbox`
- Configuration files (`*.config`, `*.yaml`, `*.json`, `*.ini`, `*.env` outside sandbox)
- Router/Server/Infrastructure files (`router/`, `server/`, `api/`, `gateway/`, `deploy/`, `infrastructure/` directories)
- System directories, user profiles, or environment variables outside the sandbox
- External network endpoints, package registries, or remote APIs

## 4. Required Deliverables
- `sandbox/prompt_drafts/` → At least 3 validated AI prompt templates (JSON/Markdown) covering distinct use cases
- `sandbox/evaluation_results/` → Structured evaluation logs/metrics for each drafted prompt (clarity, specificity, format compliance, safety alignment)
- `sandbox/run_validation.ps1` (or equivalent script) → Automated validation runner
- `sandbox/output/validation_report.md` → Pass/fail summary, metrics, observations, and next steps
- `sandbox/logs/validation_run.log` → Timestamped execution logs

## 5. Test Instructions
1. Initialize the workspace by creating required subdirectories: `prompt_drafts`, `evaluation_results`, `output`, `logs`.
2. Generate 3 distinct AI prompt drafts targeting different domains (e.g., code generation, text summarization, data analysis). Save them to `prompt_drafts/` with consistent naming conventions.
3. Run the AI evaluation module against each draft. Capture quantitative and qualitative metrics. Save results to `evaluation_results/`.
4. Execute the validation script to automate steps 2–3, ensuring deterministic outputs and consistent logging.
5. Cross-reference evaluation results against predefined success criteria (e.g., all prompts pass format checks, evaluation scores meet minimum thresholds, no runtime errors).
6. Generate the final validation report in `output/validation_report.md` summarizing pass/fail status, key metrics, anomalies, and recommendations.

## 6. Output/Report Location
All artifacts, logs, and reports must be written exclusively to:
`C:\ProjectS-Unified\orchestrator_runtime\sandbox\output\`
- Primary report: `validation_report.md`
- Supporting artifacts: `prompt_drafts/`, `evaluation_results/`, `logs/`
Do not scatter outputs across the filesystem. Maintain a flat, predictable structure.

## 7. Safety Constraints
- **STRICT ISOLATION:** Operate ONLY within `C:\ProjectS-Unified\orchestrator_runtime\sandbox`. Do not read, write, traverse, or reference any other directory.
- **NO EXTERNAL CALLS:** Disable or avoid all HTTP requests, API calls, package downloads, or external service connections. Use only local files and built-in language features.
- **READ-ONLY EXTERNAL:** Treat all paths outside the sandbox as immutable. Do not attempt to modify, backup, or reference config, router, server, or infrastructure files.
- **FALLBACK ON VIOLATION:** If any operation attempts to access forbidden paths or requires network access, abort immediately and log a `SAFETY_VIOLATION` error. Do not proceed.
- **CLEANUP & AUDIT:** Do not leave temporary files outside the sandbox. Ensure all outputs are self-contained. Maintain a clear audit trail in `logs/validation_run.log`.
- **ZERO TOLERANCE:** Any deviation from these constraints will result in immediate task termination. Prioritize safety over completion.