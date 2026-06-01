#!/usr/bin/env python3
"""
Test kill list detection by running organism in a completely fresh subprocess.
"""

import subprocess
import sys
import os

# Kill all cached Python processes
print("Clearing Python cache...")
subprocess.run(
    ['powershell', '-c', 'Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue; Write-Host "Cache cleared"'],
    check=False
)

print("\nRunning organism in fresh subprocess...")
print("=" * 60)

# Run in fresh subprocess with no bytecode caching
env = os.environ.copy()
env['PYTHONDONTWRITEBYTECODE'] = '1'

result = subprocess.run(
    [sys.executable, '-m', 'organism.core.loop', '--repo', '.', '--top', '20'],
    env=env,
    capture_output=False,
    text=True
)

print("=" * 60)
print("\nChecking results...")

# Check proposals file
proposals_path = 'organism/evidence/top_proposals.md'
if os.path.exists(proposals_path):
    content = open(proposals_path).read()
    
    # Look for kill list section
    if 'KILL LIST' in content or 'kill list' in content:
        print("[OK] Kill list section found in proposals!")
        # Show the section
        if 'KILL LIST' in content:
            idx = content.find('KILL LIST')
            print(f"\nKill list section preview (chars {idx}-{idx+200}):")
            print(content[idx:idx+400])
    else:
        print("[FAIL] Kill list section NOT found in proposals")
        
        # Check if rename task is at least mentioned
        if 'Rename' in content:
            print("   [INFO] Rename task IS mentioned - should be in kill list")
            # Count occurrences
            rename_count = content.count('Rename')
            print(f"   Found {rename_count} occurrence(s) of 'Rename'")
        else:
            print("   Rename task not found at all")
else:
    print(f"[FAIL] Proposals file not found at {proposals_path}")
