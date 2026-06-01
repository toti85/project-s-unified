# Project-S V2 Autonomy Design

Goal: Make the system self-directed and continuously improving while preserving interactive use.

## Components
- AutonomousController (core/agent/autonomous_controller.py)
  - Loop: observe → decide → act → learn
  - Uses MultiModelAIClient and ToolRegistry
  - Triggers SelfDevelopmentAgent when actions fail
  - Persists plans/actions via AutonomyStateStore
  - Safety rails: max actions per cycle, optional allowlist
- SelfDevelopmentAgent (core/self_dev_agent.py)
  - Gap analysis, tool generation, dynamic registration

## Run Modes
- Default: Interactive CLI
- Autonomous mode: add `--autonomous` to main.py; background loop runs while interactive stays available.

## Planner Contract
- decide(): AI returns JSON plan `{ actions: [{ name, params, reason }] }`
- act(): executes via ToolRegistry, on failure -> self-dev cycle, logs result via state store

## Persistence & Telemetry
- State store: `memory/state/checkpoints/autonomy_plan.jsonl` and `autonomy_actions.jsonl`
- Tail helpers: `AutonomyStateStore.tail_plans(n)`, `tail_actions(n)`

## Next Enhancements
- Persist planner/state to memory/state/checkpoints
- Add safety rails (max actions/interval, allow/deny list)
- Add telemetry dashboard (events) and health checks

## Demo
- `python main.py --autonomous` then issue interactive commands; background controller keeps improving.
