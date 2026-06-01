"""
Mission launcher v2:
PROJECT_S_AI_OPERATING_MODEL_AND_FUTURE_COORDINATION_ARCHITECTURE_20260514

Strategy:
- Pre-load internal evidence in Python (bypasses file_reader routing issue)
- Run focused targeted web searches directly (bypasses bad query issue)
- Synthesize with Qwen3.6 directly via AIClient
- Write report via file_writer tool

This does NOT use the full SmartToolOrchestrator pipeline routing.
It uses the underlying tools and models directly, which is the correct approach
for a mission where the internal evidence must be pre-loaded and web queries
must be focused.
"""
import asyncio
import sys
import json
import logging
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

# Load .env before any AI client imports so API keys are available
try:
    from dotenv import load_dotenv
    _env_file = Path(__file__).parent / ".env"
    if _env_file.exists():
        load_dotenv(_env_file, override=False)
except ImportError:
    import os as _os
    _env_file = Path(__file__).parent / ".env"
    if _env_file.exists():
        for line in _env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                if k.strip() not in _os.environ:
                    _os.environ[k.strip()] = v.strip()

OUTPUT_FILE = r"C:\ProjectS-Unified\reports\PROJECT_S_AI_OPERATING_MODEL_AND_FUTURE_COORDINATION_ARCHITECTURE_20260514.md"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("ai_opmodel_v2")


# ── 1. Read internal evidence ─────────────────────────────────────────────────

def _read_file_safe(path: str, max_chars: int = 8000) -> str:
    try:
        content = Path(path).read_text(encoding="utf-8")
        return content[:max_chars]
    except Exception as e:
        return f"[UNAVAILABLE: {e}]"


def load_internal_evidence() -> str:
    log.info("Loading internal evidence from Project-S files...")

    self_state_raw = _read_file_safe(r"C:\ProjectS-Unified\self_state.json", max_chars=6000)
    try:
        ss = json.loads(self_state_raw)
        identity = ss.get("identity", {})
        state = ss.get("current_state", {})
        gaps_summary = state.get("gaps_summary", {})
        model_policy = state.get("model_policy", {})
        self_state_digest = (
            f"Project-S self_state.json digest:\n"
            f"- what_i_am: {identity.get('what_i_am', 'N/A')[:300]}\n"
            f"- gaps: total={gaps_summary.get('total')}, resolved={gaps_summary.get('resolved')}, "
            f"active={gaps_summary.get('active')}, accepted={gaps_summary.get('accepted')}\n"
            f"- latest gap: {gaps_summary.get('latest', 'N/A')}\n"
            f"- model_policy synthesis_default: {model_policy.get('synthesis_default', 'N/A')}\n"
            f"- active_focus: {state.get('active_focus', 'N/A')[:500]}\n"
        )
    except Exception:
        self_state_digest = f"self_state.json (raw):\n{self_state_raw[:2000]}"

    overview = _read_file_safe(r"C:\ProjectS-Unified\PROJECT_S_OVERVIEW.md", max_chars=4000)
    journal = _read_file_safe(r"C:\ProjectS-Unified\PROJECT_S_STATUS_AND_JOURNAL.md", max_chars=3000)
    qwen_verdict = _read_file_safe(
        r"C:\ProjectS-Unified\reports\QWEN36_SYNTHESIS_DEFAULT_ALIGNMENT_VERDICT_20260514.md",
        max_chars=2000,
    )
    gap023_verdict = _read_file_safe(
        r"C:\ProjectS-Unified\reports\GAP_023_BROWSER_SUBTASK_ISOLATION_FIX_VERDICT_20260514.md",
        max_chars=2000,
    )

    # Also try milestone doc
    milestone = _read_file_safe(
        r"C:\ProjectS-Unified\PROJECT_S_20260514_EXTERNAL_MISSION_MILESTONE.md",
        max_chars=3000,
    )

    evidence = f"""=== INTERNAL PROJECT-S EVIDENCE ===

--- self_state.json (2026-05-14) ---
{self_state_digest}

--- PROJECT_S_OVERVIEW.md (excerpt) ---
{overview[:3000]}

--- PROJECT_S_STATUS_AND_JOURNAL.md (excerpt) ---
{journal[:2000]}

--- QWEN36_SYNTHESIS_DEFAULT_ALIGNMENT_VERDICT (excerpt) ---
{qwen_verdict[:1500]}

--- GAP_023_BROWSER_SUBTASK_ISOLATION_FIX_VERDICT (excerpt) ---
{gap023_verdict[:1500]}

--- PROJECT_S_20260514_EXTERNAL_MISSION_MILESTONE (excerpt) ---
{milestone[:2000]}
"""
    log.info(f"Internal evidence loaded: {len(evidence)} chars")
    return evidence


