# Cline Auto-Approve Guide for Toti

Apply these settings manually in Cline.

## Enable Auto-Approve

- Read files on any path.
- Edit files only in `orchestrator_runtime/sandbox/`, `reports/`, and `orchestrator_runtime/cline_outbox/`.
- Run read-only PowerShell commands such as `Get-*`, `Select-String`, `Test-Path`, `Get-ChildItem`, `Measure-Object`, and safe `python` read-only inspection commands.
- List directory contents.
- Search files.

## Keep Manual Approval Required

- Any edit in `src/`.
- Any edit in `orchestrator_runtime/governance/`, including bridge or runner logic.
- Commands such as `git push`, `git rm`, `Remove-Item -Recurse`, `Stop-Process`, `kill`, and `taskkill`.
- Any `pip install`, dependency update, or package modification.
- Browser actions or web fetches initiated by Cline.

## Kill Switch

- Turn off auto-approve immediately if Cline asks for production edits outside the safe directories.
- Cancel the current task if it proposes destructive shell flags.
- Restart with a smaller READ-ONLY mission if confidence drops.