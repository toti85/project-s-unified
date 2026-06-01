#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sai_valid2_run.py
==================
SAI output-fix live re-validation script.
Checks that the fixed pipeline returns real file content, not generic wrapper.
"""

import sys
import asyncio
from pathlib import Path

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

root = Path(__file__).parent
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / "src"))

from core.super_intelligent_ai import SuperIntelligentAI

TASK = "List all Python files in C:\\ProjectS-Unified\\witness recursively and return exact relative paths."

GROUND_TRUTH = [
    "witness\\evidence_diagnostic.py",
    "witness\\evidence_reader.py",
    "witness\\learning_diagnostic.py",
    "witness\\__init__.py",
    "witness\\bridges\\organism_to_meta.py",
    "witness\\bridges\\state_reader.py",
    "witness\\bridges\\__init__.py",
]

async def run():
    print("="*70)
    print("SAI LIVE OUTPUT VALIDATION v2 (post-fix)")
    print("="*70)

    ai = SuperIntelligentAI(use_meta_controller=True)

    print(f"\nTASK: {TASK}\n")
    result = await ai.execute_intelligent_task(task=TASK, use_meta_controller=True)

    print("\n--- RESULT ---")
    print(f"success  : {result.get('success')}")
    output = result.get("output", "")
    print(f"output   :\n{output}")
    print("-" * 70)

    # Validate against ground truth
    matched = [f for f in GROUND_TRUTH if f.replace("\\", "/") in output.replace("\\", "/") or f in output]
    match_count = len(matched)
    total = len(GROUND_TRUTH)

    print(f"\nGROUND TRUTH MATCH: {match_count}/{total}")
    for f in GROUND_TRUTH:
        found = f.replace("\\", "/") in output.replace("\\", "/") or f in output
        mark = "[FOUND]" if found else "[MISSING]"
        print(f"  {mark}  {f}")

    # Check for generic wrapper regression
    generic_only = "[OK] MetaController completed" in output and match_count == 0
    print()
    if match_count == total:
        print("VERDICT: PASS — all 7 files found in output")
        status = "PASS"
    elif match_count > 0:
        print(f"VERDICT: PARTIAL — {match_count}/{total} files found")
        status = "PARTIAL"
    elif generic_only:
        print("VERDICT: FAIL — generic wrapper returned, output propagation still broken")
        status = "FAIL"
    else:
        print("VERDICT: FAIL — no ground truth files in output")
        status = "FAIL"

    print("="*70)
    sys.exit(0 if status == "PASS" else 1)


if __name__ == "__main__":
    asyncio.run(run())
