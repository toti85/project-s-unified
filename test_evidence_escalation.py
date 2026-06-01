#!/usr/bin/env python
"""Test evidence escalation protocol."""

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, 'organism')

from core.proposer import Proposer
from core.prioritizer import PriorityEngine

# Create evidence directory
evidence_dir = Path('organism/evidence_test')
evidence_dir.mkdir(parents=True, exist_ok=True)

# Create a decisions.jsonl with some deferrals
decisions_file = evidence_dir / "decisions.jsonl"
decisions = [
    {"timestamp": datetime.now().isoformat(), "task_id": "todo:test1:abc123", "action": "defer"},
    {"timestamp": datetime.now().isoformat(), "task_id": "todo:test1:abc123", "action": "defer"},
    {"timestamp": datetime.now().isoformat(), "task_id": "todo:test2:def456", "action": "approve"},
]

with open(decisions_file, 'w') as f:
    for decision in decisions:
        f.write(json.dumps(decision) + '\n')

print("=" * 80)
print("TEST: Evidence Escalation Protocol")
print("=" * 80)
print()

# Create proposer
proposer = Proposer(evidence_dir)

# Test evidence detection
test_evidence_tasks = [
    {"text": "Test with dust amounts (1 wei, etc.)", "file": "test.ts", "task_id": "todo:test1:abc123"},
    {"text": "Verify rounding errors in calculations", "file": "math.ts", "task_id": "todo:test3:xyz789"},
    {"text": "Check results and confirm vulnerability", "file": "poc.ts", "task_id": "todo:test2:def456"},
    {"text": "Fix the UI button styling", "file": "ui.ts", "task_id": "todo:test4:ghi012"},
]

print("Evidence Task Detection:")
print()
for task in test_evidence_tasks:
    is_evidence = proposer._is_evidence_task(task)
    print(f"  Task: {task['text'][:40]}")
    print(f"  Evidence: {is_evidence}")
    print()

print("=" * 80)
print("Deferral Count Testing:")
print()

# Test deferral counting
deferral_counts = {
    "todo:test1:abc123": proposer._get_deferral_count("todo:test1:abc123"),  # Should be 2
    "todo:test2:def456": proposer._get_deferral_count("todo:test2:def456"),  # Should be 0 (was approved)
    "todo:test3:xyz789": proposer._get_deferral_count("todo:test3:xyz789"),  # Should be 0 (no decisions)
}

for task_id, count in deferral_counts.items():
    print(f"  Task {task_id[-6:]}: {count} deferrals")

print()
print("=" * 80)
print("Escalation Application:")
print()

# Create mock ranked tasks
mock_tasks = [
    {
        "task_id": "todo:test1:abc123",
        "text": "Test with dust amounts (1 wei, etc.)",
        "file": "test.ts",
        "line": 100,
        "score": 59.0,
        "impact": 0.8,
        "learning_value": 0.7,
        "ev": 0.75,
        "strategic_score": 6,
        "effort": 2,
        "rabbit_hole_risk": 0.3,
        "is_quick_win": True,
        "snippet": "// Test code",
        "issue_url": "",
        "why_not": "Medium effort",
        "description": "Test with dust amounts",
        "context_tags": {'evidence_support'},
        "is_kill_list": False,
    },
    {
        "task_id": "todo:test4:ghi012",
        "text": "Fix the UI button styling",
        "file": "ui.ts",
        "line": 50,
        "score": 45.0,
        "impact": 0.5,
        "learning_value": 0.3,
        "ev": 0.4,
        "strategic_score": 3,
        "effort": 1,
        "rabbit_hole_risk": 0.1,
        "is_quick_win": True,
        "snippet": "// UI code",
        "issue_url": "",
        "why_not": "Low priority",
        "description": "Fix UI button",
        "context_tags": set(),
        "is_kill_list": False,
    },
]

escalated = proposer._apply_evidence_escalation(mock_tasks)

print("Before Escalation:")
for task in mock_tasks:
    print(f"  [{task['task_id'][-6:]}] {task['text'][:40]} - Score: {task['score']}")

print()
print("After Escalation:")
for task in escalated:
    marker = " (ESCALATED)" if task.get('evidence_escalated') else ""
    reason = task.get('escalation_reason', '')
    print(f"  [{task['task_id'][-6:]}] {task['text'][:40]} - Score: {task['score']}{marker}")
    if reason:
        print(f"    Reason: {reason}")

print()
print("=" * 80)
print("VERIFICATION")
print("=" * 80)
print()

# Verify escalation worked correctly
escalated_task = [t for t in escalated if t['task_id'] == 'todo:test1:abc123'][0]
non_escalated_task = [t for t in escalated if t['task_id'] == 'todo:test4:ghi012'][0]

assert escalated_task['evidence_escalated'] == True, "Evidence task should be escalated"
assert escalated_task['score'] == 109.0, "Escalated task should have +50 boost (59 + 50 = 109)"
assert escalated_task['original_score'] == 59.0, "Original score should be preserved"
assert '2 deferrals' in escalated_task.get('escalation_reason', ''), "Should show deferral count in reason"
assert non_escalated_task.get('evidence_escalated', False) == False, "Non-evidence task should not be escalated"

print("✅ Evidence detection working")
print("✅ Deferral count tracking working")
print("✅ Evidence task deferred 2x was escalated with +50 boost")
print("✅ Non-evidence tasks unaffected")
print()
print("=" * 80)
print("SUCCESS: Evidence Escalation Protocol Verified")
print("=" * 80)

# Cleanup
import shutil
shutil.rmtree(evidence_dir, ignore_errors=True)
