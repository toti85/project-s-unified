#!/usr/bin/env python
"""
B2 Mission Rerun — GAP_019 Synthesis Test
Runs the B2 local model research task through the live pipeline and
saves the synthesised report to a NEW path so the original is preserved.
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent))

B2_TASK = (
    "Search the web for information about Qwen3.6-35B-A3B (a May 2026 MoE model with 35B params / 3B active) "
    "and other currently available 2026 local models including Gemma 4-31B, Llama 4 Scout, Mistral Small 3.1. "
    "Compare their coding and agentic task performance, VRAM requirements, and feasibility on a Tesla M60 16GB server. "
    "Search and find the SWE-bench scores and token throughput for each model. "
    "Write a comprehensive markdown decision memo to the file "
    r"C:\ProjectS-Unified\reports\B2_LOCAL_MODEL_SYNTHESIS_20260514.md"
    " that contains: "
    "1) candidate models list with Qwen3.6-35B-A3B included, "
    "2) comparison table of coding/agentic usefulness, deployability, hardware fit and integration risk, "
    "3) distinction of confirmed facts vs assumptions, "
    "4) sources used, "
    "5) concrete recommendation: integrate now OR test later OR defer and stay cloud-first for Project-S on OpenRouter."
)

OUTPUT_PATH = r"C:\ProjectS-Unified\reports\B2_LOCAL_MODEL_SYNTHESIS_20260514.md"
VERDICT_START = datetime.now()

async def run_b2_mission():
    print("=" * 80)
    print("B2 MISSION RERUN — GAP_019 SYNTHESIS TEST")
    print(f"Start: {VERDICT_START.isoformat()}")
    print("=" * 80)

    from src.core.super_intelligent_ai import SuperIntelligentAI
    ai = SuperIntelligentAI(use_meta_controller=True)
    print("[OK] SAI initialised (meta_controller=True)")

    print("\n[RUNNING TASK...]\n")
    result = await ai.execute_intelligent_task(task=B2_TASK)

    elapsed = (datetime.now() - VERDICT_START).total_seconds()
    print(f"\n[DONE] Elapsed: {elapsed:.1f}s")
    print("\n--- RAW RESULT ---")
    if isinstance(result, dict):
        print(f"success: {result.get('success')}")
        print(f"output (first 500 chars): {str(result.get('output',''))[:500]}")
    else:
        print(str(result)[:500])

    # Check output file
    out = Path(OUTPUT_PATH)
    if out.exists():
        size = out.stat().st_size
        content = out.read_text(encoding="utf-8", errors="replace")
        print(f"\n[OUTPUT FILE] {OUTPUT_PATH}")
        print(f"  Size: {size} bytes")
        # Check required sections
        checks = {
            "candidate models / overview": any(k in content.lower() for k in ["qwen", "gemma", "llama", "mistral"]),
            "comparison table":            "| " in content and "---" in content,
            "confirmed facts":             "confirmed" in content.lower() or "fact" in content.lower(),
            "assumptions":                 "assumption" in content.lower() or "inferred" in content.lower() or "gap" in content.lower(),
            "sources section":             "source" in content.lower() or "http" in content.lower(),
            "recommendation":              "recommend" in content.lower(),
            "NOT a raw dump":              "[web_search result]" not in content and "[web_scraper result]" not in content,
        }
        print("\n  Section checks:")
        passed = 0
        for check, ok in checks.items():
            status = "PASS" if ok else "FAIL"
            if ok:
                passed += 1
            print(f"    [{status}] {check}")

        print(f"\n  Score: {passed}/{len(checks)}")
        return result, content, checks, elapsed
    else:
        print(f"\n[WARN] Output file NOT found: {OUTPUT_PATH}")
        return result, None, {}, elapsed


if __name__ == "__main__":
    asyncio.run(run_b2_mission())
