"""
MS-AO2 Notification CLI — AO2.2

Usage:
    python notify_cli.py unread    → prints unread notifications
    python notify_cli.py summary   → 24h stats
    python notify_cli.py clear     → marks all read
"""

import sys
import json
from orchestrator_runtime.governance.notifier import Notifier


def cmd_unread():
    n = Notifier()
    entries = n.get_unread()
    if not entries:
        print("No unread notifications.")
        return
    print(f"Unread notifications: {len(entries)}")
    print("-" * 60)
    for e in entries:
        ts = e.get("timestamp", "")[:19].replace("T", " ")
        et = e.get("event_type", "")
        gid = e.get("goal_id", "")
        sev = e.get("severity", "INFO")
        msg = e.get("message", "")
        gid_str = f" [{gid}]" if gid else ""
        print(f"  [{sev}] {et}{gid_str}")
        print(f"        {msg}")
        print(f"        {ts}")
        print()


def cmd_summary():
    n = Notifier()
    stats = n.summary(hours=24)
    print("=== 24h Notification Summary ===")
    print(f"Total: {stats['total']}")
    print(f"Unread: {stats['unread']}")
    print(f"\nBy type:")
    for et, count in sorted(stats["by_type"].items()):
        print(f"  {et}: {count}")
    print(f"\nBy severity:")
    for sev, count in stats["by_severity"].items():
        if count > 0:
            print(f"  {sev}: {count}")
    if stats["recent"]:
        print(f"\nRecent (last 20):")
        for r in stats["recent"][:10]:
            ts = r["timestamp"][:19].replace("T", " ")
            print(f"  [{r['severity']}] {ts} {r['event_type']} — {r['message'][:60]}")


def cmd_budget():
    from orchestrator_runtime.governance.budget_manager import BudgetManager
    bm = BudgetManager()
    status = bm.get_status()
    print(f"Daily budget: {status['count']}/{status['limit']} used")
    print(f"Remaining: {status['remaining']}")
    print(f"Can run: {'YES' if status['can_run'] else 'NO'}")
    print(f"Date: {status['date']}")


def cmd_kill():
    from orchestrator_runtime.governance.kill_switch import KillSwitch
    ks = KillSwitch()
    reason = sys.argv[2] if len(sys.argv) > 2 else "Manual kill switch"
    ks.activate(reason)
    print(f"Kill switch ACTIVATED: {reason}")


def cmd_resume():
    from orchestrator_runtime.governance.kill_switch import KillSwitch
    ks = KillSwitch()
    result = ks.deactivate()
    print(f"Kill switch: {result['status']}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python notify_cli.py <unread|summary|clear|budget|kill|resume>")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    if cmd == "unread":
        cmd_unread()
    elif cmd == "summary":
        cmd_summary()
    elif cmd == "clear":
        cmd_clear()
    elif cmd == "budget":
        cmd_budget()
    elif cmd == "kill":
        cmd_kill()
    elif cmd == "resume":
        cmd_resume()
    else:
        print(f"Unknown command: {cmd}")
        print("Usage: python notify_cli.py <unread|summary|clear|budget|kill|resume>")
        sys.exit(1)


if __name__ == "__main__":
    main()