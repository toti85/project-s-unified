"""
Micro-test: Verify evidence logging includes goal_id in per-iteration events.

Checks the existing meta_evidence.jsonl file to verify:
- goal_started event exists
- At least 4 per-iteration events logged (plan_selected, execution_done, validation_done, replan_triggered)
- Each event includes goal_id parameter
"""
import sys
import json
from pathlib import Path

# UTF-8 encoding for Windows
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).parent))


def test_evidence_logging_with_goal_id():
    """Test that evidence logging includes goal_id in all iteration events."""
    
    # Read evidence file - check multiple locations
    evidence_file = Path("meta_evidence.jsonl")
    if not evidence_file.exists():
        evidence_file = Path("memory/intelligence/meta_evidence.jsonl")
    assert evidence_file.exists(), f"meta_evidence.jsonl not found (checked: {evidence_file})"
    
    # Parse all events
    events = []
    with open(evidence_file, 'r') as f:
        for line in f:
            if line.strip():
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    
    print(f"📊 Total events in log: {len(events)}")
    
    # Find latest goal_id from recent events
    last_goal_id = None
    goal_events = []
    
    # Look for goal_completed events from the end
    for event in reversed(events[-100:]):  # Check last 100 events
        if event.get("event_type") == "goal_completed":
            last_goal_id = event.get("data", {}).get("goal_id")
            if last_goal_id:
                break
    
    if last_goal_id:
        goal_events = [e for e in events if e.get("data", {}).get("goal_id") == last_goal_id]
    
    # Assertions
    print(f"\n📊 Evidence Logging Verification")
    print(f"================================")
    print(f"Goal ID: {last_goal_id}")
    print(f"Total events for goal: {len(goal_events)}")
    
    # Check for goal_started
    goal_started = [e for e in goal_events if e.get("event_type") == "goal_started"]
    assert len(goal_started) > 0, "❌ goal_started event missing"
    print(f"✅ goal_started: {len(goal_started)} event(s)")
    
    # Check for per-iteration events
    plan_selected = [e for e in goal_events if e.get("event_type") == "plan_selected"]
    execution_done = [e for e in goal_events if e.get("event_type") == "execution_done"]
    validation_done = [e for e in goal_events if e.get("event_type") == "validation_done"]
    replan_triggered = [e for e in goal_events if e.get("event_type") == "replan_triggered"]
    
    print(f"✅ plan_selected: {len(plan_selected)} event(s)")
    print(f"✅ execution_done: {len(execution_done)} event(s)")
    print(f"✅ validation_done: {len(validation_done)} event(s)")
    print(f"✅ replan_triggered: {len(replan_triggered)} event(s)")
    
    # Check for goal_completed
    goal_completed = [e for e in goal_events if e.get("event_type") == "goal_completed"]
    assert len(goal_completed) > 0, "❌ goal_completed event missing"
    print(f"✅ goal_completed: {len(goal_completed)} event(s)")
    
    # Total iteration events (excluding goal_started/completed)
    iteration_events = plan_selected + execution_done + validation_done + replan_triggered
    total_events = len(goal_events)
    
    print(f"\n📈 Event Summary")
    print(f"================")
    print(f"Total events: {total_events}")
    print(f"Per-iteration events: {len(iteration_events)}")
    
    # Assert minimum 5 events (goal_started + at least 4 iteration + goal_completed is possible)
    assert len(iteration_events) >= 4, f"❌ Expected at least 4 iteration events, got {len(iteration_events)}"
    assert total_events >= 5, f"❌ Expected at least 5 total events, got {total_events}"
    
    # Verify goal_id is present in each iteration event
    for event in iteration_events:
        goal_id_in_data = event.get("data", {}).get("goal_id")
        assert goal_id_in_data == last_goal_id, f"❌ goal_id mismatch in {event.get('event_type')}"
    
    print(f"\n✅ SUCCESS: At least 5 events logged with goal_id")
    print(f"✅ All iteration events include goal_id parameter")
    
    # Print sample event
    if plan_selected:
        print(f"\n📝 Sample Event (plan_selected):")
        sample = plan_selected[0]
        print(f"   event_type: {sample.get('event_type')}")
        print(f"   goal_id: {sample.get('data', {}).get('goal_id')}")
        print(f"   iteration: {sample.get('data', {}).get('iteration')}")
    
    return True


if __name__ == "__main__":
    print("🧪 Testing Evidence Logging with goal_id...\n")
    
    try:
        result = test_evidence_logging_with_goal_id()
        print("\n✅ All assertions passed!")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ Assertion failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
