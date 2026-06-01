#!/usr/bin/env python
"""Test the resistance reason categorization logic."""

import sys
sys.path.insert(0, 'organism')

from core.proposer import Proposer
from pathlib import Path

# Test tasks with different characteristics
test_tasks = [
    {
        'task_id': 'test1',
        'text': 'Fix this',
        'file': 'test.ts',
        'score': 50,
        'effort': 2,
        'impact': 0.7,
        'learning_value': 0.3,
        'ev': 0.5,
        'strategic_score': 5,
        'rabbit_hole_risk': 0.7,
        'issue_url': '',
        'context_tags': set(),
        'is_kill_list': False,
    },
    {
        'task_id': 'test2',
        'text': 'Once tBTC v2 is deployed, revisit external files',
        'file': 'config.ts',
        'score': 52,
        'effort': 2,
        'impact': 0.7,
        'learning_value': 0.3,
        'ev': 0.5,
        'strategic_score': 5,
        'rabbit_hole_risk': 0.7,
        'issue_url': '',
        'context_tags': set(),
        'is_kill_list': False,
    },
    {
        'task_id': 'test3',
        'text': 'Once Saddle vault is created, revisit hardhat config',
        'file': 'config.ts',
        'score': 52,
        'effort': 2,
        'impact': 0.7,
        'learning_value': 0.3,
        'ev': 0.5,
        'strategic_score': 5,
        'rabbit_hole_risk': 0.7,
        'issue_url': '',
        'context_tags': set(),
        'is_kill_list': False,
    },
    {
        'task_id': 'test4',
        'text': 'Investigate the possibility of adding Tendermint',
        'file': 'test.ts',
        'score': 54,
        'effort': 3,
        'impact': 0.6,
        'learning_value': 0.5,
        'ev': 0.6,
        'strategic_score': 5,
        'rabbit_hole_risk': 0.65,
        'issue_url': '',
        'context_tags': set(),
        'is_kill_list': False,
    },
]

# Create proposer and test categorization
proposer = Proposer(Path('organism/evidence'))

print("=" * 80)
print("TEST: Resistance Reason Categorization")
print("=" * 80)
print()

for task in test_tasks:
    reason = proposer._categorize_resistance_reason(task)
    print(f"Task: {task['text'][:50]}")
    print(f"  File: {task['file']}")
    print(f"  Reason: {reason}")
    print()

print("=" * 80)
print("SUCCESS: All categorizations generated")
print("=" * 80)
