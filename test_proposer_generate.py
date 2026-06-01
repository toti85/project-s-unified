#!/usr/bin/env python3
"""Test proposer to debug why sections are missing."""

from organism.core.observer import Observer
from organism.core.prioritizer import PriorityEngine
from organism.core.proposer import Proposer
from organism.core.observer import Task
from pathlib import Path

# Get tasks
observer = Observer(repo_root=".")
observation = observer.observe()

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

# Score and rank
engine = PriorityEngine()
all_scored = engine.rank(tasks, top_n=100)
top_scored = all_scored[:20]

print("=" * 80)
print("TEST: Proposer Generate")
print("=" * 80)

print(f"\nInput:")
print(f"  Top scored: {len(top_scored)}")
print(f"  All scored: {len(all_scored)}")

# Test proposer
proposer = Proposer(Path("organism/evidence"))

try:
    # Test _generate_proposal_md directly
    print("\nGenerating markdown...")
    md = proposer._generate_proposal_md(top_scored, all_tasks=all_scored)
    
    print(f"Generated {len(md)} characters")
    
    # Check for sections
    has_kill_list = "KILL LIST" in md
    has_resistance = "STRATEGIC RESISTANCE" in md
    has_approval = "Approval Instructions" in md
    
    print(f"\nSections found:")
    print(f"  Kill List: {has_kill_list}")
    print(f"  Resistance: {has_resistance}")
    print(f"  Approval: {has_approval}")
    
    # Show last 500 chars
    print("\nLast 500 chars of markdown:")
    print("---")
    print(md[-500:])
    
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
