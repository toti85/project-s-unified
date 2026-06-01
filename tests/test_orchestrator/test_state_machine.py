"""
test_state_machine.py — State Machine Unit Tests
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from src.orchestrator.state_machine import RunState, StateMachine, StateTransitionError


class TestStateMachine(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.runs_dir = Path(self.tmpdir) / "runs"
        self.runs_dir.mkdir(parents=True)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_valid_transition_succeeds(self):
        """Valid state transition should succeed."""
        sm = StateMachine(run_id="TEST_001", runs_dir=self.runs_dir)
        sm.transition(RunState.PROMPT_DRAFTED, "Test transition")
        self.assertEqual(sm.current_state, RunState.PROMPT_DRAFTED)

    def test_invalid_transition_raises_error(self):
        """Invalid state transition should raise StateTransitionError."""
        sm = StateMachine(run_id="TEST_002", runs_dir=self.runs_dir)
        with self.assertRaises(StateTransitionError):
            sm.transition(RunState.ARCHIVED, "Should fail")

    def test_state_persists_to_json(self):
        """State should persist to state.json."""
        sm = StateMachine(run_id="TEST_003", runs_dir=self.runs_dir)
        sm.transition(RunState.PROMPT_DRAFTED, "Draft")
        state_file = self.runs_dir / "TEST_003" / "state.json"
        self.assertTrue(state_file.exists())
        data = json.loads(state_file.read_text())
        self.assertEqual(data["current_state"], "PROMPT_DRAFTED")

    def test_load_existing_state(self):
        """Loading existing state should restore current_state."""
        sm1 = StateMachine(run_id="TEST_004", runs_dir=self.runs_dir)
        sm1.transition(RunState.PROMPT_DRAFTED, "Draft")
        sm2 = StateMachine.load("TEST_004", runs_dir=self.runs_dir)
        self.assertEqual(sm2.current_state, RunState.PROMPT_DRAFTED)

    def test_history_records_transitions(self):
        """History should record all transitions."""
        sm = StateMachine(run_id="TEST_005", runs_dir=self.runs_dir)
        sm.transition(RunState.PROMPT_DRAFTED, "Draft")
        sm.transition(RunState.HUMAN_REVIEW, "Review")
        history = sm.get_history()
        self.assertEqual(len(history), 3)  # initial + 2 transitions


if __name__ == "__main__":
    unittest.main()