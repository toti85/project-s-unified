"""
test_filesystem_orchestrator.py — Filesystem Orchestrator Unit Tests
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from src.orchestrator.filesystem_orchestrator import FilesystemOrchestrator, Goal, Verdict
from src.orchestrator.verdict_schema import VerdictStatus


class TestFilesystemOrchestrator(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        runtime_root = Path(self.tmpdir)
        self.orch = FilesystemOrchestrator(runtime_root=runtime_root)
        # Ensure subdirs exist
        self.orch.inbox.mkdir(parents=True, exist_ok=True)
        self.orch.cline_inbox.mkdir(parents=True, exist_ok=True)
        self.orch.cline_outbox.mkdir(parents=True, exist_ok=True)
        self.orch.sandbox.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_create_run_and_draft_prompt(self):
        """Orchestrator should create a run and draft a prompt."""
        goal = Goal(text="Test goal", raw="Test goal")
        run_id = self.orch.create_run(goal)
        self.assertTrue(run_id.startswith("FA1_"))
        prompt = self.orch.draft_prompt(run_id)
        self.assertIn(run_id, prompt)
        self.assertTrue((self.orch.cline_inbox / "next_prompt.md").exists())

    def test_read_goal_from_inbox(self):
        """Orchestrator should read goal from inbox/goal.md."""
        goal_text = "Test goal text"
        (self.orch.inbox / "goal.md").write_text(goal_text, encoding="utf-8")
        goal = self.orch.read_goal()
        self.assertIsNotNone(goal)
        self.assertIn(goal_text, goal.raw)

    def test_receive_output(self):
        """Orchestrator should receive output from cline_outbox."""
        goal = Goal(text="Test", raw="Test")
        run_id = self.orch.create_run(goal)
        # Must go through proper state flow: draft prompt (auto) -> in_progress
        self.orch.draft_prompt(run_id, auto_mode=True)
        output_text = "Test output from Cline"
        (self.orch.cline_outbox / "last_output.md").write_text(output_text, encoding="utf-8")
        received = self.orch.receive_output(run_id)
        self.assertEqual(received, output_text)

    def test_evaluate_output_returns_verdict(self):
        """Orchestrator should return a verdict for output."""
        goal = Goal(text="Test", raw="Test")
        run_id = self.orch.create_run(goal)
        # auto_mode=True skips HUMAN_REVIEW, goes straight to IN_PROGRESS
        self.orch.draft_prompt(run_id, auto_mode=True)
        (self.orch.cline_outbox / "last_output.md").write_text(
            "All tests passed. OK. Files created successfully.", encoding="utf-8"
        )
        self.orch.receive_output(run_id)
        verdict = self.orch.evaluate_output(run_id)
        self.assertIsInstance(verdict, Verdict)
        self.assertIn(verdict.status, [VerdictStatus.PASS, VerdictStatus.NEEDS_HUMAN])


if __name__ == "__main__":
    unittest.main()