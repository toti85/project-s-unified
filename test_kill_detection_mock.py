#!/usr/bin/env python3
"""
Test detect_kill_list_candidate directly with mock data.
"""

from dataclasses import dataclass, field
from organism.core.prioritizer import PriorityEngine

@dataclass
class MockTask:
    """Mock Task for testing."""
    task_id: str
    description: str
    source: str
    file: str = ""
    line: int = 0
    text: str = ""
    snippet: str = ""
    source_path: str = ""
    issue_url: str = ""
    metadata: dict = field(default_factory=dict)

# Create priority engine
engine = PriorityEngine()

# Test task: Rename
task = MockTask(
    task_id="test_rename",
    description="[TODO] Rename to EcdsLibStub (file:7)",
    source="todo",
    file="test.sol",
    line=7,
    text="Rename to EcdsLibStub",
    metadata={"priority": "TODO"}
)

# Check detection
strategic_score = 2.0  # Low strategic value
learning_value = 0.30  # Low learning

print("=" * 60)
print("TEST: detect_kill_list_candidate with Mock Task")
print("=" * 60)

print(f"\nTask: {task.text}")
print(f"Description: {task.description}")
print(f"Strategic: {strategic_score}/10")
print(f"Learning: {learning_value}")

is_kill = engine.detect_kill_list_candidate(task, strategic_score, learning_value)

print(f"\nResult: is_kill_list = {is_kill}")

if is_kill:
    print("SUCCESS: Rename task correctly flagged as kill list")
else:
    print("FAILED: Rename task NOT flagged as kill list")
    
    # Check why
    text_combined = (task.text + " " + task.description).lower()
    print(f"\nDebug: text_combined = '{text_combined[:80] }'")
    print(f"Debug: 'rename' in text_combined = {'rename' in text_combined}")
    print(f"Debug: strategic > 4 = {strategic_score > 4}")
    print(f"Debug: learning > 0.3 = {learning_value > 0.3}")
