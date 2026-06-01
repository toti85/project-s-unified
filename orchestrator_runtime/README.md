# orchestrator_runtime — MS-FA1 Internal Project-S Layer

**Created:** 2026-05-24  
**Pipeline Version:** FA1.0  
**Status:** Relocated into Project-S

---

## Overview

This directory contains the runtime data for the MS-FA1 filesystem automation pipeline.
The orchestrator package lives at `src/orchestrator/` within Project-S.

## Folder Structure

| Directory | Purpose |
|-----------|---------|
| `inbox/` | Human or Project-S writes goals here |
| `cline_inbox/` | Ready-to-copy prompts for Cline |
| `cline_outbox/` | Cline writes execution output here |
| `runs/` | One folder per run (state, verdict, notes) |
| `logs/` | Execution logs, timestamps, model versions |
| `reports/` | Generated reports (design, audit, summary) |
| `sandbox/` | Isolated workspace for Cline to work in |

## Pipeline Flow

1. **Goal defined** → `inbox/goal.md`
2. **Prompt drafted** → `cline_inbox/next_prompt.md`
3. **Human reviews** prompt
4. **Human copies** prompt to Cline
5. **Cline executes** task (sandbox only in Phase 1)
6. **Cline writes** output to `cline_outbox/last_output.md`
7. **Project-S evaluates** output
8. **Verdict issued** → `runs/FA1_XXX/verdict.json`
9. **Human reviews** verdict before next iteration

## Safety Rules (Phase 1)

- Cline may **only** modify files under `sandbox/`
- No Project-S production files may be changed
- No config/server changes
- No external network calls
- Human review required for every prompt

## Design Document

See: `C:\ProjectS-Unified\reports\MS_FA1_FILESYSTEM_AUTOMATION_PIPELINE_DESIGN_20260524.md`

## Verdict Schema

See: `verdict_schema.json`

---

**Relocated 2026-05-24 — was C:\ProjectS-Automation\**
