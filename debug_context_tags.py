#!/usr/bin/env python3
"""Debug context tag classification for evidence-support tasks."""

from organism.core.observer import Observer, Task
from organism.core.prioritizer import PriorityEngine

# Observe actual tasks
observer = Observer(repo_root=".")
observations = observer.observe()
tasks = observer.convert_observations_to_tasks()

print("=" * 60)
print("DEBUG: Context Tag Classification")
print("=" * 60)

# Look for specific tasks
target_tasks = [
    "Test with dust amounts",
    "Check results",
    "Rename to EcdsLibStub"
]

engine = PriorityEngine()

for task in tasks:
    task_text = task.text.lower()
    
    # Check if this is one of our target tasks
    match = False
    for target in target_tasks:
        if target.lower() in task_text:
            match = True
            break
    
    if not match:
        continue
    
    print(f"\nTask: {task.text}")
    print(f"  File: {task.file}")
    print(f"  Description: {task.description}")
    
    # Get context tags
    tags = engine.classify_task_context(task)
    print(f"  Context Tags: {tags}")
    
    # Check if it would be flagged
    score, strategic, learning = 5.5, 0.3, 0.3
    is_kill_list = engine.detect_kill_list_candidate(task, strategic, learning, tags)
    print(f"  Is Kill List: {is_kill_list}")
    print(f"  Reason: ", end="")
    
    if not is_kill_list:
        if "evidence_support" in tags:
            print("Protected by evidence_support tag")
        else:
            print("Other reason")

print("\n" + "=" * 60)
