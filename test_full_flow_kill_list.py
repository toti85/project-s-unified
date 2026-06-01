#!/usr/bin/env python3
"""Test full flow: observer -> prioritizer -> check is_kill_list."""

from organism.core.observer import Observer
from organism.core.prioritizer import PriorityEngine

# Get actual tasks from observer
observer = Observer(repo_root=".")
observation = observer.observe()

# Convert observations to tasks (from loop.py logic)
tasks = []
for todo in observation.todos:
    from organism.core.observer import Task
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

engine = PriorityEngine()

print("=" * 80)
print("FULL FLOW TEST: Observer -> Prioritizer -> is_kill_list")
print("=" * 80)

# Find the specific tasks we're tracking
target_tasks = {}
for task in tasks:
    if "Test with dust amounts" in task.text:
        target_tasks["Test with dust amounts"] = task
    elif "Check results" in task.text and "exploit" in task.text.lower():
        target_tasks["Check results"] = task
    elif "Rename to EcdsLibStub" in task.text:
        target_tasks["Rename to EcdsLibStub"] = task

print("\nTracing key tasks through priority engine:\n")

for name, task in target_tasks.items():
    print(f"Task: {name}")
    print(f"  Text: {task.text}")
    
    score, strategic, rabbit_hole, is_quick_win, is_kill_list, context_tags = engine.calculate_score(task)
    
    print(f"  Strategic: {strategic:.1f}/10")
    print(f"  Learning: {engine.estimate_learning_value(task):.2f}")
    print(f"  Context Tags: {context_tags}")
    print(f"  is_kill_list: {is_kill_list}")
    print()

print("=" * 80)