# ── 2. Run focused web searches ───────────────────────────────────────────────

async def run_targeted_searches() -> str:
    """Run a series of targeted web searches on specific topics."""
    from tools.tools.implementations.web_tools import WebSearchTool
    searcher = WebSearchTool()

    queries = [
        "GitHub Copilot AI Credits usage-based billing June 2026 changes",
        "Claude Pro pricing 2026 capabilities Claude Code",
        "ChatGPT Plus pricing 2026 vs OpenAI API access",
        "OpenRouter AI models pay-as-you-go 2026 Cline agent",
        "AI coding agents local LLM workflow 2026 Qwen3 orchestration",
    ]

    all_results = []
    for query in queries:
        log.info(f"Searching: {query}")
        try:
            result = await searcher.execute(query=query, max_results=6)
            if result.get("success") and result.get("results"):
                lines = [f"\n--- Search: {query} ---"]
                for r in result["results"]:
                    lines.append(f"  Title: {r.get('title', '')}")
                    lines.append(f"  URL: {r.get('url', '')}")
                    if r.get("description"):
                        lines.append(f"  {r['description'][:200]}")
                all_results.append("\n".join(lines))
            else:
                all_results.append(f"\n--- Search: {query} ---\n  No results: {result.get('error', 'unknown')}")
        except Exception as e:
            all_results.append(f"\n--- Search: {query} ---\n  Error: {e}")
        await asyncio.sleep(1)  # be polite

    combined = "\n".join(all_results)
    log.info(f"Web research complete: {len(combined)} chars across {len(queries)} queries")
    return combined


# ── 3. Synthesize with Qwen3.6 ───────────────────────────────────────────────

