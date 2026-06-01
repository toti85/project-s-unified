#!/usr/bin/env python
"""
PROJECT_S_30_DAY_OPPORTUNITY_SCAN — A/B Model Comparison Run
Executes the strategic opportunity scan mission twice:
  Run A: default synthesis model (openai/gpt-4o-mini via OpenRouter)
  Run B: qwen/qwen3.6-35b-a3b via OpenRouter
Then writes a model comparison verdict.
"""

import asyncio
import sys
import os
import json
from pathlib import Path
from datetime import datetime

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent))

# ── Output paths ──────────────────────────────────────────────────────────────
REPORTS_DIR = Path(r"C:\ProjectS-Unified\reports")
OUT_DEFAULT = REPORTS_DIR / "PROJECT_S_30_DAY_OPPORTUNITY_SCAN_DEFAULT_20260514.md"
OUT_QWEN    = REPORTS_DIR / "PROJECT_S_30_DAY_OPPORTUNITY_SCAN_QWEN36_20260514.md"
OUT_COMPARE = REPORTS_DIR / "PROJECT_S_30_DAY_OPPORTUNITY_SCAN_MODEL_COMPARISON_20260514.md"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ── Task definition ────────────────────────────────────────────────────────────
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


# ── Section checks ─────────────────────────────────────────────────────────────
SECTION_CHECKS = {
    "Executive Summary":        lambda c: "executive summary" in c.lower(),
    "Capability Fit":           lambda c: "capability" in c.lower() and "project" in c.lower(),
    "Opportunity Landscape":    lambda c: "opportunity" in c.lower() and "2026" in c,
    "Candidate Directions (≥6)":lambda c: c.lower().count("direction") >= 3 or c.count("##") >= 6,
    "Comparison Table":         lambda c: "| " in c and "---" in c and "feasibility" in c.lower(),
    "Top 3 Recommendations":    lambda c: "top 3" in c.lower() or "recommended directions" in c.lower(),
    "30-Day Action Plan":       lambda c: "action plan" in c.lower() or "30-day" in c.lower(),
    "What NOT To Do":           lambda c: "not to do" in c.lower() or "avoid" in c.lower(),
    "Confirmed Facts":          lambda c: "confirmed" in c.lower() and "fact" in c.lower(),
    "Sources":                  lambda c: "source" in c.lower() or "http" in c,
    "No bounty content":        lambda c: "bounty" not in c.lower() and "exploit" not in c.lower(),
    "NOT a raw dump":           lambda c: "[web_search result]" not in c and "[web_scraper result]" not in c,
}


def check_sections(content: str) -> dict:
    return {name: fn(content) for name, fn in SECTION_CHECKS.items()}


def score(checks: dict) -> int:
    return sum(1 for v in checks.values() if v)


# ── Single mission runner ──────────────────────────────────────────────────────
async def run_mission(label: str, output_path: Path, model_override=None) -> dict:
    from tools.tools.registry.smart_orchestrator import SmartToolOrchestrator

    # Apply model override before creating SAI (class-level attribute)
    SmartToolOrchestrator._synthesis_model_override = model_override
    model_label = model_override or "openai/gpt-4o-mini (default)"

    print()
    print("=" * 80)
    print(f"  RUN {label}  —  model: {model_label}")
    print(f"  output: {output_path}")
    print("=" * 80)

    from src.core.super_intelligent_ai import SuperIntelligentAI
    ai = SuperIntelligentAI(use_meta_controller=True)

    task = make_task(output_path)
    start = datetime.now()
    print(f"\n[START] {start.isoformat()}")
    print("[RUNNING PIPELINE...]\n")

    try:
        result = await ai.execute_intelligent_task(task=task)
    except Exception as exc:
        print(f"[ERROR] Task raised: {exc}")
        result = {"success": False, "output": str(exc)}
    finally:
        # Always reset override after run
        SmartToolOrchestrator._synthesis_model_override = None

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\n[DONE] Elapsed: {elapsed:.1f}s")

    success_flag = result.get("success") if isinstance(result, dict) else False
    print(f"success flag: {success_flag}")

    # Evaluate output
    if output_path.exists():
        content = output_path.read_text(encoding="utf-8", errors="replace")
        size = output_path.stat().st_size
        checks = check_sections(content)
        s = score(checks)
        print(f"\n[OUTPUT] {output_path.name}  ({size} bytes)")
        print(f"  Section score: {s}/{len(checks)}")
        for name, ok in checks.items():
            print(f"    [{'PASS' if ok else 'FAIL'}] {name}")
    else:
        content = ""
        size = 0
        checks = {k: False for k in SECTION_CHECKS}
        s = 0
        print(f"\n[WARN] Output file not found: {output_path}")

    return {
        "label":      label,
        "model":      model_label,
        "output":     str(output_path),
        "elapsed_s":  elapsed,
        "success":    success_flag,
        "size_bytes": size,
        "score":      s,
        "max_score":  len(SECTION_CHECKS),
        "checks":     checks,
        "content":    content,
    }


