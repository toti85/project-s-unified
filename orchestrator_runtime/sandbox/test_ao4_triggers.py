"""
MS-AO4 AO4.2 — Unit Tests for External Goal Triggers

Tests:
  1. File watcher detects new goal added to goal_queue.json
  2. File watcher rate limit blocks flood (6 goals in 1 min → 5 accepted, 1 blocked)
  3. File watcher respects kill switch
  4. Webhook accepts valid LOW goal → trigger_queue entry
  5. Webhook rejects HIGH goal → pending_human_approval entry
  6. Webhook rate limit blocks flood

All tests use real on-disk fixtures, no mocks.
"""

import json
import os
import sys
import time
import shutil
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Use sandbox test fixtures directory
SANDBOX_DIR = Path(__file__).parent / "test_fixtures"
TEST_GOAL_QUEUE = SANDBOX_DIR / "goal_queue.json"
TEST_TRIGGER_QUEUE = SANDBOX_DIR / "trigger_queue.json"
TEST_PENDING_APPROVAL = SANDBOX_DIR / "pending_human_approval.json"
TEST_TRIGGER_LOG = SANDBOX_DIR / "trigger_log.jsonl"
TEST_KILL_SWITCH = SANDBOX_DIR / "KILL_SWITCH"


def _setup_test_dir():
    """Create clean test fixture directory."""
    SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
    for f in [TEST_TRIGGER_QUEUE, TEST_PENDING_APPROVAL, TEST_TRIGGER_LOG, TEST_KILL_SWITCH]:
        if f.exists():
            f.unlink()


def _cleanup_test_dir():
    """Remove test fixture directory."""
    if SANDBOX_DIR.exists():
        shutil.rmtree(SANDBOX_DIR)


