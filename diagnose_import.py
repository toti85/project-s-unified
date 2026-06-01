#!/usr/bin/env python3
"""Diagnose import issues."""

import sys
from pathlib import Path

print("[1] Adding paths...")
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))
print("  OK")

print("[2] Setting up logging...")
import logging
logging.basicConfig(level=logging.ERROR, force=True)
print("  OK")

print("[3] Importing SuperIntelligentAI...")
try:
    from src.core.super_intelligent_ai import SuperIntelligentAI
    print("  OK - Import successful")
except Exception as e:
    print(f"  FAIL - {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("[4] Creating instance (standard path)...")
try:
    ai = SuperIntelligentAI(use_meta_controller=False)
    print("  OK - Instance created")
except Exception as e:
    print(f"  FAIL - {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("[5] All checks passed!")
