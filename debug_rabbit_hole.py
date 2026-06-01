#!/usr/bin/env python3
"""Debug rabbit hole risk detection."""

from organism.core.observer import Observer
from organism.core.prioritizer import PriorityEngine

# Extract tasks
observer = Observer('.')
observation = observer.observe()
todos = observation.todos

engine = PriorityEngine()

# Find deployment-related tasks
deployment_tasks = []
for todo in todos:
    text_lower = (todo['text'] + " " + todo.get('description', '')).lower()
    if 'deployment' in text_lower or 'ethers' in text_lower or 'hardhat' in text_lower:
        deployment_tasks.append(todo)

print(f"Found {len(deployment_tasks)} deployment-related tasks\n")

for todo in deployment_tasks[:5]:
    text_lower = (todo['text'] + " " + todo.get('description', '')).lower()
    # Create a Task object
    from organism.core.observer import Task
    task = Task(
        task_id=todo.get('file', ''),
        text=todo['text'],
        description=todo.get('description', ''),
        file=todo['file'],
        line=todo['line'],
        source='todo',
        snippet='',
        source_path=todo.get('file', ''),
        issue_url=todo.get('issue_url', ''),
        metadata={'priority': todo.get('priority', 'TODO')}
    )
    risk = engine.estimate_rabbit_hole_risk(task)
    print(f"TASK: {todo['text'][:70]}")
    print(f"  Combined text (first 100 chars): {text_lower[:100]}")
    print(f"  Estimated risk: {risk:.2f}")
    print()

# Also check what HIGH risk tasks exist
print("\n" + "="*60)
print("HIGH RISK TASKS (0.6+):\n")

from organism.core.observer import Task

high_risk_tasks = []
for todo in todos:
    task = Task(
        task_id=todo.get('file', ''),
        text=todo['text'],
        description=todo.get('description', ''),
        file=todo['file'],
        line=todo['line'],
        source='todo',
        snippet='',
        source_path=todo.get('file', ''),
        issue_url=todo.get('issue_url', ''),
        metadata={'priority': todo.get('priority', 'TODO')}
    )
    risk = engine.estimate_rabbit_hole_risk(task)
    if risk >= 0.6:
        high_risk_tasks.append((todo, risk))

high_risk_tasks.sort(key=lambda x: x[1], reverse=True)

for todo, risk in high_risk_tasks[:10]:
    print(f"[{risk:.2f}] {todo['text'][:70]}")

print(f"\nTotal HIGH risk tasks: {len(high_risk_tasks)}/{len(todos)} ({100*len(high_risk_tasks)/len(todos):.1f}%)")

# Count MEDIUM and HIGH
medium_high = 0
for todo in todos:
    task = Task(
        task_id=todo.get('file', ''),
        text=todo['text'],
        description=todo.get('description', ''),
        file=todo['file'],
        line=todo['line'],
        source='todo',
        snippet='',
        source_path=todo.get('file', ''),
        issue_url=todo.get('issue_url', ''),
        metadata={'priority': todo.get('priority', 'TODO')}
    )
    if engine.estimate_rabbit_hole_risk(task) >= 0.3:
        medium_high += 1

print(f"Total MEDIUM+HIGH risk tasks: {medium_high}/{len(todos)} ({100*medium_high/len(todos):.1f}%)")
