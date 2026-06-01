"""
test_ai_client.py - AI Client Unit Tests
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from src.orchestrator.ai_client import OrchestratorAIClient, AIConfig, AIVerdict


class TestAIClientFallback(unittest.TestCase):
    """Test AI client fallback behavior."""

    def setUp(self):
        self._orig = os.environ.pop("OPENROUTER_API_KEY", None)

    def tearDown(self):
        if self._orig:
            os.environ["OPENROUTER_API_KEY"] = self._orig

    def test_fallback_when_no_api_key(self):
        """AI client should fallback when no API key exists."""
        client = OrchestratorAIClient(
            prompt_config=AIConfig(enabled=True),
            eval_config=AIConfig(enabled=True),
        )
        prompt = client.draft_cline_prompt("Test goal", sandbox_path="/sandbox")
        self.assertIn("Test goal", prompt)
        self.assertIn("sandbox", prompt.lower())

    def test_prompt_includes_allowed_forbidden_paths(self):
        """Sandbox prompt should include allowed/forbidden paths."""
        client = OrchestratorAIClient(
            prompt_config=AIConfig(enabled=False),
            eval_config=AIConfig(enabled=False),
        )
        prompt = client.draft_cline_prompt("Test goal", sandbox_path="/my/sandbox")
        self.assertIn("/my/sandbox", prompt)
        self.assertIn("Forbidden", prompt)

    def test_evaluator_fallback(self):
        """Evaluator should fallback safely."""
        client = OrchestratorAIClient(
            prompt_config=AIConfig(enabled=False),
            eval_config=AIConfig(enabled=True),
        )
        verdict = client.evaluate_cline_output(
            run_id="TEST",
            goal_text="Test goal",
            prompt_text="Test prompt",
            output_text="All tests passed. OK. Files created successfully.",
        )
        self.assertIsInstance(verdict, AIVerdict)
        self.assertIn(verdict.status, ("PASS", "NEEDS_HUMAN"))

    def test_evaluator_rejects_invalid_json(self):
        """Evaluator should handle invalid JSON from AI."""
        client = OrchestratorAIClient()
        result = client._parse_ai_verdict("not valid json", "TEST", "goal")
        self.assertIsNone(result)

    def test_production_path_triggers_needs_human(self):
        """Production path in output should trigger NEEDS_HUMAN."""
        client = OrchestratorAIClient(
            prompt_config=AIConfig(enabled=False),
            eval_config=AIConfig(enabled=False),
        )
        verdict = client.evaluate_cline_output(
            run_id="TEST",
            goal_text="Test",
            prompt_text="Test",
            output_text="Modified src/core/main.py. Error in production.",
        )
        self.assertIn(verdict.status, ("NEEDS_HUMAN", "FIX", "ERROR"))


if __name__ == "__main__":
    unittest.main()