"""
MS-AO2 Daily Budget Manager — AO2.3

Tracks daily run budget with auto-reset and kill switch integration.

Config: orchestrator_runtime/governance/budget_config.json
State:  orchestrator_runtime/governance/daily_budget.json

Usage:
    from orchestrator_runtime.governance.budget_manager import BudgetManager
    bm = BudgetManager()
    bm.can_run()    # bool
    bm.increment()  # after successful run
    bm.remaining()  # int
"""

import json
from pathlib import Path
from datetime import datetime, timezone

BUDGET_CONFIG_PATH = Path(__file__).parent / "budget_config.json"
BUDGET_STATE_PATH = Path(__file__).parent / "daily_budget.json"

DEFAULT_DAILY_LIMIT = 10
WARNING_THRESHOLD = 3


def _load_json(path, default=None):
    if default is None:
        default = {}
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def _save_json(path, data):
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    if path.exists():
        path.unlink()
    tmp.rename(path)


class BudgetManager:
    def __init__(self):
        # Load or create config
        if not BUDGET_CONFIG_PATH.exists():
            _save_json(BUDGET_CONFIG_PATH, {"daily_limit": DEFAULT_DAILY_LIMIT})
        self._ensure_today()

    def _get_limit(self):
        config = _load_json(BUDGET_CONFIG_PATH, {"daily_limit": DEFAULT_DAILY_LIMIT})
        return config.get("daily_limit", DEFAULT_DAILY_LIMIT)

    def _ensure_today(self):
        """Ensure budget state is for today. Auto-reset if new day."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        state = _load_json(BUDGET_STATE_PATH, {})

        if state.get("date") != today:
            # New day — reset
            state = {
                "date": today,
                "count": 0,
                "limit": self._get_limit(),
            }
            _save_json(BUDGET_STATE_PATH, state)

        self._state = state

    @property
    def state(self):
        self._ensure_today()
        return self._state

    def can_run(self):
        """Check if another run is allowed within budget."""
        return self.state["count"] < self.state["limit"]

    def increment(self):
        """Increment run counter. Call AFTER a successful run starts."""
        self._ensure_today()
        self._state["count"] += 1
        _save_json(BUDGET_STATE_PATH, self._state)

        remaining = self.state["limit"] - self.state["count"]

        # Notification integration
        if remaining < WARNING_THRESHOLD and remaining >= 0:
            self._notify_budget_warning(remaining)

        if remaining <= 0:
            self._activate_kill_switch()

        return remaining

    def remaining(self):
        """Return remaining runs for today."""
        r = self.state["limit"] - self.state["count"]
        return max(0, r)

    def _notify_budget_warning(self, remaining):
        """Send BUDGET_WARNING notification."""
        try:
            from orchestrator_runtime.governance.notifier import Notifier
            n = Notifier()
            n.notify(
                "BUDGET_WARNING",
                message=f"Daily budget low: {remaining}/{self.state['limit']} runs remaining",
                severity="ERROR" if remaining == 0 else "WARN",
            )
        except Exception:
            pass

    def _activate_kill_switch(self):
        """Auto-activate kill switch when budget exhausted."""
        try:
            from orchestrator_runtime.governance.kill_switch import KillSwitch
            ks = KillSwitch()
            if not ks.is_active():
                ks.activate(f"Daily budget exhausted ({self.state['count']}/{self.state['limit']})")
        except Exception:
            pass

    def get_status(self):
        """Return full budget status."""
        return {
            "date": self.state["date"],
            "count": self.state["count"],
            "limit": self.state["limit"],
            "remaining": self.remaining(),
            "can_run": self.can_run(),
        }


if __name__ == "__main__":
    import sys
    bm = BudgetManager()

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "status":
            print(json.dumps(bm.get_status(), indent=2))
        elif cmd == "remaining":
            print(f"Remaining: {bm.remaining()}/{bm.state['limit']}")
        else:
            print(f"Unknown: {cmd}")
    else:
        print(json.dumps(bm.get_status(), indent=2))