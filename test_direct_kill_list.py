#!/usr/bin/env python3
"""
Direct test of kill list detection in organism flow.
"""

import sys
import importlib

# Force clean imports
for mod in list(sys.modules.keys()):
    if 'organism' in mod:
        del sys.modules[mod]

# Now import fresh
from organism.core.observer import Observer, Task
from organism.core.prioritizer import PriorityEngine
from organism.core.loop import DevOrganism

def test_kill_list_in_loop():
    """Test k ill list detection through actual organism loop."""
    print("=" * 60)
    print("TEST: Kill List in Organism Loop")
    print("=" * 60)
    
    # Create organism instance
    organism = DevOrganism('.', 'organism/evidence')
    
    # Get one loop cycle
    results = organism.run_once(top_n=20, use_taste_model=False)
    
    print(f"\nTop proposals: {len(results['top_proposals'])}")
    
    # Check which tasks have is_kill_list flag
    kill_list_count = 0
    for idx, task_dict in enumerate(results['top_proposals'], 1):
        is_kill = task_dict.get('is_kill_list', False)
        if is_kill:
            kill_list_count += 1
            print(f"[{idx}] {task_dict['description'][:50]}... [KILL LIST]")
        elif 'rename' in task_dict['description'].lower():
            print(f"[{idx}] {task_dict['description'][:50]}... [SHOULD BE KILL]")
    
    print(f"\nTotal kill list tasks found: {kill_list_count}")
    
    # Check proposals file for kill list section
    proposals_path = 'organism/evidence/top_proposals.md'
    with open(proposals_path) as f:
        content = f.read()
        if 'KILL LIST' in content:
            print("[OK] Kill list section in proposals!")
        else:
            print("[FAIL] No kill list section in proposals")

if __name__ == '__main__':
    test_kill_list_in_loop()
