# Continuation Runbook

Goal: Make it trivial to resume work anytime on Project S core and active bounties (270 Linode, 271 Auto‑Dev‑Server).

## 0) Prereqs
- Windows PowerShell environment
- .env configured with required API keys (OpenAI/Anthropic/etc. if needed)

## 1) Project S Core: start and inspect
- Entry: choose `main.py` or `interactive_main.py` depending on UI mode
- Validate memory subsystem
  - Check folders: `memory/state/{archive,checkpoints,conversations,sessions}`
  - Ensure read/write APIs used by core flows (see TODOs in System_Audit_Report)

## 2) Bounty 271: Auto‑Dev‑Server demo validation
- Template path: `clean-template/docker/auto-dev-server-demo`
- Key files: `main.tf`, `modules/auto-dev-server/scripts/auto-dev-server.sh`, README
- Verify run_on_start and monitoring
  - Check log: `~/auto-dev-server.log`
  - Check PID/health: `~/.auto-dev-server/*.pid`, inotifywait process
  - If watcher missing: increase `start_delay` to 15–30s, re‑push template, recreate workspace
- Demo flow (recording): clone `auto-dev-server-demo-repo`, observe detection, curl ports 3000/5000/8000, show logs and PIDs

## 3) Bounty 270: Linode demo validation
- Files: `LINODE_*`, `linode_template.json`, `create_linode_demo.py`
- Steps: run demo script, capture terraform plan/apply (or mocked), show resource outputs

## 4) Model Router & GPT‑5 Preview flag
- Add a central router module (e.g., `core/model_router.py`) with providers and feature flags
- Env flags:
  - `FEATURE_GPT5_PREVIEW=true|false`
  - Tenant/user scoping if needed (config map)
- Test with a small inference call path used by core

## 5) Tests & Coverage
- Add `pytest` config and simple coverage target
- Generate report to `reports/coverage/`

## 6) Video production checklist
- Use scripts: `video_demo_orchestrator.py`, `coder_template_complete_demo.py`, `terminal_auto_demo.py`
- Capture: template view → workspace create → git clone → detection → curl/browser verification
- Save outputs to `demo_videos/` with timestamp

## 7) Artifacts & Handoff
- Update `docs/System_Audit_Report.md` and this runbook after each session
- Store links to published demo videos

This runbook enables quick context reload and consistent continuation.
