# AO9_T7B — Aider Cloud Single-Prompt Cell Definition

Date: 2026-07-14

## Cell Parameters

| Parameter | Value |
|-----------|-------|
| Model | DeepSeek V4 Flash |
| Model string (Aider) | `openai/deepseek/deepseek-v4-flash` |
| Runtime | Aider CLI 0.86.2 |
| Endpoint | https://openrouter.ai/api/v1 |
| Provider | OpenRouter |
| Context window | 1,048,576 tokens |
| Hardware | N/A (cloud inference) |
| Aider flags | `--no-git --yes-always --no-check-update --no-show-model-warnings --no-stream` |
| Output format | whole edit format (Aider default) |
| Prompt convention | Create file X with: [JSON] |
| API key | env var OPENROUTER_API_KEY (never hardcoded) |
| **Chunk strategy** | **SINGLE PROMPT** (all 77 findings in one call) |
| Expected token load | ~20-30K input + ~5-10K output |
| Timeout | 600s |

## Cell Classification Table

| Dimension | Ornith (T5_RUN4) | Aider-Ornith (T6, INVALID) | Aider-Cloud-Chunked (T7a) | Aider-Cloud-Single (T7b) |
|-----------|-----------------|------------------------------|---------------------------|--------------------------|
| Model class | Small local (9B) | Small local (9B) | Large cloud | Large cloud |
| Interface | Custom minimal | Aider CLI | Aider CLI | Aider CLI |
| Native match? | YES | NO | YES | YES |
| Chunking | 3 chunks | 3 chunks | 3 chunks | **SINGLE PROMPT** |
| Valid measurement? | YES | NO | YES | YES |

## A/B Test Validity

T7a vs T7b: **same everything except chunking strategy** — this isolates the chunk dimension.

| Parameter | T7a (Chunked) | T7b (Single Prompt) |
|-----------|---------------|---------------------|
| Model | DeepSeek V4 Flash | **SAME** |
| Endpoint | OpenRouter | **SAME** |
| Adapter | Aider CLI 0.86.2 | **SAME** |
| Aider flags | --no-git --yes-always --no-check-update --no-show-model-warnings | **SAME** |
| Input file | scan_canonical.json (77 findings) | **SAME** |
| Output schema | Structured JSON with `chunk_id`, `start_index`, `end_index`, `finding_count`, `findings` | **SAME** (adapted: prompt_id=1, start=1, end=77, count=77) |
| Output file name | chunk_XX.json (3 files) | **single_prompt_output.json** (1 file) |
| **Chunking** | **3 chunks** (25 + 25 + 27) | **SINGLE PROMPT** (all 77) |

## Prompt Adaptation

Same format as T7a chunk prompts, but:
- Single file: `single_prompt_output.json` (not chunk_XX.json)
- All 77 findings in one listing
- prompt_id: 1, start_index: 1, end_index: 77, finding_count: 77

## Cost Model

DeepSeek V4 Flash via OpenRouter (estimated rates):
- Input: $0.07/1M tokens
- Output: $0.28/1M tokens
- Expected input tokens: ~20,000-30,000
- Expected output tokens: ~5,000-10,000
- Estimated cost: ~$0.0014-0.0021 input + ~$0.0014-0.0028 output = **~$0.003-0.005**

## Hypothesis Being Tested

**Is chunking a general pattern or a small-model workaround?**

- If T7b PASSES (77/77, valid JSON): chunking compensates for small-model context limits, not a universal pattern
- If T7b FAILS/PARTIAL: chunking provides quality benefit even at scale, validating the original pattern

---

*AO9_T7B cell definition — generated automatically for Phase C execution*