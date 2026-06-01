# ModelVault Notes — SHAYANSKA-DL380

**Location:** `F:\ModelVault\` on 46.253.140.72  
**Last updated:** 2026-05-22  
**Inference engine:** llama.cpp Vulkan b9279 (`F:\ModelVault\llama-cpp\vulkan-bin\llama-server.exe`)  
**GPU:** Tesla M60 × 2 chips (WDDM mode, Vulkan backend) | 8192 MiB × 2 = 16.3 GB VRAM total  

---

## Deployed Models

### Qwen3.6-35B-A3B-Q4_K_M
| Property | Value |
|----------|-------|
| Path | `F:\ModelVault\gguf\qwen\Qwen3.6-35B-A3B-Q4_K_M\Qwen3.6-35B-A3B-Q4_K_M.gguf` |
| Size | 19.71 GB |
| Port | 8096 (llama-server) / 8097 (Cline proxy) |
| Start script | `F:\ModelVault\scripts\start_qwen36_llama_server_vulkan.ps1` |
| GPU offload | Auto-fit (no `-ngl` — WDDM VRAM allocation limit) |
| VRAM used | ~12–13 GB (both chips) |
| Speed | ~12–14 tok/s |
| Thinking mode | ON by default — requires proxy on 8097 for Cline (`enable_thinking: false`) |
| Status | ✅ Production-ready |
| Report | `C:\ProjectS-Unified\reports\DL380_QWEN36_LOCAL_SERVICE_AND_CLINE_COMPATIBILITY_20260522.md` |

### Qwen2.5-Coder-14B-Instruct-Q4_K_M
| Property | Value |
|----------|-------|
| Path | `F:\ModelVault\gguf\coder\Qwen2.5-Coder-14B-Instruct-Q4_K_M\Qwen2.5-Coder-14B-Instruct-Q4_K_M.gguf` |
| Size | 8.57 GB |
| SHA256 | `2946D28C9E1BB2BCAE6D42E8678863A31775DF6F740315C7D7E6D6B6411F5937` |
| SHA256 file | `F:\ModelVault\gguf\coder\Qwen2.5-Coder-14B-Instruct-Q4_K_M\SHA256SUMS.txt` |
| Port | 8098 (llama-server) |
| Start script | `F:\ModelVault\scripts\start_qwen25_coder_14b_vulkan.ps1` |
| GPU offload | Full (`-ngl 99`) |
| VRAM used | GPU0: 5127 MiB + GPU1: 4599 MiB = 9726 MiB (~9.5 GB) |
| Speed | ~10–12.5 tok/s |
| Thinking mode | OFF — `content` populated directly, `reasoning_content` empty; no proxy needed |
| Context | 4096 tokens |
| Status | ✅ **BENCHMARK PASSED 2026-05-22 — approved for supervised Cline use** |
| Report | `C:\ProjectS-Unified\reports\LOCAL_CLINE_QWEN25_CODER_14B_BENCHMARK_20260522.md` |

### BGE-M3 (DEPLOYED 2026-05-22)
| Property | Value |
|----------|-------|
| File | `F:\ModelVault\gguf\embedding\bge-m3\bge-m3-Q4_K_M.gguf` |
| Size | 437,778,496 bytes (417.5 MiB) |
| SHA256 | `6D39681B26C61279AC1F82DB35A04A05009E94C415B51C858FF571489A82FC06` |
| Source | `gpustack/bge-m3-GGUF` on HuggingFace (MIT license) |
| Port | 8099 (ACTIVE) |
| Architecture | BERT encoder (xlm-roberta), Q4_K_M quantization |
| Embedding dim | 1024 |
| Max ctx | 8192 tokens |
| GPU offload | CPU-only (`-ngl 0`) — Tesla M60 VRAM untouched |
| Start script | `F:\ModelVault\scripts\start_bge_m3_embedding_server.ps1` |
| Checksum file | `F:\ModelVault\checksums\bge-m3.sha256` |
| Latency | ~50–80ms per embedding request (CPU) |
| Status | ✅ **DEPLOYED + SMOKE TESTED 2026-05-22** |
| Verdict report | `C:\ProjectS-Unified\reports\BGE_M3_EMBEDDING_ACTIVATION_VERDICT_20260522.md` |

**Smoke test results (2026-05-22):**
- Single embedding: 1024-dim vector returned ✓
- Multilingual similarity (same sentence HU/EN/UK): HU↔EN=0.7230, EN↔UK=0.7972, HU↔UK=0.7019 — all > 0.70 ✓
- Grounding probe: relevant doc ranked 0.2635 margin above irrelevant doc ✓
- CPU-only confirmed: no GPU layers loaded, VRAM free for Qwen models ✓

---

## Cline Configuration

### Qwen2.5-Coder-14B (direct — local access only)
```
Provider:   OpenAI Compatible
Base URL:   http://127.0.0.1:8098
API Key:    local
Model ID:   Qwen2.5-Coder-14B-Instruct-Q4_K_M.gguf
Context:    4096
```

### Qwen2.5-Coder-14B (remote access via SSH tunnel)
```bash
# On dev machine — open tunnel first:
ssh -L 8098:127.0.0.1:8098 Administrator@46.253.140.72 -p <ssh_port> -N
# Then Cline Base URL: http://127.0.0.1:8098
```

### Qwen3.6-35B (via proxy — no thinking mode)
```
Provider:   OpenAI Compatible
Base URL:   http://127.0.0.1:8097   (proxy strips thinking tokens)
API Key:    local
Model ID:   Qwen3.6-35B-A3B-Q4_K_M.gguf
Context:    4096
```

---

## Known Issues / Constraints

| Issue | Detail |
|-------|--------|
| CUDA unavailable | Driver 475.14 max = CUDA 11.4; all inference tools need CUDA 12.x. Not fixable without hardware swap. Vulkan is the permanent solution. |
| Port 8096/8097/8098 blocked externally | ISP/router blocks these ports. SSH tunnel or VPN required for external Cline access. WinRM (15985) works fine. |
| WDDM mode (not TCC) | Tesla M60 cannot switch to TCC on this system. Vulkan backend works correctly under WDDM. |
| Qwen3.6 OOM with fixed -ngl | Manual layer offload triggers contiguous VRAM block requests → WDDM limit. Fix: no -ngl (auto-fit). |
| 4096 token context limit | Qwen2.5-Coder-14B approved at 4096 tokens. Large file edits need chunking. |

---

## Infrastructure Files on DL380

```
F:\ModelVault\
├── llama-cpp\vulkan-bin\llama-server.exe          ← inference engine
├── scripts\
│   ├── start_qwen36_llama_server_vulkan.ps1        ← Qwen3.6 startup
│   ├── start_qwen25_coder_14b_vulkan.ps1           ← Qwen2.5-Coder startup
│   └── cline_proxy.py                              ← FastAPI proxy (port 8097)
├── gguf\
│   ├── qwen\Qwen3.6-35B-A3B-Q4_K_M\*.gguf
│   └── coder\Qwen2.5-Coder-14B-Instruct-Q4_K_M\*.gguf
├── drivers\nvidia\475.14-tesla-ws2019.exe          ← Tesla M60 driver
└── logs\                                           ← runtime logs
```

---

## Benchmark Verdicts

| Model | Date | Verdict | Key Evidence |
|-------|------|---------|--------------|
| Qwen2.5-Coder-14B | 2026-05-22 | **USABLE — supervised small tasks** | 3/3 bugs found, 8/8 tests pass, 0 hallucinations, 0 correction cycles |
| Qwen3.6-35B | 2026-05-22 | **Operational — Cline via proxy** | ~12-14 tok/s GPU, thinking mode manageable via proxy |
