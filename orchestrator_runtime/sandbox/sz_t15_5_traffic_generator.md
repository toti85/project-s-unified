# AO5_T15_5 — Traffic Generator Documentation

**Date:** 2026-06-10
**Status:** RUNNING

## What it does
Generates 1 synthetic consume() event per hour for 24 hours to feed OverseerAgent telemetry.
Each event uses run_id pattern: AO5_T15_SYNTH_{hour:02d}

## How to stop it
Close the PowerShell window, or Ctrl+C in the running terminal.

## How to verify it's still running
```
wmic process where "name='python.exe'" get processid,commandline | findstr "traffic"
```
Check overseer_observation.jsonl for new entries:
```
type orchestrator_runtime\governance\overseer_observation.jsonl
```

## Expected entries
- By CP1 (+2h): ~2 entries
- By CP2 (+8h): ~8 entries
- By CP3 (+24h): ~24 entries

## Current Status
- PowerShell PID: 40336
- Python PID: 1916
- Started: 2026-06-10T14:54:00Z