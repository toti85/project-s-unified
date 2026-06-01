#!/usr/bin/env python3
"""
Autonomy State Store
Persist and load autonomy loop state (signals, plans, actions, results).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, List


@dataclass
class PlanRecord:
    timestamp: str
    signals: Dict[str, Any]
    plan: Dict[str, Any]


@dataclass
class ActionRecord:
    timestamp: str
    action: Dict[str, Any]
    success: bool
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class AutonomyStateStore:
    def __init__(self, base_dir: Optional[Path] = None) -> None:
        self.base_dir = Path(base_dir) if base_dir else Path("memory/state/checkpoints")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.plan_log = self.base_dir / "autonomy_plan.jsonl"
        self.action_log = self.base_dir / "autonomy_actions.jsonl"

    def save_plan(self, signals: Dict[str, Any], plan: Dict[str, Any]) -> None:
        rec = PlanRecord(timestamp=datetime.utcnow().isoformat(), signals=signals, plan=plan)
        with self.plan_log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(rec)) + "\n")

    def save_action_result(
        self,
        action: Dict[str, Any],
        success: bool,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        rec = ActionRecord(
            timestamp=datetime.utcnow().isoformat(),
            action=action,
            success=success,
            error=error,
            result=result,
        )
        with self.action_log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(rec)) + "\n")

    def tail_plans(self, n: int = 10) -> List[Dict[str, Any]]:
        return self._tail_file(self.plan_log, n)

    def tail_actions(self, n: int = 10) -> List[Dict[str, Any]]:
        return self._tail_file(self.action_log, n)

    @staticmethod
    def _tail_file(path: Path, n: int) -> List[Dict[str, Any]]:
        if not path.exists():
            return []
        lines = path.read_text(encoding="utf-8").splitlines()
        out: List[Dict[str, Any]] = []
        for line in lines[-n:]:
            try:
                out.append(json.loads(line))
            except Exception:
                continue
        return out
