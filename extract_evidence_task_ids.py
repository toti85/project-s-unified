#!/usr/bin/env python
"""Extract actual task IDs to populate decisions.jsonl for testing."""

import sys
sys.path.insert(0, 'organism')

from pathlib import Path
from organism.core.observer import Observer
from organism.core.prioritizer import PriorityEngine

# Run observation
observer = Observer(repo_root='.')
observations = observer.observe_developments('.')
tasks = observer.observations_to_tasks(observations)

# Prioritize
engine = PriorityEngine()
all_scored = engine.rank(tasks)

# Find evidence tasks
print("=" * 80)
print("Evidence Tasks and Their IDs")
print("=" * 80)
print()

evidence_patterns = ['test with dust', 'check results', 'verify rounding']

for task in all_scored:
    task_text = task.get('text', '').lower()
    if any(pattern in task_text for pattern in evidence_patterns):
        print(f"Text: {task.get('text')[:60]}")
        print(f"Task ID: {task.get('task_id')}")
        print()
