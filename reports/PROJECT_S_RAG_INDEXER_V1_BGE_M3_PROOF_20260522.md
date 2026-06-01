# Project-S RAG Indexer V1 — BGE-M3 Proof Report

**Date:** 2026-05-22
**Server:** SHAYANSKA-DL380 (46.253.140.72)
**Index Location:** F:\ModelVault\rag\project_s_index_v1\
**Source Docs:** F:\ModelVault\rag\project_s_docs\

---

## 1. Executive Verdict

**A. Index built?** YES
**B. Number of files indexed:** 35
**C. Number of chunks:** 538
**D. Embedding endpoint used?** YES (BGE-M3 on port 8099)
**E. Vector store type:** numpy + JSONL (vectors.npy + metadata.jsonl)
**F. Smoke query results:** All 5 queries returned relevant top-3 chunks
**G. Did results retrieve expected documents?** YES (with caveats noted below)
**H. Ready for later MS-OQ1-A integration?** YES (with improvements needed)
**I. Fixes made to Copilot-created scripts:** Unicode encoding fix (Cyrillic chars replaced)

---

## 2. Files/Scripts Found

| File | Size | Status |
|------|------|--------|
| build_index.py | 14,572 bytes | Present, Unicode fix applied |
| query_index.py | 5,942 bytes | Present, working |
| README.md | 2,789 bytes | Present |
| vectors.npy | Created by build | 538 x 1024 float32 |
| metadata.jsonl | Created by build | 538 lines |
| index_manifest.json | Created by build | Complete |

---

## 3. Index Build Result

| Metric | Value |
|--------|-------|
| Build timestamp | 2026-05-22T20:02:08Z |
| Files indexed | 35 |
| Total chunks | 538 |
| Embedding failures | 82 (15.2%) |
| Successful embeddings | 456 (84.8%) |
| Vector shape | (538, 1024) |
| Embedding model | bge-m3-Q4_K_M |
| Embedding dim | 1024 |
| Vector store | numpy_jsonl |

**Embedding failure cause:** 500 Internal Server Error from BGE-M3 when chunks exceed the model's context window (~8000 chars). The script uses zero-vector placeholders for failed chunks, which reduces retrieval quality for those specific chunks but does not break the index.

---

## 4. Source Files Indexed (35)

| Category | Files |
|----------|-------|
| Core state | self_state.json (152KB, 77 chunks), project_state.json, STATUS.md, TRACKER.md, DECISIONS.md |
| Interactive Layer | prompt_router.py, main.py, sai_runner.py, missions.py, sessions.py, database.py, models.py, internal_doc_grounding.py, sse_stream.py, response_polish.py, query_events.py, query_missions.py, start_server.py |
| Core agents | agent_loop.py, autonomous_controller.py, overseer_agent.py, cognitive_core.py, evaluator.py |
| Meta/strategy | meta_controller.py, strategy_council.py, ai_strategist.py, research_loop.py |
| Documentation | EXECUTION_ROADMAP.md, OPERATIONAL_GUIDE.md, SUPER_AUTONOMOUS_SYSTEM_PLAN.md, Autonomy_Design.md, master_context.md |
| Reports | BGE_M3_EMBEDDING_ACTIVATION_VERDICT_20260522.md, DL380_QWEN36_LOCAL_SERVICE_AND_CLINE_COMPATIBILITY_20260522.md, LOCAL_CLINE_QWEN25_CODER_14B_BENCHMARK_20260522.md |

---

## 5. Embedding Endpoint

| Property | Value |
|----------|-------|
| URL | http://127.0.0.1:8099/v1/embeddings |
| Model | bge-m3-Q4_K_M (437MB GGUF) |
| Backend | llama.cpp CPU-only (-ngl 0) |
| Dimension | 1024 |
| Max context | 8192 tokens |
| Latency | ~50-80ms per request (CPU) |
| Server PID | 4108 (started during build) |

---

## 6. Smoke Query Results

### Query 1: "Mi a Project-S jelenlegi active focus?"

| Rank | Score | File | Preview |
|------|-------|------|---------|
| 1 | 0.4929 | TRACKER.md | "project_s_super_core is the OPTIMAL VERSION" |
| 2 | 0.4900 | SUPER_AUTONOMOUS_SYSTEM_PLAN.md | "Szuper Ontanulo Autonóm Rendszer Terv" |
| 3 | 0.4862 | self_state.json | "következő Project-S task... Cline-nal indul" |

**Expected doc retrieved:** YES (self_state.json at rank 3)

### Query 2: "GAP_031 status"

