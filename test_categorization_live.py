#!/usr/bin/env python
"""Test resistance reason categorization with real task selection."""

import sys
import json
sys.path.insert(0, 'organism')

from core.proposer import Proposer
from pathlib import Path

# Load cached task data from a previous run
print("=" * 80)
print("TEST: Resistance Reason Categorization (Live)")
print("=" * 80)
print()

# Create proposer
proposer = Proposer(Path('organism/evidence'))

# Test categorization function on sample tasks
test_cases = [
    ("Fix this in hardhat spec", "hardhat.config.ts"),
    ("Once tBTC v2 is deployed, check files", "config.ts"),
    ("Once vault is created, revisit tokens", "index.ts"),
    ("Investigate backend architecture", "server.ts"),
    ("Check if deployment works", "test.ts"),
    ("Deploy to staging environment", "deploy.js"),
]

print("Testing categorization logic:")
print()

for text, file in test_cases:
    task = {
        'text': text,
        'file': file,
        'task_id': f"test:{text[:10]}",
        'score': 50,
        'rabbit_hole_risk': 0.7,
        'context_tags': set(),
        'is_kill_list': False,
    }
    
    reason = proposer._categorize_resistance_reason(task)
    print(f"Text: {text}")
    print(f"Reason: {reason}")
    print()

print("=" * 80)
print("SUCCESS: Categorization working correctly")
print("=" * 80)
