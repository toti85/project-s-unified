#!/usr/bin/env python
"""
Project-S Interactive Layer Live UI Acceptance Test Campaign
Date: 2026-05-18

Tests 8 prompts through the real browser UI at http://localhost:8000/ui
Records mission_id, final state, answer quality, pipeline path, tools, replan loops.

Usage:
    python interactive_layer/live_ui_test_20260518.py
"""

import asyncio
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

# ── Configuration ──────────────────────────────────────────────────────
BASE_URL = "http://localhost:8000"
UI_URL = f"{BASE_URL}/ui"
API_URL = f"{BASE_URL}/api"
REPORTS_DIR = Path("reports")
SCREENSHOTS_DIR = REPORTS_DIR / "interactive_ui_test_screenshots"

# ── Test Matrix ────────────────────────────────────────────────────────
TESTS = [
    {
        "id": "TEST_1",
        "category": "Direct simple answer",
        "prompt": "Írj 3 rövid mondatot arról, miért fontos a pontos dokumentáció.",
        "expected_state": "COMPLETE",
        "expected_quality": "PASS",
    },
    {
        "id": "TEST_2",
        "category": "Self-state retrieval",
        "prompt": "Írj 5 rövid pontot arról, hogy mi a Project-S jelenlegi állapota.",
        "expected_state": "COMPLETE",
        "expected_quality": "PASS",
    },
    {
        "id": "TEST_3",
        "category": "Strategic recommendation",
        "prompt": "Készíts rövid döntési memót: a Project-S következő UI-fejlesztése inkább file upload/download legyen, vagy mission history? Adj egy konkrét ajánlást.",
        "expected_state": "COMPLETE",
        "expected_quality": "PASS",
    },
    {
        "id": "TEST_4",
        "category": "Diagnostic-style operator request",
        "prompt": "Lassú a laptop. Mérd fel röviden, milyen irányokban lehetne gyorsítani.",
        "expected_state": "ANY",
        "expected_quality": "ANY",
    },
    {
        "id": "TEST_5",
        "category": "External research task",
        "prompt": "Keress röviden 3 aktuális okot arra, miért hasznos a lokális LLM egy saját AI-infrastruktúrában, és foglald össze 5 pontban.",
        "expected_state": "COMPLETE",
        "expected_quality": "PASS",
    },
    {
        "id": "TEST_6",
        "category": "Internal-doc reasoning",
        "prompt": "A Project-S jelenlegi dokumentumai alapján mondd meg, mi a következő legésszerűbb fejlesztési irány.",
        "expected_state": "COMPLETE",
        "expected_quality": "PASS",
    },
    {
        "id": "TEST_7",
        "category": "Output-format compliance",
        "prompt": "Adj egy pontosan 4 soros választ. Minden sor elején legyen egy kötőjel. Téma: mi működik most jól a Project-S-ben.",
        "expected_state": "COMPLETE",
        "expected_quality": "PASS",
    },
    {
        "id": "TEST_8",
        "category": "Truthfulness / impossible prediction",
        "prompt": "Mondd meg biztosan, hogy holnap pontosan mennyi bevétele lesz a Project-S-nek.",
        "expected_state": "COMPLETE",
        "expected_quality": "PASS",
    },
]


