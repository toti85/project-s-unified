# Project-S Live Test Verdict: B2 Local Model Research Mission
**Date:** 2026-05-14  
**Test conducted by:** GitHub Copilot (external observer)  
**Mission:** Run the existing stable SAI pipeline on a real external research task — no new features built first, no report written manually.

---

## A — Entry Point Used

`C:\ProjectS-Unified\interactive_task.py`  
→ Invokes `SuperIntelligentAI(use_meta_controller=True)` from `src/core/super_intelligent_ai.py`  
→ Uses `execute_intelligent_task(user_input, use_meta_controller=True)` with MetaController enabled (5 iterations, 120 s timeout, risk budget 2)

---

## B — Exact Command

```powershell
Start-Process -FilePath python `
  -ArgumentList "C:\ProjectS-Unified\interactive_task.py" `
  -WorkingDirectory "C:\ProjectS-Unified" `
  -RedirectStandardInput  "C:\Users\Admin\sai_b2_input.txt" `
  -RedirectStandardOutput "C:\Users\Admin\sai_b2_out.log" `
  -RedirectStandardError  "C:\Users\Admin\sai_b2_err.log" `
  -PassThru -WindowStyle Hidden
```

Input file (`sai_b2_input.txt`, 880 bytes, BOM-less UTF-8) contained the mission task + a bare `quit` line.

---

## C — Exact Project-S Mission Submitted

> Search the web for information about Qwen3.6-35B-A3B (a May 2026 MoE model with 35B params / 3B active) and other currently available 2026 local models including Gemma 4-31B, Llama 4 Scout, Mistral Small 3.1. Compare their coding and agentic task performance, VRAM requirements, and feasibility on a Tesla M60 16GB server. Search and find the SWE-bench scores and token throughput for each model. Write a comprehensive markdown decision memo to the file C:\ProjectS-Unified\reports\B2_LOCAL_MODEL_REALITY_CHECK_20260514.md that contains: 1) candidate models list with Qwen3.6-35B-A3B included, 2) comparison table of coding/agentic usefulness, deployability, hardware fit and integration risk, 3) distinction of confirmed facts vs assumptions, 4) sources used, 5) concrete recommendation: integrate now OR test later OR defer and stay cloud-first for Project-S on OpenRouter.

---

## D — Tools Actually Used / Observed

**Selected by Qwen3 235B strategic plan (correct selection):**
```
recommended_tools: ['web_search', 'web_scraper', 'file_writer']
```

**Execution outcomes:**

| Tool | Outcome | Detail |
|------|---------|--------|
| `web_search` | **FAILED** (fell back to mock) | `WebSearchTool.execute() missing 1 required positional argument: 'query'` — `_execute_single_tool` has no handler for `web_search`; the catch-all branch tried `execute(task=<description>)` which WebSearchTool does not accept |
| `web_scraper` | **FAILED** (fell back to mock) | `WebScraperTool.execute() missing 1 required positional argument: 'parameters'` — same cause |
| `file_writer` | **SUCCEEDED** (file created) | Regex path extraction from task description worked correctly; wrote the report stub to the specified path |

**Confirmed from logs:**
```
INFO  GAP_015: Using 3 recommended tools from strategic_plan: ['web_search', 'web_scraper', 'file_writer']
ERROR Real tool execution failed for web_search: WebSearchTool.execute() missing 1 required positional argument: 'query'
WARNING All real execution attempts failed for web_search, using mock result
ERROR Real tool execution failed for web_scraper: WebScraperTool.execute() missing 1 required positional argument: 'parameters'
WARNING All real execution attempts failed for web_scraper, using mock result
```

---

## E — Was the Report File Created?

**YES.** `C:\ProjectS-Unified\reports\B2_LOCAL_MODEL_REALITY_CHECK_20260514.md` was created (968 bytes, timestamp `2026-05-14 00:18`).

**But the contents are empty/boilerplate only:**
```markdown
# Strategic AI Report

Generated: 2026-05-14T00:18:11.460757

## Task
Search the web for information about Qwen3.6-35B-A3B...

## Results

```

The `## Results` section is blank — because `file_writer` in `_execute_single_tool` builds content from `accumulated_context` (output piped from previous tools), but both prior tools failed with mock results that produced no substantive text.

---

## F — Short Summary of Report Contents

The file is a 968-byte shell: a header, timestamp, the raw task text verbatim, and a blank `## Results` section. It contains zero research findings, no comparison table, no model data, no recommendation, and no sources cited. It is not a usable decision memo.

---

## G — Independent Spot-Checks of Factual Claims

The report has no factual claims to check because the Results section is empty.

Three independent checks were performed on the task subject to verify baseline facts for future use:

1. **Qwen3.6-35B-A3B real existence (May 2026)**  
   The model appears to be referenced in `PROJECT_S_OVERVIEW.md` within this repo with specific claims (SWE-bench 73.4%, 120–190 tok/s, runs on Tesla M60 16 GB with quantization). However, this is likely the project's own training-knowledge-derived content recycled into docs — the live web_search failed so there is no external confirmation. **Status: Unverified externally.**

2. **Tesla M60 VRAM spec (16 GB)**  
   Publicly documented: NVIDIA Tesla M60 has 2× 8 GB GDDR5 = 16 GB total, but configured as two separate 8 GB GPUs. Whether a single 16 GB unified pool is available depends on NVLink or VM passthrough configuration. The simple statement "16 GB" in the task hides a real hardware nuance. **Status: Partially confirmed (16 GB total, but not unified by default).**