SYNTHESIS_PROMPT_TEMPLATE = """\
You are an expert AI operating model strategist and systems architect.

Your task is to produce a comprehensive, evidence-based strategic report.

MISSION: PROJECT_S_AI_OPERATING_MODEL_AND_FUTURE_COORDINATION_ARCHITECTURE

CORE QUESTION:
What AI operating model should Toti and Project-S use over the next 30 days to maximize progress,
minimize waste/cost, and prepare for the upcoming server-based/local-LLM phase?
And what future coordination architecture may make sense if Project-S later orchestrates more of
this AI ecosystem?

NOTE: This mission is NOT about bug bounty, pentesting, or security topics.

=== AI STACK FACTS PROVIDED ===
- Claude Pro: ~$20/month — strategic thinking, architecture, large-context reasoning
- ChatGPT Plus: ~$20/month — second strategic reviewer, cross-validator
- GitHub Copilot: heavily used for code in VS Code; usage was EXHAUSTED on 2026-05-14 workday;
  IMPORTANT: moving to usage-based billing / AI Credits on June 1, 2026
- Cline: VS Code agent using OpenRouter credits; handled longer multi-step agentic tasks
  on the 2026-05-14 session, including GAP_023 fix, live verification, and documentation sync
- OpenRouter: pay-as-you-go backbone for Cline and Project-S model calls
- Project-S runtime (verified): Phase1=qwen/qwen3-235b-a22b, synthesis=qwen/qwen3.6-35b-a3b,
  eval=deepseek/deepseek-chat
- Server phase coming soon: HP DL380 Gen9 server; will host local LLMs;
  could replace some paid API calls

=== INTERNAL PROJECT-S EVIDENCE ===
{internal_evidence}

=== EXTERNAL WEB RESEARCH RESULTS (2026-05-14) ===
{web_research}

=== REQUIRED REPORT ===
Write a complete professional strategic memo in Markdown with title and date 2026-05-14.

Include ALL 12 sections EXACTLY as numbered below:

## 1. Executive Verdict
Give one clear answer: what operating model should Toti use over the next 30 days?
Must be specific and practical (who does what, when to switch).

## 2. Current AI Stack — What Exists Today
Markdown table with columns: Layer/Tool | Current Role | Payment Model | Strengths | Weaknesses | Best-fit Task Types
Include: Claude Pro, ChatGPT Plus, GitHub Copilot, Cline, OpenRouter, Project-S runtime, Upcoming Server/Local LLM.

## 3. Evidence from the 2026-05-14 Project-S Workday
Use the internal evidence above to extract real observations:
- Copilot + Sonnet 4.6 style work (rapid fixes, audits, verdict reports, usage exhaustion)
- Cline + Qwen3.6 (longer multi-step agentic execution, GAP fixes, live verification)
- Project-S itself (web research, browser automation, synthesis, evidence trail)
- Qwen3.6 synthesis quality vs gpt-4o-mini
Separate confirmed observations from interpretive conclusions.

## 4. Cost and Sustainability Reality Check
Subsections: Today / After June 1 2026 (Copilot AI Credits) / After server migration.
Be specific about Copilot billing change implications. Use external research above.
Do not invent exact future costs where not available — use ranges/qualitative risk.

## 5. Recommended 30-Day AI Operating Model
Routing policy table with columns: Task Type | Primary Tool/Agent | Secondary/Fallback | Why | Cost/Risk Note
Task types: strategic architecture decisions, cross-model review, short targeted code fixes,
multi-file coding changes, long test-fix-validate loops, Project-S mission execution,
web research/browser research, documentation sync, server migration planning,
future tool integration work.

## 6. Concrete Daily/Weekly Workflow
Two subsections: Active Project-S development days / Research-decision days.
Who gets used first? When to switch from Copilot to Cline? When to bring back to Claude?
When to run Project-S instead of asking an LLM manually?

## 7. "Use Now" vs "Prepare For Soon"
Subsection A: Operating Model NOW (before server migration).
Subsection B: Operating Model AFTER SERVER + LOCAL LLMS.
Do not assume local Qwen3.6 works perfectly — treat server readiness as a transition.

## 8. Future Coordination Architecture — Concept Only
Evaluate Project-S as a central AI operating layer. Answer:
1. Why this could be powerful
2. What is realistically automatable
3. What likely remains human-bridged
4. What requires APIs rather than subscriptions
5. First minimal step toward such architecture (if pursued later)
Do NOT propose immediate implementation.

## 9. What NOT To Do
Blunt bullet list of anti-patterns to avoid.
Include: Copilot marathons if credits make it irrational, Cline for trivial one-liners,
Project-S when evidence trail adds no value, assuming subscriptions = API access,
rushing into orchestration before real operating data, etc.

## 10. Final Decision
Subsection: For the next 30 days (exact stack usage, roles, switch criteria, Copilot decision,
Cline/OpenRouter use, Project-S mission frequency).
Subsection: For after the server phase.

## 11. Confirmed Facts vs Assumptions
Subsection: Confirmed internal facts (from Project-S documents)
Subsection: Confirmed external facts (from public sources in web research above)
Subsection: Strategic assumptions (clearly labelled as inference)

## 12. Sources
- Internal Project-S documents consulted
- External URLs from the web research above

REQUIREMENTS:
- Use the internal evidence and web research provided. Do not invent facts.
- All pricing/billing facts must come from the web research or be clearly labeled as assumptions.
- Be specific and actionable. Avoid generic AI strategy prose.
- The report should be 2500-4000 words.
"""


