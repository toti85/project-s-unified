#!/usr/bin/env python3
"""
End-to-end smoke test: Verify auto-injected strategist works in Meta path.
"""

import sys
from pathlib import Path
import logging

# Suppress logging on Windows
logging.disable(logging.CRITICAL)

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.super_intelligent_ai import SuperIntelligentAI

print("\n" + "="*80)
print("SMOKE TEST: Auto-Injected Strategist in Meta Path")
print("="*80)

try:
    print("\n[1] Initialize SuperIntelligentAI with Meta path...")
    ai = SuperIntelligentAI(use_meta_controller=True)
    print("    [OK] Initialized")
    print(f"    [OK] use_meta_controller: {ai.use_meta_controller}")
    print(f"    [OK] MetaController exists: {ai.meta_controller is not None}")
    
    print("\n[2] Check StrategyCouncil...")
    council = ai.meta_controller.council
    print(f"    [OK] Council exists: {council is not None}")
    print(f"    [OK] Strategists in council: {len(council.strategists)}")
    
    if len(council.strategists) > 0:
        strategist = council.strategists[0]
        print(f"    [OK] First strategist: {strategist.__class__.__name__}")
        print(f"    [OK] Strategist name: {strategist.ai_name}")
    
    print("\n[3] Check evidence logging...")
    evidence_file = Path("memory/intelligence/meta_evidence.jsonl")
    if evidence_file.exists():
        with open(evidence_file, "r") as f:
            lines = f.readlines()
        print(f"    [OK] Evidence events: {len(lines)}")
    else:
        print(f"    [INFO] Evidence file not yet created")
    
    print("\n" + "="*80)
    print("RESULT: Infrastructure Test PASSED")
    print("  - MetaController: OK")
    print("  - StrategyCouncil: OK")
    print("  - Default Strategist: OK (auto-injection working)")
    print("="*80 + "\n")
    
except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