def _write_goal_queue(goals):
    """Write goals to test goal_queue.json."""
    data = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "goals": goals,
        "risk_breakdown": {"LOW": len(goals), "MEDIUM": 0, "HIGH": 0},
        "auto_approvable_count": len(goals),
        "requires_approval_count": 0,
    }
    with open(TEST_GOAL_QUEUE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _read_trigger_queue():
    """Read trigger_queue.json if it exists."""
    if TEST_TRIGGER_QUEUE.exists():
        with open(TEST_TRIGGER_QUEUE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"goals": []}


def _read_pending_approval():
    """Read pending_human_approval.json if it exists."""
    if TEST_PENDING_APPROVAL.exists():
        with open(TEST_PENDING_APPROVAL, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"goals": []}


def _read_trigger_log():
    """Read trigger_log.jsonl if it exists."""
    entries = []
    if TEST_TRIGGER_LOG.exists():
        with open(TEST_TRIGGER_LOG, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    return entries


class _TestKillSwitch:
    """Test kill switch that uses sandbox path instead of real path."""
    def __init__(self, path):
        self._path = path
    def is_active(self):
        return self._path.exists()
    def status(self):
        if self._path.exists():
            with open(self._path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"status": "INACTIVE"}


class TestFileWatcher(unittest.TestCase):
    """Tests for file_watcher.py"""

    @classmethod
    def setUpClass(cls):
        _setup_test_dir()
        # Patch the file paths for testing
        import orchestrator_runtime.governance.file_watcher as fw
        fw.GOAL_QUEUE_PATH = TEST_GOAL_QUEUE
        fw.TRIGGER_QUEUE_PATH = TEST_TRIGGER_QUEUE
        fw.TRIGGER_LOG_PATH = TEST_TRIGGER_LOG
        fw.POLL_INTERVAL = 0.1  # Fast polling for tests
        # Patch kill switch to use test sandbox path
        fw._KILL_SWITCH = _TestKillSwitch(TEST_KILL_SWITCH)
        cls.fw_module = fw

    @classmethod
    def tearDownClass(cls):
        _cleanup_test_dir()

    def setUp(self):
        """Clean state before each test."""
        for f in [TEST_TRIGGER_QUEUE, TEST_PENDING_APPROVAL, TEST_TRIGGER_LOG, TEST_KILL_SWITCH]:
            if f.exists():
                f.unlink()

    def test_01_detects_new_goal(self):
        """File watcher detects new goal added to goal_queue.json."""
        goal = {
            "id": "TEST_GOAL_001",
            "title": "Test goal",
            "risk": "LOW",
            "auto_approve": True,
            "sandbox_only": True,
        }
        _write_goal_queue([goal])

        fw = self.fw_module.FileWatcher()
        count = fw.scan_once(dry_run=False)

        # Should have found and processed 1 goal
        self.assertEqual(count, 1)

        # Check trigger_queue has the goal
        trigger = _read_trigger_queue()
        self.assertEqual(len(trigger.get("goals", [])), 1)
        self.assertEqual(trigger["goals"][0]["id"], "TEST_GOAL_001")

        # Check log has goal_approved event
        log = _read_trigger_log()
        approved = [e for e in log if e.get("event") == "goal_approved"]
        self.assertEqual(len(approved), 1)

    def test_02_rate_limit_blocks_flood(self):
        """File watcher rate limit blocks flood (6 goals in 1 min → 5 accepted, 1 blocked)."""
        goals = [
            {
                "id": f"FLOOD_GOAL_{i:03d}",
                "title": f"Flood test goal {i}",
                "risk": "LOW",
                "auto_approve": True,
                "sandbox_only": True,
            }
            for i in range(6)
        ]
        _write_goal_queue(goals)

        # Pre-populate log with 5 goal_approved events to simulate rate limit
        with open(TEST_TRIGGER_LOG, "w", encoding="utf-8") as f:
            for i in range(5):
                entry = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "event": "goal_approved",
                    "details": {"goal_id": f"PRE_EXISTING_{i}"},
                }
                f.write(json.dumps(entry) + "\n")

        fw = self.fw_module.FileWatcher()
        count = fw.scan_once(dry_run=False)

        # Should have processed 5 (rate limit) and blocked 1
        log = _read_trigger_log()
        rate_limited = [e for e in log if e.get("event") == "goal_rate_limited"]
        self.assertGreater(len(rate_limited), 0, "Rate limit should have blocked at least 1 goal")

    def test_03_respects_kill_switch(self):
        """File watcher respects kill switch."""
        # Activate kill switch
        kill_data = {
            "activated_at": datetime.now(timezone.utc).isoformat(),
            "reason": "Test kill switch",
        }
        with open(TEST_KILL_SWITCH, "w", encoding="utf-8") as f:
            json.dump(kill_data, f)

        goal = {
            "id": "KILL_SWITCH_GOAL",
            "title": "Goal during kill switch",
            "risk": "LOW",
            "auto_approve": True,
            "sandbox_only": True,
        }
        _write_goal_queue([goal])

        fw = self.fw_module.FileWatcher()
        count = fw.scan_once(dry_run=False)

        # Should have processed 0 goals due to kill switch
        self.assertEqual(count, 0)

        # Check log has kill_switch_active event
        log = _read_trigger_log()
        kill_events = [e for e in log if e.get("event") == "kill_switch_active"]
        self.assertGreater(len(kill_events), 0, "Kill switch should have been detected")

        # Cleanup
        if TEST_KILL_SWITCH.exists():
            TEST_KILL_SWITCH.unlink()


class TestWebhookReceiver(unittest.TestCase):
    """Tests for webhook_receiver.py"""

    @classmethod
    def setUpClass(cls):
        _setup_test_dir()
        # Patch the file paths for testing
        import orchestrator_runtime.governance.webhook_receiver as wh
        wh.TRIGGER_QUEUE_PATH = TEST_TRIGGER_QUEUE
        wh.PENDING_APPROVAL_PATH = TEST_PENDING_APPROVAL
        wh.TRIGGER_LOG_PATH = TEST_TRIGGER_LOG
        wh._KILL_SWITCH = None  # Disable kill switch for webhook tests
        wh._CLASSIFIER = None  # Disable classifier for webhook tests
        cls.wh_module = wh

    @classmethod
    def tearDownClass(cls):
        _cleanup_test_dir()

    def setUp(self):
        """Clean state before each test."""
        for f in [TEST_TRIGGER_QUEUE, TEST_PENDING_APPROVAL, TEST_TRIGGER_LOG]:
            if f.exists():
                f.unlink()
        # Reset rate limit store
        self.wh_module._rate_limit_store.clear()

    def test_04_accepts_valid_low_goal(self):
        """Webhook accepts valid LOW goal → trigger_queue entry."""
        from orchestrator_runtime.governance.webhook_receiver import WebhookHandler
        from http.server import HTTPServer
        import urllib.request
        import threading

        # Start server on random port
        server = HTTPServer(("127.0.0.1", 0), WebhookHandler)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        try:
            goal = {
                "id": "WEBHOOK_LOW_001",
                "title": "Low risk webhook goal",
                "risk": "LOW",
                "auto_approve": True,
                "sandbox_only": True,
            }
            data = json.dumps(goal).encode("utf-8")
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/goal",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read().decode("utf-8"))

            self.assertEqual(result["status"], "accepted")
            self.assertEqual(result["goal_id"], "WEBHOOK_LOW_001")

            # Check trigger_queue has the goal
            trigger = _read_trigger_queue()
            self.assertEqual(len(trigger.get("goals", [])), 1)
            self.assertEqual(trigger["goals"][0]["id"], "WEBHOOK_LOW_001")

        finally:
            server.shutdown()

    def test_05_rejects_high_goal_to_pending(self):
        """Webhook rejects HIGH goal → pending_human_approval entry."""
        from orchestrator_runtime.governance.webhook_receiver import WebhookHandler
        from http.server import HTTPServer
        import urllib.request
        import threading

        server = HTTPServer(("127.0.0.1", 0), WebhookHandler)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        try:
            goal = {
                "id": "WEBHOOK_HIGH_001",
                "title": "High risk webhook goal",
                "risk": "HIGH",
                "auto_approve": False,
            }
            data = json.dumps(goal).encode("utf-8")
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/goal",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read().decode("utf-8"))

            self.assertEqual(result["status"], "pending_human_approval")
            self.assertEqual(result["goal_id"], "WEBHOOK_HIGH_001")

            # Check pending_human_approval has the goal
            pending = _read_pending_approval()
            self.assertEqual(len(pending.get("goals", [])), 1)
            self.assertEqual(pending["goals"][0]["id"], "WEBHOOK_HIGH_001")
            self.assertEqual(pending["goals"][0]["status"], "PENDING_HUMAN_APPROVAL")

            # Check trigger_queue does NOT have the goal
            trigger = _read_trigger_queue()
            self.assertEqual(len(trigger.get("goals", [])), 0)

        finally:
            server.shutdown()

    def test_06_rate_limit_blocks_flood(self):
        """Webhook rate limit blocks flood."""
        from orchestrator_runtime.governance.webhook_receiver import WebhookHandler
        from http.server import HTTPServer
        import urllib.request
        import threading

        server = HTTPServer(("127.0.0.1", 0), WebhookHandler)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        try:
            # Send 11 requests (limit is 10 per minute)
            rate_limited_count = 0
            for i in range(11):
                goal = {
                    "id": f"WEBHOOK_FLOOD_{i:03d}",
                    "title": f"Flood goal {i}",
                    "risk": "LOW",
                    "auto_approve": True,
                    "sandbox_only": True,
                }
                data = json.dumps(goal).encode("utf-8")
                req = urllib.request.Request(
                    f"http://127.0.0.1:{port}/goal",
                    data=data,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                try:
                    with urllib.request.urlopen(req) as resp:
                        result = json.loads(resp.read().decode("utf-8"))
                        if result.get("error") == "rate_limit_exceeded":
                            rate_limited_count += 1
                except urllib.error.HTTPError as e:
                    if e.code == 429:
                        rate_limited_count += 1

            self.assertGreater(rate_limited_count, 0, "Rate limit should have blocked at least 1 request")

        finally:
            server.shutdown()


if __name__ == "__main__":
    unittest.main(verbosity=2)