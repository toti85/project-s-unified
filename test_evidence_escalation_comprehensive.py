#!/usr/bin/env python
"""Final comprehensive test of evidence escalation feature."""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, 'organism')

from core.proposer import Proposer

print("="*90)
print("COMPREHENSIVE EVIDENCE ESCALATION TEST")
print("="*90) 
print()

# Create test evidence directory with realistic scenario
evidence_dir = Path('organism/evidence_escalation_test')
evidence_dir.mkdir(parents=True, exist_ok=True)

# Create a realistic decisions.jsonl with deferrals
decisions_file = evidence_dir / "decisions.jsonl"

# Scenario: "Check results" task has been deferred twice
evidence_task_id = "todo:docs/archiv/testnet_fork_setup.py:363:e5a7b2f1"

decisions_data = [
    {
        "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(), 
        "task_id": evidence_task_id,
        "action": "defer",
        "reason": "Waiting for setup to complete"
    },
    {
        "timestamp": (datetime.now() - timedelta(hours=0.5)).isoformat(),
        "task_id": evidence_task_id, 
        "action": "defer",
        "reason": "Prioritizing deployment tasks first"
    },
]

with open(decisions_file, 'w') as f:
    for decision in decisions_data:
        f.write(json.dumps(decision) + '\n')

print("SCENARIO: Evidence task deferred 2 times")
print("-"*90)
print()
print("Decision History:")
for i, decision in enumerate(decisions_data, 1):
    print(f"  {i}. {decision['action'].upper()} - {decision['reason']}")
print()

# Create proposer and test escalation
proposer = Proposer(evidence_dir)

# Test evidence task matching
test_tasks = [
    {
        "task_id": evidence_task_id,
        "text": "Check results (after running exploit test)",
        "file": "docs/archiv/testnet_fork_setup.py",
        "line": 363,
        "score": 56.65,
        "impact": 0.8,
        "learning_value": 0.9,
        "ev": 0.85,
        "strategic_score": 8,
        "effort": 1.5,
        "rabbit_hole_risk": 0.2,
        "is_quick_win": True,
        "snippet": "# Verify exploit worked correctly",
        "issue_url": "",
        "why_not": "Quick validation",
        "description": "Check results",
        "context_tags": {'evidence_support'},
        "is_kill_list": False,
    },
    {
        "task_id": "todo:other_task:123:xyz",
        "text": "Fix the routing configuration",
        "file": "src/config.ts",
        "line": 42,
        "score": 45.0,
        "impact": 0.5,
        "learning_value": 0.3,
        "ev": 0.4,
        "strategic_score": 3,
        "effort": 2.0,
        "rabbit_hole_risk": 0.1,
        "is_quick_win": False,
        "snippet": "// Router setup",
        "issue_url": "",
        "why_not": "Not critical",
        "description": "Fix routing",
        "context_tags": set(),
        "is_kill_list": False,
    },
]

print("ESCALATION TE ST")
print("-"*90)
print()

# Check deferral count
deferral_count = proposer._get_deferral_count(evidence_task_id)
print(f"Deferral count for evidence task: {deferral_count}")
print(f"Escalation eligible (>= 2): {deferral_count >= 2}")
print()

# Apply escalation
escalated = proposer._apply_evidence_escalation(test_tasks)

print("RESULTS")
print("-"*90)
print()

for task in escalated:
    is_evidence = proposer._is_evidence_task(task)
    is_escalated = task.get('evidence_escalated', False)
    
    print(f"Task: {task['text']}")
    print(f"  Evidence: {is_evidence}")
    print(f"  Original Score: {test_tasks[escalated.index(task)]['score']}")
    print(f"  Final Score: {task['score']}")
    
    if is_escalated:
        original = task.get('original_score', 0)
        boost = task['score'] - original
        print(f"  Boost: +{boost} 🔴 ESCALATED")
        print(f"  Reason: {task['escalation_reason']}")
    print()

print("="*90)
print("VERIFICATION")
print("="*90)
print()

evidence_task = escalated[0]
other_task = escalated[1]

checks = [
    ("Evidence task detected", proposer._is_evidence_task(evidence_task), True),
    ("Evidence task escalated", evidence_task.get('evidence_escalated'), True),
    ("Score boosted (~+50)", round(evidence_task['score'] - 56.65, 1), 50.0),
    ("Original score preserved", evidence_task.get('original_score'), 56.65),
    ("Other task NOT escalated", other_task.get('evidence_escalated', False), False),
    ("Other task score unchanged", other_task['score'], 45.0),
]

all_pass = True
for check_name, actual, expected in checks:
    match = actual == expected
    symbol = "✓" if match else "✗"
    print(f"  {symbol} {check_name}")
    if not match:
        print(f"    Expected: {expected}, Got: {actual}")
        all_pass = False

print()
if all_pass:
    print("="*90)
    print("ALL TESTS PASSED - EVIDENCE ESCALATION PROTOCOL VERIFIED")
    print("="*90)
else:
    print("="*90)
    print("SOME TESTS FAILED")
    print("="*90)

# Cleanup
import shutil
shutil.rmtree(evidence_dir, ignore_errors=True)
