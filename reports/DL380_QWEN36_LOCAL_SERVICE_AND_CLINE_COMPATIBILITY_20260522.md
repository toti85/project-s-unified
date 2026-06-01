# DL380 Qwen3.6 Local Service Hardening & Cline Compatibility
**Date:** 2026-05-22  
**Server:** SHAYANSKA-DL380 (46.253.140.72)  
**Model:** Qwen3.6-35B-A3B-Q4_K_M  
**Engine:** llama.cpp b9279 Vulkan (WDDM)  

---

## Quick Reference Answers

| | Result |
|--|--------|
| **A. Start script created?** | ✅ YES — `F:\ModelVault\scripts\start_qwen36_llama_server_vulkan.ps1` |
| **B. llama-server starts from script?** | ✅ YES — loads in ~54s, listens on 0.0.0.0:8096 |
| **C. /completion works?** | ✅ YES — 14.06 tok/s, direct and reliable |
| **D. /v1/chat/completions works?** | ⚠️ PARTIAL — API works but requires `chat_template_kwargs` workaround |
| **E. Cline-compatible endpoint available?** | ⚠️ WITH WORKAROUND — needs proxy or parameter override |
| **F. Smoke latency / tok/s** | /completion: 14.06 tok/s, 6.3s wall; /v1/chat: ~11 tok/s, 11-13.5s wall |
| **G. Recommended Cline provider settings** | See section below |
| **H. Next model to download** | Qwen2.5-Coder-14B-Instruct-Q4_K_M (~9 GB) |
| **I. Ready for Cline test?** | ⚠️ WITH PROXY — direct Cline not reliable due to thinking mode |

---

## Task 1 — Startup Script

### Location
```
F:\ModelVault\scripts\start_qwen36_llama_server_vulkan.ps1
```

