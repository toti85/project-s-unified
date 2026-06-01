"""
test_verdict_evaluator.py — Verdict Evaluator Unit Tests
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from src.orchestrator.verdict_schema import VerdictStatus


class TestVerdictEvaluator(unittest.TestCase):
    """Test heuristic evaluation logic from FilesystemOrchestrator."""

    def setUp(self):
        from src.orchestrator.filesystem_orchestrator import FilesystemOrchestrator
        import tempfile
        from pathlib import Path
        self.tmpdir = tempfile.mkdtemp()
        self.orch = FilesystemOrchestrator(runtime_root=Path(self.tmpdir))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_pass_for_clear_successful_output(self):
        """Evaluator should return PASS for clear successful output."""
        output = (
            "All tests passed.\n"
            "Ran 3 tests in 0.023s\n"
            "OK\n"
            "Files created successfully."
        )
        verdict = self.orch._heuristic_evaluate("TEST", "goal", output)
        self.assertEqual(verdict.status, VerdictStatus.PASS)
        self.assertGreaterEqual(verdict.confidence, 0.8)

    def test_needs_human_for_ambiguous_output(self):
        """Evaluator should return NEEDS_HUMAN for ambiguous output."""
        output = "Some things were done. Not sure about tests."
        verdict = self.orch._heuristic_evaluate("TEST", "goal", output)
        self.assertIn(verdict.status, [VerdictStatus.NEEDS_HUMAN, VerdictStatus.FIX])

    def test_fix_for_failing_tests(self):
        """Evaluator should return FIX or NEEDS_HUMAN for failing tests."""
        output = "Ran 3 tests. FAILED (failures=1). Error in test_foo."
        verdict = self.orch._heuristic_evaluate("TEST", "goal", output)
        self.assertIn(verdict.status, [VerdictStatus.FIX, VerdictStatus.NEEDS_HUMAN])
        self.assertLess(verdict.confidence, 0.8)


if __name__ == "__main__":
    unittest.main()