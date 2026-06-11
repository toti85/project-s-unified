# AO5_T14 — Overseer Integration Plan

**Date:** 2026-06-10
**Status:** INTEGRATION PLAN

## Decision: Which OverseerAgent method to call?

**Chosen method:** `get_system_health()`

**Rationale:**
- Returns a dict with health assessment (health_status, health_score, success_rate, avg_execution_time, etc.)
- Non-blocking, read-only operation
- No side effects (doesn't modify state or publish events)
- Provides meaningful cognitive insight about system state
- Async method, but can be called synchronously with asyncio.run()

## Input to Pass
- No input required (method takes no parameters)
- Context: run_id and iteration for logging purposes

## Output to Capture
- Dict from `get_system_health()` containing:
  - health_status: "excellent" | "good" | "fair" | "poor" | "unknown"
  - health_score: float 0.0-1.0
  - success_rate: float
  - avg_execution_time: float
  - total_metrics: int
  - optimization_suggestions: int
  - learning_enabled: bool

## Integration Pattern
Mirror CWI advisory hook pattern:
1. Feature flag: OVERSEER_ADVISORY_ENABLED = False (default OFF)
2. Safe wrapper function with try/except
3. Called before verdict computation
4. Result logged but never blocks consumption
5. Fail-open: exceptions caught and logged, never raised

## Hook Location
In `consume_executor_output()`, after CWI advisory hook, before verdict computation.

## Safety Constraints
- OverseerAgent requires EventBus instance
- EventBus is self-contained (no external dependencies)
- OverseerAgent creates SQLite DB (overseer_memory.db) — use in-memory or temp path to avoid side effects
- All calls wrapped in try/except
- Timeout protection if needed