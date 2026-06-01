"""
Test suite for MetaController (Phase 3).

Tests the complete decision→execute→validate→replan loop with mocked components.
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock

from .meta_controller import MetaController, MetaControllerConfig
from .decision import Decision, AIOpinion
from .validation_result import ValidationResult, ValidationCheck, ValidationIssue


logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


class MockEvidenceLogger:
    """Mock evidence logger for testing."""
    
    def __init__(self):
        self.events = []
    
    def log_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        self.events.append({
            "type": event_type,
            "data": event_data
        })
    
    def get_log_path(self) -> str:
        return "mock_evidence.jsonl"


class MockExecutor:
    """Mock executor that returns configurable results."""
    
    def __init__(self, results: list):
        self.results = results
        self.call_count = 0
    
    async def execute(self, goal: str, decision: Decision) -> Dict[str, Any]:
        result = self.results[self.call_count] if self.call_count < len(self.results) else self.results[-1]
        self.call_count += 1
        return result


class MockValidator:
    """Mock validator that returns configurable validation results."""
    
    def __init__(self, results: list):
        self.results = results
        self.call_count = 0
    
    async def validate(
        self,
        execution_result: Dict[str, Any],
        goal: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        validation = self.results[self.call_count] if self.call_count < len(self.results) else self.results[-1]
        self.call_count += 1
        return validation


class MockCouncil:
    """Mock strategy council that decides based on state."""
    
    def __init__(self, decisions: list):
        self.decisions = decisions
        self.call_count = 0
    
    async def decide(
        self,
        goal: str,
        state: Dict[str, Any],
        constraints: Optional[Dict[str, Any]] = None
    ) -> Decision:
        decision = self.decisions[self.call_count] if self.call_count < len(self.decisions) else self.decisions[-1]
        self.call_count += 1
        return decision


async def test_fail_replan_pass():
    """
    Test scenario: First execution FAILS validation → replan → Second execution PASSES
    
    Expected: 2 iterations, success status
    """
    print("\n" + "="*70)
    print("TEST: FAIL → REPLAN → PASS")
    print("="*70)
    
    goal = "Test goal: fail then pass"
    
    # Setup: Mock components
    evidence = MockEvidenceLogger()
    
    # Decisions: Always approve
    decisions = [
        Decision(
            decision_id="dec_1",
            goal=goal,
            decision="approved",
            consensus_type="unanimous",
            approval_ratio=1.0,
            avg_feasibility=95,
            avg_confidence=95,
            recommended_plan="Execute goal with standard approach"
        ),
        Decision(
            decision_id="dec_2",
            goal=goal,
            decision="approved",
            consensus_type="unanimous",
            approval_ratio=1.0,
            avg_feasibility=95,
            avg_confidence=95,
            recommended_plan="Execute goal with revised approach (addressing issues)"
        )
    ]
    council = MockCouncil(decisions)
    
    # Execution results: Same success for both (issue is in validation)
    exec_results = [
        {
            "status": "success",
            "output": "Task completed (first attempt)",
            "execution_time_ms": 100
        },
        {
            "status": "success",
            "output": "Task completed (second attempt with fixes)",
            "execution_time_ms": 150
        }
    ]
    executor = MockExecutor(exec_results)
    
    # Validation results: FAIL first, PASS second
    issue = ValidationIssue(
        severity="high",
        category="quality",
        description="Missing execution metrics",
        found_by="test_validator",
        location="execution_result",
        recommendation="Add timing information"
    )
    
    validations = [
        # First validation: FAIL (majority_pass but we'll use failed)
        ValidationResult(
            passed=False,
            confidence=60,
            consensus_type="failed",
            checks=[
                ValidationCheck(
                    validator_name="test",
                    check_type="quality",
                    passed=False,
                    confidence=50,
                    issues=[issue],
                    reasoning="Quality check failed"
                )
            ],
            all_issues=[issue],
            critical_issues=[],
            validation_id="val_1"
        ),
        # Second validation: PASS
        ValidationResult(
            passed=True,
            confidence=90,
            consensus_type="unanimous_pass",
            checks=[
                ValidationCheck(
                    validator_name="test",
                    check_type="quality",
                    passed=True,
                    confidence=90,
                    issues=[],
                    reasoning="All checks passed"
                )
            ],
            all_issues=[],
            critical_issues=[],
            validation_id="val_2"
        )
    ]
    validator = MockValidator(validations)
    
    # Create controller with minimal config
    config = MetaControllerConfig(max_iters=5, step_timeout_sec=10)
    controller = MetaController(council, executor, validator, evidence, config)
    
    # Run goal
    result = await controller.run_goal(goal)
    
    # Verify results
    print(f"\n[RESULT] Status: {result['status']}")
    print(f"[RESULT] Iterations: {result['iterations']}")
    print(f"[RESULT] Final validation: {result.get('final_validation', {})}")
    
    # Assertions
    assert result['status'] == 'success', f"Expected success, got {result['status']}"
    assert result['iterations'] == 2, f"Expected 2 iterations, got {result['iterations']}"
    assert result['final_validation']['passed'], "Expected final validation to pass"
    
    # Check evidence logging
    print(f"\n[EVIDENCE] Events logged: {len(evidence.events)}")
    event_types = [e['type'] for e in evidence.events]
    print(f"[EVIDENCE] Event types: {event_types}")
    
    assert 'goal_started' in event_types, "Missing goal_started event"
    assert 'replan_triggered' in event_types, "Missing replan_triggered event"
    assert 'goal_completed' in event_types, "Missing goal_completed event"
    
    # Verify council was called twice (replan)
    assert council.call_count == 2, f"Expected 2 council calls, got {council.call_count}"
    assert executor.call_count == 2, f"Expected 2 executor calls, got {executor.call_count}"
    assert validator.call_count == 2, f"Expected 2 validator calls, got {validator.call_count}"
    
    print("\n[PASS] ✅ FAIL→REPLAN→PASS TEST PASSED")
    return True


async def test_immediate_success():
    """
    Test scenario: First execution PASSES immediately
    
    Expected: 1 iteration, success status
    """
    print("\n" + "="*70)
    print("TEST: IMMEDIATE SUCCESS")
    print("="*70)
    
    evidence = MockEvidenceLogger()
    
    decisions = [
        Decision(
            decision_id="dec_1",
            goal="Immediate success goal",
            decision="approved",
            consensus_type="unanimous",
            approval_ratio=1.0,
            avg_feasibility=95,
            avg_confidence=95,
            recommended_plan="Execute goal"
        )
    ]
    council = MockCouncil(decisions)
    
    exec_results = [
        {"status": "success", "output": "Done", "execution_time_ms": 100}
    ]
    executor = MockExecutor(exec_results)
    
    validations = [
        ValidationResult(
            passed=True,
            confidence=95,
            consensus_type="unanimous_pass",
            checks=[],
            all_issues=[],
            critical_issues=[],
            validation_id="val_1"
        )
    ]
    validator = MockValidator(validations)
    
    config = MetaControllerConfig(max_iters=5, step_timeout_sec=10)
    controller = MetaController(council, executor, validator, evidence, config)
    
    result = await controller.run_goal("Immediate success goal")
    
    print(f"\n[RESULT] Status: {result['status']}")
    print(f"[RESULT] Iterations: {result['iterations']}")
    
    assert result['status'] == 'success', f"Expected success, got {result['status']}"
    assert result['iterations'] == 1, f"Expected 1 iteration, got {result['iterations']}"
    assert council.call_count == 1, f"Expected 1 council call, got {council.call_count}"
    
    print("\n[PASS] ✅ IMMEDIATE SUCCESS TEST PASSED")
    return True


async def test_council_rejection():
    """
    Test scenario: Council rejects plan
    
    Expected: Failed status, single iteration
    """
    print("\n" + "="*70)
    print("TEST: COUNCIL REJECTION")
    print("="*70)
    
    evidence = MockEvidenceLogger()
    
    decisions = [
        Decision(
            decision_id="dec_1",
            goal="Risky goal",
            decision="rejected",
            consensus_type="split",
            approval_ratio=0.33,
            avg_feasibility=20,
            avg_confidence=30,
            recommended_plan="Plan rejected due to risk"
        )
    ]
    council = MockCouncil(decisions)
    
    executor = MockExecutor([])
    validator = MockValidator([])
    
    config = MetaControllerConfig(max_iters=5, step_timeout_sec=10)
    controller = MetaController(council, executor, validator, evidence, config)
    
    result = await controller.run_goal("Risky goal")
    
    print(f"\n[RESULT] Status: {result['status']}")
    print(f"[RESULT] Reason: {result.get('reason', 'N/A')}")
    
    assert result['status'] == 'failed', f"Expected failed, got {result['status']}"
    assert 'rejected' in result.get('reason', '').lower(), "Expected rejection reason"
    assert executor.call_count == 0, "Executor should not be called"
    
    print("\n[PASS] ✅ COUNCIL REJECTION TEST PASSED")
    return True


async def run_all_tests():
    """Run all MetaController tests."""
    print("\n" + "="*70)
    print("METACONTROLLER TEST SUITE")
    print("="*70)
    
    results = {
        "fail_replan_pass": False,
        "immediate_success": False,
        "council_rejection": False
    }
    
    try:
        results["fail_replan_pass"] = await test_fail_replan_pass()
    except AssertionError as e:
        logger.error(f"FAIL_REPLAN_PASS test failed: {e}")
        print(f"\n[FAIL] ❌ TEST FAILED: {e}")
    except Exception as e:
        logger.error(f"FAIL_REPLAN_PASS test error: {e}", exc_info=True)
        print(f"\n[ERROR] ❌ TEST ERROR: {e}")
    
    try:
        results["immediate_success"] = await test_immediate_success()
    except AssertionError as e:
        logger.error(f"IMMEDIATE_SUCCESS test failed: {e}")
        print(f"\n[FAIL] ❌ TEST FAILED: {e}")
    except Exception as e:
        logger.error(f"IMMEDIATE_SUCCESS test error: {e}", exc_info=True)
        print(f"\n[ERROR] ❌ TEST ERROR: {e}")
    
    try:
        results["council_rejection"] = await test_council_rejection()
    except AssertionError as e:
        logger.error(f"COUNCIL_REJECTION test failed: {e}")
        print(f"\n[FAIL] ❌ TEST FAILED: {e}")
    except Exception as e:
        logger.error(f"COUNCIL_REJECTION test error: {e}", exc_info=True)
        print(f"\n[ERROR] ❌ TEST ERROR: {e}")
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_flag in results.items():
        status = "✅ PASS" if passed_flag else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - METACONTROLLER VERIFIED")
    else:
        print(f"\n⚠️  {total - passed} TEST(S) FAILED")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)
