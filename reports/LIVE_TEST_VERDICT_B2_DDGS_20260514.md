# Live Test Verdict — B2 Rerun with DDGS Backend
**Date:** 2026-05-14  
**Prior Verdict (DDGS-unpatched run):** PARTIAL (web search returned 0 results; Google blocked)  
**This Verdict:** PASS

---

## A. Files Changed

| File | Change |
|------|--------|
| `tools/tools/implementations/web_tools.py` | Replaced `WebSearchTool` body — removed brittle Google HTML scraper; implemented DDGS-based backend as sole search path |
| `tests/test_web_search_tool.py` | **New file** — 15 focused unit tests for the DDGS WebSearchTool |

---

## B. Dependency Added

```
ddgs==9.14.2
primp==1.2.3  (transitive dependency of ddgs)
```

**Install command:** `pip install ddgs`

The `ddgs` package (formerly `duckduckgo-search`) uses the `primp` HTTP client, which handles TLS fingerprinting to avoid bot detection. No API key required.

---

## C. Test Results

```
26 passed, 5 warnings in 20.91s
```

| Test suite | Tests | Result |
|-----------|-------|--------|
| `tests/test_web_search_tool.py` | 15 | PASS |
| `tests/test_gap_017_018_web_tools.py` | 11 | PASS |
| **Total** | **26** | **PASS** |

### New test coverage (test_web_search_tool.py):

| Class | Tests |
|-------|-------|
| `TestWebSearchQuery` | query passed correctly; max_results forwarded |
| `TestWebSearchSchema` | top-level keys; result item keys; href→url mapping; body→description mapping; query echoed |
| `TestWebSearchZeroResults` | empty list → success=True, count=0; None return → success=False |
| `TestWebSearchException` | backend exception → success=False; error key present |
| `TestWebSearchMalformedResults` | no-href results skipped; non-dict skipped; missing title defaults ""; missing body defaults "" |

---

## D. Live Rerun Verdict: PASS

### Execution Summary

- **Status reported by SAI:** `True`
- **MetaController:** Goal achieved in **1 iteration** (vs 5 failed iterations previously)
- **Evaluator action:** `continue` (not `replan`)
- **Tools executed:** `web_search` → `web_scraper` → `file_writer`

### Tool Execution Outcomes

| Tool | Outcome |
|------|---------|
| `web_search` | 10 real results returned (Brave, DuckDuckGo, Mojeek backends) |
| `web_scraper` | Successfully scraped `apxml.com/models/qwen36-35b-a3b` (first search result URL) |
| `file_writer` | Wrote 6,587-char report to target path |

### DDGS backend activity observed in logs:

```
INFO [primp] response: https://html.duckduckgo.com/html/ 200
INFO [primp] response: https://search.brave.com/search?q=... 200
INFO [primp] response: https://www.mojeek.com/... 403  (fallback handled)
```

---

## E. Generated Report

**Path:** `C:\ProjectS-Unified\reports\B2_LOCAL_MODEL_REALITY_CHECK_20260514.md`  
**Size:** 6,587 characters

### Grounded Facts Present (spot-checks)

1. **Qwen3.6-35B-A3B SWE-bench score: 73.4%** — confirmed from dev.to and buildfastwithai.com
2. **Gemma 4-31B SWE-bench score: 17.4%** — confirmed from same source; noted as 4x lower with 10x more active params
3. **Release date: April 16, 2026** — confirmed from aibase.com and marktechpost.com
4. **Architecture: 256 experts, 8 routed + 1 shared per token** — confirmed from marktechpost.com
5. **10 unique source URLs** with titles and snippets, including: Hugging Face, Ollama, AWS Bedrock, dev.to, buildfastwithai.com, insiderllm.com, progressiverobot.com, zoliben.com, aibase.com, marktechpost.com

### Content Structure Note

The file is the SAI's accumulated tool output written directly (web_search formatted results + web_scraper extracted data). It is **not** a fully formatted decision memo with comparison table and recommendation sections. The SAI's `file_writer` wrote what the tools returned rather than synthesising the data into the requested memo structure.

**This is a content synthesis gap in the AI pipeline, not a tool connectivity failure.** The original task requirements (comparison table, VRAM analysis, explicit recommendation) require the AI to transform raw search data into structured prose — which requires a separate synthesis step that the current `file_writer` handler does not perform.

---

## F. Before/After Comparison

| Metric | Run 1 (no fix) | Run 2 (GAP_017+018 fix) | Run 3 (DDGS backend) |
|--------|----------------|--------------------------|----------------------|
| TypeError on web_search | YES | NO | NO |
| web_search results count | 0 | 0 | 10 |
| web_scraper executed | NO | NO | YES (1 page) |
| Report file size | ~1,060 chars stub | ~1,060 chars stub | 6,587 chars |
| Real grounded content | NO | NO | YES |
| Status truthfulness | FALSE (True when failed) | CORRECT (False) | CORRECT (True) |
| MetaController iterations | 1 (false positive) | 5 exhausted | 1 (genuine success) |
| Verdict | FAIL | PARTIAL | PASS |

---

## G. Implementation Design Decisions

**Option A chosen (full replacement):** The Google HTML scraper was removed entirely. There was no value in keeping it as a fallback — it reliably returns 0 results on this IP due to bot detection. DDGS uses the `primp` TLS-fingerprint-spoofing HTTP client which successfully reaches Brave, DuckDuckGo, and Mojeek backends without an API key.

**Thread-executor pattern:** DDGS is synchronous. The `execute` method is `async`, so `_ddgs_search` is dispatched via `asyncio.get_event_loop().run_in_executor(None, ...)` to avoid blocking the event loop.

**Return schema preserved:** The existing schema (`success`, `query`, `results[{title, url, description}]`, `count`) is unchanged. The orchestrator's GAP_017 handler and the test suite both rely on this schema.

---

## H. Remaining Gap (Out of Scope for this Task)

The report contains raw tool output, not a structured decision memo. To produce the comparison table and recommendation sections, the pipeline would need a synthesis step: pass accumulated search data to an LLM and request a structured markdown document. This is a planning/synthesis gap in the `file_writer` handler, not a search tool defect.