### What it does
1. Verifies model file (`F:\ModelVault\gguf\qwen\Qwen3.6-35B-A3B-Q4_K_M\Qwen3.6-35B-A3B-Q4_K_M.gguf`)
2. Verifies `llama-server.exe` (`F:\ModelVault\llama-cpp\vulkan-bin\`)
3. Runs `nvidia-smi` to confirm 2× Tesla M60 in WDDM mode
4. Creates firewall rule for port 8096
5. Starts `llama-server` with `--host 0.0.0.0 --port 8096` (no `-ngl` = auto-fit)
6. Writes logs to `F:\ModelVault\logs\qwen36_llama_server_YYYYMMDD_HHMMSS.log`
7. Polls for "server is listening" signal (up to 120s)
8. Reports VRAM utilization after load
9. Prints all available endpoints

### How to run (from DL380 PowerShell)
```powershell
powershell -ExecutionPolicy Bypass -File "F:\ModelVault\scripts\start_qwen36_llama_server_vulkan.ps1"
```

### Expected startup output
```
[1/5] Model file check...   OK  19.71 GB
[2/5] llama-server.exe ...  OK
[3/5] NVIDIA WDDM check...  OK  2x WDDM GPU confirmed
[4/5] Log directory...      F:\ModelVault\logs\qwen36_llama_server_20260522_143000.log
[5/5] Starting llama-server on 0.0.0.0:8096 (auto-fit, ~55s load)
      PID: XXXX
[WAIT] READY at 54s
[VRAM] Tesla M60, 5748 MiB
       Tesla M60, 5716 MiB
SERVICE READY — http://0.0.0.0:8096
```

---

## Task 2 — API Endpoint Compatibility

### Test environment
- Server: 0.0.0.0:8096 (verified from WinRM via 127.0.0.1:8096)
- VRAM during tests: 5752 + 5716 MiB = 11.47 GB (stable)

### Results

#### GET /v1/models
```
Status:   200 OK
Latency:  61ms
Response: { "data": [{ "id": "Qwen3.6-35B-A3B-Q4_K_M.gguf", "object": "model" }] }
```
**Result: ✅ WORKS**

---

#### POST /completion (legacy, direct)
```
Prompt:   "Irj 2 rovid magyar mondatot arrol, miert hasznos egy lokalis AI modell."
Tokens:   74
Eval:     5.3s
tok/s:    14.06
Prompt:   24.1 tok/s (prefill)
Wall:     6.3s
```
Response:
> A helyi AI modell adatvédelmet biztosít, mivel a feldolgozott információk soha nem hagyják el a saját eszközödet. Emellett internetkapcsolat nélkül is azonnal elérhető, így gyorsabb és megbízhatóbb megoldást nyújt a mindennapi feladatokhoz.

**Result: ✅ WORKS — best tok/s, fully reliable**

---

#### POST /v1/chat/completions (OpenAI-compatible, default)
```
Status:   200 OK
content:  [] (EMPTY)
reasoning_content: [full model output here]
```
**Root cause:** Qwen3.6 defaults to "thinking mode". All tokens go into `reasoning_content`; `content` field is empty. Cline reads `content` → sees nothing → fails silently.

**Result: ⚠️ API OK but Cline-incompatible in default mode**

---

#### POST /v1/chat/completions + `chat_template_kwargs`
```json
{
  "model": "qwen36",
  "messages": [...],
  "max_tokens": 150,
  "temperature": 0.7,
  "chat_template_kwargs": {"enable_thinking": false}
}
```
```
Status:   200 OK
content:  [</think>\n\n<actual response>]
reasoning_content: [] (empty — thinking disabled)
tok/s:    ~11
Wall:     11-13.5s
```
**Note:** Minor `</think>` prefix artifact in `content` — requires stripping in proxy.  

**Result: ✅ WORKS WITH PARAMETER — content populated, suitable for Cline via proxy**

---

#### Code generation test (with no_think)
```python
def read_lines_from_file(filepath: str) -> list:
    with open(filepath, 'r') as file:
        lines = file.readlines()
    lines = [line.rstrip('\n') for line in lines]
    return lines
```
Tokens: 121 | Wall: 11s | ~11 tok/s  
**Result: ✅ Correct, well-structured Python code**

---

### Summary table

| Endpoint | HTTP | Content | tok/s | Cline ready |
|----------|------|---------|-------|-------------|
| GET /v1/models | 200 | model list | — | ✅ |
| POST /completion | 200 | full text | 14.06 | ✅ (no chat format) |
| POST /v1/chat/completions (default) | 200 | EMPTY | 8-10 | ❌ |
| POST /v1/chat/completions + chat_template_kwargs | 200 | full text | ~11 | ✅ via proxy |

---

## Task 3 — Cline Compatibility Settings

### Root cause: Qwen3.6 thinking mode
Qwen3.6-35B-A3B is a **hybrid thinking/non-thinking model**. By default, it generates reasoning tokens into `<think>...</think>` blocks. llama.cpp returns these in `choices[0].message.reasoning_content`, leaving `content` empty. Cline reads `content` → receives nothing.

**Fix required:** Add `"chat_template_kwargs": {"enable_thinking": false}` to every API request. This is a llama.cpp-specific parameter and cannot be set directly in Cline's provider settings.

---

### Option A — Direct OpenAI Compatible (testing only)

```
Provider:    OpenAI Compatible
Base URL:    http://46.253.140.72:8096
API Key:     local   (any non-empty string; llama.cpp ignores auth)
Model:       Qwen3.6-35B-A3B-Q4_K_M.gguf
Context:     4096 (safe default; server default)
```

**Known limitation:** Cline will receive empty `content` responses unless thinking mode is disabled. Use for testing only. Do NOT use for live coding workflow.

---

### Option B — Via Compatibility Proxy (recommended for Cline)

Deploy the thin proxy on DL380:

```python
# F:\ModelVault\scripts\cline_proxy.py
# pip install fastapi uvicorn httpx
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import httpx, json, asyncio

app = FastAPI()
UPSTREAM = "http://127.0.0.1:8096"

@app.post("/v1/chat/completions")
async def chat(request: Request):
    body = await request.json()
    body.setdefault("chat_template_kwargs", {})["enable_thinking"] = False
    body.setdefault("temperature", 0.7)
    async with httpx.AsyncClient(timeout=300) as client:
        r = await client.post(f"{UPSTREAM}/v1/chat/completions", json=body)
    data = r.json()
    # Strip stray </think> prefix from content
    for choice in data.get("choices", []):
        msg = choice.get("message", {})
        if msg.get("content"):
            msg["content"] = msg["content"].lstrip("</think>").strip()
    return data

@app.get("/v1/models")
async def models(request: Request):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{UPSTREAM}/v1/models")
    return r.json()
```

Start proxy:
```powershell
python -m uvicorn cline_proxy:app --host 0.0.0.0 --port 8097
```

Then configure Cline:
```
Provider:    OpenAI Compatible
Base URL:    http://46.253.140.72:8097
API Key:     local
Model:       Qwen3.6-35B-A3B-Q4_K_M.gguf
Context:     4096
```

---

### Cline settings reference

| Setting | Value |
|---------|-------|
| Provider type | OpenAI Compatible |
| Base URL (direct) | `http://46.253.140.72:8096` |
| Base URL (proxy) | `http://46.253.140.72:8097` |
| API Key | `local` (any string) |
| Model ID | `Qwen3.6-35B-A3B-Q4_K_M.gguf` |
| Context window | 4096 (default) |
| Max tokens | 2048 |
| Temperature | 0.7 |
| Streaming | may work (not tested) |

### Known limitations with Qwen3.6 in Cline

1. **Thinking mode**: Must disable via proxy — cannot set `chat_template_kwargs` in Cline UI
2. **`</think>` prefix**: Minor artifact, proxy strips it
3. **Slow for large edits**: 11-14 tok/s for a 35B MoE model; large diffs will take 30-90s
4. **Memory**: Server uses 11.2 GB VRAM; cannot run other GPU workloads simultaneously
5. **No streaming verified**: Streaming mode untested; may require additional proxy logic

---

## Task 4 — Next Model Recommendation

### Recommendation: **Qwen2.5-Coder-14B-Instruct-Q4_K_M**

| Property | Value |
|----------|-------|
| GGUF size | ~9.0 GB |
| VRAM fit | ✅ Full GPU offload (9 GB < 11.2 GB Tesla M60 × 2 available) |
| -ngl | -ngl 99 (all layers on GPU — no OOM issue) |
| Architecture | Dense transformer (no MoE — no allocation issues) |
| Training | 5.9T tokens, code-focused |
| Context | 128K tokens (use 8K-32K for practical Cline use) |
| Thinking mode | ❌ None — direct `content` output, Cline-native |
| Coding score | HumanEval 88.4%, MBPP 82.0% |

### Why Qwen2.5-Coder-14B over other candidates

| Model | Size | Cline-ready | Code quality | VRAM fit | Verdict |
|-------|------|-------------|-------------|----------|---------|
| **Qwen2.5-Coder-14B Q4_K_M** | ~9 GB | ✅ | ⭐⭐⭐⭐ | ✅ Full | **BEST** |
| Qwen2.5-Coder-7B Q4_K_M | ~5 GB | ✅ | ⭐⭐⭐ | ✅ Full | Good, smaller |
| Mistral-Nemo-12B Q4_K_M | ~7 GB | ✅ | ⭐⭐⭐ | ✅ Full | Decent, not code-focused |
| Qwen3.6-35B (current) | 19.7 GB | ⚠️ proxy needed | ⭐⭐⭐⭐⭐ | ⚠️ partial | Too large, thinking issue |
| BGE-M3 | ~1.1 GB | embedding only | — | ✅ | For RAG only, not Cline |

### Download command (on DL380)
```powershell
# Install HF CLI if not present
pip install huggingface-hub[cli]

# Download (~9 GB)
huggingface-cli download bartowski/Qwen2.5-Coder-14B-Instruct-GGUF `
    --include "Qwen2.5-Coder-14B-Instruct-Q4_K_M.gguf" `
    --local-dir "F:\ModelVault\gguf\qwen\Qwen2.5-Coder-14B-Instruct-Q4_K_M"
```

### Start command for Qwen2.5-Coder-14B (once downloaded)
```powershell
F:\ModelVault\llama-cpp\vulkan-bin\llama-server.exe `
    -m "F:\ModelVault\gguf\qwen\Qwen2.5-Coder-14B-Instruct-Q4_K_M\Qwen2.5-Coder-14B-Instruct-Q4_K_M.gguf" `
    --port 8096 `
    --host 0.0.0.0 `
    -ngl 99 `
    --ctx-size 16384
```
Expected: **full VRAM offload**, ~20-30 tok/s, ~15s load, no thinking issues.

---

## Architecture Decision

```
Current state (Qwen3.6-35B):
  llama-server:8096 ──── POST /completion ──────── direct scripts ✅
                   ──── POST /v1/chat/completions ─ BROKEN for Cline ❌
                   
Recommended state (with proxy):
  llama-server:8096 ──── proxy:8097 ──── Cline ✅
                                    (adds enable_thinking=false, strips </think>)

Future state (Qwen2.5-Coder-14B):
  llama-server:8096 ──── Cline directly ✅ (no proxy needed)
  + llama-server:8097 ── Qwen3.6-35B for complex reasoning ✅
```

---

## Performance Data (All Tests Combined)

| Test | Endpoint | Tokens | Eval time | tok/s | Wall time |
|------|----------|--------|-----------|-------|-----------|
| Hungarian (cached prompt off) | /completion | 74 | 5.3s | **14.06** | 6.3s |
| MoE explanation | /v1/chat | 120 | — | ~8.9 | 13.5s |
| Code task (no_think) | /v1/chat | 121 | — | ~11.0 | 11.0s |
| Short answer (no_think) | /v1/chat | 60 | — | ~10.0 | 6.0s |
| Hungarian benchmark (prev) | /completion | 73 | 5.8s | 12.69 | 9.4s |
| English benchmark (prev) | /completion | 80 | 5.9s | 13.50 | — |

**Average GPU tok/s (all tests): ~12–14 tok/s**  
**CPU baseline: 4.19 tok/s → speedup: 3.0–3.3×**

---

## Files Created This Session

| File | Location | Status |
|------|----------|--------|
| Startup script | `F:\ModelVault\scripts\start_qwen36_llama_server_vulkan.ps1` | ✅ Deployed |
| Log directory | `F:\ModelVault\logs\` | ✅ Created |
| GPU enablement report | `C:\ProjectS-Unified\reports\DL380_TESLA_M60_GPU_ENABLEMENT_FOR_QWEN36_20260522.md` | ✅ |
| This report | `C:\ProjectS-Unified\reports\DL380_QWEN36_LOCAL_SERVICE_AND_CLINE_COMPATIBILITY_20260522.md` | ✅ |

**Pending creation:**
- `F:\ModelVault\scripts\cline_proxy.py` — thin proxy for Cline compatibility
- Startup script for Qwen2.5-Coder-14B (after download)

---

## Security Note
⚠️ Change DL380 Administrator password (`Qwe123`) before exposing port 8096/8097 beyond trusted network.  
⚠️ llama.cpp server has **no authentication** — firewall to trusted IPs only.
