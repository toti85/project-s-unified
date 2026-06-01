"""
Mission launcher:
PROJECT_S_SERVER_PHASE_BLUEPRINT_AND_LOCAL_INTELLIGENCE_ACTIVATION_20260515

Runs natively through the full Project-S pipeline:
  SuperIntelligentAI(use_meta_controller=True)
  → MetaController → Qwen3 235B planning → SmartToolOrchestrator
  → file_reader + web_search + synthesis → file_writer → Evaluator
"""
import asyncio
import sys
import json
import logging
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Load .env so OPENROUTER_API_KEY reaches AIClient
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

from src.core.super_intelligent_ai import SuperIntelligentAI

OUTPUT_FILE = (
    r"C:\ProjectS-Unified\reports"
    r"\PROJECT_S_SERVER_PHASE_BLUEPRINT_AND_LOCAL_INTELLIGENCE_ACTIVATION_20260515.md"
)

TASK = """\
MISSION: PROJECT_S_SERVER_PHASE_BLUEPRINT_AND_LOCAL_INTELLIGENCE_ACTIVATION_20260515

CORE QUESTION:
How should Project-S transition from the current DEV-machine/OpenRouter-assisted state into \
its upcoming server-based 24/7 phase with local LLM capacity — and what exact architecture, \
migration order, model-routing policy, and first-week operating plan should be adopted?

This is NOT a generic server migration checklist. This is a strategic + technical blueprint \
for Project-S's next operational phase.

Do NOT include bug bounty, pentesting, vulnerability research, audit target selection, \
or security scanner content. The bounty thread is separate.

=== INTERNAL DOCUMENTS TO READ FIRST ===
Use file_reader to read these files before any web research:
- C:\\ProjectS-Unified\\self_state.json
- C:\\ProjectS-Unified\\PROJECT_S_OVERVIEW.md
- C:\\ProjectS-Unified\\PROJECT_S_STATUS_AND_JOURNAL.md
- C:\\ProjectS-Unified\\PROJECT_S_20260514_EXTERNAL_MISSION_MILESTONE.md
- C:\\ProjectS-Unified\\reports\\AI_OPERATING_MODEL_NATIVE_PIPELINE_RECOVERY_VERDICT_20260514.md

=== CURRENT PROJECT-S STATE (as of 2026-05-15) ===
- Canonical runtime: SuperIntelligentAI(use_meta_controller=True) → MetaController \
  → Qwen3 235B planning → SmartToolOrchestrator → Evaluator → Witness/meta_evidence
- AgentLoop archived. Standalone MetaController dispatcher dormant.
- 15+ real tools active/verified. DDGS web search live. Browser automation live.
- file_reader dispatch fixed (GAP_024). file_writer path-corruption fixed (GAP_025).
- Qwen3.6-35B-A3B is the verified runtime synthesis default.
- self_state.json restored and validated. Gap state: 25 total / 24 resolved / 1 accepted / 0 active.

=== HARDWARE / SERVER CONTEXT ===
Upcoming Project-S server:
- HP ProLiant DL380 Gen9
- 2x Xeon E5-2699 v3 (18-core each, 36 cores / 72 threads)
- 128 GB DDR4 ECC RAM
- Tesla M60 GPU (2x Maxwell GM204, 16 GB GDDR5 total; or 2x 8 GB boards)
- ~1.6 TB NVMe storage
- Dual PSU — enables 24/7 uptime
- Windows Server 2019 image present on arrival
- Prior architectural idea included Proxmox with 4 VMs:
  1. Factory Systems / isolated business-critical services
  2. Project-S + Organism / cognitive core
  3. AI Models VM / GPU-bound local LLMs
  4. Dream Mode / sandbox experiments
The report should NOT blindly assume Proxmox is right. Evaluate Windows Server-first vs Proxmox-first.

=== EXTERNAL RESEARCH TOPICS ===
[SEARCH QUERY] Qwen3.6 35B local deployment GGUF llama.cpp Ollama Tesla M60 16GB quantization 2026 server LLM
Use web_search and web_scraper to gather CURRENT 2026 public facts on:
1. Local Qwen3.6-35B-A3B (or equivalent MoE) deployment options:
   - llama.cpp / GGUF availability and quantization levels
   - Ollama support for MoE models
   - LM Studio support
   - vLLM / transformers feasibility
   - realistic VRAM requirements on Tesla M60 (GDDR5, Maxwell, no NVLink between boards)
2. Tesla M60 for LLM inference in 2026:
   - reported benchmarks, community experience, token throughput
   - whether CUDA support (SM 5.2) is still workable with current llama.cpp / vLLM builds
   - real-world examples of running 7B, 13B, 35B class models on M60
3. Alternative local models for Project-S roles (synthesis, coding, evaluator, planning):
   - Qwen-family smaller models (Qwen3-8B, Qwen3-14B, Qwen2.5-Coder)
   - Llama 4 Scout, Gemma 4-31B feasibility on Tesla M60
   - Best 2026 "Q4_K_M or Q5_K_M that fits 16GB" models for agentic/synthesis tasks
4. Always-on Python AI service deployment patterns in 2026:
   - FastAPI + async service, systemd/NSSM persistence, state backup strategies
   - GPU sharing / contention management
5. Windows Server 2019 vs Proxmox for local LLM + Python AI service hosting

=== REQUIRED OUTPUT ===
Write a complete markdown report to:
""" + OUTPUT_FILE + """

Required sections (ALL 14 must be present):
## 1. Executive Verdict — primary migration strategy recommendation (one clear choice)
## 2. Current Project-S State — What Is Actually Ready To Move
## 3. Server Reality Check — component-by-component table for DL380 Gen9
## 4. Migration Architecture Options — compare Windows-first vs Proxmox-first vs Two-stage hybrid
## 5. Recommended Phase Architecture — concrete target architecture with text diagram
## 6. Local LLM Activation Strategy — role routing: which moves local first vs stays API
## 7. Qwen3.6 Local Feasibility Decision — hard answer with evidence; "Our first local model experiment should be: X."
## 8. 72-Hour Server Activation Plan — 0-24h / 24-48h / 48-72h concrete steps
## 9. First 7 Days of 24/7 Project-S Operation — table of daily/nightly jobs
## 10. Risks, Failure Modes, and Anti-Patterns — blunt list
## 11. Decision Gates — explicit go/no-go criteria
## 12. Final Recommendation — 5 concrete points: choice, first model, immediate action, what NOT to do, highest-leverage next action
## 13. Confirmed Facts vs Assumptions — internal confirmed / external confirmed / strategic assumptions
## 14. Sources — internal docs read + external URLs

The report must:
- Use evidence from internal Project-S documents (read via file_reader)
- Use current 2026 public facts from web research
- Make a specific concrete migration architecture decision, not generic advice
- Distinguish hard evidence about Tesla M60 LLM feasibility from speculation
- Include a real 72-hour activation plan and 7-day operating schedule with tasks
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
    "## 13.",
    "## 14.",
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
log = logging.getLogger("server_blueprint_mission")


async def run():
    t0 = time.time()
    ai = SuperIntelligentAI(use_meta_controller=True)

    # Extended timeout: synthesis + browser can be slow
    if hasattr(ai, "meta_controller") and ai.meta_controller is not None:
        ai.meta_controller.config.step_timeout_sec = 300
        ai.meta_controller.config.max_iters = 3
        log.info("MetaController patched: step_timeout_sec=300, max_iters=3")

    result = await ai.execute_intelligent_task(task=TASK)
    elapsed = round(time.time() - t0, 1)

    success = result.get("success", False)
    log.info("Mission complete: success=%s elapsed=%ss", success, elapsed)

    out_path = Path(OUTPUT_FILE)
    file_ok = out_path.exists()
    file_size = out_path.stat().st_size if file_ok else 0
    content = out_path.read_text(encoding="utf-8") if file_ok else ""

    section_results = {s: (s in content) for s in REQUIRED_SECTIONS}
    pass_count = sum(section_results.values())
    total = len(REQUIRED_SECTIONS)

    # Key log lines
    tool_seq_lines    = [m for m in log_capture.records if "GAP_015: Using" in m]
    synthesis_lines   = [m for m in log_capture.records if "Synthesis model" in m or "GAP_019: Synthesis" in m]
    file_reader_lines = [m for m in log_capture.records if "GAP_024" in m or ("file_reader" in m.lower() and "read" in m.lower())]
    browser_lines     = [m for m in log_capture.records if "browser_automation" in m and ("Executing" in m or "GAP_023" in m)]
    gap025_lines      = [m for m in log_capture.records if "GAP_025" in m]

    verdict = "PASS" if pass_count == total and file_ok and success else (
        "PARTIAL" if pass_count >= 10 and file_ok else "FAIL"
    )

    print("\n" + "=" * 70)
    print("MISSION: SERVER PHASE BLUEPRINT & LOCAL INTELLIGENCE ACTIVATION")
    print("=" * 70)
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
    for line in file_reader_lines[:3]:
        print(f"  {line}")
    print(f"browser_auto:     {'YES' if browser_lines else 'NO'}")
    print(f"GAP_025 output path:")
    for line in gap025_lines[:2]:
        print(f"  {line}")
    print(f"Synthesis model:")
    for line in synthesis_lines[:3]:
        print(f"  {line}")
    print()
    print(f"VERDICT: {verdict}")
    print("=" * 70)

    summary = {
        "mission": "PROJECT_S_SERVER_PHASE_BLUEPRINT_AND_LOCAL_INTELLIGENCE_ACTIVATION_20260515",
        "success": success,
        "elapsed_s": elapsed,
        "output_file": OUTPUT_FILE,
        "file_exists": file_ok,
        "file_size_bytes": file_size,
        "section_score": f"{pass_count}/{total}",
        "section_results": section_results,
        "tool_sequences": tool_seq_lines,
        "file_reader_used": bool(file_reader_lines),
        "file_reader_lines": file_reader_lines[:5],
        "browser_used": bool(browser_lines),
        "gap025_lines": gap025_lines[:3],
        "synthesis_model_lines": synthesis_lines[:3],
        "verdict": verdict,
    }
    Path("server_blueprint_mission_run.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print("Summary saved: server_blueprint_mission_run.json")
    return summary


if __name__ == "__main__":
    summary = asyncio.run(run())
    sys.exit(0 if summary["verdict"] in ("PASS", "PARTIAL") else 1)
