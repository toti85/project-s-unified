"""
MS-AO2 Operator Notification System — AO2.2

File-based notification system for governance events.
Primary: append-only JSONL feed in orchestrator_runtime/notifications/feed.jsonl

Event types:
  GOAL_APPROVED, GOAL_DONE, GOAL_FAILED, ESCALATION,
  SELF_STATE_UPDATED, BUDGET_WARNING

Usage:
    from orchestrator_runtime.governance.notifier import Notifier
    n = Notifier()
    n.notify("GOAL_DONE", goal_id="GOAL_001", message="PASS")
    unread = n.get_unread()
    stats = n.summary()
"""

import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

NOTIFICATIONS_DIR = Path(__file__).parent.parent / "notifications"
FEED_PATH = NOTIFICATIONS_DIR / "feed.jsonl"
STATE_PATH = NOTIFICATIONS_DIR / "state.json"

EVENT_TYPES = [
    "GOAL_APPROVED", "GOAL_DONE", "GOAL_FAILED",
    "ESCALATION", "SELF_STATE_UPDATED", "BUDGET_WARNING",
]

SEVERITY_MAP = {
    "GOAL_APPROVED": "INFO",
    "GOAL_DONE": "INFO",
    "GOAL_FAILED": "ERROR",
    "ESCALATION": "WARN",
    "SELF_STATE_UPDATED": "INFO",
    "BUDGET_WARNING": "WARN",
}


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


class Notifier:
    def __init__(self):
        NOTIFICATIONS_DIR.mkdir(parents=True, exist_ok=True)
        if not FEED_PATH.exists():
            FEED_PATH.touch()

    def notify(self, event_type, goal_id=None, message="", severity=None):
        """
        Append a notification entry to the feed.

        Args:
            event_type: One of GOAL_APPROVED, GOAL_DONE, etc.
            goal_id: Optional goal identifier
            message: Human-readable message
            severity: INFO/WARN/ERROR (auto-assigned if None)

        Returns:
            dict with the notification entry
        """
        if severity is None:
            severity = SEVERITY_MAP.get(event_type, "INFO")

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "goal_id": goal_id,
            "message": message,
            "severity": severity,
            "read": False,
        }

        with open(FEED_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        return entry

    def get_unread(self):
        """Return unread notification entries."""
        if not FEED_PATH.exists():
            return []

        entries = []
        with open(FEED_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entry = json.loads(line)
                        if not entry.get("read", False):
                            entries.append(entry)
                    except json.JSONDecodeError:
                        continue

        return entries

    def mark_all_read(self):
        """Mark all entries as read. Rewrites the feed."""
        if not FEED_PATH.exists():
            return 0

        entries = []
        count = 0
        with open(FEED_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entry = json.loads(line)
                        if not entry.get("read", False):
                            entry["read"] = True
                            count += 1
                        entries.append(entry)
                    except json.JSONDecodeError:
                        continue

        if count > 0:
            with open(FEED_PATH, "w", encoding="utf-8") as f:
                for entry in entries:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        return count

    def summary(self, hours=24):
        """
        Return stats for the last N hours.

        Returns:
            dict with counts by event_type and severity
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        counts = {
            "total": 0,
            "unread": 0,
            "by_type": {},
            "by_severity": {"INFO": 0, "WARN": 0, "ERROR": 0},
            "recent": [],
        }

        if not FEED_PATH.exists():
            return counts

        with open(FEED_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # Check time window
                try:
                    ts = datetime.fromisoformat(entry["timestamp"])
                except (ValueError, KeyError):
                    continue

                if ts < cutoff:
                    continue

                counts["total"] += 1
                if not entry.get("read", False):
                    counts["unread"] += 1

                et = entry.get("event_type", "UNKNOWN")
                counts["by_type"][et] = counts["by_type"].get(et, 0) + 1

                sev = entry.get("severity", "INFO")
                if sev in counts["by_severity"]:
                    counts["by_severity"][sev] += 1

                counts["recent"].append({
                    "timestamp": entry["timestamp"],
                    "event_type": et,
                    "severity": sev,
                    "message": entry.get("message", ""),
                })

        # Sort recent by timestamp descending
        counts["recent"] = sorted(counts["recent"], key=lambda x: x["timestamp"], reverse=True)[:20]

        return counts


if __name__ == "__main__":
    n = Notifier()

    # Demo notifications
    n.notify("GOAL_APPROVED", goal_id="GOAL_001", message="LOW risk goal auto-approved")
    n.notify("GOAL_DONE", goal_id="GOAL_001", message="PASS — goal completed successfully")
    n.notify("ESCALATION", goal_id="GOAL_004", message="HIGH risk goal requires human review")
    n.notify("SELF_STATE_UPDATED", message="Milestone #36 added via apply_updates()")

    print("Feed entries:", sum(1 for _ in open(FEED_PATH, encoding="utf-8")))
    print("Unread:", len(n.get_unread()))

    stats = n.summary()
    print(f"\n24h summary: {stats['total']} total, {stats['unread']} unread")
    print(f"By type: {stats['by_type']}")
    print(f"By severity: {stats['by_severity']}")