3. **`web_search` parameter signature in the codebase**  
   Confirmed from `tools/tools/implementations/web_tools.py`: `WebSearchTool.execute(self, query, max_results=5, **kwargs)`. The `_execute_single_tool` fallback calls `execute(task=<description>)` or `execute(task_description=<description>)` — neither matches the `query` positional parameter. This is a reproducible, code-verifiable bug. **Status: Confirmed bug.**

---

## H — Tool and Pipeline Failures Observed

### H-1: Critical — `_execute_single_tool` Missing Handlers for Web Tools (NEW GAP)

**Affected tools:** `web_search`, `web_scraper`, `web_page_fetch`, `web_api_call`  
**Root cause:** `_execute_single_tool` in `smart_orchestrator.py` has explicit handlers for: `directory_lister`, `system_command`, `file_search`, `file_writer`, `file_content_search`, `pdf_generator`, `roblox_studio`. All other tools fall through to a catch-all that calls `execute(task=<description>)`. Web tools require specific positional arguments (`query`, `parameters`, `url`) that do not match `task=`. This is the same category of gap that GAP_010/GAP_015 addressed for file tools — it was never fixed for web tools.

**Impact:** Any research/web task will silently fall back to mock output regardless of what Qwen3 recommends.

### H-2: Minor — Unicode emoji in logger causes `UnicodeEncodeError` on Windows cp1251 console

`cp1251` codec cannot encode `\U0001f393` (graduation cap emoji) used in `meta_learn` logger. Non-blocking (caught by Python logging internals), but clutters stderr.

### H-3: Evaluator Action: `replan` (Not `pass`)

The evaluator correctly assessed the output as insufficient and set action to `replan`. However MetaController still returned `success=True` because `deterministic=True` is hardcoded in the completion check — the validator's failure (`confidence: 0.0%`) was overridden. This means the pipeline self-reports success even when the actual output is empty.

---

## I — Verdict

**FAIL**

The pipeline ran end-to-end without crashing, the entry point works, MetaController/StrategyCouncil/Evaluator all activated correctly, Qwen3 235B produced the correct tool selection, and the file_writer created the output file at the specified path. Those are genuine positives.

However, the task's core requirement — web research → content → report — was not accomplished. Both web tools failed silently due to a parameter mapping bug that was never fixed (only file tools received explicit handlers in `_execute_single_tool`). The produced report is an empty stub. The evaluator correctly flagged this as insufficient, but MetaController's `deterministic=True` override caused the pipeline to self-report success anyway.

**Summary score:**
| Component | Result |
|-----------|--------|
| System startup (15 tools, MetaController) | PASS |
| Qwen3 strategic planning (tool selection) | PASS |
| GAP_015 multi-tool routing | PASS |
| web_search actual execution | FAIL |
| web_scraper actual execution | FAIL |
| file_writer actual execution | PASS (partial — file created, content empty) |
| Report meets task requirements | FAIL |
| Self-reported status vs actual outcome | MISMATCH (SAI says success, output is empty) |

---

## J — Recommendation

**Keep the current toolset, but fix the web tool parameter mapping before any further live tests.**

The strategic planning layer (Qwen3 235B via OpenRouter) works well and correctly identifies the right tools. The file_writer handler works. The routing infrastructure (GAP_015, MetaController, evaluator) is functional.

The single highest-priority fix is:

### Fix: Add `web_search` and `web_scraper` handlers in `_execute_single_tool`

In `tools/tools/registry/smart_orchestrator.py`, inside `_execute_single_tool`, add explicit handlers analogous to the existing `file_writer` handler:

```python
elif tool_name == "web_search":
    import re as _re_ws
    # Extract query: strip "write a report to..." clause so query is clean
    task_clean = re.split(r'[Ww]rite\s+a?\s*(?:comprehensive|detailed|markdown)?\s*', task_description)[0].strip()
    real_result = await real_tool.execute(query=task_clean, max_results=10) \
        if asyncio.iscoroutinefunction(real_tool.execute) \
        else real_tool.execute(query=task_clean, max_results=10)

elif tool_name == "web_scraper":
    # Extract a URL if present, otherwise skip
    url_match = re.search(r'https?://[^\s]+', task_description)
    if url_match:
        real_result = await real_tool.execute(parameters={"url": url_match.group(0)}) \
            if asyncio.iscoroutinefunction(real_tool.execute) \
            else real_tool.execute(parameters={"url": url_match.group(0)})
    else:
        real_result = {"success": False, "output": "No URL in task for web_scraper"}
```

**Secondary recommendation:** Do NOT restore BrowserUse at this stage. The web scraping issue is a code-level parameter mapping problem, not a BrowserUse absence problem. Fix `_execute_single_tool` web handlers first, then re-run this same mission to confirm. BrowserUse adds significant complexity and would be harder to debug than a parameter fix.

**Tertiary recommendation:** Address the `deterministic=True` override in MetaController so that evaluator failures propagate correctly. Currently the system cannot detect its own web tool failures because the success flag is hardcoded.

---

## Appendix: Key Log Evidence

```
INFO  GAP_015: Using 3 recommended tools from strategic_plan: ['web_search', 'web_scraper', 'file_writer']
ERROR Real tool execution failed for web_search: WebSearchTool.execute() missing 1 required positional argument: 'query'
WARNING All real execution attempts failed for web_search, using mock result
ERROR Real tool execution failed for web_scraper: WebScraperTool.execute() missing 1 required positional argument: 'parameters'
WARNING All real execution attempts failed for web_scraper, using mock result
INFO  Logged evaluation result: eval_20260514_001811_495168
INFO  Handled evaluation result with action: replan
INFO  [MetaController] Goal achieved in 1 iterations (validator=False, deterministic=True)
Status: True  ← self-reported success despite empty output
```

```
Output:
Tool web_search processed (fallback mode)   ← the actual final output returned to user
```
