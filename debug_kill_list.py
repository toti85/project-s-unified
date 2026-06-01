#!/usr/bin/env python3
"""Debug kill list detection."""

from organism.core.observer import Observer, Task
from organism.core.prioritizer import PriorityEngine

# Extract observations
observer = Observer('.')
observation = observer.observe()
todos = observation.todos

engine = PriorityEngine()

# Check a few candidates
candidates_to_check = [
    'rename',
    'comment',
    'documentation',
    'formatting',
]

print("=" * 60)
print("TESTING KILL LIST DETECTION")
print("=" * 60)

for search_term in candidates_to_check:
    print(f"\n{search_term.upper()} TASKS:")
    for todo in todos:
        if search_term in todo['text'].lower():
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
            
            strategic = engine.estimate_strategic_score(task)
            learning = engine.estimate_learning_value(task)
            is_kill = engine.detect_kill_list_candidate(task, strategic, learning)
            
            print(f"  {todo['text'][:60]}")
            print(f"    Strategic: {strategic:.1f}/10, Learning: {learning:.2f}")
            print(f"    Kill List: {is_kill}")
            print()

# Now test full scoring
print("\n" + "=" * 60)
print("FULL SCORING WITH KILL LIST")
print("=" * 60)

rename_count = 0
kill_count = 0

for todo in todos:
    if 'rename' in todo['text'].lower():
        rename_count += 1
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
        
        score, strategic, rabbit_hole, is_quick_win, is_kill_list = engine.calculate_score(task)
        learning = engine.estimate_learning_value(task)
        
        if is_kill_list:
            kill_count += 1
            print(f"KILL: {todo['text'][:50]}")
            print(f"  Score: {score:.2f} (after -25 penalty)")
            print(f"  Strategic: {strategic:.1f}/10, Learning: {learning:.2f}")
            print()

print(f"Total RENAME tasks: {rename_count}")
print(f"Total KILLED: {kill_count}")
