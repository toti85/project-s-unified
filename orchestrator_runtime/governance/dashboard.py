"""
MS-AO4 AO4.4 — Production Monitoring Dashboard

Single-command governance state overview.

Usage:
  python orchestrator_runtime/governance/dashboard.py status
  python orchestrator_runtime/governance/dashboard.py status --json
  python orchestrator_runtime/governance/dashboard.py watch --interval 30
"""

import json
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

# File paths
GOV_DIR = Path(__file__).parent
KILL_SWITCH_PATH = GOV_DIR / "KILL_SWITCH"
BUDGET_CONFIG_PATH = GOV_DIR / "budget_config.json"
DAILY_BUDGET_PATH = GOV_DIR / "daily_budget.json"
TRIGGER_QUEUE_PATH = GOV_DIR / "trigger_queue.json"
PENDING_APPROVAL_PATH = GOV_DIR / "pending_human_approval.json"
ESCALATION_QUEUE_PATH = GOV_DIR / "escalation_queue.json"
IMPROVEMENT_SUGGESTIONS_PATH = GOV_DIR / "improvement_suggestions.json"
CYCLE_LOG_PATH = GOV_DIR / "cycle_log.jsonl"
NOTIFICATIONS_PATH = GOV_DIR / "notifications.jsonl"


def _load_json(path, default=None):
    if default is None:
        default = {}
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return default
    return default


def _get_kill_switch_state():
    if KILL_SWITCH_PATH.exists():
        try:
            with open(KILL_SWITCH_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {
                "status": "ACTIVE",
                "reason": data.get("reason", ""),
                "activated_at": data.get("activated_at", ""),
            }
        except (json.JSONDecodeError, IOError):
            return {"status": "ACTIVE", "reason": "unreadable", "activated_at": ""}
    return {"status": "INACTIVE", "reason": "", "activated_at": ""}


def _get_budget_state():
    config = _load_json(BUDGET_CONFIG_PATH, {})
    daily = _load_json(DAILY_BUDGET_PATH, {})

    daily_limit = config.get("daily_goal_limit", daily.get("daily_limit", 0))
    used = daily.get("used", 0)
    remaining = max(0, daily_limit - used)
    reset_time = daily.get("reset_at", "")

    return {
        "daily_limit": daily_limit,
        "used": used,
        "remaining": remaining,
        "reset_at": reset_time,
    }


def _get_trigger_queue_count():
    data = _load_json(TRIGGER_QUEUE_PATH, {"goals": []})
    return len(data.get("goals", []))


def _get_pending_approval_count():
    data = _load_json(PENDING_APPROVAL_PATH, {"goals": []})
    return len(data.get("goals", []))


def _get_escalation_count():
    data = _load_json(ESCALATION_QUEUE_PATH, {"entries": []})
    entries = data.get("entries", [])
    return len([e for e in entries if e.get("status") == "ESCALATED"])


def _get_improvement_suggestions_count():
    data = _load_json(IMPROVEMENT_SUGGESTIONS_PATH, {"suggestions": []})
    suggestions = data.get("suggestions", [])
    return len([s for s in suggestions if s.get("status") == "PENDING_HUMAN_REVIEW"])


def _get_last_cycle_log_entries(count=5):
    entries = []
    if CYCLE_LOG_PATH.exists():
        try:
            with open(CYCLE_LOG_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entries.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
        except IOError:
            pass
    # Return last N entries
    return entries[-count:] if len(entries) > count else entries


def _get_last_notifications(count=3):
    entries = []
    if NOTIFICATIONS_PATH.exists():
        try:
            with open(NOTIFICATIONS_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entries.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
        except IOError:
            pass
    # Return last N unread entries
    unread = [e for e in entries if not e.get("read", False)]
    return unread[-count:] if len(unread) > count else unread


def status():
    """Return full governance state as dict."""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "kill_switch": _get_kill_switch_state(),
        "budget": _get_budget_state(),
        "trigger_queue_pending": _get_trigger_queue_count(),
        "pending_human_approval": _get_pending_approval_count(),
        "escalation_queue_unresolved": _get_escalation_count(),
        "improvement_suggestions_pending": _get_improvement_suggestions_count(),
        "last_cycle_log_entries": _get_last_cycle_log_entries(5),
        "last_notifications": _get_last_notifications(3),
    }


def _print_human_readable(state):
    """Print human-readable dashboard."""
    print("=" * 60)
    print("  PROJECT-S GOVERNANCE DASHBOARD")
    print(f"  {state['timestamp']}")
    print("=" * 60)

    # Kill switch
    ks = state["kill_switch"]
    ks_status = ks["status"]
    print(f"\n[{'!!' if ks_status == 'ACTIVE' else 'OK'}] Kill Switch: {ks_status}", end="")
    if ks.get("reason"):
        print(f" — {ks['reason']}", end="")
    print()

    # Budget
    bud = state["budget"]
    print(f"[B] Budget: {bud['used']}/{bud['daily_limit']} used, {bud['remaining']} remaining", end="")
    if bud.get("reset_at"):
        print(f" (resets: {bud['reset_at']})", end="")
    print()

    # Queues
    print(f"[Q] Trigger Queue: {state['trigger_queue_pending']} pending")
    print(f"[Q] Pending Human Approval: {state['pending_human_approval']}")
    print(f"[Q] Escalation Queue: {state['escalation_queue_unresolved']} unresolved")
    print(f"[Q] Improvement Suggestions: {state['improvement_suggestions_pending']} pending review")

    # Last cycle log entries
    cycle = state.get("last_cycle_log_entries", [])
    if cycle:
        print(f"\n[C] Last {len(cycle)} cycle log entries:")
        for entry in cycle:
            event = entry.get("event", "?")
            run_id = entry.get("run_id", "?")
            ts = entry.get("logged_at", entry.get("timestamp", "?"))
            result = entry.get("result", {})
            status_str = result.get("status", "") if isinstance(result, dict) else ""
            print(f"  {event} | {run_id} | {status_str} | {ts}")

    # Last notifications
    notifs = state.get("last_notifications", [])
    if notifs:
        print(f"\n[N] Last {len(notifs)} unread notifications:")
        for n in notifs:
            etype = n.get("event_type", "?")
            gid = n.get("goal_id", "")
            msg = n.get("message", "")
            ts = n.get("timestamp", "?")
            print(f"  {etype} | {gid} | {msg[:60]} | {ts}")

    print("\n" + "=" * 60)


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python dashboard.py status [--json]")
        print("  python dashboard.py watch --interval 30")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "status":
        state = status()
        if "--json" in sys.argv:
            print(json.dumps(state, indent=2, ensure_ascii=False))
        else:
            _print_human_readable(state)

    elif cmd == "watch":
        interval = 30
        if "--interval" in sys.argv:
            idx = sys.argv.index("--interval")
            if idx + 1 < len(sys.argv):
                interval = int(sys.argv[idx + 1])

        print(f"Dashboard watch mode (refresh every {interval}s). Ctrl+C to stop.")
        try:
            while True:
                # Clear screen (ANSI)
                sys.stdout.write("\033[2J\033[H")
                state = status()
                _print_human_readable(state)
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nStopped.")

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()