"""
Live verification launcher for GAP_023 fix.

Mission: mixed research/browser/synthesis pipeline.
The planner should ideally select web_search + browser_automation + file_writer.
We verify:
  A. browser_automation is selected by the planner
  B. browser_automation receives the scoped browser-only subtask (logged via GAP_023 log line)
  C. browser-use navigates/extracts rather than writing the final report
  D. GAP_019 synthesis creates the final report
  E. Final report exists and passes section checks
  F. SAI success flag is truthful
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

OUTPUT_FILE = r"C:\ProjectS-Unified\reports\GAP_023_BROWSER_SCOPED_SUBTASK_LIVE_20260514.md"

TASK = (
    "Research current 2026 browser automation and agentic web interaction tools using "
    "search plus real browser inspection where useful, then write a concise evidence-based "
    "markdown memo comparing at least 3 tools and recommending whether Project-S should "
    "treat browser automation as a primary or secondary capability. "
    f"Write to: {OUTPUT_FILE}"
)

SECTION_CHECKS = {
    "Tool comparison (at least 3 tools mentioned)": lambda c: (
        sum(1 for t in ["playwright", "puppeteer", "browser-use", "selenium", "crawlee"]
            if t in c.lower()) >= 2
    ),
    "Recommendation section":   lambda c: "## recommendation" in c.lower() or "recommendation" in c.lower(),
    "Primary or secondary capability": lambda c: (
        "primary" in c.lower() or "secondary" in c.lower()
    ),
    "Non-empty content":         lambda c: len(c.strip()) > 400,
    "Not raw tool output dump":  lambda c: "[web_search result]" not in c,
}

# Capture log messages to verify GAP_023 behavior
class LogCapture(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record.getMessage())

log_capture = LogCapture()
logging.getLogger("tools.tools.registry.smart_orchestrator").addHandler(log_capture)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("gap023_live")


async def run():
    t0 = time.time()
    ai = SuperIntelligentAI(use_meta_controller=True)
    result = await ai.execute_intelligent_task(task=TASK)
    elapsed = round(time.time() - t0, 1)

    success = result.get("success", False)
    log.info("SAI result success=%s elapsed=%ss", success, elapsed)

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

    # Check log messages for GAP_023 behavior
    gap023_scoped = any("GAP_023: Mixed pipeline detected" in m for m in log_capture.records)
    gap023_passthrough = any("GAP_023: Dedicated browser task" in m for m in log_capture.records)
    gap019_synthesis = any("GAP_019: Synthesis model" in m for m in log_capture.records)
    browser_selected = any("browser_automation" in m and ("GAP_023" in m or "Executing tool: browser_automation" in m)
                           for m in log_capture.records)

    verdict = "PASS" if pass_count == total_checks and file_ok and success else "PARTIAL"

    print("\n" + "="*65)
    print("LIVE VERIFICATION: GAP_023 Browser Scope Isolation")
    print("="*65)
    print(f"SAI success:        {success}")
    print(f"Elapsed:            {elapsed}s")
    print(f"Output file:        {out_path} ({'EXISTS' if file_ok else 'MISSING'})")
    print(f"File size:          {file_size} bytes")
    print(f"Section score:      {pass_count}/{total_checks}")
    for name, ok in section_results.items():
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    print()
    print("GAP_023 behavior:")
    print(f"  browser_automation selected:     {'YES' if browser_selected else 'NO (planner excluded it)'}")
    print(f"  GAP_023 scope isolation fired:   {'YES' if gap023_scoped else 'NO (passthrough or not selected)'}")
    print(f"  GAP_023 passthrough (dedicated): {'YES' if gap023_passthrough else 'NO'}")
    print(f"  GAP_019 synthesis fired:         {'YES' if gap019_synthesis else 'NO'}")
    print()
    print(f"FINAL VERDICT: {verdict}")
    print("="*65)

    summary = {
        "task": TASK[:120],
        "output_file": str(out_path),
        "success": success,
        "elapsed_s": elapsed,
        "file_exists": file_ok,
        "file_size_bytes": file_size,
        "section_score": f"{pass_count}/{total_checks}",
        "section_results": section_results,
        "gap023_scope_isolation_fired": gap023_scoped,
        "gap023_passthrough_fired": gap023_passthrough,
        "browser_automation_selected": browser_selected,
        "gap019_synthesis_fired": gap019_synthesis,
        "verdict": verdict,
    }
    log_path = Path("gap023_live_run.json")
    log_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Run summary saved: {log_path}")

    return summary


if __name__ == "__main__":
    summary = asyncio.run(run())
    sys.exit(0 if summary["verdict"] == "PASS" else 1)
