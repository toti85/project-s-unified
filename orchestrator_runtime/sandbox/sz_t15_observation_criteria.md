# AO5_T15 — Observation Success Criteria

**Date:** 2026-06-10
**Observation Period:** 24 hours

## Criteria

C1. At least 10 real consume() runs happened with flag ON
C2. Zero unhandled exceptions in bridge_runner due to advisory
C3. Verdict distribution unchanged vs baseline:
    - ACCEPTED rate within +/-5% of pre-T14 baseline
C4. Latency stable:
    - 95th percentile latency <= 250ms
    - mean latency advisory_only <= 150ms
    - no latency drift over 24h
C5. Advisory output evolves:
    - "insufficient_data" -> some real metric
    - this proves OverseerAgent is actually learning over time
C6. self_state.json untouched by overseer path

## Checkpoints

CP1 — at +2h: quick sanity check (10 lines summary)
CP2 — at +8h: midpoint review
CP3 — at +24h: full T15 verdict report