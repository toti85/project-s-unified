#!/usr/bin/env python3
"""
Test kill list detection integration with organism.

This script runs a fresh Python interpreter to avoid module caching issues.
"""

import subprocess
import sys
import json

def run_fresh_organism():
    """Run organism in a fresh Python process."""
    # Run organism using direct Python execution, not python -m
    cmd = [
        sys.executable, 
        'organism/core/loop.py'
    ]
    
    # Set environment to clear module cache
    env = {
        'PYTHONDONTWRITEBYTECODE': '1',  # Don't create .pyc files
        'PYTHONHASHSEED': '0',
    }
    
    result = subprocess.run(
        cmd, 
        capture_output=True, 
        text=True,
        cwd='.',
        env={**os.environ, **env}
    )
    
    return result.stdout, result.stderr

if __name__ == '__main__':
    import os
    
    print("=" * 60)
    print("TEST: Kill List Integration")
    print("=" * 60)
    
    # Run organism fresh
    stdout, stderr = run_fresh_organism()
    
    # Parse output
    print("\nSTDOUT:")
    print(stdout)
    
    if stderr:
        print("\nSTDERR:")
        print(stderr)
    
    # Check if kill list section appears in proposals
    proposals_file = 'organism/evidence/top_proposals.md'
    if os.path.exists(proposals_file):
        content = open(proposals_file).read()
        if 'KILL LIST' in content or 'kill list' in content:
            print("\n✅ Kill list section found in proposals!")
        else:
            print("\n❌ Kill list section NOT found in proposals")
            print("   Checking for tasks with low strategic scores...")
            
            # Check the top_proposals.md for Rename task
            if 'Rename' in content:
                print("   Found 'Rename' task - should be flagged as kill list")
