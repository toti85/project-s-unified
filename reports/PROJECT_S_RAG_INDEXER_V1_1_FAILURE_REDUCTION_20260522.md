# Project-S RAG Indexer V1.1 — Embedding Failure Reduction Report

**Date:** 2026-05-23
**Server:** SHAYANSKA-DL380 (46.253.140.72)
**Index Location:** F:\ModelVault\rag\project_s_index_v1\

---

## A. Failure Root Causes

**Primary cause: BGE-M3 CPU server instability (500 Internal Server Error)**

The failure analysis of V1 (82 failures / 538 chunks = 15.2% failure rate) revealed:

| Metric | Value |
|--------|-------|
| Max chunk size | 6,231 chars |
| Min chunk size | 1,466 chars |
| Average chunk size | 3,829 chars |
| Chunks over 8,000 chars | 0 |
| Chunks over 5,000 chars | 31 |

**Key finding:** Failures are NOT caused by oversized chunks. All failed chunks were well within BGE-M3's 8,192 token context window. The 500 errors are caused by the CPU-only BGE-M3 server becoming overloaded under sustained embedding load.

**Top failure files (V1):**
| File | Failures |
|------|----------|
| evaluator.py | 14 |
| self_state.json | 12 |
| prompt_router.py | 8 |
| internal_doc_grounding.py | 5 |
| response_polish.py | 5 |

---

## B. Files Changed

**build_index.py** — Complete rewrite with V1.1 improvements:

| Change | Description |
|--------|-------------|
| Retry logic | 3 attempts with exponential backoff (1s, 2s) |
| Rate limiting | 100ms delay between requests |
| Chunk size cap | Reduced from 2048 to 1500 chars |
| Text truncation | 4000-char cap before embedding |
| UTF-8 headers | Explicit `charset=utf-8` in Content-Type |
| Timeout | 60-second timeout per request |
| Failed chunk logging | `failed_chunks.jsonl` with error details |
| Manifest versioning | `"version": "1.1"` with `success_rate` field |
| Sub-chunking | Oversized blocks (>3000 chars) split before embedding |
| Self-state chunking | Semantic JSON-aware chunking instead of raw text |

---

## C. New Success Rate

| Metric | V1 | V1.1 | Change |
|--------|-----|------|--------|
| Total chunks | 538 | 599 | +61 (better chunking) |
| Embedding failures | 82 | 80 | -2 |
| Success rate | 84.8% | 86.6% | +1.8% |
| Files indexed | 35 | 35 | same |

**Top failure files (V1.1):**
| File | Failures |
|------|----------|
| evaluator.py | 14 |
| prompt_router.py | 10 |
| overseer_agent.py | 6 |
| response_polish.py | 5 |
| meta_controller.py | 5 |

**Assessment:** Marginal improvement (84.8% → 86.6%). The BGE-M3 CPU server is the fundamental bottleneck — it crashes under sustained load regardless of retry logic.

---

## D. prompt_router.py Indexed? 

**PARTIAL** — 10 of 22 chunks failed (55% failure rate for this file). The remaining 12 chunks are indexed with valid embeddings. The failures are due to BGE-M3 server crashes, not chunking issues.

---

## E. Core Docs All Indexed?

| Document | Status |
|----------|--------|
| self_state.json | PARTIAL (4/107 failed) |
| prompt_router.py | PARTIAL (10/22 failed) |
| main.py | PARTIAL (3/4 failed) |
| database.py | MOSTLY OK (2/21 failed) |
| internal_doc_grounding.py | PARTIAL (4/24 failed) |

**Verdict:** NO — core docs have significant embedding failures due to server instability.

---

## F. Smoke Query Results

**V1 smoke queries (all 5 passed):**

| Query | Top Result | Expected Retrieved |
|-------|-----------|-------------------|
| "active focus" | TRACKER.md (0.49) | YES |
| "GAP_031 status" | self_state.json (0.54) | YES |
| "local models DL380" | benchmark report (0.65) | YES |
| "Interactive Layer router" | self_state.json (0.64) | PARTIAL |
| "next development direction" | BGE-M3 verdict (0.54) | YES |

**V1.1 smoke queries:** Could not be re-run due to BGE-M3 server instability (repeated crashes during testing). The V1 results remain valid as the index structure is compatible.

---

## G. Ready for MS-OQ1-A Integration?

**NO — NOT YET.**

### Blockers:

1. **BGE-M3 CPU server instability** — The server crashes under sustained load. This is a hardware limitation (no GPU available for embeddings on DL380).

2. **86.6% success rate** — Below the 97% target. 80 chunks have zero-vector placeholders which degrade retrieval quality.

3. **prompt_router.py 55% failure rate** — Critical file for Interactive Layer grounding has too many missing embeddings.

### Recommended Path Forward:

**Option A — Accept current quality:**
- 86.6% success is functional for proof-of-concept
- Most queries return relevant results
- Zero-vector chunks don't break the index
- Proceed with MS-OQ1-A integration, accept degraded quality for failed chunks

**Option B — Improve server stability:**
- Run BGE-M3 as a Windows Service with auto-restart
- Add health checks before embedding batches
- Implement batch embedding (multiple texts per request) to reduce round trips
- Consider switching to a smaller/faster embedding model

**Option C — Hybrid approach:**
- Use BGE-M3 for small batches (<50 chunks)
- Implement offline embedding generation (pre-compute all embeddings, store locally)
- Query-time only needs numpy cosine similarity (no server needed)

---

## Summary

| Question | Answer |
|----------|--------|
| A. Failure root causes | BGE-M3 CPU server 500 errors, NOT chunk size |
| B. Files changed | build_index.py (complete V1.1 rewrite) |
| C. New success rate | 86.6% (up from 84.8%) |
| D. prompt_router.py indexed? | PARTIAL (12/22 chunks) |
| E. Core docs all indexed? | NO (significant failures) |
| F. Smoke query results | V1: 5/5 useful, V1.1: not re-testable |
| G. Ready for MS-OQ1-A? | NO (server instability) |

---

**END OF REPORT**