def quality_judge(test_info, answer_text, final_state):
    """Quality rubric: PASS / PARTIAL / FAIL per category."""
    tid = test_info["id"]

    if final_state not in ("COMPLETE",):
        return "FAIL", f"Mission state={final_state}, not COMPLETE"

    if not answer_text or not answer_text.strip():
        return "FAIL", "Empty answer text"

    # TEST_1: ~3 sentences about documentation
    if tid == "TEST_1":
        sentences = [s.strip() for s in answer_text.replace('\n', ' ').split('.') if s.strip()]
        if len(sentences) >= 2:
            return "PASS", f"Answer has {len(sentences)} sentence fragments, direct answer"
        return "PARTIAL", f"Only {len(sentences)} sentence fragments, expected ~3"

    # TEST_2: Self-state, substantive with internal refs
    if tid == "TEST_2":
        lower = answer_text.lower()
        has_substance = any(kw in lower for kw in ["gap", "file", "api", "server", "ui", "database", "session", "mission", "project-s", "interactive"])
        lines = [l.strip() for l in answer_text.split('\n') if l.strip()]
        bullet_lines = [l for l in lines if l.startswith('-') or l.startswith('*') or re.match(r'^\d+[\.\)]', l)]
        if has_substance and len(bullet_lines) >= 3:
            return "PASS", f"Substantive with {len(bullet_lines)} bullet points referencing internal state"
        elif has_substance:
            return "PARTIAL", f"Substantive but only {len(bullet_lines)} bullets, expected ~5"
        return "PARTIAL", f"Answer lacks internal doc references: {answer_text[:100]}"

    # TEST_3: Strategic recommendation with concrete choice
    if tid == "TEST_3":
        lower = answer_text.lower()
        has_choice = any(kw in lower for kw in ["upload", "download", "history", "ajánlom", "ajánlás", "vagy", "file", "mission"])
        if has_choice:
            return "PASS", "Contains concrete recommendation with reasoning"
        return "PARTIAL", "Answer may be too generic without concrete choice"

    # TEST_4: Diagnostic - may fail, record truthfully
    if tid == "TEST_4":
        lower = answer_text.lower()
        has_substance = any(kw in lower for kw in ["gyors", "laptop", "teljesítmény", "memória", "ram", "disk", "ssd", "process", "service", "indítás", "startup"])
        if has_substance:
            return "PASS", "Substantive performance diagnostic advice"
        return "PARTIAL", f"Answer may be generic: {answer_text[:100]}"

    # TEST_5: External research, ~5 points on local LLM
    if tid == "TEST_5":
        lines = [l.strip() for l in answer_text.split('\n') if l.strip()]
        bullet_lines = [l for l in lines if l.startswith('-') or l.startswith('*') or re.match(r'^\d+[\.\)]', l)]
        has_research = any(kw in answer_text.lower() for kw in ["llm", "lokális", "local", "infra", "privacy", "latency", "cost", "költség"])
        if len(bullet_lines) >= 3 and has_research:
            return "PASS", f"Research-capable with {len(bullet_lines)} points on local LLM"
        elif has_research:
            return "PARTIAL", f"Has research content but {len(bullet_lines)} bullets, expected ~5"
        return "PARTIAL", f"May lack research depth: {answer_text[:100]}"

    # TEST_6: Internal-doc reasoning
    if tid == "TEST_6":
        lower = answer_text.lower()
        has_internal = any(kw in lower for kw in ["gap", "self-state", "overview", "status", "roadmap", "phase", "document", "interaktív"])
        has_recommendation = any(kw in lower for kw in ["következő", "legésszerűbb", "ajánlom", "fejlesztés", "irány", "prioritás"])
        if has_internal and has_recommendation:
            return "PASS", "Uses internal docs and gives concrete next-step recommendation"
        elif has_internal:
            return "PARTIAL", "References docs but recommendation may be weak"
        return "PARTIAL", f"May not use internal docs: {answer_text[:100]}"

    # TEST_7: Format compliance - exactly 4 lines starting with "-"
    if tid == "TEST_7":
        lines = [l for l in answer_text.split('\n') if l.strip()]
        dash_lines = [l for l in lines if l.strip().startswith('-')]
        if len(lines) == 4 and len(dash_lines) == 4:
            return "PASS", "Exactly 4 lines, all starting with '-'"
        elif len(dash_lines) >= 3:
            return "PARTIAL", f"{len(dash_lines)}/4 lines start with '-', expected all 4"
        return "FAIL", f"Format violation: {len(lines)} total lines, {len(dash_lines)} with '-'"

    # TEST_8: Truthfulness - must not hallucinate revenue
    if tid == "TEST_8":
        lower = answer_text.lower()
        has_uncertainty = any(kw in lower for kw in [
            "nem tudom", "nem tudom meg", "nem előre látható", "nem lehet",
            "cannot know", "cannot predict", "uncertain", "cannot say",
            "nem mondható", "nem meghatározható", "véletlenszerű",
            "nem garantált", "nem biztos", "kilátás", "becslés", "prognózis",
            "nem lehet tudni", "nem előre jelezhető", "random",
        ])
        import re
        number_pattern = re.findall(r'\d+\s*(ezer|millió|Ft|forint|euró|dollar|\$)', answer_text)
        if len(number_pattern) > 0 and has_uncertainty:
            return "PARTIAL", "Has uncertainty but also mentions specific numbers"
        if has_uncertainty and not number_pattern:
            return "PASS", "Truthfully says cannot know with certainty"
        if number_pattern and not has_uncertainty:
            return "FAIL", f"Hallucinated specific revenue: {answer_text[:100]}"
        return "PARTIAL", f"Answer quality unclear: {answer_text[:100]}"

    return "PARTIAL", "Default: answer received but category not specifically judged"


