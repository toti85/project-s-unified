#!/usr/bin/env python3
"""
Direct test of kill list detection in organism flow.
"""

import sys
import traceback

try:
    # Force clean imports
    for mod in list(sys.modules.keys()):
        if 'organism' in mod:
            del sys.modules[mod]
    
    # Now import fresh
    from organism.core.observer import Observer, Task
    from organism.core.prioritizer import PriorityEngine
    from organism.core.loop import DevOrganism
    
    print("=" * 60)
    print("TEST: Kill List in Organism Loop")
    print("=" * 60)
    
    # Create organism instance
    organism = DevOrganism('.', 'organism/evidence')
    
    # Get one loop cycle
    print("\nRunning organism cycle...")
    results = organism.run_once(top_n=20, use_taste_model=False)
    
    print(f"\nAnalyzing results...")
    print(f"Top proposals: {len(results['top_proposals'])}")
    
    # Check which tasks have is_kill_list flag
    kill_list_count = 0
    rename_found = False
    for idx, task_dict in enumerate(results['top_proposals'], 1):
        is_kill = task_dict.get('is_kill_list', False)
        has_rename = 'rename' in task_dict['description'].lower()
        
        if is_kill:
            kill_list_count += 1
            print(f"[{idx}] KILL: {task_dict['description'][:50]}")
        elif has_rename:
            rename_found = True
            print(f"[{idx}] RENAME (not flagged): {task_dict['description'][:50]}")
    
    print(f"\nTotal kill list tasks: {kill_list_count}")
    print(f"Rename task found but not flagged: {rename_found}")
    
    # Check proposals file for kill list section  
    import os
    proposals_path = 'organism/evidence/top_proposals.md'
    if os.path.exists(proposals_path):
        with open(proposals_path) as f:
            content = f.read()
            if 'KILL LIST' in content:
                print("[OK] Kill list section in proposals")
            else:
                print("[FAIL] Kill list NOT in proposals")
    
    print("\n" + "=" * 60)

except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()
