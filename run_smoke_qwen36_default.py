"""
Smoke launcher: verify Qwen3.6 is now the runtime synthesis default.
Does NOT set _synthesis_model_override — relying on the new code default.
"""
import asyncio
import sys
import json
import logging
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from tools.tools.registry.smart_orchestrator import SmartToolOrchestrator
from src.core.super_intelligent_ai import SuperIntelligentAI

# Confirm override is clear
assert SmartToolOrchestrator._synthesis_model_override is None, \
    "Override must be None for this smoke test to be meaningful"

OUTPUT_FILE = r"C:\ProjectS-Unified\reports\QWEN_DEFAULT_SYNTHESIS_SMOKE_20260514.md"

TASK = (
    "Search the web for 2026 developments in local AI workflow orchestration. "
    "Write a concise strategic memo to "
    f"{OUTPUT_FILE} "
    "with the following sections: "
    "## Executive Summary, ## Key Findings (3 bullet points), "
    "## Recommendation, ## Sources."
)

SECTION_CHECKS = {
    "Executive Summary section": lambda c: "## executive summary" in c.lower(),
    "Key Findings section":      lambda c: "## key findings" in c.lower(),
    "Recommendation section":    lambda c: "## recommendation" in c.lower(),
    "Sources section":           lambda c: "## sources" in c.lower(),
    "Non-empty content":         lambda c: len(c.strip()) > 300,
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("smoke_qwen36")


async def run():
    t0 = time.time()
    ai = SuperIntelligentAI(use_meta_controller=True)
    result = await ai.execute_intelligent_task(task=TASK)
    elapsed = round(time.time() - t0, 1)

    success = result.get("success", False)
    has_output = bool(result.get("output") or result.get("result"))
    log.info("SAI result success=%s has_output=%s elapsed=%ss", success, has_output, elapsed)

    # Check output file
    out_path = Path(OUTPUT_FILE)

    file_ok = out_path.exists()
    file_size = out_path.stat().st_size if file_ok else 0
    file_content = out_path.read_text(encoding="utf-8") if file_ok else ""

    section_results = {}
    for name, check in SECTION_CHECKS.items():
        try:
            section_results[name] = check(file_content)
        except Exception:
            section_results[name] = False

    pass_count = sum(section_results.values())
    total_checks = len(SECTION_CHECKS)
    verdict = "PASS" if pass_count == total_checks and file_ok and success else "PARTIAL"

    print("\n" + "="*60)
    print(f"SMOKE TEST: Qwen3.6 as Default Synthesis")
    print("="*60)
    print(f"SAI success:   {success}")
    print(f"Elapsed:       {elapsed}s")
    print(f"Output file:   {out_path} ({'EXISTS' if file_ok else 'MISSING'})")
    print(f"File size:     {file_size} bytes")
    print(f"Section score: {pass_count}/{total_checks}")
    for name, ok in section_results.items():
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    print(f"\nFINAL VERDICT: {verdict}")
    print("="*60)

    # Save run summary
    summary = {
        "task": TASK[:120],
        "output_file": str(out_path),
        "success": success,
        "elapsed_s": elapsed,
        "file_exists": file_ok,
        "file_size_bytes": file_size,
        "section_score": f"{pass_count}/{total_checks}",
        "section_results": section_results,
        "synthesis_model_override": SmartToolOrchestrator._synthesis_model_override,
        "expected_synthesis_model": "qwen/qwen3.6-35b-a3b",
        "verdict": verdict,
    }
    log_path = Path("smoke_qwen36_run.json")
    log_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Run summary saved: {log_path}")

    return verdict == "PASS"


if __name__ == "__main__":
    ok = asyncio.run(run())
    sys.exit(0 if ok else 1)
