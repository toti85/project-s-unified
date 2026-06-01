#!/usr/bin/env python3
"""
Test kill list detection using organism's exact task creation flow.
"""

from organism.core.observer import Observer, Task
from organism.core.prioritizer import PriorityEngine

# Get observations same way organism does
observer = Observer('.')
observation = observer.observe()

# Create Priority Engine
engine = PriorityEngine()

print("=" * 60)
print("TEST: Kill List Detection with Organism Task Creation")
print("=" * 60)

# Create tasks the same way organism does (from _convert_observation_to_tasks)
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

print(f"\nCreated {len(tasks)} tasks from observationn")

# Find rename tasks and check if they get flagged as kill list
rename_count = 0
rename_killed = 0

for task in tasks:
    if 'rename' in task.text.lower():
        rename_count += 1
        
        # Calculate strategic and learning scores like rank() does
        strategic = engine.estimate_strategic_score(task)
        learning = engine.estimate_learning_value(task)
        
        # Check if it's kill list
        is_kill = engine.detect_kill_list_candidate(task, strategic, learning)
        
        print(f"\nTask: {task.text}")
        print(f"  Description: {task.description}")
        print(f"  Strategic: {strategic:.1f}/10")
        print(f"  Learning: {learning:.2f}")
        print(f"  Is Kill List: {is_kill}")
        
        if is_kill:
            rename_killed += 1

print(f"\n{'=' * 60}")
print(f"Summary:")
print(f"  Rename tasks found: {rename_count}")
print(f"  Rename tasks flagged as kill list: {rename_killed}")

if rename_killed == rename_count:
    print("\nSUCCESS: All rename tasks correctly flagged!")
else:
    print(f"\nFAILED: Only {rename_killed}/{rename_count} rename tasks flagged")
