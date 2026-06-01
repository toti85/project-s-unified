# Browser Test Report — Live Pipeline
**Timestamp:** 2026-04-29 16:11:48
**Execution Time:** 67.16s
**Task:** Navigate to https://example.com, extract title + text
**Model:** openai/gpt-4o-mini via OpenRouter
**Browser:** Chromium (Playwright, headless=True)

## Result

**Overall Status:** ✓ PASS

## Browser Output

```
{'success': True, 'result': AgentHistoryList(all_results=[ActionResult(is_done=False, success=None, error=None, attachments=None, long_term_memory='Navigated to https://example.com', extracted_content='🔗 Navigated to https://example.com', include_extracted_content_only_once=False, include_in_memory=True), ActionResult(is_done=False, success=None, error=None, attachments=None, long_term_memory='Page Link: https://example.com/\nQuery: Extract the page title, the first 500 characters of visible text content, and any links found on the page.\nExtracted Content:\n```json\n{\n  "page_title": "Example Domain",\n  "visible_text_content": "This domain is for use in documentation examples without needing permission. Avoid use in operations.",\n  "links": [\n    {\n      "text": "Learn more",\n      "url": "https://iana.org/domains/example"\n    }\n  ]\n}\n```', extracted_content='Page Link: https://example.com/\nQuery: Extract the page title, the first 500 characters of visible text content, and any links found on the page.\nExtracted Content:\n```json\n{\n  "page_title": "Example Domain",\n  "visible_text_content": "This domain is for use in documentation examples without needing permission. Avoid use in operations.",\n  "links": [\n    {\n      "text": "Learn more",\n      "url": "https://iana.org/domains/example"\n    }\n  ]\n}\n```', include_extracted_content_only_once=False, include_in_memory=False), ActionResult(is_done=False, success=None, error=None, attachments=None, long_term
```

## AI Analysis

```
(none)
```

## Technical Details

- Framework: Project-S meta_launcher_browser pattern
- AIClient: `src/integrations/ai_models/multi_model_ai_client.py`
- ToolRegistry: `tools/tools/registry/tool_registry_golden.py`
- BrowserTool: `browser_automation` (Playwright + browser-use)
- Execution time: 67.16s

## Pipeline Proof

This test replicates the **2026-02-19 architecture** that produced:
`browser_automation_report_20260219_081337.md` (Success=True, 190.2s)

*Generated: 2026-04-29 16:11:48*