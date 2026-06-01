# Cline Prompt: Auto Mode v1 Validation Run

## 1. Goal Description
Execute an Auto Mode v1 validation run to verify the functionality of the AI prompt drafting pipeline and the AI evaluation module. Confirm that both components operate correctly, produce expected outputs, and integrate seamlessly within the isolated environment.

## 2. Allowed Directory
`C:\ProjectS-Unified\orchestrator_runtime\sandbox`
All file operations, script executions, temporary artifacts, and logs must be strictly confined to this directory and its subdirectories.

## 3. Forbidden Paths
- Any directory or file outside `C:\ProjectS-Unified\orchestrator_runtime\sandbox`
- Configuration files (`*.config`, `*.yaml`, `*.json`, `.env`, etc.)
- Router modules (`src/router/**`, `routes/**`, `middleware/**`)
- Server files (`src/server/**`, `app.js`, `server.js`, `main.py`, `docker-compose.yml`, etc.)
- System directories, environment variables, package managers, or external APIs

## 4. Required Deliverables
- `test_prompt_drafting.py` (or `.js`): A self-contained test script that simulates AI prompt drafting, validates output structure, and verifies required fields/templates.
- `test_ai_evaluation.py` (or `.js`): A self-contained test script that simulates AI evaluation metrics, validates scoring logic, and verifies rating ranges.
- `validation_report.md`: A