# AO9_T7B — Cline Onboarding Summary

Date: 2026-07-14 (written during Phase A context recovery)
Author: Cline (joining measurement thread in progress)

---

## 1. What We've Been Measuring

The AO9 measurement chain evaluates **executor cells** — model + adapter combinations — running a **chunk-merge-verify** pattern against a frozen 77-finding classification task. The task is to take a canonical scan of TODO/FIXME markers across the Project-S codebase (501 files scanned, 12 files with findings, 77 total findings) and produce structured JSON output with severity classifications.

The pattern is:
- **Chunk**: Split findings into groups, send each to the model
- **Merge**: Combine chunk outputs into a single JSON array
- **Verify**: Check completeness, deduplication, and schema conformance

Outcomes are classified using the **AO8N 7-state outcome model** (execution_status, handoff_status, artifact_status, verification_status, quality_status, merge_ready, outcome_confidence).

---

## 2. What the T5_RUN4 Baseline Established

**Ornith Cell — PASS (Scenario A)**

| Dimension | Value |
|-----------|-------|
| Model | Ornith-1.0-9B Q4_K_M (local, small) |
| Adapter | Custom Python adapter (ornith_adapter.py) |
| Endpoint | localhost:8766 (llama.cpp) |
| Chunking | 3 chunks (25 + 25 + 27 findings) |
| Chunk 1 | PASS / 158.09s / 2,564 tokens / 16.2 tps |
| Chunk 2 | PASS / 145.68s / 2,415 tokens / 16.6 tps |
| Chunk 3 | PASS / 183.45s / 3,000 tokens / 16.4 tps |
| Total latency | 487s |
| Cost | $0 (local) |
| Reconciliation | 77/77, zero duplicates, no missing indices |
| merge_ready | True |
| Checks passed | 11/11 |
| Classification | PASS |

T5_RUN4 established that the chunk-merge-verify pattern works with a small local model when using a custom-tuned adapter. It also created the frozen input file `scan_canonical.json` (77 findings) that all subsequent cells use.

---

## 3. What T6 Found and Why It Was Invalidated

**Aider + Ornith LOCAL — FAIL (later reclassified as INVALID)**

| Dimension | Value |
|-----------|-------|
| Model | Ornith-1.0-9B Q4_K_M (SAME as T5) |
| Adapter | Aider CLI 0.86.2 (instead of custom adapter) |
| Endpoint | localhost:8766 (SAME) |
| Chunking | 3 chunks (SAME) |
| Chunk 1 | FAIL / 300.01s timeout / no file created |
| Chunk 2 | PASS / 262.97s / file created, JSON valid |
| Chunk 3 | FAIL / 300.01s timeout / file created but JSON invalid |
| Total latency | 863s (partial) |
| Cost | $0 (local) |
| Reconciliation | 25/77 (only Chunk 2 data survived) |
| merge_ready | False |
| Classification | SCENARIO C — FAIL |

**Invalidation reason**: Aider CLI is designed for large cloud models. Ornith-1.0-9B is a small local model. The timeouts were caused by a **model-class mismatch**, not an adapter failure. The comparison was confounded — the variable under test was supposed to be the adapter, but the model class was incompatible with the adapter's design assumptions.

T6 result is **DISCARDED** as a measurement of Aider capability. It is retained as a finding about adapter-model compatibility requirements.

---

## 4. What T7a Is/Was Measuring

**Aider + DeepSeek V4 Flash via OpenRouter — CHUNKED (T7a)**

| Dimension | Value |
|-----------|-------|
| Model | DeepSeek V4 Flash (large cloud model) |
| Model string | `openai/deepseek/deepseek-v4-flash` |
| Adapter | Aider CLI 0.86.2 (native configuration) |
| Endpoint | https://openrouter.ai/api/v1 |
| Chunking | 3 chunks (SAME pattern) |
| Chunk 1 | PASS / 144.54s |
| Chunk 2 | PASS / 126.08s |
| Chunk 3 | PASS / 183.68s |
| Total latency | 454s |
| Cost | $0.0000 (estimated — token usage not captured) |
| Reconciliation | 77/77, zero duplicates, no missing indices |
| merge_ready | True |
| Checks passed | 11/11 |
| Classification | **SCENARIO A — PASS** |

