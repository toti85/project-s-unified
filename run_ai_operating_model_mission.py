"""
Mission launcher:
PROJECT_S_AI_OPERATING_MODEL_AND_FUTURE_COORDINATION_ARCHITECTURE_20260514

Patches MetaController step_timeout_sec to 300s (browser-safe).
"""
import asyncio
import sys
import json
import logging
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# STEP 2 — launcher env bootstrap: load .env so OPENROUTER_API_KEY reaches AIClient
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass  # dotenv not installed; key must already be in environment

from src.core.super_intelligent_ai import SuperIntelligentAI

OUTPUT_FILE = r"C:\ProjectS-Unified\reports\PROJECT_S_AI_OPERATING_MODEL_AND_FUTURE_COORDINATION_ARCHITECTURE_20260514.md"

TASK = """\
MISSION: PROJECT_S_AI_OPERATING_MODEL_AND_FUTURE_COORDINATION_ARCHITECTURE_20260514

CORE QUESTION: What AI operating model should Toti and Project-S use over the next 30 days \
to maximize progress, minimize waste/cost, and prepare for the upcoming server-based/local-LLM \
phase — and what future coordination architecture may make sense if Project-S later orchestrates \
more of this AI ecosystem?

This mission is NOT about bug bounty. Do not include bounty hunting, pentesting, or security topics.

=== INTERNAL DOCUMENTS TO READ FIRST ===
Use file_reader to read these files before doing any web research:
- C:\\ProjectS-Unified\\self_state.json
- C:\\ProjectS-Unified\\PROJECT_S_OVERVIEW.md
- C:\\ProjectS-Unified\\PROJECT_S_STATUS_AND_JOURNAL.md
- C:\\ProjectS-Unified\\reports\\QWEN36_SYNTHESIS_DEFAULT_ALIGNMENT_VERDICT_20260514.md
- C:\\ProjectS-Unified\\reports\\GAP_023_BROWSER_SUBTASK_ISOLATION_FIX_VERDICT_20260514.md

=== EXTERNAL RESEARCH TOPICS ===
[SEARCH QUERY] GitHub Copilot AI Credits June 2026 billing changes Claude Pro pricing OpenRouter agent workflow 2026
Use web_search and web_scraper to gather CURRENT 2026 public facts on:
1. GitHub Copilot June 1 2026 usage-based billing / AI Credits — what changes, cost model for heavy users
2. Claude Pro current pricing and capabilities (Claude Code, long-context reasoning)
3. ChatGPT Plus pricing and how it differs from OpenAI API access
4. OpenRouter pay-as-you-go model and its role for AI agent workflows
5. Current 2026 landscape: AI coding agents, IDE assistants, local LLM workflows, multi-model orchestration

=== AI STACK FACTS ===
- Claude Pro: ~$20/month — strategic thinking, architecture, large-context reasoning
- ChatGPT Plus: ~$20/month — second strategic reviewer, cross-validator
- GitHub Copilot: heavily used for code in VS Code; usage was EXHAUSTED on 2026-05-14 workday; \
  moving to usage-based billing / AI Credits on June 1 2026
- Cline: VS Code agent using OpenRouter credits; handled longer multi-step agentic tasks this session
- OpenRouter: pay-as-you-go backbone for Cline and Project-S model calls
- Project-S runtime: Phase1=qwen/qwen3-235b-a22b, synthesis=qwen/qwen3.6-35b-a3b, eval=deepseek/deepseek-chat
- Server phase coming soon: local LLMs on DL380 Gen9; could replace some paid API calls

=== REQUIRED OUTPUT ===
Write a complete markdown report to:
""" + OUTPUT_FILE + """

Required sections (ALL 12 must be present):
## 1. Executive Verdict — concrete 30-day operating model recommendation
## 2. Current AI Stack — table: Layer/Tool | Role | Payment | Strengths | Weaknesses | Best-fit tasks
## 3. Evidence from 2026-05-14 Project-S Workday — Copilot vs Cline vs Project-S observations
## 4. Cost and Sustainability Reality Check — today / after June 1 / after server migration
## 5. Recommended 30-Day AI Operating Model — routing policy table
## 6. Concrete Daily/Weekly Workflow — active dev days vs research days
## 7. "Use Now" vs "Prepare For Soon" — current vs post-server operating model
## 8. Future Coordination Architecture — concept only, not implementation proposal
## 9. What NOT To Do — blunt list
## 10. Final Decision — exact stack roles, switch criteria, 30-day recommendations
## 11. Confirmed Facts vs Assumptions — internal confirmed / external confirmed / strategic assumptions
## 12. Sources — internal docs + external URLs consulted

The report must use evidence from the internal Project-S documents AND fresh public facts from web research.
It must make a specific 30-day routing recommendation, not generic prose.
Do NOT invent pricing/facts not found in sources.
"""

