"""
GAP_029 Unit Tests: Replan Delta Validation

Tests for the evaluator_gap029 module that validates replan actions
require concrete corrective delta before being allowed to trigger replanning.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.evaluator_gap029 import (
    has_concrete_corrective_delta,
    normalize_evaluator_action,
    validate_replan_action,
    track_replan_count,
    CORRECTIVE_DELTA_FIELDS,
    VAGUE_REPLAN_FAIL_CONFIDENCE_THRESHOLD,
)


class TestHasConcreteCorrectiveDelta:
    """Test the has_concrete_corrective_delta function."""
    
    def test_specific_issues_string(self):
        """specific_issues as non-empty string → True."""
        result = has_concrete_corrective_delta({
            "specific_issues": "The output lacks bullet points"
        })
        assert result is True
    
    def test_specific_issues_list(self):
        """specific_issues as non-empty list → True."""
        result = has_concrete_corrective_delta({
            "specific_issues": ["Missing bullet points", "No substantive content"]
        })
        assert result is True
    
    def test_proposed_change_string(self):
        """proposed_change as non-empty string → True."""
        result = has_concrete_corrective_delta({
            "proposed_change": "Add 5 bullet points with substantive information"
        })
        assert result is True
    
    def test_details_string(self):
        """details as non-empty string → True."""
        result = has_concrete_corrective_delta({
            "details": "The output is a wrapper without content"
        })
        assert result is True
    
    def test_details_in_recommendations(self):
        """details in recommendations → True."""
        result = has_concrete_corrective_delta({
            "recommendations": {
                "action": "replan",
                "details": "Need actual content, not just a summary"
            }
        })
        assert result is True
    
    def test_specific_issues_in_recommendations(self):
        """specific_issues in recommendations → True."""
        result = has_concrete_corrective_delta({
            "recommendations": {
                "action": "replan",
                "specific_issues": ["Output is a stub"]
            }
        })
        assert result is True
    
    def test_empty_specific_issues(self):
        """Empty specific_issues → False."""
        result = has_concrete_corrective_delta({
            "specific_issues": ""
        })
        assert result is False
    
    def test_empty_list_specific_issues(self):
        """Empty list specific_issues → False."""
        result = has_concrete_corrective_delta({
            "specific_issues": []
        })
        assert result is False
    
    def test_no_delta_fields(self):
        """No delta fields at all → False."""
        result = has_concrete_corrective_delta({
            "success": False,
            "confidence": 0.5,
            "goal_achieved": False,
            "assessment": "Output is insufficient"
        })
        assert result is False
    
    def test_only_recommendations_action(self):
        """Only recommendations.action=replan, no delta → False."""
        result = has_concrete_corrective_delta({
            "recommendations": {
                "action": "replan",
                "reason": "Output quality insufficient"
            }
        })
        assert result is False
    
    def test_whitespace_only_string(self):
        """Whitespace-only string → False."""
        result = has_concrete_corrective_delta({
            "specific_issues": "   "
        })
        assert result is False
    
    def test_multiple_delta_fields(self):
        """Multiple delta fields present → True."""
        result = has_concrete_corrective_delta({
            "specific_issues": ["Missing content"],
            "proposed_change": "Add actual bullet points",
            "details": "The output is just a wrapper"
        })
        assert result is True


class TestNormalizeEvaluatorAction:
    """Test the normalize_evaluator_action function."""
    
    def test_replan_with_specific_issues(self):
        """replan + specific_issues → stays replan."""
        result = normalize_evaluator_action({
            "success": False,
            "confidence": 0.7,
            "goal_achieved": False,
            "assessment": "Output lacks content",
            "specific_issues": ["Missing bullet points"],
            "recommendations": {
                "action": "replan",
                "reason": "Need actual content"
            }
        })
        assert result["normalized_action"] == "replan"
        assert result["gap029_status"] == "valid_replan"
        assert "corrective delta" in result["gap029_reason"].lower()
    
    def test_replan_with_proposed_change(self):
        """replan + proposed_change → stays replan."""
        result = normalize_evaluator_action({
            "success": False,
            "confidence": 0.6,
            "goal_achieved": False,
            "assessment": "Output is insufficient",
            "proposed_change": "Add 5 bullet points with substantive information",
            "recommendations": {
                "action": "replan",
                "reason": "Need more detail"
            }
        })
        assert result["normalized_action"] == "replan"
        assert result["gap029_status"] == "valid_replan"
    
    def test_replan_with_details(self):
        """replan + details → stays replan."""
        result = normalize_evaluator_action({
            "success": False,
            "confidence": 0.8,
            "goal_achieved": False,
            "assessment": "Output is a stub",
            "details": "The output is just a wrapper without actual content",
            "recommendations": {
                "action": "replan",
                "reason": "Need actual content"
            }
        })
        assert result["normalized_action"] == "replan"
        assert result["gap029_status"] == "valid_replan"
    
    def test_replan_without_delta_low_confidence(self):
        """replan without delta, low confidence → downgraded to continue."""
        result = normalize_evaluator_action({
            "success": False,
            "confidence": 0.3,
            "goal_achieved": True,
            "assessment": "Output is acceptable but could be better",
            "recommendations": {
                "action": "replan",
                "reason": "Output quality insufficient"
            }
        })
        assert result["normalized_action"] == "continue"
        assert result["gap029_status"] == "downgraded_continue"
        assert "continue" in result["gap029_reason"].lower()
    
    def test_replan_without_delta_medium_confidence(self):
        """replan without delta, medium confidence → downgraded to continue."""
        result = normalize_evaluator_action({
            "success": False,
            "confidence": 0.5,
            "goal_achieved": False,
            "assessment": "Output is insufficient",
            "recommendations": {
                "action": "replan",
                "reason": "Output quality insufficient"
            }
        })
        assert result["normalized_action"] == "continue"
        assert result["gap029_status"] == "downgraded_continue"
    
    def test_replan_without_delta_high_confidence_goal_false(self):
        """replan without delta, high confidence + goal_achieved=False → downgraded to fail."""
        result = normalize_evaluator_action({
            "success": False,
            "confidence": 0.9,
            "goal_achieved": False,
            "assessment": "Output is completely inadequate",
            "recommendations": {
                "action": "replan",
                "reason": "Output quality insufficient"
            }
        })
        assert result["normalized_action"] == "fail"
        assert result["gap029_status"] == "downgraded_fail"
        assert "fail" in result["gap029_reason"].lower()
    
    def test_replan_without_delta_at_threshold(self):
        """replan without delta, confidence exactly at threshold + goal_achieved=False → fail."""
        result = normalize_evaluator_action({
            "success": False,
            "confidence": VAGUE_REPLAN_FAIL_CONFIDENCE_THRESHOLD,
            "goal_achieved": False,
            "assessment": "Output is inadequate",
            "recommendations": {
                "action": "replan",
                "reason": "Output quality insufficient"
            }
        })
        assert result["normalized_action"] == "fail"
        assert result["gap029_status"] == "downgraded_fail"
    
    def test_replan_without_delta_just_below_threshold(self):
        """replan without delta, confidence just below threshold → continue."""
        result = normalize_evaluator_action({
            "success": False,
            "confidence": VAGUE_REPLAN_FAIL_CONFIDENCE_THRESHOLD - 0.01,
            "goal_achieved": False,
            "assessment": "Output is somewhat inadequate",
            "recommendations": {
                "action": "replan",
                "reason": "Output quality insufficient"
            }
        })
        assert result["normalized_action"] == "continue"
        assert result["gap029_status"] == "downgraded_continue"
    
    def test_continue_action_unchanged(self):
        """continue action → unchanged."""
        result = normalize_evaluator_action({
            "success": True,
            "confidence": 0.9,
            "goal_achieved": True,
            "assessment": "Output is good",
            "recommendations": {
                "action": "continue",
                "reason": "Goal achieved"
            }
        })
        assert result["normalized_action"] == "continue"
        assert result["gap029_status"] == "not_replan"
    
    def test_improve_tool_action_unchanged(self):
        """improve_tool action → unchanged."""
        result = normalize_evaluator_action({
            "success": True,
            "confidence": 0.7,
            "goal_achieved": True,
            "assessment": "Output is good but tool could be better",
            "recommendations": {
                "action": "improve_tool",
                "reason": "Tool needs optimization"
            }
        })
        assert result["normalized_action"] == "improve_tool"
        assert result["gap029_status"] == "not_replan"
    
    def test_top_level_action_replan_no_delta(self):
        """Top-level action=replan (backward compat) without delta → downgraded."""
        result = normalize_evaluator_action({
            "success": False,
            "confidence": 0.5,
            "goal_achieved": False,
            "assessment": "Output is insufficient",
            "action": "replan"
        })
        assert result["normalized_action"] == "continue"
        assert result["gap029_status"] == "downgraded_continue"
    
    def test_top_level_action_replan_with_delta(self):
        """Top-level action=replan with delta → stays replan."""
        result = normalize_evaluator_action({
            "success": False,
            "confidence": 0.7,
            "goal_achieved": False,
            "assessment": "Output is insufficient",
            "action": "replan",
            "specific_issues": ["Missing content"]
        })
        assert result["normalized_action"] == "replan"
        assert result["gap029_status"] == "valid_replan"


class TestValidateReplanAction:
    """Test the validate_replan_action quick-check function."""
    
    def test_valid_replan(self):
        """Replan with delta → True."""
        result = validate_replan_action({
            "specific_issues": ["Missing content"],
            "recommendations": {"action": "replan"}
        })
        assert result is True
    
    def test_invalid_replan(self):
        """Replan without delta → False."""
        result = validate_replan_action({
            "recommendations": {
                "action": "replan",
                "reason": "Output quality insufficient"
            }
        })
        assert result is False
    
    def test_non_replan_action(self):
        """Non-replan action → False (not a replan to validate)."""
        result = validate_replan_action({
            "recommendations": {
                "action": "continue"
            }
        })
        assert result is False


class TestTrackReplanCount:
    """Test the track_replan_count function."""
    
    def test_empty_events(self):
        """No events → replan_count stays at existing value."""
        mission = {
            "replan_count": 3,
            "events": [],
            "state_history": []
        }
        result = track_replan_count(mission)
        assert result["replan_count"] == 3
        assert result["metadata"]["gap029_replan_count_verified"] == 3
    
    def test_events_with_replan_type(self):
        """Events with replan type → count increments."""
        mission = {
            "replan_count": 0,
            "events": [
                {"event_type": "replan", "data": {"action": "replan"}},
                {"event_type": "replan", "data": {"action": "replan"}},
            ],
            "state_history": []
        }
        result = track_replan_count(mission)
        assert result["replan_count"] == 2
        assert result["metadata"]["gap029_replan_count_verified"] == 2
    
    def test_events_with_replan_action(self):
        """Events with replan action → count increments."""
        mission = {
            "replan_count": 0,
            "events": [
                {"event_type": "evaluation.result", "data": {"action": "replan"}},
                {"event_type": "evaluation.result", "data": {"action": "replan"}},
                {"event_type": "evaluation.result", "data": {"action": "continue"}},
            ],
            "state_history": []
        }
        result = track_replan_count(mission)
        assert result["replan_count"] == 2
    
    def test_existing_count_higher(self):
        """Existing count higher than event count → use existing."""
        mission = {
            "replan_count": 5,
            "events": [
                {"event_type": "replan", "data": {"action": "replan"}},
            ],
            "state_history": []
        }
        result = track_replan_count(mission)
        assert result["replan_count"] == 5
    
    def test_dict_replan_count(self):
        """replan_count as dict → extract count."""
        mission = {
            "replan_count": {"count": 3},
            "events": [],
            "state_history": []
        }
        result = track_replan_count(mission)
        assert result["replan_count"] == 3


class TestIntegrationEvaluatorActionFlow:
    """Integration tests: full evaluator action flow through normalization."""
    
    def test_full_replan_with_delta_flow(self):
        """Full flow: replan with delta → stays replan, no downgrade."""
        eval_result = {
            "success": False,
            "confidence": 0.7,
            "goal_achieved": False,
            "assessment": "Output lacks the requested bullet points",
            "issues_found": ["missing_content"],
            "specific_issues": ["Output is a wrapper, not 5 bullet points"],
            "recommendations": {
                "action": "replan",
                "reason": "Need actual bullet points with content",
                "proposed_change": "Use file_reader to read self_state.json and extract 5 bullet points"
            }
        }
        normalized = normalize_evaluator_action(eval_result)
        assert normalized["normalized_action"] == "replan"
        assert normalized["gap029_status"] == "valid_replan"
        # The normalized result should still have all original fields
        assert normalized["goal_achieved"] is False
        assert normalized["confidence"] == 0.7
    
    def test_full_vague_replan_flow(self):
        """Full flow: vague replan → downgraded to continue."""
        eval_result = {
            "success": False,
            "confidence": 0.5,
            "goal_achieved": False,
            "assessment": "Output quality insufficient",
            "issues_found": ["quality"],
            "recommendations": {
                "action": "replan",
                "reason": "Output quality insufficient"
            }
        }
        normalized = normalize_evaluator_action(eval_result)
        assert normalized["normalized_action"] == "continue"
        assert normalized["gap029_status"] == "downgraded_continue"
        # goal_achieved is preserved from original
        assert normalized["goal_achieved"] is False
    
    def test_full_high_confidence_fail_flow(self):
        """Full flow: high-confidence vague replan → downgraded to fail."""
        eval_result = {
            "success": False,
            "confidence": 0.95,
            "goal_achieved": False,
            "assessment": "Output is completely inadequate for the task",
            "issues_found": ["no_content", "wrong_format"],
            "recommendations": {
                "action": "replan",
                "reason": "Output quality insufficient"
            }
        }
        normalized = normalize_evaluator_action(eval_result)
        assert normalized["normalized_action"] == "fail"
        assert normalized["gap029_status"] == "downgraded_fail"