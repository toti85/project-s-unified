"""
MS-AO4 AO4.4 — Unit Tests for Production Monitoring Dashboard

Tests:
  1. status() returns all required fields
  2. JSON mode produces valid JSON
  3. Missing files handled gracefully (empty state, no crash)
  4. kill switch state reflected correctly
  5. budget state reflected correctly

All tests use real on-disk fixtures, no mocks.
"""

import json
import os
import sys
import shutil
import unittest
from pathlib import Path
from datetime import datetime, timezone
from io import StringIO

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

SANDBOX_DIR = Path(__file__).parent / "test_dashboard_fixtures"
TEST_KILL_SWITCH = SANDBOX_DIR / "KILL_SWITCH"
TEST_BUDGET_CONFIG = SANDBOX_DIR / "budget_config.json"
TEST_DAILY_BUDGET = SANDBOX_DIR / "daily_budget.json"
TEST_TRIGGER_QUEUE = SANDBOX_DIR / "trigger_queue.json"
TEST_PENDING_APPROVAL = SANDBOX_DIR / "pending_human_approval.json"
TEST_ESCALATION = SANDBOX_DIR / "escalation_queue.json"
TEST_IMPROVEMENT = SANDBOX_DIR / "improvement_suggestions.json"
TEST_CYCLE_LOG = SANDBOX_DIR / "cycle_log.jsonl"
TEST_NOTIFICATIONS = SANDBOX_DIR / "notifications.jsonl"


def _setup():
    SANDBOX_DIR.mkdir(parents=True, exist_ok=True)


def _cleanup():
    if SANDBOX_DIR.exists():
        shutil.rmtree(SANDBOX_DIR)


class TestDashboard(unittest.TestCase):
    """Tests for dashboard.py"""

    @classmethod
    def setUpClass(cls):
        _setup()
        import orchestrator_runtime.governance.dashboard as db
        db.KILL_SWITCH_PATH = TEST_KILL_SWITCH
        db.BUDGET_CONFIG_PATH = TEST_BUDGET_CONFIG
        db.DAILY_BUDGET_PATH = TEST_DAILY_BUDGET
        db.TRIGGER_QUEUE_PATH = TEST_TRIGGER_QUEUE
        db.PENDING_APPROVAL_PATH = TEST_PENDING_APPROVAL
        db.ESCALATION_QUEUE_PATH = TEST_ESCALATION
        db.IMPROVEMENT_SUGGESTIONS_PATH = TEST_IMPROVEMENT
        db.CYCLE_LOG_PATH = TEST_CYCLE_LOG
        db.NOTIFICATIONS_PATH = TEST_NOTIFICATIONS
        cls.db = db

    @classmethod
    def tearDownClass(cls):
        _cleanup()

    def test_01_status_returns_all_fields(self):
        """status() returns all required fields."""
        state = self.db.status()

        required_fields = [
            "timestamp", "kill_switch", "budget",
            "trigger_queue_pending", "pending_human_approval",
            "escalation_queue_unresolved", "improvement_suggestions_pending",
            "last_cycle_log_entries", "last_notifications",
        ]
        for field in required_fields:
            self.assertIn(field, state, f"Missing field: {field}")

    def test_02_json_mode_valid(self):
        """JSON mode produces valid JSON."""
        state = self.db.status()
        json_str = json.dumps(state, indent=2, ensure_ascii=False)
        # Verify it parses back
        parsed = json.loads(json_str)
        self.assertEqual(parsed["timestamp"], state["timestamp"])

    def test_03_missing_files_no_crash(self):
        """Missing files handled gracefully (empty state, no crash)."""
        # Ensure all test files are missing
        for f in [TEST_KILL_SWITCH, TEST_BUDGET_CONFIG, TEST_DAILY_BUDGET,
                  TEST_TRIGGER_QUEUE, TEST_PENDING_APPROVAL, TEST_ESCALATION,
                  TEST_IMPROVEMENT, TEST_CYCLE_LOG, TEST_NOTIFICATIONS]:
            if f.exists():
                f.unlink()

        # Should not crash
        state = self.db.status()
        self.assertIn("timestamp", state)
        self.assertEqual(state["kill_switch"]["status"], "INACTIVE")
        self.assertEqual(state["budget"]["daily_limit"], 0)
        self.assertEqual(state["trigger_queue_pending"], 0)

    def test_04_kill_switch_state_reflected(self):
        """kill switch state reflected correctly."""
        # Active
        with open(TEST_KILL_SWITCH, "w", encoding="utf-8") as f:
            json.dump({"reason": "test", "activated_at": "2026-06-02T00:00:00Z"}, f)

        state = self.db.status()
        self.assertEqual(state["kill_switch"]["status"], "ACTIVE")
        self.assertEqual(state["kill_switch"]["reason"], "test")

        # Inactive
        TEST_KILL_SWITCH.unlink()
        state = self.db.status()
        self.assertEqual(state["kill_switch"]["status"], "INACTIVE")

    def test_05_budget_state_reflected(self):
        """budget state reflected correctly."""
        # Write budget config and daily budget
        with open(TEST_BUDGET_CONFIG, "w", encoding="utf-8") as f:
            json.dump({"daily_goal_limit": 10}, f)
        with open(TEST_DAILY_BUDGET, "w", encoding="utf-8") as f:
            json.dump({"used": 3, "reset_at": "2026-06-03T00:00:00Z"}, f)

        state = self.db.status()
        self.assertEqual(state["budget"]["daily_limit"], 10)
        self.assertEqual(state["budget"]["used"], 3)
        self.assertEqual(state["budget"]["remaining"], 7)
        self.assertEqual(state["budget"]["reset_at"], "2026-06-03T00:00:00Z")


if __name__ == "__main__":
    unittest.main(verbosity=2)