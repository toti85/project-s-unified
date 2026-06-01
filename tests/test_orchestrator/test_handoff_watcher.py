"""
test_handoff_watcher.py - Handoff Watcher Unit Tests
"""
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from src.orchestrator.handoff_watcher import HandoffWatcher, HandoffSignal


class TestHandoffWatcher(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.watcher = HandoffWatcher(runtime_root=Path(self.tmpdir))
        self.watcher.cline_inbox.mkdir(parents=True, exist_ok=True)
        self.watcher.cline_outbox.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_prompt_ready_json_creation(self):
        """prompt_ready.json should be created with correct fields."""
        path = self.watcher.prepare_handoff("FA1_006", 1, "Test prompt")
        self.assertTrue(path.exists())
        data = json.loads(path.read_text())
        self.assertEqual(data["run_id"], "FA1_006")
        self.assertEqual(data["iteration"], 1)
        self.assertEqual(data["status"], "ready")
        self.assertTrue(len(data["checksum"]) == 16)

    def test_output_ready_json_detection(self):
        """output_ready.json should be detected and consumed."""
        output_text = "All tests passed. OK."
        (self.watcher.cline_outbox / "last_output.md").write_text(output_text, encoding="utf-8")
        self.watcher.write_output_ready("FA1_006", 1, output_text)
        result = self.watcher.consume_output("FA1_006", 1)
        self.assertEqual(result, output_text)

    def test_run_id_mismatch_rejected(self):
        """Output with wrong run_id should be rejected."""
        output_text = "Some output."
        (self.watcher.cline_outbox / "last_output.md").write_text(output_text, encoding="utf-8")
        self.watcher.write_output_ready("FA1_999", 1, output_text)
        result = self.watcher.consume_output("FA1_006", 1)
        self.assertIsNone(result)

    def test_stale_output_ignored(self):
        """Consumed output should not be re-consumed."""
        output_text = "All tests passed. OK."
        (self.watcher.cline_outbox / "last_output.md").write_text(output_text, encoding="utf-8")
        self.watcher.write_output_ready("FA1_006", 1, output_text)
        self.watcher.consume_output("FA1_006", 1)
        # Second consume should return None (already consumed)
        result = self.watcher.consume_output("FA1_006", 1)
        self.assertIsNone(result)

    def test_checksum_mismatch_handled(self):
        """Checksum mismatch should warn but not fail."""
        output_text = "All tests passed. OK."
        (self.watcher.cline_outbox / "last_output.md").write_text(output_text, encoding="utf-8")
        # Write with wrong checksum
        ready_path = self.watcher.cline_outbox / "output_ready.json"
        ready_path.write_text(json.dumps({
            "run_id": "FA1_006", "iteration": 1,
            "timestamp": "2026-01-01T00:00:00Z",
            "status": "ready", "checksum": "0000000000000000"
        }) + "\n", encoding="utf-8")
        result = self.watcher.consume_output("FA1_006", 1)
        self.assertIsNotNone(result)

    def test_watcher_timeout(self):
        """Watch should timeout safely."""
        result = self.watcher.watch_for_output("FA1_006", 1, timeout=1, poll_interval=0.2)
        self.assertIsNone(result)

    def test_is_output_ready(self):
        """is_output_ready should return correct state."""
        self.assertFalse(self.watcher.is_output_ready("FA1_006", 1))
        self.watcher.write_output_ready("FA1_006", 1, "test")
        self.assertTrue(self.watcher.is_output_ready("FA1_006", 1))

    def test_fix_iteration_creates_new_prompt_ready(self):
        """Fix iteration should create new prompt_ready.json."""
        self.watcher.prepare_handoff("FA1_006", 1, "First prompt")
        data1 = json.loads((self.watcher.cline_inbox / "prompt_ready.json").read_text())
        self.watcher.prepare_handoff("FA1_006", 2, "Fix prompt")
        data2 = json.loads((self.watcher.cline_inbox / "prompt_ready.json").read_text())
        self.assertEqual(data2["iteration"], 2)


if __name__ == "__main__":
    unittest.main()