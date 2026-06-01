#!/usr/bin/env python3
"""
legacy_golden_recovery/launchers/run_example_browser_test.py

Minimális élő browser teszt a 2026-02-19 pipeline mintájára.
- Task: Navigate to https://example.com, return title + first 500 chars
- Browser: Playwright Chromium (headless)
- Model: OpenRouter gpt-4o-mini (vagy qwen3-235b)
- Output: legacy_golden_recovery/reports/browser_test_report.md

Futtatás:
  cd C:\ProjectS-Unified
  python legacy_golden_recovery\launchers\run_example_browser_test.py
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# Paths
WORKSPACE_ROOT = Path(__file__).parent.parent.parent
REPORTS_DIR = Path(__file__).parent.parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

sys.path.insert(0, str(WORKSPACE_ROOT / "src"))
sys.path.insert(0, str(WORKSPACE_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

TASK = """
Navigate to https://example.com
Extract:
1. The page title (the <title> tag text)
2. The first 500 characters of visible text content
3. Any links found on the page

Return results as JSON:
{
  "title": "page title here",
  "text_preview": "first 500 chars of text",
  "links": ["link1", "link2"]
}
"""

async def main():
    start_time = datetime.now()
    success = False
    error_msg = None
    browser_result = None
    ai_analysis = None

    logger.info("=" * 72)
    logger.info("LIVE BROWSER TEST — example.com scrape + AI analysis")
    logger.info(f"Timestamp: {start_time.isoformat()}")
    logger.info("=" * 72)

    try:
        # Step 1: Initialize components (same as meta_launcher_browser.py)
        logger.info("\n[STEP 1] Initializing AIClient...")
        from src.integrations.ai_models.multi_model_ai_client import AIClient
        ai_client = AIClient()
        logger.info("✓ AIClient initialized")

        # Step 2: Initialize ToolRegistry
        logger.info("\n[STEP 2] Initializing ToolRegistry...")
        from tools.tools.registry.tool_registry_golden import ToolRegistry
        registry = ToolRegistry()
        tool_count = len(registry.tools) if hasattr(registry, 'tools') else '?'
        logger.info(f"✓ ToolRegistry initialized ({tool_count} tools)")

        # Step 3: Get BrowserAutomationTool
        logger.info("\n[STEP 3] Getting BrowserAutomationTool from registry...")
        browser_tool = registry.tools.get("browser_automation")
        if not browser_tool:
            raise RuntimeError(f"browser_automation not in registry. Keys: {list(registry.tools.keys())}")
        logger.info(f"✓ BrowserAutomationTool found: {type(browser_tool).__name__}")

        # Step 4: Execute browser task
        logger.info("\n[STEP 4] Executing browser task on https://example.com ...")
        logger.info("  Browser: Chromium (headless)")
        logger.info("  Timeout: 60s")

        try:
            browser_result = await browser_tool.execute(
                task=TASK,
                headless=True,
                timeout=60,
                screenshot=False
            )
            logger.info(f"✓ Browser task completed")
            logger.info(f"  Result type: {type(browser_result)}")
            if isinstance(browser_result, dict):
                logger.info(f"  Success: {browser_result.get('success', 'unknown')}")
                logger.info(f"  Output length: {len(str(browser_result.get('output', '')))} chars")
        except Exception as e:
            logger.error(f"Browser execution error: {e}")
            browser_result = {"success": False, "error": str(e), "output": ""}

        # Step 5: AI analysis of browser output
        scraped_text = ""
        if isinstance(browser_result, dict):
            scraped_text = str(browser_result.get("output", browser_result.get("extracted_data", browser_result)))
        else:
            scraped_text = str(browser_result)

        logger.info(f"\n[STEP 5] AI analysis of scraped data ({len(scraped_text)} chars)...")
        logger.info("  Model: gpt-4o-mini (OpenRouter)")

        analysis_prompt = f"""The following text was scraped from https://example.com using a real Chromium browser.

SCRAPED DATA:
{scraped_text[:2000]}

Please analyze this data and confirm:
1. Was example.com successfully loaded? (yes/no)
2. What is the page title?
3. What is the main content/purpose of the page?

Return a brief JSON response:
{{
  "loaded": true/false,
  "title": "...",
  "content_summary": "...",
  "data_quality": "good/partial/failed"
}}"""

        try:
            ai_analysis = await ai_client.generate_response(
                prompt=analysis_prompt,
                model="gpt-4o-mini",
                system_message="You are a web scraping analyst. Analyze scraped data and provide structured JSON responses.",
                task_type="analysis",
                temperature=0.1,
                max_tokens=500
            )
            logger.info(f"✓ AI analysis completed")
            logger.info(f"  Response length: {len(str(ai_analysis))} chars")
            logger.info(f"  Preview: {str(ai_analysis)[:150]}")
        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            ai_analysis = f"AI ERROR: {e}"

        success = bool(
            browser_result and
            (isinstance(browser_result, dict) and browser_result.get("success", False) or
             isinstance(browser_result, str) and len(browser_result) > 50)
        )

    except Exception as e:
        import traceback
        logger.error(f"Pipeline error: {e}")
        traceback.print_exc()
        error_msg = str(e)

    # Generate report
    elapsed = (datetime.now() - start_time).total_seconds()
    timestamp = start_time.strftime("%Y-%m-%d %H:%M:%S")

    report_lines = [
        "# Browser Test Report — Live Pipeline",
        f"**Timestamp:** {timestamp}",
        f"**Execution Time:** {elapsed:.2f}s",
        f"**Task:** Navigate to https://example.com, extract title + text",
        f"**Model:** openai/gpt-4o-mini via OpenRouter",
        f"**Browser:** Chromium (Playwright, headless=True)",
        "",
        "## Result",
        "",
        f"**Overall Status:** {'✓ PASS' if success else '✗ FAIL'}",
        "",
        "## Browser Output",
        "",
        "```",
        str(browser_result)[:1500] if browser_result else "(none)",
        "```",
        "",
        "## AI Analysis",
        "",
        "```",
        str(ai_analysis)[:1000] if ai_analysis else "(none)",
        "```",
        "",
    ]

    if error_msg:
        report_lines += [
            "## Error",
            "",
            f"```",
            error_msg,
            "```",
            "",
        ]

    report_lines += [
        "## Technical Details",
        "",
        f"- Framework: Project-S meta_launcher_browser pattern",
        f"- AIClient: `src/integrations/ai_models/multi_model_ai_client.py`",
        f"- ToolRegistry: `tools/tools/registry/tool_registry_golden.py`",
        f"- BrowserTool: `browser_automation` (Playwright + browser-use)",
        f"- Execution time: {elapsed:.2f}s",
        "",
        "## Pipeline Proof",
        "",
        "This test replicates the **2026-02-19 architecture** that produced:",
        "`browser_automation_report_20260219_081337.md` (Success=True, 190.2s)",
        "",
        f"*Generated: {timestamp}*",
    ]

    report_path = REPORTS_DIR / "browser_test_report.md"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    logger.info("\n" + "=" * 72)
    logger.info(f"LIVE BROWSER TEST — {'PASS' if success else 'FAIL'}")
    logger.info(f"Elapsed: {elapsed:.2f}s")
    logger.info(f"Report: {report_path}")
    logger.info("=" * 72)

    return success


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
