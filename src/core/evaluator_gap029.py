"""
GAP_029: Replan Delta Validation

This module provides a normalization/validation layer for evaluator actions.
The strategic evaluator returns action="replan" without concrete corrective
feedback (specific_issues, proposed_change), causing the MetaController to
blindly re-run the same plan in a non-converging loop.

Fix: replan is VALID only when the evaluator provides actionable correction
data. Vague replan is downgraded to continue or fail based on the most
truthful policy.
"""

import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("evaluator_gap029")

# Concrete corrective delta fields that make a replan valid
CORRECTIVE_DELTA_FIELDS = ["specific_issues", "proposed_change", "details"]

# Downgrade thresholds
# If confidence >= this threshold and no corrective delta → downgrade to fail
# (the output is clearly inadequate, not just imperfect)
VAGUE_REPLAN_FAIL_CONFIDENCE_THRESHOLD = 0.8


def has_concrete_corrective_delta(evaluation_result: Dict[str, Any]) -> bool:
    """
    Check if the evaluator result contains concrete corrective delta.
    
    A replan is valid only if at least one of these is present and non-empty:
    - specific_issues
    - proposed_change
    - details (from recommendations)
    
    Returns True if concrete corrective delta exists, False otherwise.
    """
    # Check top-level fields
    for field in CORRECTIVE_DELTA_FIELDS:
        val = evaluation_result.get(field)
        if val and isinstance(val, str) and val.strip():
            return True
        if val and isinstance(val, list) and len(val) > 0:
            return True
        if val and isinstance(val, dict) and len(val) > 0:
            return True
    
    # Check recommendations sub-object
    recs = evaluation_result.get("recommendations", {})
    if isinstance(recs, dict):
        for field in CORRECTIVE_DELTA_FIELDS:
            val = recs.get(field)
            if val and isinstance(val, str) and val.strip():
                return True
            if val and isinstance(val, list) and len(val) > 0:
                return True
            if val and isinstance(val, dict) and len(val) > 0:
                return True
    
    return False


def normalize_evaluator_action(
    evaluation_result: Dict[str, Any],
    replan_count: int = 0,
    max_replan_count: int = 5
) -> Dict[str, Any]:
    """
    Normalize the evaluator's action by validating replan requests.
    
    If action=replan is returned WITHOUT concrete corrective delta:
    - Downgrade to 'continue' if the output is substantively acceptable
    - Downgrade to 'fail' if the output is clearly inadequate
    
    If action=replan is returned WITH concrete corrective delta:
    - Keep as 'replan' (valid replan)
    
    Returns a normalized evaluation result dict with:
    - normalized_action: the validated action
    - gap029_status: one of 'valid_replan', 'downgraded_continue', 'downgraded_fail'
    - gap029_reason: explanation of the normalization decision
    """
    # Extract the action from recommendations (or top-level for backward compat)
    recs = evaluation_result.get("recommendations")
    if isinstance(recs, dict) and "action" in recs:
        action = recs.get("action", "")
    else:
        # Fallback to top-level action for backward compatibility
        action = str(evaluation_result.get("action", ""))
    
    # If not a replan action, return unchanged
    if action not in ("replan", "create_new_tool"):
        normalized = evaluation_result.copy()
        normalized["normalized_action"] = action
        normalized["gap029_status"] = "not_replan"
        normalized["gap029_reason"] = f"Action is '{action}', no replan validation needed"
        return normalized
    
    # This is a replan action — check for concrete corrective delta
    has_delta = has_concrete_corrective_delta(evaluation_result)
    
    if has_delta:
        # Valid replan — keep as-is
        normalized = evaluation_result.copy()
        normalized["normalized_action"] = "replan"
        normalized["gap029_status"] = "valid_replan"
        normalized["gap029_reason"] = "Replan has concrete corrective delta"
        logger.info(f"GAP_029: replan accepted with corrective delta")
        return normalized
    
    # Vague replan — no concrete delta
    # Decide: downgrade to continue or fail?
    
    # Check confidence level
    confidence = evaluation_result.get("confidence", 0.5)
    goal_achieved = evaluation_result.get("goal_achieved", None)
    
    # If confidence is high AND goal_achieved is False → the evaluator is
    # confident the goal was NOT achieved, but can't say WHY.
    # This means the output is clearly inadequate → downgrade to FAIL.
    if confidence >= VAGUE_REPLAN_FAIL_CONFIDENCE_THRESHOLD and goal_achieved is False:
        normalized = evaluation_result.copy()
        normalized["normalized_action"] = "fail"
        normalized["gap029_status"] = "downgraded_fail"
        normalized["gap029_reason"] = (
            f"Vague replan downgraded to FAIL: confidence={confidence}, "
            f"goal_achieved=False, but no specific_issues/proposed_change provided"
        )
        logger.info(f"GAP_029: vague replan downgraded to fail (confidence={confidence}, goal_achieved=False)")
        return normalized
    
    # If confidence is low or goal_achieved is True → the output may be
    # acceptable but the evaluator is uncertain → downgrade to CONTINUE.
    normalized = evaluation_result.copy()
    normalized["normalized_action"] = "continue"
    normalized["gap029_status"] = "downgraded_continue"
    normalized["gap029_reason"] = (
        f"Vague replan downgraded to CONTINUE: confidence={confidence}, "
        f"no corrective delta — output accepted as-is"
    )
    logger.info(f"GAP_029: vague replan downgraded to continue (confidence={confidence})")
    return normalized


def validate_replan_action(evaluation_result: Dict[str, Any]) -> bool:
    """
    Quick check: should this replan be allowed?
    
    Returns True if the replan has concrete corrective delta.
    Returns False if the replan is vague and should be downgraded.
    """
    return has_concrete_corrective_delta(evaluation_result)


def track_replan_count(mission_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Track and update the replan count in mission metadata.
    
    This fixes the secondary bug where failed missions showed
    replan_count: 0 even when multiple replans occurred.
    
    Returns the updated mission data with correct replan_count.
    """
    # Get current replan count from state history or metadata
    state_history = mission_data.get("state_history", [])
    events = mission_data.get("events", [])
    
    # Count replan transitions (EXECUTING → EXECUTING without COMPLETE)
    replan_count = 0
    for event in events:
        event_type = event.get("event_type", "")
        data = event.get("data", {})
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except:
                pass
        if isinstance(data, dict):
            if data.get("action") == "replan" or event_type == "replan":
                replan_count += 1
    
    # Also check existing replan_count in mission data
    existing_count = mission_data.get("replan_count", 0)
    if isinstance(existing_count, dict):
        existing_count = existing_count.get("count", 0)
    
    # Use the maximum of the two counts
    actual_count = max(replan_count, existing_count)
    
    # Update mission data
    mission_data["replan_count"] = actual_count
    
    # Add metadata about replan tracking
    if "metadata" not in mission_data:
        mission_data["metadata"] = {}
    mission_data["metadata"]["gap029_replan_count_verified"] = actual_count
    
    return mission_data