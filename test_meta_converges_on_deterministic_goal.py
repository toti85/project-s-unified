"""
Test: Meta path converges on deterministic goals
- Iteration 1: Empty output → validator fails → replan triggered
- Iteration 2: Non-empty output, no critical issues → should PASS via deterministic criterion
"""
import asyncio
import sys
import json
from pathlib import Path
from dataclasses import dataclass

# UTF-8 encoding for Windows
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).parent))

from src.core.meta.meta_controller import MetaController, MetaControllerConfig


@dataclass
class MockValidationResult:
    """Mock validation result."""
    passed: bool
    consensus_type: str
    confidence: float
    critical_issues: list = None
    all_issues: list = None
    
    def __post_init__(self):
        if self.critical_issues is None:
            self.critical_issues = []
        if self.all_issues is None:
            self.all_issues = []


@dataclass
class MockValidationIssue:
    """Mock validation issue with proper object structure."""
    category: str = "formatting"
    description: str = "Minor issue"
    severity: str = "low"
    recommendation: str = "Consider improving"


class MockStrategyCouncil:
    """Mock council that approves decisions."""
    def __init__(self):
        self.call_count = 0
    
    async def decide(self, goal, context=None):
        """Always approve."""
        from dataclasses import dataclass
        
        @dataclass
        class MockDecision:
            decision: str = "proceed"
            consensus_type: str = "unanimous"
            approval_ratio: float = 1.0
            avg_confidence: float = 0.9
        
        return MockDecision()


class DeterministicExecutor:
    """Mock executor that returns empty output first, then non-empty."""
    def __init__(self):
        self.call_count = 0
    
    async def execute(self, decision, context=None):
        """Iteration 1: empty, Iteration 2+: non-empty output."""
        self.call_count += 1
        
        if self.call_count == 1:
            # First iteration: empty output
            return {
                "status": "success",
                "output": "",
                "execution_time_ms": 100
            }
        else:
            # Second iteration: non-empty output
            return {
                "status": "success",
                "output": "Generated content for goal",
                "result": ["item1", "item2"],
                "execution_time_ms": 100
            }


class DeterministicValidator:
    """Mock validator that fails on empty output, passes with non-empty and no critical issues."""
    def __init__(self):
        self.call_count = 0
    
    async def validate(self, execution_result, goal):
        """Iteration 1: fail, Iteration 2: conditional with no critical issues."""
        self.call_count += 1
        
        if self.call_count == 1:
            # First iteration: validation fails (empty output)
            return MockValidationResult(
                passed=False,
                consensus_type="failed",
                confidence=0.0,
                critical_issues=[],
                all_issues=[MockValidationIssue(category="output", description="No output generated", severity="high")]
            )
        else:
            # Second iteration: conditional but no critical issues
            return MockValidationResult(
                passed=False,  # Validator says conditional
                consensus_type="conditional",
                confidence=0.5,
                critical_issues=[],  # But NO critical issues
                all_issues=[MockValidationIssue(category="formatting", description="Minor formatting suggestion", severity="low")]
            )


class MockEvidenceLogger:
    """Mock evidence logger that writes to JSONL."""
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
    
    def log_event(self, event_type: str, event_data: dict):
        """Log event to JSONL."""
        import json
        from datetime import datetime
        
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": event_data
        }
        
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")
    
    def get_log_path(self):
        """Return log path."""
        return str(self.path)


