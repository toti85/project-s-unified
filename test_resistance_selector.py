#!/usr/bin/env python3
"""Test Strategic Resistance selector - verify up to 3 tasks are selected with proper filtering."""

from organism.core.observer import Observer
from organism.core.prioritizer import PriorityEngine
from organism.core.proposer import Proposer
from pathlib import Path

# Get actual tasks from observer
observer = Observer(repo_root=".")
observation = observer.observe()

# Convert observations to tasks
from organism.core.observer import Task
tasks = []
for todo in observation.todos:
    task = Task(
        task_id=todo['task_id'],
        description=f"[{todo['priority']}] {todo['text']} ({todo['file']}:{todo['line']})",
        source='todo',
        file=todo['file'],
        line=todo['line'],
        metadata={'priority': todo['priority']},
        text=todo['text'],
        snippet=todo['snippet'],
        source_path=todo['file'],
        issue_url=todo.get('issue_url', '')
    )
    tasks.append(task)

# Score and rank them
engine = PriorityEngine()
scored = engine.rank(tasks, top_n=100)

print("=" * 80)
print("TEST: Strategic Resistance Selector")
print("=" * 80)

# Test the resistance selector
proposer = Proposer(Path("organism/evidence"))
resistance_with_reasons = proposer._select_resistance_tasks(scored, max_resistance=3, debug=True)

print("\n" + "=" * 80)
print("RESULTS")
print("=" * 80)

print(f"\n✓ Resistance cases selected: {len(resistance_with_reasons)}/3")
print()

for i, (task, reason) in enumerate(resistance_with_reasons, 1):
    print(f"[{i}] {task['text'][:60]}")
    print(f"    Task ID: {task['task_id']}")
    print(f"    Rabbit Hole: {task.get('rabbit_hole_risk', 0):.2f}")
    print(f"    Strategic: {task.get('strategic_score', 0):.1f}/10")
    print(f"    Context Tags: {task.get('context_tags', set())}")
    print(f"    Is Kill List: {task.get('is_kill_list', False)}")
    print(f"    Reason: {reason}")
    print()

# Verify evidence tasks are never selected
evidence_tasks = [t for t in scored if 'evidence_support' in t.get('context_tags', set())]
resistance_task_ids = {t['task_id'] for t, _ in resistance_with_reasons}
evidence_in_resistance = [t for t in evidence_tasks if t['task_id'] in resistance_task_ids]

print("=" * 80)
print("VALIDATION")
print("=" * 80)
print(f"✓ Total evidence support tasks: {len(evidence_tasks)}")
print(f"✓ Evidence tasks in resistance: {len(evidence_in_resistance)}")

if len(evidence_in_resistance) == 0:
    print("  ✅ PASS: No evidence tasks in resistance (protected correctly)")
else:
    print("  ❌ FAIL: Evidence tasks leaked into resistance:")
    for t in evidence_in_resistance:
        print(f"    - {t['text'][:50]}")

print(f"✓ Kill list tasks in resistance: {sum(1 for t, _ in resistance_with_reasons if t.get('is_kill_list', False))}")

# Show some candidates that were filtered out
print("\n" + "=" * 80)
print("FILTERING ANALYSIS")
print("=" * 80)

candidates_after_filter = [
    t for t in scored
    if not t.get('is_kill_list', False)
    and 'evidence_support' not in t.get('context_tags', set())
]

print(f"Total tasks: {len(scored)}")
print(f"After protection filtering: {len(candidates_after_filter)}")
print(f"Resistance selected: {len(resistance_with_reasons)}")
print(f"Resistance rate: {len(resistance_with_reasons) / max(len(candidates_after_filter), 1) * 100:.1f}%")

print("\n" + "=" * 80)
