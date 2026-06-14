# Sz Proposed Missions Workflow

## Purpose

This folder stores draft mission prompts that Sz prepares for Toti to paste into Cline.

## Workflow

1. Run `python orchestrator_runtime\sz_prompt_generator.py`.
2. The script reads `self_state.json`, recent report heads, `orchestrator_runtime\goal_queue.json`, and `orchestrator_runtime\cline_outbox\last_output.md`.
3. It generates one draft mission prompt based on goal priority, `next_concrete_step`, and recent evidence.
4. The prompt is saved to `MS_AO5_T<N>_DRAFT_<timestamp>.md` in this folder.
5. The same prompt is printed to STDOUT so Toti can copy-paste it immediately.
6. Toti reviews the prompt briefly, usually for 1 to 2 minutes.
7. Toti pastes the prompt into Cline with auto-approve enabled for safe operations.
8. Cline executes and writes the result to `orchestrator_runtime\cline_outbox\last_output.md`.
9. Toti brings `last_output.md` back to Claude for analysis and the next decision.

## Kill Switch

- Stop the current Cline task immediately if it proposes `src/` edits without explicit approval.
- Disable Cline auto-approve before retrying if the task starts asking for risky commands.
- If output quality degrades, archive the draft and rerun the generator instead of continuing blindly.
- If a task starts touching destructive shell commands, cancel it and restart from a smaller read-only mission.

## Cline Auto-Approve Guidance

- Enable auto-approve for safe reads, searches, directory listing, and allowed-path edits.
- Keep destructive shell actions manual.
- Keep production-code edits manual until Toti explicitly wants them.

## Manual Boundaries

- Keep `src/` edits manual.
- Keep `orchestrator_runtime/governance/` edits manual.
- Keep package installs, environment changes, and browser actions manual.