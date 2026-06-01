"""
test_ai_evaluation.py - Self-contained test script for AI evaluation validation.

Simulates AI evaluation metrics, validates scoring logic, and verifies rating ranges.
"""

import unittest


def evaluate_output(output, criteria):
    """Simulate AI evaluation with scoring logic."""
    score = 0.0
    passed = []
    failed = []

    for criterion in criteria:
        if criterion.lower() in output.lower():
            score += 1.0
            passed.append(criterion)
        else:
            failed.append(criterion)

    confidence = score / len(criteria) if criteria else 0.0

    if confidence >= 0.8:
        status = "PASS"
    elif confidence >= 0.5:
        status = "FIX"
    else:
        status = "NEEDS_HUMAN"

    return {
        "status": status,
        "confidence": round(confidence, 2),
        "passed": passed,
        "failed": failed,
        "total": len(criteria),
    }


class TestAiEvaluation(unittest.TestCase):
    """Validate AI evaluation metrics and scoring logic."""

    def test_pass_when_all_criteria_met(self):
        output = "Created file and ran tests successfully"
        criteria = ["Created file", "ran tests"]
        result = evaluate_output(output, criteria)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["confidence"], 1.0)

    def test_fix_when_partial_criteria_met(self):
        output = "Created file but tests failed"
        criteria = ["Created file", "tests passed"]
        result = evaluate_output(output, criteria)
        self.assertEqual(result["status"], "FIX")
        self.assertEqual(result["confidence"], 0.5)

    def test_needs_human_when_no_criteria_met(self):
        output = "Nothing done"
        criteria = ["Created file", "ran tests"]
        result = evaluate_output(output, criteria)
        self.assertEqual(result["status"], "NEEDS_HUMAN")
        self.assertEqual(result["confidence"], 0.0)

    def test_confidence_range_valid(self):
        output = "Some work done"
        criteria = ["Created file", "ran tests", "wrote report"]
        result = evaluate_output(output, criteria)
        self.assertGreaterEqual(result["confidence"], 0.0)
        self.assertLessEqual(result["confidence"], 1.0)

    def test_passed_and_failed_lists_correct(self):
        output = "Created file and wrote report"
        criteria = ["Created file", "ran tests", "wrote report"]
        result = evaluate_output(output, criteria)
        self.assertIn("Created file", result["passed"])
        self.assertIn("ran tests", result["failed"])
        self.assertEqual(result["total"], 3)


if __name__ == "__main__":
    unittest.main()