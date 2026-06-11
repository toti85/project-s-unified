# AO5_T23 CWI Bridge Advisory Integration — PASS

**Date:** 2026-06-11
**Status:** PASS
**Run ID:** AO5_T23_CWI_BRIDGE_ADVISORY

## Summary
Integrated CWI advisory into bridge_runner.py, mirroring the OverseerAgent flag-based pattern. Both advisories are now independent, fail-open, and independently telemetry-tracked.

## Changes Made

### 1. CWI Advisory Flag (env-var based)
Changed from hardcoded `CWI_ADVISORY_ENABLED = False` to:
```python
CWI_ADVISORY_ENABLED = (
    os.environ.get("CWI_ADVISORY", "false").lower() == "true"
)
```

### 2. CWI Advisory Timing & Status Tracking
Added timing variables parallel to OverseerAgent pattern:
- `_cwi_start` — perf_counter start
- `_cwi_advisory_status` — "OK" / "ERROR" / "SKIPPED"
- `_cwi_advisory_output` — first 200 chars of advisory output
- `_cwi_latency_ms` — CWI-only latency

### 3. Telemetry Schema Extended
observation.jsonl now includes:
- `overseer_enabled`, `overseer_status`, `overseer_output_first_200`, `overseer_latency_ms`
- `cwi_enabled`, `cwi_status`, `cwi_output_first_200`, `cwi_latency_ms`
- `latency_ms_total`, `verdict`, `errors`

### 4. Both Advisories Independent
- OverseerAgent failure does NOT block CWI
- CWI failure does NOT block verdict computation
- Both are fail-open by design

## Files Modified
- `orchestrator_runtime/governance/bridge_runner.py` — CWI flag env-var, timing, telemetry schema

## Backup
- `orchestrator_runtime/governance/bridge_runner.py.bak_t23`

## Rollback Command
```bash
git restore -- orchestrator_runtime/governance/bridge_runner.py
```

## Verification
- CWI import: ✅ OK
- CWI advisory flag: ✅ env-var based
- Telemetry schema: ✅ extended with CWI fields
- Both advisories independent: ✅ yes

## Production Defaults
- `CWI_ADVISORY` env var: not set → disabled
- `OVERSEER_ADVISORY` env var: not set → disabled
- Both flags OFF by default → no surprise overhead

## Verdict
**PASS** — CWI advisory integrated into bridge_runner. Both advisories independent, fail-open, env-var controlled.

## Ready for T24
**yes** — 24h CWI observation can begin with `$env:CWI_ADVISORY = "true"`