**Status**: T7a execution log confirms PASS. The chunk-merge-verify pattern IS portable to Aider + cloud when the model is a native fit (large cloud model, Aider's intended use case).

T7a invalidates the T6 conclusion: the earlier failure was not "Aider doesn't work with chunk-merge-verify" but rather "Aider doesn't work with small local models." With a properly matched model, Aider is a valid executor.

Two valid cells now confirmed: Ornith custom adapter (T5_RUN4) and Aider + cloud chunked (T7a).

---

## 5. What T7b (This Mission) Will Measure

**T7b — Aider + DeepSeek V4 Flash via OpenRouter — SINGLE PROMPT**

Same everything as T7a EXCEPT chunking strategy:

| Parameter | T7a (Chunked) | T7b (Single Prompt) |
|-----------|---------------|---------------------|
| Model | DeepSeek V4 Flash | DeepSeek V4 Flash (SAME) |
| Endpoint | OpenRouter | OpenRouter (SAME) |
| Adapter | Aider CLI 0.86.2 | Aider CLI 0.86.2 (SAME) |
| Flags | --no-git --yes-always --no-check-update --no-show-model-warnings | SAME |
| Input | scan_canonical.json (77 findings) | scan_canonical.json (77 findings, SAME) |
| Output schema | Structured JSON array | Structured JSON array (SAME) |
| **Chunk strategy** | **3 chunks** (25 + 25 + 27) | **SINGLE PROMPT** (all 77 in one call) |
| Expected token load | ~2,500-3,000 per chunk | ~15,000-30,000 input + ~5,000-10,000 output |
| Expected cost | ~$0.00 (not captured) | ~$0.10-0.30 |

The model has a 1,048,576 token context window, so the single prompt is well within limits.

---

## 6. Why T7b Matters — The Hypothesis

**The core question**: Is the chunk-merge-verify architecture a **general pattern** required for reliable model task execution, or is it **compensation for small-model context limits**?

**Two competing hypotheses:**

| Hypothesis | If True | Implication |
|------------|---------|-------------|
| **Chunking is a general pattern** | T7b single-prompt FAILS (or quality degrades) | Chunking provides inherent quality benefit regardless of model size. Even with large context, splitting work improves reliability. |
| **Chunking is a small-model workaround** | T7b single-prompt PASSES (77/77, valid JSON, no issues) | Chunking was compensating for Ornith's 9B context limits. With large cloud models, single-prompt is simpler, cheaper, and equally effective. |

**Strategic importance**:
- If T7b PASSES → the "Large ≠ Single Prompt" principle from T5_RUN4 needs revision: "Large ≠ Single Prompt on small local models" but cloud models can handle full tasks.
- If T7b FAILS → the original principle stands: chunking is a general quality pattern, relevant at all scales.

**This test is designed to challenge the chunk architecture hypothesis, not confirm it.** Both outcomes are valuable.

---

## 7. Constraint: Same Everything Except Chunking

| Dimension | Constraint | Status |
|-----------|------------|--------|
| Model | DeepSeek V4 Flash (same exact string as T7a) | Must verify |
| Endpoint | OpenRouter (same) | Same |
| Adapter | Aider CLI 0.86.2 (same flags) | Same |
| Input file | scan_canonical.json (77 findings, frozen) | Same |
| Output schema | Structured JSON array (same structure) | Same |
| **Chunking** | **SINGLE PROMPT (different from T7a's 3 chunks)** | **Isolated variable** |
| Model string | `openai/deepseek/deepseek-v4-flash` | Must match T7a exactly |

This isolates the chunk dimension — the only variable changed between T7a and T7b.

---

## Files Read During Phase A

| File | Status |
|------|--------|
| reports/AO9_T5_RUN4_*.md | NOT FOUND (standalone) — data inferred from T6 comparison and result file |
| reports/AO9_T6_AIDER_CELL_DEFINITION_20260712.md | READ |
| reports/AO9_T6_ORNITH_VS_AIDER_COMPARISON_20260712.md | READ |
| reports/AO9_T6_AIDER_EXECUTION_LOG_20260712.md | READ |
| reports/AO9_T7_AIDER_CLOUD_CELL_DEFINITION_20260713.md | READ |
| reports/AO9_T7_AIDER_CLOUD_EXECUTION_LOG_20260713.md | READ |
| reports/AO9_T7_COST_REPORT_20260713.md | READ |
| reports/AO9_T7_THREE_CELL_COMPARISON_20260713.md | READ |
| reports/AO8N_5_STRUCTURED_OUTCOME_MODEL_20260701.md | READ |
| reports/AO8N_6_OUTCOME_CONFIDENCE_REPAIR_20260701.md | READ |
| orchestrator_runtime/sandbox/ornith_executor_trial/ao9_t5_run4/scan_canonical.json | READ (77 findings) |
| orchestrator_runtime/sandbox/ornith_executor_trial/ao9_t5_run4/ao9_t5_run4_result.json | READ (T5_RUN4 baseline confirmed) |

---

**Phase A complete. Awaiting Toti confirmation before proceeding to Phase B execution.**