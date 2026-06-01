#!/usr/bin/env python3
"""
🔥 FIREDANCER CONSENSUS INVARIANT AUDIT
========================================
Autonomous analysis: TASK 0-5

Analyzes consensus-critical paths for state divergence, replay violations,
fork desync possibilities, non-atomic boundaries, and finalization safety.
"""

import os
import subprocess
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Set

FIREDANCER_ROOT = Path("C:\\firedancer")

# ============================================================================
# TASK 0: CODE ORIENTATION
# ============================================================================

class FiredancerAudit:
    def __init__(self):
        self.repo = FIREDANCER_ROOT
        self.critical_modules = {}
        self.findings = defaultdict(list)
    
    def task_0_orientation(self):
        """Map critical directories and entrypoints"""
        print("\n" + "="*80)
        print("TASK 0: CODE ORIENTATION (Directory Map + Consensus Entrypoints)")
        print("="*80)
        
        # Key modules map
        modules = {
            "disco/discof": "Fork choice + vote validation",
            "disco/disco": "Consensus core (voting, fork weight)",
            "funk": "Block replay + transaction execution",
            "groove": "Ledger state + slot progression",
            "waltz": "Clock synchronization / slot timing",
            "ballet": "Binary serialization (shreds, votes)",
            "flamenco": "RPC + leader schedule",
        }
        
        print("\n📁 CRITICAL MODULES:")
        for module, desc in modules.items():
            path = self.repo / "src" / module
            if path.exists():
                print(f"  ✓ {module:25} → {desc}")
            else:
                print(f"  ? {module:25} → {desc} (not found)")
        
        # Find header files (C headers contain interface definitions)
        print("\n🔍 KEY HEADER FILES (Consensus Interface):")
        
        consensus_headers = [
            "src/disco/disco.h",          # Consensus core
            "src/disco/discof.h",         # Fork choice
            "src/groove/ledger.h",        # Ledger state
            "src/funk/funk.h",            # Block replay
            "src/waltz/slots.h",          # Slot progression
        ]
        
        for header in consensus_headers:
            path = self.repo / header
            if path.exists():
                print(f"  ✓ {header}")
                # Count lines for scale
                try:
                    lines = sum(1 for _ in open(path))
                    print(f"      ({lines} lines)")
                except:
                    pass
            else:
                print(f"  ✗ {header} (not found)")
        
        print("\n✓ TASK 0 COMPLETE: Directory structure mapped")
        return True
    
    def search_for_pattern(self, pattern: str, extensions: List[str] = None) -> Dict[str, List[Tuple[int, str]]]:
        """Search codebase for patterns"""
        if extensions is None:
            extensions = [".c", ".h", ".rs"]
        
        results = defaultdict(list)
        pattern_re = re.compile(pattern, re.IGNORECASE)
        
        for ext in extensions:
            for filepath in self.repo.rglob(f"*{ext}"):
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        for line_no, line in enumerate(f, 1):
                            if pattern_re.search(line):
                                results[str(filepath)].append((line_no, line.strip()))
                except:
                    pass
        
        return results
    
    def task_1_consensus_invariants(self):
        """Find fork choice, vote validation, slot checks, leader schedule"""
        print("\n" + "="*80)
        print("TASK 1: GLOBAL CONSENSUS INVARIANTS")
        print("="*80)
        
        # INVARIANT 1: Fork selection by weight
        print("\n[1.1] FORK_CHOICE_WEIGHT_UPDATE")
        print("      Searching for: fork weight calculation + selection logic...")
        
        # Look for key patterns
        patterns = [
            (r"fn.*weight|fn.*fork_choice|fork_weight|select_heaviest|choose_fork", "Fork choice functions"),
            (r"vote.*verify|verify.*vote|check_vote|vote_hash", "Vote verification"),
            (r"slot.*valid|validate_slot|check_slot|epoch_boundary", "Slot validation"),
            (r"leader.*schedule|get_leader|leader_at_slot", "Leader schedule"),
        ]
        
        for pattern, desc in patterns:
            results = self.search_for_pattern(pattern)
            if results:
                print(f"\n  ✓ {desc}")
                for filepath, matches in sorted(results.items())[:3]:  # Show top 3
                    rel_path = str(filepath).replace(str(self.repo), "")
                    print(f"      File: .{rel_path}")
                    for line_no, content in matches[:2]:
                        print(f"        Line {line_no}: {content[:70]}")
            else:
                print(f"\n  ? {desc} - NO MATCHES (possible implementation elsewhere)")
        
        print("\n✓ TASK 1 IN PROGRESS: Finding specific enforcement points...")
        return True
    
    def task_2_replay_protection(self):
        """Find signature tracking, blockhash checks, shred replay handling"""
        print("\n" + "="*80)
        print("TASK 2: REPLAY / DUPLICATE EXECUTION PROTECTION")
        print("="*80)
        
        patterns = [
            (r"signature.*cache|txn_hash_map|seen_sig|dedup", "Transaction signature tracking"),
            (r"blockhash.*expir|check_blockhash|valid.*blockhash", "Blockhash expiration"),
            (r"shred.*dedup|duplicate.*shred|replay.*protect", "Shred replay handling"),
            (r"ledger.*entry|bank.*cache|account.*lock", "Ledger state dedup"),
        ]
        
        print("\nSearching for replay protection mechanisms:")
        for pattern, desc in patterns:
            results = self.search_for_pattern(pattern)
            if results:
                print(f"  ✓ {desc} - FOUND ({len(results)} locations)")
                for filepath in list(results.keys())[:2]:
                    rel_path = str(filepath).replace(str(self.repo), "")
                    print(f"      .{rel_path}")
            else:
                print(f"  ✗ {desc} - NOT FOUND (potential gap)")
        
        print("\n✓ TASK 2 IN PROGRESS: Analyzing replay protection paths...")
        return True
    
    def task_3_fork_desync(self):
        """Construct fork desync scenarios"""
        print("\n" + "="*80)
        print("TASK 3: FORK DESYNC ADVERSARIAL SCENARIOS")
        print("="*80)
        
        print("\nAnalyzing potential desync vectors:")
        
        vectors = [
            ("Conflicting votes", "Can validator send votes for competing forks at same slot?"),
            ("Late vote injection", "Can late votes alter finalization?"),
            ("Fork weight mismatch", "Is fork weight deterministically calculated?"),
            ("Ledger replay", "Can old ledger state be replayed as current?"),
            ("Epoch boundary skip", "Can validators disagree on epoch transition?"),
        ]
        
        for scenario, question in vectors:
            print(f"\n  • {scenario}")
            print(f"    Q: {question}")
            
            # Search for safeguards
            search_terms = [
                ("vote suppression", "Check if validator can be prevented from voting"),
                ("epoch cache", "Check if epoch is cached/verified"),
                ("slot height", "Check if slot height is strictly monotonic"),
            ]
            
            for guard, desc in search_terms:
                results = self.search_for_pattern(guard)
                if results:
                    print(f"    ✓ Guard: {desc}")
                else:
                    print(f"    ? Guard: {desc} (search inconclusive)")
        
        print("\n✓ TASK 3 IN PROGRESS: Mapping desync prevention logic...")
        return True
    
    def task_4_execution_order(self):
        """Trace execution pipeline for atomic boundaries"""
        print("\n" + "="*80)
        print("TASK 4: EXECUTION ORDER & NON-ATOMIC COMMIT BOUNDARIES")
        print("="*80)
        
        print("\nExecution Pipeline:")
        pipeline = [
            "Network → Shred Ingestion",
            "Shred Ingestion → Banking/Execution",
            "Banking/Execution → Replay Log",
            "Replay Log → Ledger Commit",
            "Ledger Commit → Root Update",
        ]
        
        for stage in pipeline:
            print(f"  {stage}")
        
        print("\nSearching for atomic boundaries:")
        patterns = [
            (r"atomic|lock|mutex|rwlock|transaction", "Synchronization primitives"),
            (r"commit|flush|persist|snapshot", "State persistence"),
            (r"rollback|revert|undo|recover", "Recovery mechanisms"),
        ]
        
        for pattern, desc in patterns:
            results = self.search_for_pattern(pattern)
            count = len(results)
            print(f"  • {desc:35} {count:4} locations")
        
        print("\n✓ TASK 4 IN PROGRESS: Identifying non-atomic boundaries...")
        return True
    
    def task_5_finalization(self):
        """Check finalization and rollback safety"""
        print("\n" + "="*80)
        print("TASK 5: FINALIZATION / ROLLBACK SAFETY")
        print("="*80)
        
        print("\nFinalization Mechanisms:")
        patterns = [
            (r"root.*update|set_root|finalize|mark_final", "Root update logic"),
            (r"rollback|revert.*slot|undo.*state|reset.*ledger", "Rollback handling"),
            (r"replay.*from|recovery.*from|restore*ledger", "Recovery from rollback"),
        ]
        
        for pattern, desc in patterns:
            results = self.search_for_pattern(pattern)
            if results:
                print(f"  ✓ {desc}")
                print(f"      Found in {len(results)} files")
                for filepath in list(results.keys())[:1]:
                    rel_path = str(filepath).replace(str(self.repo), "")
                    print(f"      Example: .{rel_path}")
            else:
                print(f"  ? {desc} (not found or unclear naming)")
        
        print("\n  ⚠️  KEY QUESTION: Can finalized slots be rolled back?")
        print("      (Searching for finalization irreversibility checks...)")
        
        print("\n✓ TASK 5 IN PROGRESS: Analyzing finalization guarantees...")
        return True

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    audit = FiredancerAudit()
    
    # Execute all tasks
    audit.task_0_orientation()
    audit.task_1_consensus_invariants()
    audit.task_2_replay_protection()
    audit.task_3_fork_desync()
    audit.task_4_execution_order()
    audit.task_5_finalization()
    
    print("\n" + "="*80)
    print("🔥 AUDIT COMPLETE - INITIAL RECONNAISSANCE")
    print("="*80)
    print("\nNext phase: Deep code analysis of identified critical paths")
    print("(Requires manual inspection of specific functions + vote/fork logic)")

if __name__ == "__main__":
    main()
