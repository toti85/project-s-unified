# DL380 Qwen2.5-Coder-14B — Local Cline Candidate
**Date:** 2026-05-22  
**Server:** SHAYANSKA-DL380 (46.253.140.72)  
**Model:** Qwen2.5-Coder-14B-Instruct-Q4_K_M  
**Engine:** llama.cpp b9279 Vulkan / Tesla M60 ×2 WDDM  

---

## Quick Reference Answers

| | Result |
|--|--------|
| **A. Download completed?** | ✅ YES — 8571.7 MB, BITS transfer |
| **B. File size / SHA256?** | 8571.7 MB (8,988,111,072 bytes) / `2946D28C9E1BB2BCAE6D42E8678863A31775DF6F740315C7D7E6D6B6411F5937` |
| **C. Server starts?** | ✅ YES — 18 seconds load time |
| **D. Full GPU offload?** | ✅ YES — `-ngl 99` works, 9.26 GB VRAM used |
| **E. Benchmark tok/s** | 11.0–12.5 tok/s (avg ~12.1) |
| **F. /v1/chat compatible?** | ✅ YES — `content` populated directly, `reasoning_content` empty |
| **G. Cline proxy needed?** | ❌ NO — direct OpenAI API, no thinking mode issues |
| **H. Cline settings** | See section below |
| **I. Verdict** | ✅ **STRONG LOCAL CLINE CANDIDATE** |
| **J. Next model** | Qwen2.5-Coder-7B-Q4_K_M or BGE-M3 |

---

## Task 1 — Download

### File

| Property | Value |
|----------|-------|
| Source | `bartowski/Qwen2.5-Coder-14B-Instruct-GGUF` |
| File | `Qwen2.5-Coder-14B-Instruct-Q4_K_M.gguf` |
| Location | `F:\ModelVault\gguf\coder\Qwen2.5-Coder-14B-Instruct-Q4_K_M\` |
| Size | 8571.7 MB (8,988,111,072 bytes) |
| SHA256 | `2946D28C9E1BB2BCAE6D42E8678863A31775DF6F740315C7D7E6D6B6411F5937` |
| Method | Windows BITS transfer (Start-BitsTransfer) |
| Download speed | ~9.3 MB/s from HuggingFace (unauthenticated) |
| Download time | ~15 minutes |

**Note:** The `hf` CLI download tool stalled (0 bytes, low CPU) — switched to `Start-BitsTransfer` which completed reliably. BITS is recommended for future large file downloads on this server.

SHA256 file saved at: `F:\ModelVault\gguf\coder\Qwen2.5-Coder-14B-Instruct-Q4_K_M\SHA256SUMS.txt`

---

## Task 2 — Start Script

### Location
```
F:\ModelVault\scripts\start_qwen25_coder_14b_vulkan.ps1
```

### Usage
```powershell
# Auto-fit mode (default)
powershell -ExecutionPolicy Bypass -File "...\start_qwen25_coder_14b_vulkan.ps1"

# Full GPU offload (recommended — verified working)
powershell -ExecutionPolicy Bypass -File "...\start_qwen25_coder_14b_vulkan.ps1" -NglMode full

# Custom ngl layers
powershell -ExecutionPolicy Bypass -File "...\start_qwen25_coder_14b_vulkan.ps1" -NglMode 80
```

### Key defaults
- Port: 8098
- Host: 0.0.0.0
- Context: 8192 tokens
- Logs: `F:\ModelVault\logs\qwen25coder14b_YYYYMMDD_HHMMSS.log`

### Verified working command
```powershell
F:\ModelVault\llama-cpp\vulkan-bin\llama-server.exe `
    -m "F:\ModelVault\gguf\coder\Qwen2.5-Coder-14B-Instruct-Q4_K_M\Qwen2.5-Coder-14B-Instruct-Q4_K_M.gguf" `
    --port 8098 --host 0.0.0.0 `
    -ngl 99 --ctx-size 4096
```

---

## Task 3 — Benchmark Results

### Hardware state during tests

| Metric | Value |
|--------|-------|
| GPU0 VRAM used | 5127–5131 MiB |
| GPU1 VRAM used | 4599–4603 MiB |
| Total VRAM used | ~9.73 GB (stable) |
| Free VRAM | ~6.5 GB |
| GPU offload | **Full** (-ngl 99, all 48 layers on GPU) |
| Load time | **18 seconds** |