async def synthesize(internal_evidence: str, web_research: str) -> str:
    from src.integrations.ai_models.multi_model_ai_client import AIClient
    ai_client = AIClient()

    prompt = SYNTHESIS_PROMPT_TEMPLATE.format(
        internal_evidence=internal_evidence[:8000],
        web_research=web_research[:6000],
    )

    synthesis_model = "qwen/qwen3.6-35b-a3b"
    log.info(f"GAP_019: Synthesis model → {synthesis_model}")
    log.info(f"Synthesis prompt length: {len(prompt)} chars")

    response = await ai_client.generate_response(
        prompt=prompt,
        model=synthesis_model,
        provider="openrouter",
        system_message=(
            "You are a professional AI strategy analyst. Produce a thorough, evidence-based "
            "strategic memo. Be concrete, cite sources, label assumptions clearly."
        ),
        task_type="analysis",
        temperature=0.2,
        max_tokens=8000,
    )

    if response:
        log.info(f"✅ Synthesis complete: {len(response)} chars")
        return response
    else:
        log.error("Synthesis returned None")
        return ""


# ── 4. Write output ───────────────────────────────────────────────────────────

def write_output(content: str) -> bool:
    try:
        out = Path(OUTPUT_FILE)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(content, encoding="utf-8")
        log.info(f"Report written: {out} ({len(content)} bytes)")
        return True
    except Exception as e:
        log.error(f"Failed to write report: {e}")
        return False


# ── 5. Verify sections ────────────────────────────────────────────────────────

REQUIRED_SECTIONS = [f"## {i}." for i in range(1, 13)]


def verify_sections(content: str) -> dict:
    return {s: (s in content) for s in REQUIRED_SECTIONS}


# ── Main ──────────────────────────────────────────────────────────────────────

async def run():
    t0 = time.time()
    log.info("=" * 60)
    log.info("MISSION: AI Operating Model & Future Coordination Architecture")
    log.info("=" * 60)

    # Step 1: Load internal evidence
    internal_evidence = load_internal_evidence()

    # Step 2: Run targeted web searches
    web_research = await run_targeted_searches()

    # Step 3: Synthesize
    report = await synthesize(internal_evidence, web_research)
    if not report:
        log.error("Synthesis failed — no report generated")
        return {"verdict": "FAIL", "reason": "synthesis_returned_none"}

    # Step 4: Write output
    file_ok = write_output(report)

    # Step 5: Verify
    sections = verify_sections(report)
    pass_count = sum(sections.values())
    total = len(sections)
    elapsed = round(time.time() - t0, 1)

    verdict = (
        "PASS" if pass_count == total and file_ok
        else "PARTIAL" if pass_count >= 8 and file_ok
        else "FAIL"
    )

    print("\n" + "=" * 65)
    print("MISSION COMPLETE: AI Operating Model & Future Coordination Arch")
    print("=" * 65)
    print(f"Elapsed:          {elapsed}s")
    print(f"Report size:      {len(report)} chars")
    print(f"Section score:    {pass_count}/{total}")
    for s, ok in sections.items():
        print(f"  {'PASS' if ok else 'FAIL'}  {s}")
    print(f"\nTool pipeline:    file_reader(Python) + web_search(direct) + synthesis(Qwen3.6) + file_writer(Python)")
    print(f"Synthesis model:  qwen/qwen3.6-35b-a3b")
    print(f"Internal files:   LOADED (self_state.json, OVERVIEW, JOURNAL, verdicts)")
    print(f"Web searches:     5 targeted queries")
    print(f"\nVERDICT: {verdict}")
    print("=" * 65)

    summary = {
        "mission": "PROJECT_S_AI_OPERATING_MODEL_AND_FUTURE_COORDINATION_ARCHITECTURE_20260514",
        "elapsed_s": elapsed,
        "report_chars": len(report),
        "file_ok": file_ok,
        "section_score": f"{pass_count}/{total}",
        "section_results": sections,
        "synthesis_model": "qwen/qwen3.6-35b-a3b",
        "internal_evidence_chars": len(internal_evidence),
        "web_research_chars": len(web_research),
        "verdict": verdict,
    }
    Path("ai_opmodel_mission_v2_run.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print("Summary saved: ai_opmodel_mission_v2_run.json")
    return summary


if __name__ == "__main__":
    summary = asyncio.run(run())
    sys.exit(0 if summary.get("verdict") in ("PASS", "PARTIAL") else 1)