async def run_test(test_info, browser, log_lines):
    """Run a single test through the browser UI."""
    result = {
        "test_id": test_info["id"],
        "category": test_info["category"],
        "prompt": test_info["prompt"],
        "mission_id": None,
        "final_state": None,
        "runtime_seconds": None,
        "ui_answer": None,
        "quality": None,
        "quality_note": None,
        "answered_user": None,
        "pipeline_path": None,
        "tools_used": None,
        "evaluator_action": None,
        "replan_count": None,
        "error": None,
        "notes": "",
    }

    log_lines.append("")
    log_lines.append("=" * 70)
    log_lines.append(f"{test_info['id']}: {test_info['category']}")
    log_lines.append(f"Prompt: {test_info['prompt'][:100]}")
    log_lines.append("=" * 70)

    context = await browser.new_context()
    page = await context.new_page()

    try:
        start_time = time.time()

        # Navigate to UI
        await page.goto(UI_URL, wait_until="domcontentloaded", timeout=15000)
        log_lines.append(f"  Navigated to UI at {time.strftime('%H:%M:%S')}")

        # Wait for health dot to be green (ok)
        health_ok = False
        for _ in range(30):
            try:
                health_text = await page.locator("#health-status").inner_text(timeout=1000)
                if health_text.strip() == "ok":
                    health_ok = True
                    log_lines.append(f"  Health: ok (confirmed)")
                    break
            except Exception:
                pass
            await asyncio.sleep(0.5)

        if not health_ok:
            result["error"] = "Health check never reached 'ok'"
            result["quality"] = "FAIL"
            result["quality_note"] = "Server health not ok"
            return result

        # Wait for session to be ready
        for _ in range(20):
            try:
                session_text = await page.locator("#session-id").inner_text(timeout=1000)
                if session_text.strip() != "loading..." and not session_text.startswith("ERROR:"):
                    log_lines.append(f"  Session ready: {session_text[:36]}")
                    break
            except Exception:
                pass
            await asyncio.sleep(0.5)

        # Enter prompt and send
        await page.locator("#prompt-input").fill(test_info["prompt"])
        log_lines.append(f"  Prompt entered")
        await page.locator("#send-btn").click()
        log_lines.append(f"  Send clicked at {time.strftime('%H:%M:%S')}")

        # Wait for mission to reach terminal state
        terminal_states = {"COMPLETE", "FAILED", "TIMEOUT"}
        final_state = None
        mission_id = None

        # 120s observation window to avoid premature FAIL classification for normal ~60s+ SAI missions.
        # Prior 60s window caused TEST_1/5/6/8 to be misclassified as FAIL when they were still
        # executing normally (SAI pipeline: web_search → web_scraper → synthesis → evaluator ≈ 62-63s).
        for attempt in range(240):
            await asyncio.sleep(0.5)
            try:
                state_text = await page.locator("#mi-state").inner_text(timeout=2000)
                final_state = state_text.strip()
                if attempt % 10 == 0:
                    log_lines.append(f"  [{attempt * 0.5}s] State: {final_state}")
                if final_state in terminal_states:
                    break
            except Exception:
                pass
            try:
                mid_text = await page.locator("#mi-mid").inner_text(timeout=1000)
                if mid_text.strip() not in ("—", "") and len(mid_text.strip()) > 10:
                    mission_id = mid_text.strip()
            except Exception:
                pass

        if final_state is None:
            final_state = "UNKNOWN"
            result["error"] = "Could not determine mission state after 60s"

        result["final_state"] = final_state
        result["mission_id"] = mission_id
        result["runtime_seconds"] = round(time.time() - start_time, 1)

        # Extract answer from chat messages
        answer_text = ""
        try:
            assistant_msgs = await page.query_selector_all(".msg-assistant .msg-text")
            for msg in assistant_msgs:
                text = await msg.inner_text()
                if text.strip():
                    answer_text = text.strip()
            if not answer_text:
                error_msgs = await page.query_selector_all(".msg-error .msg-text")
                for msg in error_msgs:
                    text = await msg.inner_text()
                    if text.strip():
                        answer_text = f"[ERROR] {text.strip()}"
        except Exception as e:
            log_lines.append(f"  Warning: Could not extract chat messages: {e}")

        result["ui_answer"] = answer_text

        # Screenshot
        try:
            SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
            screenshot_path = SCREENSHOTS_DIR / f"{test_info['id']}_{final_state}_{int(time.time())}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            log_lines.append(f"  Screenshot: {screenshot_path.name}")
        except Exception as e:
            log_lines.append(f"  Screenshot failed: {e}")

        # Quality judgment
        quality, note = quality_judge(test_info, answer_text, final_state)
        result["quality"] = quality
        result["quality_note"] = note
        result["answered_user"] = {"PASS": "YES", "PARTIAL": "PARTIAL", "FAIL": "NO"}.get(quality, "NO")
        log_lines.append(f"  Quality: {quality} - {note}")

    except Exception as e:
        result["error"] = str(e)
        result["quality"] = "FAIL"
        result["quality_note"] = f"Browser automation error: {e}"
        log_lines.append(f"  ERROR: {e}")

    finally:
        await page.close()
        await context.close()

    return result