### Benchmark A — Hungarian response
**Prompt:** "Irj 3 rovid magyar mondatot arrol, mire jo egy lokalis kodolo modell."  
**Response:**
> Íme 3 rövid magyar mondat a helyi kódolási modell előnyeiről:
> 1. Jóanálja a helyi nyelvtani és kultúráli elemeket pontosabban.  
> 2. Jobban megérti és kezelheti a helyi ügyfeleket és piaci igényeket.  
> 3. Növeli a termék- vagy szolgáltatás elfogadtságát a helyi piacokon.

| Metric | Value |
|--------|-------|
| Tokens | 114 |
| Wall time | 10.2s |
| **tok/s** | **11.2** |
| Quality | Acceptable (minor quirk: "kódolási" vs "coding" — model interpreted "kodolo" as "encoding" rather than "coding model") |

### Benchmark B — UUID v4 validator (Python)
**Prompt:** "Write a Python function that validates whether a string is a UUID v4. Include 3 simple tests."  
**Response (summarized):**
```python
import uuid

def is_uuid_v4(uuid_str):
    try:
        test_uuid = uuid.UUID(uuid_str, version=4)
        return str(test_uuid) == uuid_str
    except ValueError:
        return False
```
- Correct implementation using Python `uuid` module
- Function correctly validates UUID version via `uuid.UUID(..., version=4)` with string comparison

| Metric | Value |
|--------|-------|
| Tokens | 300 (max, truncated) |
| Wall time | 24s |
| **tok/s** | **12.5** |
| Quality | ✅ Correct function; test values contained one UUID v1 (minor test case error, function itself is correct) |

### Benchmark C — Project-S style (prompt router)
**Prompt:** "Explain what a prompt router should do in an AI operator system in 5 bullet points."  
**Response:**
1. **Route Requests Efficiently** — direct requests to the most appropriate AI model
2. **Load Balancing** — distribute workload evenly across available models
3. **Scalability** — handle varying traffic levels without quality degradation
4. **Fault Tolerance** — detect and reroute around failed models
5. **Context Management** — maintain interaction history for coherent responses

| Metric | Value |
|--------|-------|
| Tokens | 208 |
| Wall time | 16.6s |
| **tok/s** | **12.5** |
| Quality | ✅ Excellent — precise, actionable, well-structured |

### Benchmark summary

| Test | Prompt type | Tokens | Wall | tok/s |
|------|------------|--------|------|-------|
| A: Hungarian | Conversational | 114 | 10.2s | **11.2** |
| B: Code generation | Function + tests | 300 | 24.0s | **12.5** |
| C: Technical bullet | Project-S style | 208 | 16.6s | **12.5** |
| /completion code | FIM/autocomplete | 60 | 4.8s | **12.44** |
| Cline code review | Code + explanation | 113 | 10.3s | **11.0** |

**Average: ~12.1 tok/s**  
**Prefill (prompt): 7.5 tok/s** (measured on /completion endpoint)

---

## Task 4 — Cline Compatibility

### Critical difference vs Qwen3.6

| | Qwen3.6-35B | Qwen2.5-Coder-14B |
|--|-------------|-------------------|
| Thinking mode | ON by default | ❌ None |
| `content` field | Empty (default) | ✅ Directly populated |
| `reasoning_content` | Full output | Empty |
| Proxy required | YES | **NO** |
| Cline-native | ❌ | ✅ |

### API endpoint results

| Endpoint | Status | Notes |
|----------|--------|-------|
| GET /v1/models | ✅ OK | Model ID: `Qwen2.5-Coder-14B-Instruct-Q4_K_M.gguf` |
| POST /completion | ✅ OK | 12.44 tok/s, code completion works |
| POST /v1/chat/completions | ✅ OK | `content` populated directly, no workaround needed |

### Cline provider settings

```
Provider:       OpenAI Compatible
Base URL:       http://46.253.140.72:8098
API Key:        local    (any non-empty string; no auth on llama.cpp)
Model ID:       Qwen2.5-Coder-14B-Instruct-Q4_K_M.gguf
Context window: 4096 (safe default with -ngl 99)
Max tokens:     2048
Temperature:    0.3–0.5 for coding tasks
```

**No proxy needed.** Connect Cline directly to port 8098.

### Cline-style test result

**Input:** Code review of a `load_model` function with unclosed file handle  
**Response:**
> The function can be improved by adding a context manager to handle the file opening and closing automatically, which ensures the file is properly closed even if an error occurs.
> 
> ```python
> def load_model(path):
>     import json
>     with open(path) as f:
>         return json.load(f)
> ```
> Using `with open(path) as f:` ensures the file is closed after the block, even if an exception is raised.

**Quality:** ✅ Excellent — identified the exact issue (resource leak), provided minimal correct fix, explained rationale

---

