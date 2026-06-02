"""
MS-AO4 AO4.3 — Unit Tests for Self-Improvement Suggestion Loop

Tests:
  1. Analyzer reads escalation_queue + cycle_log → generates suggestion
  2. Suggestion always has auto_apply: false
  3. Suggestion always has requires_human_approval: true
  4. risk_classifier loads approved_adjustments when file exists
  5. risk_classifier uses defaults when file missing
  6. No self-modification without approved_adjustments.json

All tests use real on-disk fixtures, no mocks.
"""

import json
import os
import sys
import shutil
import unittest
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Sandbox test fixtures
SANDBOX_DIR = Path(__file__).parent / "test_improvement_fixtures"
TEST_ESCALATION = SANDBOX_DIR / "escalation_queue.json"
TEST_CYCLE_LOG = SANDBOX_DIR / "cycle_log.jsonl"
TEST_SUGGESTIONS = SANDBOX_DIR / "improvement_suggestions.json"
TEST_APPROVED_ADJ = SANDBOX_DIR / "approved_adjustments.json"


def _setup():
    SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
    for f in [TEST_SUGGESTIONS, TEST_APPROVED_ADJ]:
        if f.exists():
            f.unlink()


def _cleanup():
    if SANDBOX_DIR.exists():
        shutil.rmtree(SANDBOX_DIR)


class TestImprovementAnalyzer(unittest.TestCase):
    """Tests for improvement_analyzer.py"""

    @classmethod
    def setUpClass(cls):
        _setup()
        import orchestrator_runtime.governance.improvement_analyzer as ia
        ia.ESCALATION_QUEUE_PATH = TEST_ESCALATION
        ia.CYCLE_LOG_PATH = TEST_CYCLE_LOG
        ia.SUGGESTIONS_PATH = TEST_SUGGESTIONS
        cls.ia = ia

    @classmethod
    def tearDownClass(cls):
        _cleanup()

    def setUp(self):
        for f in [TEST_SUGGESTIONS]:
            if f.exists():
                f.unlink()

    def test_01_analyzer_generates_suggestion(self):
        """Analyzer reads escalation_queue + cycle_log → generates suggestion."""
        # Write escalation queue with a failed goal
        esc = {
            "entries": [{
                "goal_id": "TEST_FAIL_001",
                "reason": "Max retries exhausted",
                "attempts": 3,
                "escalated_at": datetime.now(timezone.utc).isoformat(),
                "status": "ESCALATED",
            }]
        }
        with open(TEST_ESCALATION, "w", encoding="utf-8") as f:
            json.dump(esc, f)

        # Write cycle log with FAIL verdicts
        log_entries = [
            {
                "event": "verdict",
                "result": {
                    "goal_id": "TEST_FAIL_001",
                    "status": "FAIL",
                    "action": "RETRY",
                    "reason": "dependencies still missing",
                },
            },
            {
                "event": "verdict",
                "result": {
                    "goal_id": "TEST_FAIL_001",
                    "status": "FAIL",
                    "action": "ESCALATED",
                    "reason": "Max retries exhausted",
                },
            },
        ]
        with open(TEST_CYCLE_LOG, "w", encoding="utf-8") as f:
            for entry in log_entries:
                f.write(json.dumps(entry) + "\n")

        suggestions = self.ia.analyze_failures()

        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0]["goal_id"], "TEST_FAIL_001")
        self.assertIn(suggestions[0]["failure_pattern"], ["prompt_quality", "retry_strategy", "risk_misclassification"])

    def test_02_auto_apply_always_false(self):
        """Suggestion always has auto_apply: false."""
        esc = {
            "entries": [{
                "goal_id": "TEST_AUTO_001",
                "reason": "Max retries",
                "attempts": 3,
                "escalated_at": datetime.now(timezone.utc).isoformat(),
                "status": "ESCALATED",
            }]
        }
        with open(TEST_ESCALATION, "w", encoding="utf-8") as f:
            json.dump(esc, f)

        log_entries = [
            {"event": "verdict", "result": {"goal_id": "TEST_AUTO_001", "status": "FAIL", "action": "ESCALATED", "reason": "Max retries"}},
        ]
        with open(TEST_CYCLE_LOG, "w", encoding="utf-8") as f:
            for entry in log_entries:
                f.write(json.dumps(entry) + "\n")

        suggestions = self.ia.analyze_failures()
        for s in suggestions:
            self.assertFalse(s["auto_apply"], "auto_apply must always be False")

    def test_03_requires_human_approval_always_true(self):
        """Suggestion always has requires_human_approval: true."""
        esc = {
            "entries": [{
                "goal_id": "TEST_HUMAN_001",
                "reason": "Max retries",
                "attempts": 3,
                "escalated_at": datetime.now(timezone.utc).isoformat(),
                "status": "ESCALATED",
            }]
        }
        with open(TEST_ESCALATION, "w", encoding="utf-8") as f:
            json.dump(esc, f)

        log_entries = [
            {"event": "verdict", "result": {"goal_id": "TEST_HUMAN_001", "status": "FAIL", "action": "ESCALATED", "reason": "Max retries"}},
        ]
        with open(TEST_CYCLE_LOG, "w", encoding="utf-8") as f:
            for entry in log_entries:
                f.write(json.dumps(entry) + "\n")

        suggestions = self.ia.analyze_failures()
        for s in suggestions:
            self.assertTrue(s["requires_human_approval"], "requires_human_approval must always be True")


class TestThresholdAdjustments(unittest.TestCase):
    """Tests for risk_classifier load_threshold_adjustments"""

    @classmethod
    def setUpClass(cls):
        _setup()
        import orchestrator_runtime.governance.risk_classifier as rc
        rc._APPROVED_ADJUSTMENTS_PATH = TEST_APPROVED_ADJ
        cls.rc = rc

    @classmethod
    def tearDownClass(cls):
        _cleanup()

    def test_04_loads_approved_adjustments(self):
        """risk_classifier loads approved_adjustments when file exists."""
        # Write approved adjustments
        adj = {
            "approved": [
                {"key": "MEDIUM_AUTO_APPROVE", "value": True, "approved_by": "human", "approved_at": datetime.now(timezone.utc).isoformat()},
            ]
        }
        with open(TEST_APPROVED_ADJ, "w", encoding="utf-8") as f:
            json.dump(adj, f)

        thresholds = self.rc.load_threshold_adjustments()
        self.assertTrue(thresholds["MEDIUM_AUTO_APPROVE"], "Approved adjustment should be applied")

    def test_05_uses_defaults_when_missing(self):
        """risk_classifier uses defaults when approved_adjustments.json missing."""
        if TEST_APPROVED_ADJ.exists():
            TEST_APPROVED_ADJ.unlink()

        thresholds = self.rc.load_threshold_adjustments()
        self.assertEqual(thresholds["MEDIUM_AUTO_APPROVE"], False, "Default should be False")
        self.assertEqual(thresholds["LOW_AUTO_APPROVE"], True, "Default should be True")

    def test_06_no_self_modification_without_approved(self):
        """No self-modification without approved_adjustments.json."""
        if TEST_APPROVED_ADJ.exists():
            TEST_APPROVED_ADJ.unlink()

        thresholds = self.rc.load_threshold_adjustments()
        # Should return defaults unchanged
        self.assertEqual(thresholds, {"MEDIUM_AUTO_APPROVE": False, "LOW_AUTO_APPROVE": True})


if __name__ == "__main__":
    unittest.main(verbosity=2)