#!/usr/bin/env python3
"""Detailed debug of kill list impact on "Rename" tasks."""

from organism.core.observer import Observer, Task
from organism.core.prioritizer import PriorityEngine

# Extract observations
observer = Observer('.')
observation = observer.observe()
todos = observation.todos

engine = PriorityEngine()

print("=" * 70)
print("ALL RENAME TASKS - DETAILED BREAKDOWN")
print("=" * 70)

rename_tasks = [t for t in todos if 'rename' in t['text'].lower()]

for todo in rename_tasks:
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
    
    impact = engine.estimate_impact(task)
    learning = engine.estimate_learning_value(task)
    ev = engine.estimate_ev(task)
    effort = engine.estimate_effort(task)
    strategic = engine.estimate_strategic_score(task)
    rabbit_hole = engine.estimate_rabbit_hole_risk(task)
    
    # Calculate base score (without kill penalty)
    base_score = (impact * 8) + (strategic * 10) + (learning * 4) + (ev * 3) - effort
    base_score -= rabbit_hole * 8
    
    # Quick win bonus check
    is_quick_win = effort <= 2 and impact >= 0.70
    if is_quick_win:
        base_score += 15
    
    # Kill list check
    is_kill = engine.detect_kill_list_candidate(task, strategic, learning)
    
    # Final score with kill penalty
    final_score = base_score
    if is_kill:
        final_score -= 25
    
    print(f"\nTask: {todo['text'][:60]}")
    print(f"  File: {todo['file']}:{todo['line']}")
    print(f"\n  Component Scores:")
    print(f"    Impact: {impact:.2f}")
    print(f"    Learning: {learning:.2f}")
    print(f"    EV: {ev:.2f}")
    print(f"    Strategic: {strategic:.1f}/10")
    print(f"    Effort: {effort:.1f}/10")
    print(f"    Rabbit Hole: {rabbit_hole:.2f}")
    print(f"\n  Score Calculation:")
    print(f"    Base: (impact*8) + (strategic*10) + (learning*4) + (ev*3) - effort - (rabbit*8)")
    print(f"    = ({impact:.2f}*8) + ({strategic:.1f}*10) + ({learning:.2f}*4) + ({ev:.2f}*3) - {effort:.1f} - ({rabbit_hole:.2f}*8)")
    print(f"    = {base_score:.2f}")
    print(f"\n  Kill List Check:")
    print(f"    Strategic <= 4: {strategic <= 4}")
    print(f"    Learning <= 0.3: {learning <= 0.3}")
    print(f"    Is Kill List: {is_kill}")
    print(f"\n  Final Score: {final_score:.2f}")
    if is_kill:
        print(f"    (base {base_score:.2f} - 25 penalty)")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"Total RENAME tasks: {len(rename_tasks)}")