## Comparison: Qwen2.5-Coder-14B vs Qwen3.6-35B

| Metric | Qwen2.5-Coder-14B | Qwen3.6-35B |
|--------|-------------------|-------------|
| File size | 8.37 GB | 19.71 GB |
| GPU offload | ✅ Full (-ngl 99) | ⚠️ Partial (auto-fit) |
| VRAM used | 9.26 GB | 11.2 GB |
| Load time | **18s** | 54s |
| Average tok/s | **~12.1** | ~13.1 |
| Cline-native | ✅ YES | ❌ Needs proxy |
| Code specialization | ✅ Code-focused | General |
| Context | 4K–8K | 4K–8K |
| Architecture | Dense (48 layers) | MoE (64 experts) |

**Winner for Cline:** Qwen2.5-Coder-14B — faster load, no proxy, code-tuned, stable full GPU offload.

---

## Port Allocation (DL380 Local Service Stack)

| Port | Model | Engine | Status |
|------|-------|--------|--------|
| 8096 | Qwen3.6-35B-A3B-Q4_K_M | llama.cpp Vulkan | Manual start |
| 8097 | — | cline_proxy.py (for Qwen3.6) | Manual start |
| **8098** | **Qwen2.5-Coder-14B-Instruct-Q4_K_M** | **llama.cpp Vulkan** | **Active** |

Both 8096 and 8098 can run simultaneously (total VRAM: 9.26 + 11.2 = 20.5 GB > 16.3 GB available → **cannot run both at once**). Allocate per use case.

---

## ModelVault Manifest Update

| Model | Size | Path | GPU | Status |
|-------|------|------|-----|--------|
| Qwen3.6-35B-A3B-Q4_K_M | 19.71 GB | `gguf\qwen\Qwen3.6-35B-A3B-Q4_K_M\` | Vulkan partial | Ready |
| **Qwen2.5-Coder-14B-Q4_K_M** | **8.37 GB** | `gguf\coder\Qwen2.5-Coder-14B-Instruct-Q4_K_M\` | **Vulkan full** | **Ready** |

Total GGUF storage used: ~28 GB / 422 GB free on F:

---

## Next Model Recommendations

### Option 1 — Qwen2.5-Coder-7B-Instruct-Q4_K_M (speed tier)
- Size: ~4.7 GB
- Fits in ONE Tesla M60 chip (8 GB VRAM)
- Expected: 20–30 tok/s (single GPU)
- Use case: Fast inline completions in Cline

```powershell
hf download bartowski/Qwen2.5-Coder-7B-Instruct-GGUF `
    Qwen2.5-Coder-7B-Instruct-Q4_K_M.gguf `
    --local-dir "F:\ModelVault\gguf\coder\Qwen2.5-Coder-7B-Instruct-Q4_K_M"
```

### Option 2 — BGE-M3 (embedding / RAG)
- Size: ~1.1 GB
- Enables vector search and RAG in Project-S
- No GPU needed (CPU inference is fine for embedding)
- Download: `BAAI/bge-m3`

### Option 3 — Qwen2.5-Coder-32B-Instruct-Q4_K_M (power tier)
- Size: ~19 GB
- Partial GPU offload (similar to Qwen3.6 scenario)
- Use case: Complex refactoring, architecture review
- **Recommendation: Lower priority, current 14B is sufficient for most tasks**

### Recommended priority order
1. ✅ Qwen2.5-Coder-14B — **DONE**
2. 🔜 BGE-M3 — small, enables RAG/embedding stack
3. 🔜 Qwen2.5-Coder-7B — speed tier for fast completions
4. 📋 Qwen2.5-Coder-32B — power tier (if needed later)

---

## Files Created This Session

| File | Location | Status |
|------|----------|--------|
| Model GGUF | `F:\ModelVault\gguf\coder\Qwen2.5-Coder-14B-Instruct-Q4_K_M\Qwen2.5-Coder-14B-Instruct-Q4_K_M.gguf` | ✅ 8572 MB |
| SHA256 | `F:\ModelVault\gguf\coder\Qwen2.5-Coder-14B-Instruct-Q4_K_M\SHA256SUMS.txt` | ✅ |
| Start script | `F:\ModelVault\scripts\start_qwen25_coder_14b_vulkan.ps1` | ✅ 5605 bytes |
| This report | `C:\ProjectS-Unified\reports\DL380_QWEN25_CODER_14B_LOCAL_CLINE_CANDIDATE_20260522.md` | ✅ |

---

## Security Note
⚠️ Port 8098 has no authentication. Expose only on trusted network.  
⚠️ Change DL380 Administrator password (`Qwe123`) before any external exposure.
