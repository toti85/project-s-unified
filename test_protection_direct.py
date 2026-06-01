#!/usr/bin/env python3
"""Direct test of context tag protection."""

from organism.core.observer import Task
from organism.core.prioritizer import PriorityEngine

engine = PriorityEngine()

# Manually create a task for "Test with dust amounts"
task = Task(
    task_id="test1",
    description="Test with dust amounts (1 wei, etc.)",
    source='todo',
    file='docs/archiv/testnet_fork_setup.py',
    line=393,
    metadata={},
    text="Test with dust amounts (1 wei, etc.)",
    snippet="# TODO: Test with dust amounts (1 wei, etc.)",
    source_path='docs/archiv/testnet_fork_setup.py',
    issue_url=''
)

print("=" * 60)
print("TEST: Context Tag Classification & Kill List Protection")
print("=" * 60)

# Step 1: Classify context
tags = engine.classify_task_context(task)
print(f"\nTask: {task.text}")
print(f"Context Tags: {tags}")

# Step 2: Check kill list status
is_kill = engine.detect_kill_list_candidate(task, strategic=5.5, learning=0.3, context_tags=tags)
print(f"Is Kill List (with protection): {is_kill}")

# Step 3: Test without context_tags (old behavior)
is_kill_no_protection = engine.detect_kill_list_candidate(task, strategic=5.5, learning=0.3, context_tags=None)
print(f"Is Kill List (without tags): {is_kill_no_protection}")

print("\n" + "=" * 60)
print("EXPECTED: is_kill=False (protected by evidence_support tag)")
print("ACTUAL:  is_kill={}".format(is_kill))
print("STATUS:  {}".format("PASS" if not is_kill else "FAIL"))
