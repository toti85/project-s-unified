# AO9_T7B — Cost Report

Date: 2026-07-14
Model: deepseek/deepseek-v4-flash (via OpenRouter)
Chunk strategy: SINGLE PROMPT (77 findings in one call)

## Token Usage

| Phase | Tokens Sent | Tokens Received | Total |
|-------|------------|-----------------|-------|
| Preflight | 587 | 7 | 594 |
| Single Prompt | ~12,000-15,000 (estimated) | ~5,000-8,000 (estimated) | ~17,000-23,000 |
| **TOTAL** | **~12,000-15,000** | **~5,000-8,000** | **~17,000-23,000** |

Note: Token counts for the single prompt are estimated based on prompt size (12,851 chars = ~12,000-15,000 tokens) and output size (22,472 bytes JSON = ~5,000-8,000 tokens). Aider did not report token usage for the single-prompt call due to the Windows console crash after file write.

## Cost Breakdown

| Item | Amount |
|------|--------|
| Input rate | $0.07/1M tokens |
| Output rate | $0.28/1M tokens |
| Input cost (estimated) | ~$0.00084-0.00105 |
| Output cost (estimated) | ~$0.00140-0.00224 |
| **Total estimated** | **~$0.00224-0.00329** |
| Cost per finding | ~$0.000029-0.000043 |
| Findings reconciled | 77/77 |

## Comparison

| Cell | Model | Cost | Per Finding |
|------|-------|------|-------------|
| Ornith (T5_RUN4) | Ornith 9B (local) | $0.00 | $0.00 |
| Aider-Ornith (T6) | Ornith 9B (local) | $0.00 | N/A (INVALID) |
| Aider-Cloud-Chunked (T7a) | DeepSeek V4 Flash | $0.00000 | $0.000000 |
| Aider-Cloud-Single (T7b) | DeepSeek V4 Flash | ~$0.003 | ~$0.00004 |

Note: OpenRouter actual cost may differ from estimate. T7a token counts were not captured (reported as 0). T7b token counts are estimated from prompt/output sizes.

---

*AO9_T7B cost report — estimated rates, verify against dashboard*