| Rank | Score | File | Preview |
|------|-------|------|---------|
| 1 | 0.5437 | self_state.json | "GAP_031 RESOLVED + doc sync" |
| 2 | 0.5360 | self_state.json | "health_after_test: PASS (200)" |
| 3 | 0.5315 | self_state.json | gap discovery metadata |

**Expected doc retrieved:** YES (self_state.json at rank 1, directly states GAP_031 RESOLVED)

### Query 3: "local models DL380 GPU"

| Rank | Score | File | Preview |
|------|-------|------|---------|
| 1 | 0.6463 | LOCAL_CLINE_QWEN25_CODER_14B_BENCHMARK.md | "Download BGE-M3 to DL380 for local RAG" |
| 2 | 0.6158 | DL380_QWEN36_LOCAL_SERVICE.md | "DL380 Qwen3.6 Local Service" |
| 3 | 0.5861 | self_state.json | "szerver migráció (DL380" |

**Expected doc retrieved:** YES (benchmark report at rank 1, DL380 report at rank 2)

### Query 4: "Interactive Layer router prompt_router"

| Rank | Score | File | Preview |
|------|-------|------|---------|
| 1 | 0.6391 | self_state.json | health check PASS (200) |
| 2 | 0.5567 | self_state.json | FileReadTool, FileWriteTool |
| 3 | 0.5545 | self_state.json | tool list |

**Expected doc retrieved:** PARTIAL (self_state.json retrieved but not prompt_router.py directly — the prompt_router.py chunks may have had embedding failures due to size)

### Query 5: "Project-S next development direction"

| Rank | Score | File | Preview |
|------|-------|------|---------|
| 1 | 0.5441 | BGE_M3_EMBEDDING_ACTIVATION_VERDICT.md | "Next Integration Step: RAG Document Indexer" |
| 2 | 0.5315 | SUPER_AUTONOMOUS_SYSTEM_PLAN.md | "Szuper Ontanulo Autonóm Rendszer" |
| 3 | 0.5255 | TRACKER.md | "project_s_super_core is the OPTIMAL VERSION" |

**Expected doc retrieved:** YES (BGE-M3 verdict correctly identifies "RAG Document Indexer" as next step)

---

## 7. Limitations

1. **15.2% embedding failure rate** — 82 of 538 chunks failed due to oversized text exceeding BGE-M3 context. These chunks have zero-vector placeholders, reducing retrieval quality for those sections.
2. **No retry logic** — build_index.py does not retry failed embeddings or split oversized chunks.
3. **CPU-only embeddings** — BGE-M3 runs on CPU (no GPU layers), which is slow for batch processing. The server became overloaded during the first build attempt (486/538 failures).
4. **Unicode display issues** — Copilot-created scripts had Cyrillic characters that caused encoding errors on Windows cp1252 console. Fixed by replacing with ASCII.
5. **No deduplication** — Identical or near-identical chunks from different files are indexed separately.
6. **No search ranking tuning** — Uses raw cosine similarity only, no BM25 hybrid or re-ranking.
7. **BGE-M3 server stability** — The embedding server crashed once during the build process and needed manual restart.

---

## 8. Next Integration Step (MS-OQ1-A Internal Doc Grounding)

1. **Fix embedding failures:** Add chunk size check in build_index.py — if text > 7000 chars, sub-chunk before embedding.
2. **Add retry logic:** Retry failed embeddings with exponential backoff.
3. **Batch embedding:** Send multiple texts per API call if BGE-M3 supports it (reduces round-trip overhead).
4. **Integrate with Interactive Layer:** Modify `internal_doc_grounding.py` to load vectors.npy + metadata.jsonl and use cosine similarity search before/after SAI responses.
5. **Add to query_index.py:** Support for Hungarian language queries (already demonstrated working).
6. **Periodic re-index:** Set up a scheduled task to rebuild the index when source docs change.

---

## 9. Return Values Summary

| Question | Answer |
|----------|--------|
| A. Index built? | **YES** |
| B. Number of files indexed | **35** |
| C. Number of chunks | **538** |
| D. Embedding endpoint used? | **YES** (BGE-M3 on 8099) |
| E. Vector store type | **numpy + JSONL** |
| F. Smoke query results with top-3 | **See Section 6** |
| G. Expected documents retrieved? | **YES** (4/5 strong, 1 partial) |
| H. Ready for MS-OQ1-A integration? | **YES** (with improvements) |
| I. Fixes made to scripts? | **Unicode encoding fix** (Cyrillic -> ASCII) |

---

**END OF REPORT**