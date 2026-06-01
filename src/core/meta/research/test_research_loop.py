"""
Test Research Loop - Verify bug bounty research pipeline using Meta Layer.
Simulates: first hypothesis fails → validator feedback → replan → second hypothesis accepted.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Optional

from .research_goal import ResearchGoal
from .research_state import ResearchState
from .research_loop import ResearchLoop, ResearchResult


@pytest.fixture
def research_goal():
    """Create a test research goal."""
    return ResearchGoal(
        target_name="TestAPI-v1",
        scope="Public endpoints only",
        focus_vectors=["broken_auth", "idor", "api_rate_limits"],
        stop_condition="submission_ready",
        description="Test research objective",
        max_iterations=3,
    )


@pytest.fixture
def mock_meta_controller():
    """Create a mock MetaController for testing."""
    controller = AsyncMock()
    controller._log_evidence = MagicMock()
    return controller


@pytest.mark.asyncio
async def test_research_goal_creation(research_goal):
    """Test that ResearchGoal is created correctly."""
    assert research_goal.target_name == "TestAPI-v1"
    assert research_goal.scope == "Public endpoints only"
    assert len(research_goal.focus_vectors) == 3
    assert research_goal.stop_condition == "submission_ready"


@pytest.mark.asyncio
async def test_research_goal_validation():
    """Test ResearchGoal validation."""
    # Valid goal
    goal = ResearchGoal(
        target_name="Test",
        scope="test",
        focus_vectors=["vec1"],
        stop_condition="submission_ready"
    )
    assert goal is not None
    
    # Invalid stop_condition
    with pytest.raises(ValueError):
        ResearchGoal(
            target_name="Test",
            scope="test",
            focus_vectors=["vec1"],
            stop_condition="invalid_condition"
        )
    
    # Empty target_name
    with pytest.raises(ValueError):
        ResearchGoal(
            target_name="",
            scope="test",
            focus_vectors=["vec1"],
            stop_condition="submission_ready"
        )
    
    # Empty focus_vectors
    with pytest.raises(ValueError):
        ResearchGoal(
            target_name="Test",
            scope="test",
            focus_vectors=[],
            stop_condition="submission_ready"
        )


@pytest.mark.asyncio
async def test_research_state_management():
    """Test ResearchState state management."""
    state = ResearchState()
    
    # Test vector tracking
    state.mark_vector_explored("broken_auth")
    assert "broken_auth" in state.explored_vectors
    
    state.discard_vector("idor", "false_positive")
    assert "idor" in state.discarded_vectors
    
    # Test finding recording
    state.add_finding(
        hypothesis="API missing rate limits",
        vector="api_rate_limits",
        confidence=0.85,
        evidence="Can trigger 1000 requests per second",
        status="promising"
    )
    assert len(state.findings) == 1
    assert state.findings[0]["status"] == "promising"
    
    # Test remaining vectors
    all_vectors = ["broken_auth", "idor", "api_rate_limits", "xss"]
    remaining = state.get_remaining_vectors(all_vectors)
    assert "xss" in remaining
    assert "broken_auth" not in remaining  # explored
    assert "idor" not in remaining  # discarded


@pytest.mark.asyncio
async def test_research_state_serialization():
    """Test ResearchState serialization to/from dict."""
    state = ResearchState(iteration=2)
    state.mark_vector_explored("vec1")
    state.add_finding("hyp1", "vec1", 0.9, "evidence", "promising")
    
    # Serialize
    data = state.to_dict()
    assert data["iteration"] == 2
    assert "vec1" in data["explored_vectors"]
    assert len(data["findings"]) == 1
    
    # Deserialize
    restored = ResearchState.from_dict(data)
    assert restored.iteration == 2
    assert "vec1" in restored.explored_vectors


@pytest.mark.asyncio
async def test_research_loop_initialization(mock_meta_controller, research_goal):
    """Test ResearchLoop initialization."""
    loop = ResearchLoop(mock_meta_controller)
    assert loop.meta_controller is mock_meta_controller


@pytest.mark.asyncio
async def test_research_loop_failure_replan_success(mock_meta_controller, research_goal):
    """
    Test research loop: First hypothesis fails → Validator feedback → Replan → Success.
    
    Scenario:
    1. MetaController.run_goal called with first hypothesis
    2. Validator returns false_positive feedback
    3. ResearchLoop converts feedback to constraints
    4. Next iteration with constraints applied
    5. Second hypothesis accepted
    """
    
    loop = ResearchLoop(mock_meta_controller)
    
    # Simulate MetaController returning success
    mock_meta_controller.run_goal = AsyncMock(return_value={
        "status": "success",
        "iterations": 2,
        "goal": research_goal.to_dict(),
    })
    
    # Run research
    result = await loop.run(research_goal)
    
    # Verify result
    assert isinstance(result, ResearchResult)
    assert result.goal == research_goal
    assert result.success is True
    assert result.iteration_count > 0
    
    # Verify MetaController was called
    assert mock_meta_controller.run_goal.called
    call_args = mock_meta_controller.run_goal.call_args
    assert call_args is not None
    # Now we just pass goal string, not dict/state/constraints
    assert "TestAPI-v1" in str(call_args)
    
    # Verify evidence logging
    assert mock_meta_controller._log_evidence.called
    log_calls = [call[0][0] for call in mock_meta_controller._log_evidence.call_args_list]
    assert "research_started" in log_calls
    assert "research_completed" in log_calls


@pytest.mark.asyncio
async def test_research_loop_error_handling(mock_meta_controller, research_goal):
    """Test research loop error handling."""
    
    loop = ResearchLoop(mock_meta_controller)
    
    # Simulate MetaController throwing error
    mock_meta_controller.run_goal = AsyncMock(side_effect=Exception("Orchestration failed"))
    
    # Run research
    result = await loop.run(research_goal)
    
    # Verify error result
    assert result.success is False
    assert result.completion_reason == "error"
    assert result.iteration_count == 0
    
    # Verify error was logged
    log_calls = [call[0][0] for call in mock_meta_controller._log_evidence.call_args_list]
    assert "research_error" in log_calls


@pytest.mark.asyncio
async def test_validator_feedback_conversion(mock_meta_controller, research_goal):
    """Test conversion of validator feedback to research constraints."""
    
    loop = ResearchLoop(mock_meta_controller)
    
    # Test false_positive feedback
    constraints = loop.handle_validator_feedback(
        "false_positive",
        {"vector": "broken_auth", "hypothesis": "Missing password validation"}
    )
    assert "exclude_vectors" in constraints
    assert "broken_auth" in constraints["exclude_vectors"]
    
    # Verify evidence logged
    assert mock_meta_controller._log_evidence.called
    log_calls = [call[0][0] for call in mock_meta_controller._log_evidence.call_args_list]
    assert "hypothesis_rejected" in log_calls
    
    # Reset mock
    mock_meta_controller._log_evidence.reset_mock()
    
    # Test low_impact feedback
    constraints = loop.handle_validator_feedback(
        "low_impact",
        {"vector": "idor", "hypothesis": "Predictable user IDs"}
    )
    assert "low_impact_vectors" in constraints
    
    # Test duplicate feedback
    constraints = loop.handle_validator_feedback(
        "duplicate",
        {"vector": "api_rate_limits", "hypothesis": "No rate limiting"}
    )
    assert "exclude_vectors" in constraints
    
    # Test promising feedback
    constraints = loop.handle_validator_feedback(
        "promising",
        {"vector": "xss", "hypothesis": "Stored XSS in comments", "confidence": 0.95}
    )
    log_calls = [call[0][0] for call in mock_meta_controller._log_evidence.call_args_list]
    assert "hypothesis_promoted" in log_calls


@pytest.mark.asyncio
async def test_research_loop_evidence_events(mock_meta_controller, research_goal):
    """Test that research loop logs all required evidence events."""
    
    loop = ResearchLoop(mock_meta_controller)
    mock_meta_controller.run_goal = AsyncMock(return_value={
        "status": "success",
        "iterations": 1,
    })
    
    # Run research
    await loop.run(research_goal)
    
    # Verify evidence events
    log_calls = [call[0][0] for call in mock_meta_controller._log_evidence.call_args_list]
    
    assert "research_started" in log_calls, "research_started event not logged"
    assert "research_completed" in log_calls, "research_completed event not logged"
    
    # Verify event data
    start_call = None
    for call in mock_meta_controller._log_evidence.call_args_list:
        if call[0][0] == "research_started":
            start_call = call[0][1]
            break
    
    assert start_call is not None
    assert start_call["target_name"] == research_goal.target_name
    assert start_call["scope"] == research_goal.scope
    assert start_call["focus_vectors"] == research_goal.focus_vectors


@pytest.mark.asyncio
async def test_full_research_workflow(mock_meta_controller):
    """
    Test full research workflow: Create goal → Run loop → Validate result.
    """
    
    goal = ResearchGoal(
        target_name="MobileApp-iOS",
        scope="Authentication only",
        focus_vectors=["biometric_bypass", "session_fixation"],
        stop_condition="submission_ready",
        max_iterations=2,
    )
    
    loop = ResearchLoop(mock_meta_controller)
    
    # Simulate successful research
    mock_meta_controller.run_goal = AsyncMock(return_value={
        "status": "success",
        "iterations": 2,
    })
    
    # Run research
    result = await loop.run(goal)
    
    # Validate workflow
    assert result.goal.target_name == "MobileApp-iOS"
    assert result.success is True
    assert result.completion_reason == "submission_ready"
    
    # Verify MetaController was invoked with correct goal string
    call_kwargs = mock_meta_controller.run_goal.call_args
    # Now we pass goal as positional arg (string)
    assert call_kwargs is not None
    # The goal string should contain the research target name
    assert "MobileApp-iOS" in str(call_kwargs)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
