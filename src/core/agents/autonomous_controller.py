#!/usr/bin/env python3
"""
Autonomous Controller - Project-S V2
Central loop that plans -> acts -> learns using existing components.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import sys

_src_dir = str(Path(__file__).parent.parent.parent)
_repo_root = str(Path(__file__).parent.parent.parent.parent)
sys.path.insert(0, _repo_root)
sys.path.insert(0, _src_dir)

from core.self_dev_agent import SelfDevelopmentAgent
from integrations.ai_models.multi_model_ai_client import AIClient
from tools.tools.registry.tool_registry_golden import ToolRegistry
from core.infrastructure.event_bus import EventBus
from core.state.autonomy_state import AutonomyStateStore

logger = logging.getLogger(__name__)

class AutonomousController:
    """
    High-level autonomous loop:
      - Observe: collect signals, recent logs, failures
      - Decide: plan tasks with AI router
      - Act: execute tools / workflows
      - Learn: run self-dev agent on failures to close capability gaps
    """

    def __init__(self, workdir: Optional[Path] = None):
        self.workdir = Path(workdir) if workdir else Path.cwd()
        self.event_bus = EventBus()
        self.tool_registry = ToolRegistry()
        self.ai_client = AIClient()
        self.self_dev = SelfDevelopmentAgent(self.ai_client, self.tool_registry)
        self.state = AutonomyStateStore()
        # Safety rails
        self.max_actions_per_cycle = 3
        self.allowed_tools: Optional[set[str]] = None  # e.g., set(["web_fetch", "file_read"]) or None for all

    async def observe(self) -> Dict[str, Any]:
        """Collect basic signals for planning.
        Returns a dict with environment info and recent events.
        """
        signals: Dict[str, Any] = {
            "cwd": str(self.workdir),
            "tools_available": list(self.tool_registry.tools.keys()),
        }
        return signals

    async def decide(self, signals: Dict[str, Any]) -> Dict[str, Any]:
        """Use AI to propose next tasks (simple planner)."""
        prompt = (
            "You are the Project-S autonomous planner. Given available tools and the current goal\n"
            "(stabilize demos 270/271 and improve autonomy), propose 1-3 concrete actions.\n"
            "Return JSON with actions: [{name, params, reason}]."
        )
        try:
            resp = await self.ai_client.generate_response(prompt=prompt, model="qwen3-235b", temperature=0.2)
            # Best-effort parse
            import json
            plan = json.loads(resp) if resp.strip().startswith("{") or resp.strip().startswith("[") else {"actions": []}
        except Exception:
            plan = {"actions": []}
        plan = await super().decide(signals) if hasattr(super(), "decide") else plan
        # Safety: truncate actions
        actions = plan.get("actions", [])
        if len(actions) > self.max_actions_per_cycle:
            actions = actions[: self.max_actions_per_cycle]
            plan["actions"] = actions
        # Filter by allowlist if present
        if self.allowed_tools is not None:
            plan["actions"] = [a for a in actions if a.get("name") in self.allowed_tools]
        # Persist
        self.state.save_plan(signals, plan)
        return plan

    async def act(self, plan: Dict[str, Any]) -> None:
        """Execute planned actions via ToolRegistry when possible."""
        actions = plan.get("actions", [])
        for action in actions:
            name = action.get("name")
            params = action.get("params", {})
            if self.allowed_tools is not None and name not in self.allowed_tools:
                self.state.save_action_result(action, success=False, error="blocked_by_allowlist")
                continue
            if name in self.tool_registry.tools:
                try:
                    result = await self.tool_registry.execute_tool(name, **params)
                    self.state.save_action_result(action, success=True, result=result)
                except Exception as e:
                    self.state.save_action_result(action, success=False, error=str(e))
                    logger.error(f"Action {name} failed: {e}")
                    await self.self_dev.autonomous_improvement_cycle({
                        "task_description": f"Execute {name}",
                        "tool_name": name,
                        "error": str(e),
                        "params": params,
                    })
            else:
                self.state.save_action_result(action, success=False, error="tool_not_found")

    async def learn_from_logs(self) -> None:
        """Placeholder: inspect recent errors and trigger self-dev if needed."""
        return

    async def run_once(self):
        signals = await self.observe()
        plan = await self.decide(signals)
        await self.act(plan)
        await self.learn_from_logs()

    async def run_forever(self, interval_sec: int = 60):
        logger.info("🤖 AutonomousController loop starting...")
        while True:
            try:
                await self.run_once()
            except Exception as e:
                logger.error(f"Autonomous loop error: {e}")
            await asyncio.sleep(interval_sec)
