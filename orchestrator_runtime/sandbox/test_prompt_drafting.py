"""
test_prompt_drafting.py — Self-contained test script for AI prompt drafting validation.

Simulates AI prompt drafting, validates output structure, and verifies required fields/templates.
"""

import unittest


def draft_prompt(goal: str, sandbox_path: str) -> str:
    """Simulate AI prompt drafting with required sections."""
    return (
        f"# Cline Prompt: {goal}\n\n"
        f"## 1. Goal Description\n{goal}\n\n"
        f"## 2. Allowed Directory\n`{sandbox_path}`\n\n"
        f"## 3. Forbidden Paths\n- Any path outside `{sandbox_path}`\n\n"
        f"## 4. Required Deliverables\n- Create files in sandbox\n\n"
        f"## 5. Test Instructions\nRun all tests. All must pass.\n\n"
        f"## 6. Output/Report Location\nWrite report to cline_outbox/last_output.md\n\n"
        f"## 7. Safety Constraints\nSandbox only. No network calls.\n"
    )


REQUIRED_SECTIONS = [
    "Goal Description",
    "Allowed Directory",
    "Forbidden Paths",
    "Required Deliverables",
    "Test Instructions",
    "Output/Report Location",
    "Safety Constraints",
]


class TestPromptDrafting(unittest.TestCase):
    """Validate AI prompt drafting output structure."""

    def test_prompt_contains_all_required_sections(self):
        prompt = draft_prompt("Test goal", "/sandbox")
        for section in REQUIRED_SECTIONS:
            self.assertIn(section, prompt, f"Missing section: {section}")

    def test_prompt_includes_goal_text(self):
        goal = "Create a CSV counter helper"
        prompt = draft_prompt(goal, "/sandbox")
        self.assertIn(goal, prompt)

    def test_prompt_includes_sandbox_path(self):
        sandbox = "/safe/sandbox/path"
        prompt = draft_prompt("Test", sandbox)
        self.assertIn(sandbox, prompt)

    def test_prompt_length_reasonable(self):
        prompt = draft_prompt("Test goal", "/sandbox")
        self.assertGreater(len(prompt), 100, "Prompt too short")
        self.assertLess(len(prompt), 5000, "Prompt too long")

    def test_prompt_starts_with_header(self):
        prompt = draft_prompt("Test goal", "/sandbox")
        self.assertTrue(prompt.startswith("# Cline Prompt:"), "Prompt must start with header")


if __name__ == "__main__":
    unittest.main()