async def test_meta_converges_on_deterministic_goal():
    """Test that Meta path converges via deterministic criterion."""
    
    print("\n" + "="*80)
    print("TEST: Meta Converges on Deterministic Goal")
    print("="*80)
    
    # Setup
    council = MockStrategyCouncil()
    executor = DeterministicExecutor()
    validator = DeterministicValidator()
    
    # Evidence log in temp location
    evidence_path = Path("memory/intelligence/test_deterministic_evidence.jsonl")
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.unlink(missing_ok=True)  # Clear if exists
    
    logger = MockEvidenceLogger(evidence_path)
    
    config = MetaControllerConfig(max_iters=5, step_timeout_sec=30)
    controller = MetaController(council, executor, validator, logger, config)
    
    # Execute
    goal = "Generate output for processing"
    print(f"\n📝 Goal: {goal}")
    print(f"📋 Config: max_iters={config.max_iters}")
    
    result = await controller.run_goal(goal)
    
    print(f"\n📊 Result:")
    print(f"  Status: {result['status']}")
    print(f"  Status reason: {result.get('status_reason', 'N/A')}")
    print(f"  Iterations: {result['iterations']}")
    
    # Read evidence
    events = []
    with open(evidence_path, 'r') as f:
        for line in f:
            if line.strip():
                events.append(json.loads(line))
    
    print(f"\n📋 Evidence Events ({len(events)} total):")
    for evt in events:
        evt_type = evt.get('event_type')
        data = evt.get('data', {})
        iteration = data.get('iteration', 'N/A')
        print(f"  - {evt_type} (iteration={iteration})")
    
    # Assertions
    print(f"\n🔍 Assertions:")
    
    # 1. Status must be "passed"
    assert result['status'] == "passed", f"❌ Status should be 'passed', got {result['status']}"
    print(f"  ✅ Status is 'passed'")
    
    # 2. Reason should be deterministic
    assert "deterministic" in result.get('status_reason', ''), \
        f"❌ Should converge via deterministic criterion, got {result.get('status_reason')}"
    print(f"  ✅ Converged via deterministic criterion (not validator approval)")
    
    # 3. Should complete in 2 iterations (not max)
    assert result['iterations'] == 2, f"❌ Should complete in 2 iterations, got {result['iterations']}"
    print(f"  ✅ Completed in exactly 2 iterations")
    
    # 4. Evidence must contain both iterations
    goal_started = [e for e in events if e.get('event_type') == 'goal_started']
    plan_selected = [e for e in events if e.get('event_type') == 'plan_selected']
    execution_done = [e for e in events if e.get('event_type') == 'execution_done']
    validation_done = [e for e in events if e.get('event_type') == 'validation_done']
    goal_completed = [e for e in events if e.get('event_type') == 'goal_completed']
    
    assert len(goal_started) == 1, f"❌ Should have 1 goal_started, got {len(goal_started)}"
    print(f"  ✅ goal_started: 1 event")
    
    assert len(plan_selected) == 2, f"❌ Should have 2 plan_selected, got {len(plan_selected)}"
    print(f"  ✅ plan_selected: 2 events (one per iteration)")
    
    assert len(execution_done) == 2, f"❌ Should have 2 execution_done, got {len(execution_done)}"
    print(f"  ✅ execution_done: 2 events (one per iteration)")
    
    assert len(validation_done) == 2, f"❌ Should have 2 validation_done, got {len(validation_done)}"
    print(f"  ✅ validation_done: 2 events (one per iteration)")
    
    assert len(goal_completed) == 1, f"❌ Should have 1 goal_completed, got {len(goal_completed)}"
    print(f"  ✅ goal_completed: 1 event with status='passed'")
    
    # 5. Check validation_done includes issue counts
    val_done_events = [e for e in events if e.get('event_type') == 'validation_done']
    for idx, val_event in enumerate(val_done_events):
        data = val_event.get('data', {})
        assert 'critical_issues' in data, f"❌ Missing critical_issues in validation_done"
        assert 'total_issues' in data, f"❌ Missing total_issues in validation_done"
        print(f"  ✅ Iteration {idx+1} validation: critical={data['critical_issues']}, total={data['total_issues']}")
    
    # 6. goal_completed should include status_reason and last_validation_summary
    completed = goal_completed[0]
    data = completed.get('data', {})
    assert 'status_reason' in data, f"❌ Missing status_reason in goal_completed"
    assert 'last_validation_summary' in data, f"❌ Missing last_validation_summary in goal_completed"
    print(f"  ✅ goal_completed includes status_reason and last_validation_summary")
    
    print(f"\n✅ ALL ASSERTIONS PASSED")
    print(f"✅ Meta path successfully converges on deterministic goal in 2 iterations\n")
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_meta_converges_on_deterministic_goal())
        sys.exit(0 if success else 1)
    except AssertionError as e:
        print(f"\n❌ {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