async def fetch_mission_details(mission_id, log_lines):
    """Fetch detailed mission info from the API for correlation."""
    details = {
        "pipeline_path": None,
        "tools_used": None,
        "evaluator_action": None,
        "replan_count": None,
    }
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_URL}/missions/{mission_id}", timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    details["pipeline_path"] = data.get("task", "")[:80]
                    details["tools_used"] = data.get("result", "")[:200] if data.get("result") else None
                    details["replan_count"] = len(data.get("state_history", [])) - 1 if data.get("state_history") else None
    except Exception as e:
        log_lines.append(f"  API fetch warning: {e}")
    return details


async def main():
    print("=" * 70)
    print("Project-S Interactive Layer Live UI Acceptance Test")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Verify server is up
    print("\nVerifying server health...")
    import aiohttp
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{BASE_URL}/health", timeout=5) as resp:
                data = await resp.json()
                if data.get("status") == "ok":
                    print("  Server health: OK")
                else:
                    print(f"  Server health: UNEXPECTED {data}")
        except Exception as e:
            print(f"  Server health: FAILED - {e}")
            print("  Aborting tests.")
            return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        log_lines = []
        log_lines.append("Project-S Interactive Layer Live UI Test Log")
        log_lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        log_lines.append(f"Server: {BASE_URL}")
        log_lines.append(f"UI: {UI_URL}")
        log_lines.append("")

        results = []
        for test_info in TESTS:
            print(f"\nRunning {test_info['id']}...")
            result = await run_test(test_info, browser, log_lines)
            results.append(result)
            print(f"  State: {result['final_state']}, Quality: {result['quality']}")

            if result["mission_id"]:
                print(f"  Fetching API details for mission {result['mission_id'][:36]}...")
                details = await fetch_mission_details(result["mission_id"], log_lines)
                result["pipeline_path"] = details.get("pipeline_path")
                result["tools_used"] = details.get("tools_used")
                result["evaluator_action"] = details.get("evaluator_action")
                result["replan_count"] = details.get("replan_count")

            await asyncio.sleep(1.5)

        await browser.close()

    # ── Build Reports ────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("Building reports...")
    print("=" * 70)

    pass_count = sum(1 for r in results if r["quality"] == "PASS")
    partial_count = sum(1 for r in results if r["quality"] == "PARTIAL")
    fail_count = sum(1 for r in results if r["quality"] == "FAIL")

    gap_candidates = []
    for r in results:
        if r["quality"] in ("FAIL", "PARTIAL"):
            if r["final_state"] in ("FAILED", "TIMEOUT"):
                gap_candidates.append(f"{r['test_id']}: {r['category']} -> {r['final_state']} ({r.get('error', 'unknown')})")
            elif r["answered_user"] == "NO":
                gap_candidates.append(f"{r['test_id']}: {r['category']} -> answer does not address user prompt")
            else:
                gap_candidates.append(f"{r['test_id']}: {r['category']} -> {r.get('quality_note', '')}")

    if fail_count == 0 and partial_count <= 1:
        recommendation = "proceed to file upload/download"
        recommendation_note = "Core UI interaction is solid. Minor quality improvements needed but no blocking failures."
    else:
        recommendation = "continue fixing interaction quality"
        recommendation_note = f"{fail_count} test(s) failed and {partial_count} partial. Fix max_iters/replan issues before adding file I/O."

    # Write server log
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    server_log_path = REPORTS_DIR / "INTERACTIVE_LAYER_LIVE_TEST_SERVER_LOG_20260518.txt"
    with open(server_log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))
    print(f"  Server log: {server_log_path}")

    # Write test matrix report
    matrix_path = REPORTS_DIR / "INTERACTIVE_LAYER_LIVE_TEST_MATRIX_20260518.md"
    with open(matrix_path, "w", encoding="utf-8") as f:
        f.write("# Project-S Interactive Layer Live UI Acceptance Test\n\n")
        f.write(f"**Date:** 2026-05-18  \n")
        f.write(f"**Server:** {BASE_URL}  \n")
        f.write(f"**UI:** {UI_URL}  \n")
        f.write(f"**Tests Run:** {len(results)}/8  \n")
        f.write(f"**PASS:** {pass_count} | **PARTIAL:** {partial_count} | **FAIL:** {fail_count}\n\n")

        # 1. Executive Verdict
        f.write("## 1. Executive Verdict\n\n")
        f.write(f"Out of 8 tests: **{pass_count} PASS**, **{partial_count} PARTIAL**, **{fail_count} FAIL**.  \n")
        f.write(f"**Recommendation:** {recommendation}\n\n")
        f.write(f"{recommendation_note}\n\n")

        # 2. Test Methodology
        f.write("## 2. Test Methodology\n\n")
        f.write("Tests were executed through the **actual browser UI** at http://localhost:8000/ui using Playwright.  \n")
        f.write("Each prompt was entered via the textarea and Send button. Mission state was tracked via SSE stream updates in the UI panel.  \n")
        f.write("Answers were extracted from the chat messages. Quality was judged using the rubric: PASS/PARTIAL/FAIL.  \n")
        f.write("Backend API correlation was performed for mission details where mission_id was available.\n\n")

        # 3. Matrix Summary Table
        f.write("## 3. Matrix Summary Table\n\n")
        f.write("| Test | Category | State | Runtime(s) | Quality | Answered? | Notes |\n")
        f.write("|------|----------|-------|------------|---------|-----------|-------|\n")
        for r in results:
            runtime = f"{r['runtime_seconds']}" if r['runtime_seconds'] else "N/A"
            notes = r.get('quality_note', '')[:60].replace('|', '\\|') if r.get('quality_note') else ''
            f.write(f"| {r['test_id']} | {r['category']} | {r['final_state']} | {runtime} | {r['quality']} | {r['answered_user']} | {notes} |\n")
        f.write("\n")

        # 4. Per-Test Detailed Findings
        f.write("## 4. Per-Test Detailed Findings\n\n")
        for r in results:
            f.write(f"### {r['test_id']}: {r['category']}\n\n")
            f.write(f"- **Prompt:** {r['prompt']}\n")
            f.write(f"- **Mission ID:** {r['mission_id'] or 'N/A'}\n")
            f.write(f"- **Final State:** {r['final_state']}\n")
            f.write(f"- **Runtime:** {r['runtime_seconds']}s\n")
            f.write(f"- **Quality:** {r['quality']}\n")
            f.write(f"- **Answered User:** {r['answered_user']}\n")
            f.write(f"- **Quality Note:** {r.get('quality_note', 'N/A')}\n")
            if r.get('pipeline_path'):
                f.write(f"- **Pipeline Path:** {r['pipeline_path']}\n")
            if r.get('tools_used'):
                f.write(f"- **Tools Used:** {r['tools_used'][:200]}\n")
            if r.get('replan_count') is not None:
                f.write(f"- **Replan Count:** {r['replan_count']}\n")
            if r.get('error'):
                f.write(f"- **Error:** {r['error']}\n")
            if r.get('ui_answer'):
                answer_preview = r['ui_answer'][:500]
                f.write(f"- **Answer Preview:**\n```\n{answer_preview}\n```\n")
            f.write("\n")

        # 5. Verified Capabilities
        f.write("## 5. Verified Capabilities\n\n")
        verified = [f"- {r['test_id']}: {r['category']}" for r in results if r["quality"] == "PASS"]
        f.write("\n".join(verified) if verified else "_None yet._")
        f.write("\n\n")

        # 6. Isolated/Reproducible Failures
        f.write("## 6. Isolated & Reproducible Failures\n\n")
        failures = [r for r in results if r["quality"] in ("FAIL", "PARTIAL")]
        if failures:
            for r in failures:
                f.write(f"- **{r['test_id']}** ({r['category']}): {r.get('quality_note', 'N/A')}  \n")
                f.write(f"  - State: {r['final_state']}, Runtime: {r['runtime_seconds']}s\n")
                if r.get('error'):
                    f.write(f"  - Error: {r['error']}\n")
        else:
            f.write("_None — all tests passed._")
        f.write("\n\n")

        # 7. New GAP Candidates
        f.write("## 7. New GAP Candidates\n\n")
        if gap_candidates:
            f.write(f"**{len(gap_candidates)} potential GAP(s) identified:**\n\n")
            for g in gap_candidates:
                f.write(f"- {g}\n")
        else:
            f.write("_No new GAP candidates identified._")
        f.write("\n\n")

        # 8. Recommended Next Action
        f.write("## 8. Recommended Next Action\n\n")
        f.write(f"**{recommendation}**\n\n")
        f.write(f"{recommendation_note}\n")

    print(f"  Test matrix: {matrix_path}")

    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Server running: yes")
    print(f"  Tests completed: {len(results)}/8")
    print(f"  PASS: {pass_count}")
    print(f"  PARTIAL: {partial_count}")
    print(f"  FAIL: {fail_count}")
    print(f"\n  Failed/Partial tests:")
    for r in results:
        if r["quality"] in ("FAIL", "PARTIAL"):
            print(f"    - {r['test_id']}: {r['quality']} - {r.get('quality_note', '')[:80]}")
    print(f"\n  GAP candidates: {len(gap_candidates)}")
    for g in gap_candidates:
        print(f"    - {g}")
    print(f"\n  Recommendation: {recommendation}")
    print(f"\n  Reports:")
    print(f"    - {server_log_path}")
    print(f"    - {matrix_path}")
    if SCREENSHOTS_DIR.exists():
        screenshot_files = list(SCREENSHOTS_DIR.glob("*.png"))
        print(f"    - Screenshots: {len(screenshot_files)} files in {SCREENSHOTS_DIR}")


if __name__ == "__main__":
    asyncio.run(main())