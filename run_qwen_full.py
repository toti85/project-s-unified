#!/usr/bin/env python
"""
PROJECT_S_30_DAY_OPPORTUNITY_SCAN — Qwen3.6-35B-A3B Full Run
Re-runs only Run B with max_tokens=8000 to complete the previously truncated report.
Writes:
  - C:\ProjectS-Unified\reports\PROJECT_S_30_DAY_OPPORTUNITY_SCAN_QWEN36_FULL_20260514.md
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

REPORTS_DIR = Path(r"C:\ProjectS-Unified\reports")
OUTPUT_PATH = REPORTS_DIR / "PROJECT_S_30_DAY_OPPORTUNITY_SCAN_QWEN36_FULL_20260514.md"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

MODEL = "qwen/qwen3.6-35b-a3b"

SECTION_CHECKS = {
    "Executive Summary":         lambda c: "executive summary" in c.lower(),
    "Capability Fit":            lambda c: "capability" in c.lower() and "project" in c.lower(),
    "Opportunity Landscape":     lambda c: "opportunity" in c.lower() and "2026" in c,
    "Candidate Directions (>=6)": lambda c: c.lower().count("direction") >= 3 or c.count("##") >= 6,
    "Comparison Table":          lambda c: "| " in c and "---" in c and "feasibility" in c.lower(),
    "Top 3 Recommendations":     lambda c: "top 3" in c.lower() or "recommended direction" in c.lower(),
    "30-Day Action Plan":        lambda c: "action plan" in c.lower() or "30-day" in c.lower(),
    "What NOT To Do":            lambda c: "not to do" in c.lower() or "avoid" in c.lower(),
    "Confirmed Facts":           lambda c: "confirmed" in c.lower() and "fact" in c.lower(),
    "Sources":                   lambda c: "source" in c.lower() or "http" in c,
    "No bounty content":         lambda c: "bounty" not in c.lower() and "exploit" not in c.lower(),
    "NOT a raw dump":            lambda c: "[web_search result]" not in c and "[web_scraper result]" not in c,
}


def make_task(output_path: Path) -> str:
    return (
        "Search the web for current 2026 developments and opportunities in each of the "
        "following areas: local AI agents, AI workflow automation, personal AI operating systems, "
        "AI research assistants, autonomous coding agents, small-team AI operations, "
        "local LLM deployment, AI browser automation, AI decision support systems, "
        "AI tools for teachers and education automation, AI infrastructure for one-person businesses, "
        "and agentic workflows with audit trails. "
        "Search for real 2026 market developments, tools, platforms, and use cases. "
        "Then write a comprehensive strategic decision memo to the file "
        f"{output_path} "
        "that answers: 'What is the highest-leverage non-security application for Project-S over "
        "the next 30 days, given its current capabilities: persistent self_state, Witness evidence "
        "trail, multi-tool orchestration, web search + scrape + synthesis, local/server ambitions, "
        "and multi-AI coordination?' "
        "The memo must include ALL of the following sections exactly as listed: "
        "1) Executive Summary, "
        "2) Project-S Current Capability Fit, "
        "3) External Opportunity Landscape 2026, "
        "4) Candidate Directions with at least 6 options each including a practical use case and rationale, "
        "5) Comparison Table with columns: Direction, 30-day feasibility, monetization potential, "
        "fit with Project-S, required missing capability, risk of scope creep, recommended priority, "
        "6) Top 3 Recommended Directions with detailed reasoning, "
        "7) 30-Day Action Plan with concrete daily/weekly milestones, "
        "8) What NOT To Do (explicitly exclude bounty hunting, security scanning, and offensive security ideas), "
        "9) Confirmed Facts vs Assumptions (clearly separate what is evidence-backed from what is inferred), "
        "10) Sources (list every URL used). "
        "Do NOT include bug bounty, exploit development, vulnerability hunting, penetration testing, "
        "offensive cyber, or any security scanner ideas anywhere in the memo."
    )


def check_sections(content: str) -> dict:
    return {name: fn(content) for name, fn in SECTION_CHECKS.items()}


def score(checks: dict) -> int:
    return sum(1 for v in checks.values() if v)


async def main():
    print("=" * 80)
    print(f"  QWEN FULL RUN — {MODEL}")
    print(f"  max_tokens: 8000  (was 6000)")
    print(f"  output: {OUTPUT_PATH}")
    print(f"  {datetime.now().isoformat()}")
    print("=" * 80)

    from tools.tools.registry.smart_orchestrator import SmartToolOrchestrator
    SmartToolOrchestrator._synthesis_model_override = MODEL

    from src.core.super_intelligent_ai import SuperIntelligentAI
    ai = SuperIntelligentAI(use_meta_controller=True)

    task = make_task(OUTPUT_PATH)
    start = datetime.now()
    print(f"\n[START] {start.isoformat()}")
    print(f"[MODEL] {MODEL}")
    print("[RUNNING PIPELINE...]\n")

    try:
        result = await ai.execute_intelligent_task(task=task)
    except Exception as exc:
        print(f"[ERROR] Task raised: {exc}")
        result = {"success": False, "partial": False, "output": str(exc)}
    finally:
        SmartToolOrchestrator._synthesis_model_override = None

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\n[DONE] Elapsed: {elapsed:.1f}s")

    # ── Extract result fields ──────────────────────────────────────────────────
    if isinstance(result, dict):
        success_flag  = result.get("success", False)
        partial_flag  = result.get("partial", False)
        raw_output    = result.get("output") or result.get("result") or ""
    else:
        success_flag  = False
        partial_flag  = False
        raw_output    = str(result) if result else ""

    print(f"\n[RESULT FLAGS]")
    print(f"  success = {success_flag}")
    print(f"  partial = {partial_flag}")
    print(f"  raw_output len = {len(raw_output)}")

    # Get execution history to extract real evaluator action
    history = getattr(ai, 'execution_history', [])
    eval_action = None
    if history:
        last = history[-1]
        print(f"\n[EXECUTION HISTORY last entry]")
        print(f"  history.success = {last.get('success')}")
        eval_data = last.get("evaluation") or {}
        recs = eval_data.get("recommendations") or {}
        eval_action = recs.get("action") or eval_data.get("action")
        print(f"  evaluator action = {eval_action}")
        print(f"  evaluator goal_achieved = {eval_data.get('goal_achieved')}")

    # ── Check output file ──────────────────────────────────────────────────────
    if OUTPUT_PATH.exists():
        content = OUTPUT_PATH.read_text(encoding="utf-8", errors="replace")
        size = OUTPUT_PATH.stat().st_size
        checks = check_sections(content)
        s = score(checks)
        truncated = content.endswith("...") or len(content) < 3000
        print(f"\n[OUTPUT FILE] {OUTPUT_PATH.name}")
        print(f"  Size:          {size} bytes  ({len(content)} chars)")
        print(f"  Section score: {s}/{len(checks)}")
        print(f"  Truncated?     {'YES — < 3000 chars or ends with ...' if truncated else 'No'}")
        print()
        for name, ok in checks.items():
            marker = "PASS" if ok else "FAIL"
            print(f"    [{marker}] {name}")
    else:
        content = ""
        size = 0
        checks = {k: False for k in SECTION_CHECKS}
        s = 0
        truncated = True
        print(f"\n[WARN] Output file NOT found: {OUTPUT_PATH}")

    # ── Print machine-readable summary ────────────────────────────────────────
    print()
    print("=" * 80)
    print("SUMMARY")
    print(f"  model          = {MODEL}")
    print(f"  max_tokens     = 8000")
    print(f"  success        = {success_flag}")
    print(f"  partial        = {partial_flag}")
    print(f"  eval_action    = {eval_action}")
    print(f"  size_bytes     = {size}")
    print(f"  section_score  = {s}/{len(checks)}")
    print(f"  truncated      = {truncated}")
    print(f"  elapsed_s      = {elapsed:.1f}")
    print("=" * 80)

    return {
        "model": MODEL,
        "success": success_flag,
        "partial": partial_flag,
        "eval_action": eval_action,
        "size_bytes": size,
        "section_score": s,
        "max_score": len(checks),
        "truncated": truncated,
        "elapsed_s": elapsed,
        "checks": checks,
    }


if __name__ == "__main__":
    asyncio.run(main())
