"""
MS-AO4 AO4.2 — File Watcher for External Goal Triggers

Watches orchestrator_runtime/goal_queue.json for changes.
On change: reads new goals, filters auto-approvable (LOW/MEDIUM + sandbox_only),
passes to risk_classifier, writes approved goals to trigger_queue.json.

Rules:
  - Rate limit: max 5 new goals per minute (flood protection)
  - Kill switch check before processing any trigger
  - Log all events to trigger_log.jsonl
  - start(dry_run=True) — detects changes but doesn't write trigger_queue
  - start(dry_run=False) — full processing

Usage:
  from orchestrator_runtime.governance.file_watcher import FileWatcher
  fw = FileWatcher()
  fw.start(dry_run=True)  # runs once then exits
"""

import json
import time
import hashlib
import threading
from pathlib import Path
from datetime import datetime, timezone

GOAL_QUEUE_PATH = Path(__file__).parent.parent / "goal_queue.json"
TRIGGER_QUEUE_PATH = Path(__file__).parent / "trigger_queue.json"
TRIGGER_LOG_PATH = Path(__file__).parent / "trigger_log.jsonl"

# Rate limit: max goals per minute
MAX_GOALS_PER_MINUTE = 5

# Poll interval in seconds
POLL_INTERVAL = 1.0

# Kill switch integration
try:
    from orchestrator_runtime.governance.kill_switch import KillSwitch
    _KILL_SWITCH = KillSwitch()
except ImportError:
    _KILL_SWITCH = None

# Risk classifier integration
try:
    from orchestrator_runtime.governance.risk_classifier import classify_goal
    _CLASSIFIER = classify_goal
except ImportError:
    _CLASSIFIER = None


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