REQUIRED_SECTIONS = [
    "## 1.",
    "## 2.",
    "## 3.",
    "## 4.",
    "## 5.",
    "## 6.",
    "## 7.",
    "## 8.",
    "## 9.",
    "## 10.",
    "## 11.",
    "## 12.",
]


class LogCapture(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record.getMessage())


log_capture = LogCapture()
for logger_name in [
    "tools.tools.registry.smart_orchestrator",
    "evaluator",
    "src.core.super_intelligent_ai",
    "core.meta.meta_controller",
]:
    logging.getLogger(logger_name).addHandler(log_capture)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("ai_opmodel_mission")


async def run():
    t0 = time.time()
    ai = SuperIntelligentAI(use_meta_controller=True)

    # Extend timeout so browser+synthesis pipelines can complete
    if hasattr(ai, "meta_controller") and ai.meta_controller is not None:
        ai.meta_controller.config.step_timeout_sec = 300
        ai.meta_controller.config.max_iters = 3
        log.info("MetaController patched: step_timeout_sec=300, max_iters=3")

    result = await ai.execute_intelligent_task(task=TASK)
    elapsed = round(time.time() - t0, 1)

    success = result.get("success", False)
    log.info("Mission complete: success=%s elapsed=%ss", success, elapsed)

    # Verify output
    out_path = Path(OUTPUT_FILE)
    file_ok = out_path.exists()
    file_size = out_path.stat().st_size if file_ok else 0
    content = out_path.read_text(encoding="utf-8") if file_ok else ""

    section_results = {s: (s in content) for s in REQUIRED_SECTIONS}
    pass_count = sum(section_results.values())
    total = len(REQUIRED_SECTIONS)

    # Extract key log observations
    tool_seq_lines = [m for m in log_capture.records if "GAP_015: Using" in m]
    gap023_lines = [m for m in log_capture.records if "GAP_023" in m]
    synthesis_lines = [m for m in log_capture.records if "GAP_019: Synthesis model" in m or "Synthesis model" in m]
    file_reader_lines = [m for m in log_capture.records if "file_reader" in m.lower()]
    browser_lines = [m for m in log_capture.records if "browser_automation" in m and "Executing" in m]

    verdict = "PASS" if pass_count == total and file_ok and success else (
        "PARTIAL" if pass_count >= 8 and file_ok else "FAIL"
    )

    print("\n" + "=" * 65)
    print("MISSION: AI Operating Model & Future Coordination Architecture")
    print("=" * 65)
    print(f"Success:          {success}")
    print(f"Elapsed:          {elapsed}s")
    print(f"Output file:      {'EXISTS' if file_ok else 'MISSING'} ({file_size} bytes)")
    print(f"Section score:    {pass_count}/{total}")
    for s, ok in section_results.items():
        print(f"  {'PASS' if ok else 'FAIL'}  {s}")
    print()
    print("Tool pipeline:")
    for line in tool_seq_lines:
        print(f"  {line}")
    print(f"file_reader used: {'YES' if file_reader_lines else 'NO'}")
    print(f"browser_auto:     {'YES' if browser_lines else 'NO'}")
    for line in gap023_lines:
        print(f"  GAP_023: {line}")
    print(f"Synthesis model:")
    for line in synthesis_lines[:3]:
        print(f"  {line}")
    print()
    print(f"VERDICT: {verdict}")
    print("=" * 65)

    summary = {
        "mission": "PROJECT_S_AI_OPERATING_MODEL_AND_FUTURE_COORDINATION_ARCHITECTURE_20260514",
        "success": success,
        "elapsed_s": elapsed,
        "output_file": str(out_path),
        "file_exists": file_ok,
        "file_size_bytes": file_size,
        "section_score": f"{pass_count}/{total}",
        "section_results": section_results,
        "tool_sequences": tool_seq_lines,
        "file_reader_used": bool(file_reader_lines),
        "browser_used": bool(browser_lines),
        "gap023_fired": bool(gap023_lines),
        "synthesis_model_lines": synthesis_lines[:3],
        "verdict": verdict,
    }
    Path("ai_opmodel_mission_run.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print("Summary saved: ai_opmodel_mission_run.json")
    return summary


if __name__ == "__main__":
    summary = asyncio.run(run())
    sys.exit(0 if summary["verdict"] in ("PASS", "PARTIAL") else 1)
