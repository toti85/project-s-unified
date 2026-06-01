# Bounty 270 & 271 Demo Guide

Purpose: Provide step‑by‑step instructions to produce the final demo videos for Linode (270) and Auto‑Dev‑Server (271).

## Common Setup
- Ensure templates/scripts are updated
- Prepare recording (OBS or similar)
- Terminal shell: PowerShell (Windows)

## 271: Auto‑Dev‑Server Demo Flow
1) Show template source
   - Path: `clean-template/docker/auto-dev-server-demo`
   - Highlight: `main.tf` (no pre‑install of Flask/Django), inotify install, venv creation
   - Show module script: `modules/auto-dev-server/scripts/auto-dev-server.sh` (JIT install, detection patterns, start_file_monitor)
2) Create workspace
   - Push template, create workspace in Coder
   - Wait until init complete
3) Validate monitoring
   - In workspace terminal:
     - `ps aux | grep -E "inotify|auto-dev-server"`
     - `tail -f ~/auto-dev-server.log`
     - `ls -la ~/.auto-dev-server/`
4) Clone demo repo
   - `git clone https://github.com/Toti85/auto-dev-server-demo-repo.git test-project`
   - Watch log for detection within 2–3s
5) Verify servers
   - Node: `curl http://localhost:3000`
   - Flask: `curl http://localhost:5000`
   - Django: `curl http://localhost:8000`
6) Show logs & PIDs
   - `cat ~/.auto-dev-server/*.log`
   - `ls ~/.auto-dev-server/*.pid`
7) Closeout
   - Summarize benefits; link to module source (PR #271)

## 270: Linode Template Demo Flow
1) Show artifacts
   - `LINODE_BOUNTY_270_OVERVIEW.md`, `linode_template.json`, `create_linode_demo.py`
2) Run demo script (dry‑run/plan)
   - Show terraform plan/apply output or mocked output
   - Explain persistent home and provisioning
3) Validate deliverables
   - Checklist from `LINODE_BOUNTY_270_PLAN.md`
4) Closeout
   - Summarize infra readiness and how to extend

## Troubleshooting
- Auto‑Dev‑Server watcher not running → Increase `start_delay`, ensure `run_on_start=true`, check `~/auto-dev-server.log`
- Ports not responding → verify server PIDs, logs, and health checks
- Network limits → use workspace port forwarding

Produce and store videos under `demo_videos/` with timestamps.