# ── Comparison verdict writer ──────────────────────────────────────────────────
def write_comparison(run_a: dict, run_b: dict):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    def check_table_row(name):
        a = "✅" if run_a["checks"].get(name) else "❌"
        b = "✅" if run_b["checks"].get(name) else "❌"
        return f"| {name} | {a} | {b} |"

    rows = "\n".join(check_table_row(k) for k in SECTION_CHECKS)

    winner_score = "A" if run_a["score"] >= run_b["score"] else "B"
    a_score = run_a["score"]
    b_score = run_b["score"]

    # Qualitative scoring (heuristic, based on section passes)
    def qual_score(r):
        c = r["checks"]
        return {
            "tool_selection":     "✅ Good" if r["success"] else "❌ Pipeline failed",
            "search_quality":     "✅ Web data present" if c.get("NOT a raw dump") and r["size_bytes"] > 1000 else "❌ Possibly empty",
            "synthesis_quality":  f"{r['score']}/{r['max_score']} sections",
            "concreteness":       "✅ Specific" if c.get("30-Day Action Plan") and c.get("Top 3 Recommendations") else "❌ Vague",
            "hallucination_risk": "Low" if c.get("Confirmed Facts") and c.get("NOT a raw dump") else "Medium",
            "usefulness":         "✅ Actionable" if c.get("30-Day Action Plan") else "❌ Not actionable",
            "elapsed":            f"{r['elapsed_s']:.0f}s",
        }

    qa = qual_score(run_a)
    qb = qual_score(run_b)

    def qual_table():
        lines = ["| Metric | Run A (Default) | Run B (Qwen3.6-35B-A3B) |",
                 "|--------|-----------------|-------------------------|"]
        for k in qa:
            lines.append(f"| {k} | {qa[k]} | {qb[k]} |")
        return "\n".join(lines)

    verdict_text = f"""# MODEL COMPARISON VERDICT
## PROJECT_S_30_DAY_OPPORTUNITY_SCAN
**Generated**: {now}

---

## Run Summary

| Attribute | Run A — Default (`gpt-4o-mini`) | Run B — `qwen/qwen3.6-35b-a3b` |
|-----------|--------------------------------|--------------------------------|
| Model | {run_a['model']} | {run_b['model']} |
| Elapsed | {run_a['elapsed_s']:.0f}s | {run_b['elapsed_s']:.0f}s |
| Pipeline success | {'✅' if run_a['success'] else '❌'} | {'✅' if run_b['success'] else '❌'} |
| Output size | {run_a['size_bytes']} bytes | {run_b['size_bytes']} bytes |
| Section score | {run_a['score']}/{run_a['max_score']} | {run_b['score']}/{run_b['max_score']} |
| Output file | `{Path(run_a['output']).name}` | `{Path(run_b['output']).name}` |

---

## Section Check Comparison

| Section | Run A | Run B |
|---------|-------|-------|
{rows}

---

## Qualitative Score

{qual_table()}

---

## Verdict

**Winner: Run {winner_score}** — scored {run_a['score'] if winner_score=='A' else run_b['score']}/{run_a['max_score']} vs {run_b['score'] if winner_score=='A' else run_a['score']}/{run_a['max_score']}

### Run A (`gpt-4o-mini`)
- Sections passing: {a_score}/{run_a['max_score']}
- File: `{Path(run_a['output']).name}`
- Elapsed: {run_a['elapsed_s']:.0f}s

### Run B (`qwen/qwen3.6-35b-a3b`)
- Sections passing: {b_score}/{run_b['max_score']}
- File: `{Path(run_b['output']).name}`
- Elapsed: {run_b['elapsed_s']:.0f}s
- Note: Success depends on OpenRouter availability for this model.

---

## Recommended Next Action for Project-S

Based on the run results above, the recommended synthesis model for production use is:
**{"Run A default (gpt-4o-mini)" if winner_score=='A' else "Run B (qwen/qwen3.6-35b-a3b)"}**

If Run B produced a higher-quality report, consider setting `SmartToolOrchestrator._synthesis_model_override = "qwen/qwen3.6-35b-a3b"` as a persistent default in `smart_orchestrator.py`.

If Run A tied or won, keep the current default — `openai/gpt-4o-mini` is faster, cheaper, and proven on B2.

Next steps regardless of winner:
1. Read the higher-scoring report and pick one candidate direction.
2. Build a minimal prototype for that direction over the next 7 days.
3. Use Project-S itself (web_search → synthesis → file_writer) for any follow-up research needed.

---
*Generated by run_opportunity_scan.py | Project-S GAP_019 synthesis pipeline*
"""

    OUT_COMPARE.write_text(verdict_text, encoding="utf-8")
    print(f"\n[COMPARISON VERDICT] Written to {OUT_COMPARE}")
    return verdict_text


# ── Main ──────────────────────────────────────────────────────────────────────
async def main():
    print("=" * 80)
    print("  PROJECT_S_30_DAY_OPPORTUNITY_SCAN — A/B MODEL COMPARISON")
    print(f"  {datetime.now().isoformat()}")
    print("=" * 80)

    # Run A — default model
    run_a = await run_mission("A", OUT_DEFAULT, model_override=None)

    # Run B — qwen3.6-35b-a3b
    run_b = await run_mission("B", OUT_QWEN, model_override="qwen/qwen3.6-35b-a3b")

    # Comparison verdict
    print("\n\n" + "=" * 80)
    print("  GENERATING COMPARISON VERDICT")
    print("=" * 80)
    write_comparison(run_a, run_b)

    print("\n\n--- FINAL SUMMARY ---")
    print(f"  Run A score: {run_a['score']}/{run_a['max_score']}  ({run_a['elapsed_s']:.0f}s)")
    print(f"  Run B score: {run_b['score']}/{run_b['max_score']}  ({run_b['elapsed_s']:.0f}s)")
    print(f"  Comparison: {OUT_COMPARE}")
    print("--- END ---")


if __name__ == "__main__":
    asyncio.run(main())
