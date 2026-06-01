#!/usr/bin/env python3
"""
FIREDANCER CONSENSUS AUDIT - DEEP ANALYSIS
============================================
Targeted search for consensus-critical functions and invariant enforcement.
"""

import os
import re
from pathlib import Path
from collections import defaultdict

FIREDANCER = Path("C:\\firedancer")

def search_files(directory, pattern, extensions=[".c", ".h"]):
    """Search files for pattern"""
    results = defaultdict(list)
    pattern_re = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
    
    for ext in extensions:
        for filepath in directory.rglob(f"*{ext}"):
            if any(skip in str(filepath) for skip in [".git", "build", "test_"]):
                continue
            try:
                content = filepath.read_text(errors='ignore')
                for i, line in enumerate(content.split('\n'), 1):
                    if pattern_re.search(line):
                        results[str(filepath)].append((i, line.strip()))
            except:
                pass
    
    return results

def find_consensus_functions():
    """Find critical consensus functions"""
    print("\n" + "="*80)
    print("FIREDANCER CONSENSUS - CRITICAL FUNCTIONS & INVARIANTS")
    print("="*80)
    
    # SEARCH 1: Fork choice / weight calculation
    print("\n[1] FORK CHOICE & WEIGHT CALCULATION")
    print("-" * 80)
    
    searches = [
        ("weight", "Fork weight", 3),
        ("fork_choice|choose.*fork|select.*fork", "Fork selection", 3),
        ("heaviest|best.*fork", "Heaviest chain", 3),
        ("slot_vote|voted_slot|tower", "Tower voting", 3),
    ]
    
    for pattern, desc, limit in searches:
        results = search_files(FIREDANCER / "src", pattern)
        if results:
            print(f"\n  ✓ {desc}")
            count = 0
            for filepath, matches in sorted(results.items()):
                if count >= limit:
                    break
                print(f"    File: {Path(filepath).relative_to(FIREDANCER)}")
                for line_no, line in matches[:2]:
                    print(f"      Line {line_no}: {line[:75]}")
                count += 1
        else:
            print(f"\n  ? {desc} - NOT FOUND")
    
    # SEARCH 2: Vote verification & validation
    print("\n\n[2] VOTE VERIFICATION & VALIDATION")
    print("-" * 80)
    
    searches = [
        ("verify.*vote|vote.*verify|check_vote", "Vote verification", 3),
        ("vote_epoch|vote_slot|voted_for", "Vote tracking", 3),
        ("voting_keypair|vote_account", "Vote authority", 3),
        ("lockout|vote_weight", "Vote weight/lockout", 3),
    ]
    
    for pattern, desc, limit in searches:
        results = search_files(FIREDANCER / "src", pattern)
        if results:
            print(f"\n  ✓ {desc}")
            for filepath, matches in sorted(results.items())[:limit]:
                print(f"    File: {Path(filepath).relative_to(FIREDANCER)}")
                for line_no, line in matches[:1]:
                    print(f"      Line {line_no}: {line[:70]}")


        else:
            print(f"\n  ? {desc}")
    
    # SEARCH 3: Root updates & finalization
    print("\n\n[3] ROOT UPDATES & FINALIZATION")
    print("-" * 80)
    
    searches = [
        ("root|finalized|set_root", "Root updates", 5),
        ("commit|snapshot|persist", "State persistence", 5),
        ("rollback|revert|undo", "Rollback safety", 5),
    ]
    
    for pattern, desc, limit in searches:
        results = search_files(FIREDANCER / "src", pattern)
        if results:
            print(f"\n  ✓ {desc} ({len(results)} locations)")
            for filepath, matches in list(sorted(results.items()))[:3]:
                rel = Path(filepath).relative_to(FIREDANCER)
                print(f"    {rel}")
    
    # SEARCH 4: Replay protection
    print("\n\n[4] REPLAY PROTECTION & DEDUPLICATION")
    print("-" * 80)
    
    searches = [
        ("signature.*cache|txn_hash|sig_cache|dedup", "Signature tracking", 5),
        ("blockhash.*check|check_blockhash|valid.*hash", "Blockhash validation", 5),
        ("shred.*dup|duplicate.*shred|replay", "Shred deduplication", 5),
    ]
    
    for pattern, desc, limit in searches:
        results = search_files(FIREDANCER / "src", pattern)
        if results:
            print(f"\n  ✓ {desc}")
            print(f"    Found in {min(len(results), limit)} files")
    
    # SEARCH 5: Atomic commit boundaries
    print("\n\n[5] ATOMIC COMMIT BOUNDARIES")
    print("-" * 80)
    
    # Look for potential non-atomic operations
    print("\n  Searching for multi-step operations without clear atomicity...")
    
    patterns = [
        ("bank.*hash|state.*hash|account.*hash", "Hash calculations"),
        ("slot_increment|next_slot|advance.*slot", "Slot progression"),
        ("epoch.*update|leader.*schedule|epoch.*data", "Epoch transitions"),
    ]
    
    for pattern, desc in patterns:
        results = search_files(FIREDANCER / "src", pattern)
        if results:
            print(f"  ✓ {desc} - {len(results)} locations")

if __name__ == "__main__":
    find_consensus_functions()
    print("\n" + "="*80)
    print("END RECONNAISSANCE")
    print("="*80)