def _log_event(event_type, details=None):
    """Append event to trigger_log.jsonl."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event_type,
        "details": details or {},
    }
    with open(TRIGGER_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _get_file_hash(path):
    """Get SHA-256 hash of file contents for change detection."""
    if not path.exists():
        return None
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _check_rate_limit():
    """Check if we're within the rate limit (max 5 goals per minute)."""
    log_entries = []
    if TRIGGER_LOG_PATH.exists():
        with open(TRIGGER_LOG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entry = json.loads(line)
                        if entry.get("event") == "goal_approved":
                            log_entries.append(entry)
                    except json.JSONDecodeError:
                        pass

    # Count goals approved in the last 60 seconds
    now = datetime.now(timezone.utc)
    recent_count = 0
    for entry in log_entries:
        try:
            ts = datetime.fromisoformat(entry.get("timestamp", ""))
            if (now - ts).total_seconds() < 60:
                recent_count += 1
        except (ValueError, TypeError):
            pass

    return recent_count < MAX_GOALS_PER_MINUTE, recent_count


def _is_auto_approvable(goal):
    """Check if a goal is auto-approvable (LOW/MEDIUM + sandbox_only or auto_approve)."""
    risk = goal.get("risk", "HIGH")
    auto_approve = goal.get("auto_approve", False)
    sandbox_only = goal.get("sandbox_only", False)

    if risk == "LOW" and auto_approve:
        return True
    if risk == "MEDIUM" and sandbox_only:
        return True
    if risk == "LOW" and sandbox_only:
        return True
    return False


class FileWatcher:
    def __init__(self):
        self._last_hash = None
        self._running = False

    def _check_kill_switch(self):
        """Check if kill switch is active."""
        if _KILL_SWITCH is not None and _KILL_SWITCH.is_active():
            status = _KILL_SWITCH.status()
            _log_event("kill_switch_active", {"reason": status.get("reason", "")})
            return True
        return False

    def _process_new_goals(self, dry_run):
        """Process new goals from goal_queue.json."""
        if self._check_kill_switch():
            return 0

        queue = _load_json(GOAL_QUEUE_PATH, {"goals": []})
        goals = queue.get("goals", [])

        # Load existing trigger queue to avoid duplicates
        trigger_queue = _load_json(TRIGGER_QUEUE_PATH, {"goals": []})
        existing_ids = {g.get("id") for g in trigger_queue.get("goals", [])}

        processed = 0
        for goal in goals:
            goal_id = goal.get("id", "")
            if goal_id in existing_ids:
                continue

            if not _is_auto_approvable(goal):
                _log_event("goal_skipped", {"goal_id": goal_id, "reason": "not_auto_approvable"})
                continue

            # Rate limit check
            within_limit, recent_count = _check_rate_limit()
            if not within_limit:
                _log_event("goal_rate_limited", {
                    "goal_id": goal_id,
                    "recent_count": recent_count,
                    "limit": MAX_GOALS_PER_MINUTE,
                })
                continue

            # Risk classifier check
            if _CLASSIFIER is not None:
                try:
                    result = _CLASSIFIER(goal_id)
                    if result.get("decision") == "REJECTED":
                        _log_event("goal_rejected", {"goal_id": goal_id, "reason": result.get("reason", "")})
                        continue
                except Exception as e:
                    _log_event("classifier_error", {"goal_id": goal_id, "error": str(e)})

            # Approve and add to trigger queue
            if not dry_run:
                trigger_queue["goals"].append(goal)
                _save_json(TRIGGER_QUEUE_PATH, trigger_queue)

            _log_event("goal_approved", {"goal_id": goal_id, "dry_run": dry_run})
            processed += 1

        return processed

    def scan_once(self, dry_run=True):
        """Scan goal_queue.json once for changes. Returns count of new goals found."""
        current_hash = _get_file_hash(GOAL_QUEUE_PATH)

        if current_hash == self._last_hash:
            return 0

        self._last_hash = current_hash
        _log_event("goal_queue_changed", {"hash": current_hash, "dry_run": dry_run})

        return self._process_new_goals(dry_run)

    def start(self, dry_run=True, max_scans=None):
        """
        Start watching goal_queue.json for changes.

        Args:
            dry_run: If True, detect changes but don't write trigger_queue
            max_scans: If set, stop after this many scans (useful for testing)
        """
        self._running = True
        self._last_hash = _get_file_hash(GOAL_QUEUE_PATH)
        _log_event("watcher_started", {"dry_run": dry_run})

        scans = 0
        while self._running:
            if max_scans is not None and scans >= max_scans:
                _log_event("watcher_stopped", {"reason": "max_scans_reached"})
                break

            time.sleep(POLL_INTERVAL)
            new_count = self.scan_once(dry_run)
            if new_count > 0:
                _log_event("scan_complete", {"new_goals": new_count})
            scans += 1

        _log_event("watcher_stopped", {"reason": "normal"})

    def stop(self):
        """Stop the file watcher."""
        self._running = False


if __name__ == "__main__":
    import sys

    fw = FileWatcher()
    dry_run = "--dry-run" in sys.argv or len(sys.argv) < 2
    timeout = None
    if "--timeout" in sys.argv:
        idx = sys.argv.index("--timeout")
        if idx + 1 < len(sys.argv):
            timeout = int(sys.argv[idx + 1])

    if "--scan-once" in sys.argv:
        count = fw.scan_once(dry_run=dry_run)
        print(f"Scan complete: {count} new goals found")
    else:
        print(f"File Watcher starting (dry_run={dry_run}, timeout={timeout}s)...")
        print(f"Watching: {GOAL_QUEUE_PATH}")
        print(f"Press Ctrl+C to stop")
        try:
            if timeout:
                def _timeout_stop():
                    time.sleep(timeout)
                    fw.stop()
                t = threading.Thread(target=_timeout_stop, daemon=True)
                t.start()
            fw.start(dry_run=dry_run)
        except KeyboardInterrupt:
            fw.stop()
            print("\nFile Watcher stopped")
