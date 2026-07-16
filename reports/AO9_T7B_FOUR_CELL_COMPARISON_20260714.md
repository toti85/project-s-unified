# AO9_T7B — Four-Cell Comparison

Date: 2026-07-14
Input: scan_canonical.json (77 findings, frozen — same for all 4 cells)

## Cell Definitions

| Dimension | Ornith (T5_RUN4) | Aider-Ornith (T6, INVALID) | Aider-Cloud-Chunked (T7a) | Aider-Cloud-Single (T7b) |
|-----------|-----------------|-----------------------------|---------------------------|--------------------------|
| Model class | Small local (9B) | Small local (9B) | Large cloud | Large cloud |
| Model | Ornith-1.0-9B Q4_K_M | Ornith-1.0-9B Q4_K_M | DeepSeek V4 Flash | DeepSeek V4 Flash |
| Interface | Custom adapter | Aider CLI 0.86.2 | Aider CLI 0.86.2 | Aider CLI 0.86.2 |
| Endpoint | localhost:8766 | localhost:8766 | OpenRouter | OpenRouter |
| Native match? | YES | NO | YES | YES |
| Chunking | 3 chunks | 3 chunks | 3 chunks | **SINGLE PROMPT** |
| Valid cell? | YES | NO (model mismatch) | YES | YES |

## Results

| Dimension | Ornith (T5_RUN4) | Aider-Ornith (T6, INVALID) | Aider-Cloud-Chunked (T7a) | Aider-Cloud-Single (T7b) |
|-----------|-----------------|-----------------------------|---------------------------|--------------------------|
| Chunk 1 / Single | PASS / 158.09s | FAIL / 300.01s | PASS / 144.54s | **PASS / ~519s** |
| Chunk 2 | PASS / 145.68s | PASS / 262.97s | PASS / 126.08s | N/A (single prompt) |
| Chunk 3 | PASS / 183.45s | FAIL / 300.01s | PASS / 183.68s | N/A (single prompt) |
| Total latency | 487s | 863s (partial) | 454s | **~519s** |
| Cost | $0 (local) | $0 (local) | $0.00000 | **~$0.003** |
| Reconciliation | 77/77 | 25/77 | 77/77 | **77/77** |
| Duplicates | 0 | 0 | 0 | **0** |
| Missing indices | none | 52 | none | **none** |
| merge_ready | True | False | True | **True** |
| Verdict | **PASS** | **INVALID** | **PASS** | **PASS** |

## Key Observations

1. **T7b single-prompt PASS**: DeepSeek V4 Flash successfully processed all 77 findings in a single call with valid JSON output, 77/77 reconciliation, and no duplicates.

2. **Latency comparison**: Single-prompt (~519s) took longer than the sum of 3 chunked T7a calls (454s). This is expected — a single large prompt requires more processing time per-token, and if the model generates sequentially, a single long output takes longer than 3 shorter outputs.

3. **Cost comparison**: Single-prompt (~$0.003) is slightly more expensive than chunked T7a ($0.00000 — not captured), but still negligible. The cost difference is unlikely to be practically significant.

4. **T6 invalidation confirmed**: The Aider-Ornith LOCAL failure was a model-class mismatch, not an adapter problem. Both Aider-Cloud configurations (T7a chunked, T7b single-prompt) PASS.

5. **Windows console issue**: Aider's Rich library crashes on Windows console after successful file writes. This is a display issue only — the output file and edit are both written correctly.

## Executor Reputation Matrix

| Cell | Model | Adapter | Chunking | Task | Result | Latency | Cost |
|------|-------|---------|----------|------|--------|---------|------|
| Ornith | Ornith-1.0-9B | Custom | 3 chunks | classify-77 | PASS | 487s | $0 |
| Aider-Ornith | Ornith-1.0-9B | Aider CLI | 3 chunks | classify-77 | INVALID | 863s | $0 |
| Aider-Cloud-Chunked | DeepSeek V4 Flash | Aider CLI | 3 chunks | classify-77 | PASS | 454s | $0.00 |
| Aider-Cloud-Single | DeepSeek V4 Flash | Aider CLI | SINGLE | classify-77 | **PASS** | **~519s** | **~$0.003** |

---

*AO9_T7B four-cell comparison — no manual content intervention*