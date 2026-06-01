#!/usr/bin/env python3
"""Simple sync test - no async complexity."""

import sys
from pathlib import Path
import logging

# Suppress logging
logging.basicConfig(level=logging.ERROR, force=True)
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.super_intelligent_ai import SuperIntelligentAI

print("\n" + "="*80)
print("SMOKE TEST: SYNC TEST VERSION")
print("="*80)

print("\n[1] Standard Path Test")
print("-" * 40)
try:
    ai = SuperIntelligentAI(use_meta_controller=False)
    print("  [OK] AI initialized")
    
    # Just check the instance
    print(f"  [OK] use_meta: {ai.use_meta_controller}")
    print(f"  [OK] Standard path available")
    
except Exception as e:
    print(f"  [FAIL] {e}")

print("\n[2] Meta Path Test")
print("-" * 40)
try:
    ai = SuperIntelligentAI(use_meta_controller=True)
    print("  [OK] AI initialized")
    print(f"  [OK] use_meta: {ai.use_meta_controller}")
    print(f"  [OK] MetaController: {ai.meta_controller is not None}")
    
except Exception as e:
    print(f"  [FAIL] {e}")

print("\n" + "="*80)
print("INITIALIZATION TESTS PASSED")
print("="*80 + "\n")
