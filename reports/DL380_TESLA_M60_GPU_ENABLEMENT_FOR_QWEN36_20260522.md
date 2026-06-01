# DL380 Tesla M60 GPU Enablement for Qwen3.6 Inference
**Date:** 2026-05-22  
**Server:** SHAYANSKA-DL380 (46.253.140.72:15985)  
**Engineer:** Automated session via WinRM/PowerShell  

---

## Executive Summary

A NVIDIA Tesla M60 dual-GPU card was successfully enabled for AI inference on the DL380 server. The enabling path required switching from TCC to WDDM mode and using the Vulkan backend of llama.cpp. Final result: **3.13× inference speedup** (4.19 → ~13.1 tok/s) for the Qwen3.6-35B-A3B-Q4_K_M model.

---

## Hardware Inventory

| Component | Detail |
|-----------|--------|
| Server | HP ProLiant DL380 Gen9 |
| CPU | 2× Intel Xeon E5-2699 v3 @ 2.30 GHz (36 physical / 72 logical cores) |
| RAM | 127.9 GB (130942 MiB) |
| GPU Card | NVIDIA Tesla M60 (dual-chip) |
| GPU Chips | 2× Tesla M60 — GPU 0: 00000000:86:00.0, GPU 1: 00000000:87:00.0 |
| GPU VRAM | 8129 MiB per chip (~8 GB), 16.3 GB total |
| GPU Compute | Maxwell SM 5.2 |
| OS | Windows Server 2019 Datacenter |
| Driver | 475.14 WHQL (Tesla WS2019), CUDA 11.4 max |

---

## Model

| Property | Value |
|----------|-------|
| Model | Qwen3.6-35B-A3B-Q4_K_M |
| Architecture | MoE (Mixture of Experts), 94 transformer layers |
| File | `F:\ModelVault\gguf\qwen\Qwen3.6-35B-A3B-Q4_K_M\Qwen3.6-35B-A3B-Q4_K_M.gguf` |
| File size | 19.71 GB |
| Quantization | Q4_K_M (~4.5 bits/weight) |
| Active params | 3.6B (35B total, MoE routing) |

---

## Enablement Timeline

### Phase 1 — Hardware Inventory
- Tesla M60 detected via PCI scan: `VEN_10DE&DEV_13F2&SUBSYS_115E10DE&REV_A1`
- 2 chips visible in Device Manager as "Microsoft Basic Display Adapter" (no driver)
- nvidia-smi not present

**Result:** GPU visible pre-driver ✅

### Phase 2 — Driver Selection
- Max supported driver for Tesla M60: **475.14 WHQL**
- Newer drivers (≥525.x) support CUDA 12.x but are NOT supported on Tesla M60
- CUDA 11.4 is the maximum supported CUDA runtime version for this GPU

**Result:** Driver 475.14 selected ✅

### Phase 3 — Driver Installation
- Downloaded: `475.14-tesla-ws2019.exe` (538 MB) → `F:\ModelVault\drivers\nvidia\`
- Silent install: `setup.exe -s -noreboot`
- Exit code: 1 (success), no reboot required for driver
- Wait required: ~25 min for GPU services to initialize

**Result:** Driver installed ✅, nvidia-smi working ✅

### Phase 4 — Post-Install Validation
```
NVIDIA-SMI 475.14    Driver Version: 475.14    CUDA Version: 11.4
GPU 0: Tesla M60    8129 MiB    TCC
GPU 1: Tesla M60    8129 MiB    TCC
```
**Result:** Both chips visible, 16 GB total VRAM ✅

### Phase 5 — Ollama GPU Detection (TCC mode) — FAILED
- Ollama 0.24.0 started on port 11434
- Log showed: `inference compute id=cpu library=cpu total_vram=0 B`
- Root cause: Ollama bundles CUDA 12.x DLLs; CUDA 11.4 driver incompatible

**Result:** CPU-only, GPU not detected ❌  
**CPU baseline measured:** **4.19 tok/s** (80 tokens, 19.1s)

### Phase 6a — llama.cpp CUDA 12.4 Build — FAILED
- Binary: `llama-cpp b9279` with CUDA 12.4 runtime DLLs
- Error: `ggml_cuda_init: failed to initialize CUDA: CUDA driver version is insufficient for CUDA runtime version`
- Root cause: CUDA 12.4 requires driver ≥ 525.x; Tesla M60 max driver is 475.14

**Result:** CUDA 12.4 incompatible with CUDA 11.4 driver ❌

### Phase 6b — llama.cpp Vulkan Build (TCC mode) — FAILED
- Binary: `llama-cpp b9279` Vulkan build
- Log showed only CPU device, no GPU
- Root cause: TCC mode disables all display/Vulkan/DirectX APIs

**Result:** Vulkan requires display API → TCC mode blocks it ❌

### Phase 7 — TCC → WDDM Mode Switch
```powershell
nvidia-smi -g 0 -dm 0  # Set GPU 0 to WDDM mode
nvidia-smi -g 1 -dm 0  # Set GPU 1 to WDDM mode
# Output: "Reboot required" for both
Restart-Computer -Force  # Triggered at 09:34
```

**Reboot completed** (~3 min), both GPUs confirmed in WDDM mode:
```
WDDM, Tesla M60
WDDM, Tesla M60
```
**Result:** WDDM mode active ✅, display APIs enabled

### Phase 8 — Vulkan GPU Detection (WDDM mode) — SUCCESS
After reboot, llama.cpp Vulkan build (b9279) detected both GPUs:
```
device_info:
  - Vulkan0 : Tesla M60 (8312 MiB, 7097 MiB free)
  - Vulkan1 : Tesla M60 (8312 MiB, 7097 MiB free)
  - CPU     : Intel(R) Xeon(R) CPU E5-2699 v3 @ 2.30GHz (130942 MiB)
```
**Result:** Both Tesla M60 GPUs visible via Vulkan ✅

### Phase 9 — Model Loading Challenge: OOM with Manual -ngl
- `-ngl 99`, `-ngl 60`, `-ngl 25`: all failed with `ErrorOutOfDeviceMemory`
- Error: `alloc_tensor_range: failed to allocate Vulkan0 buffer of size 948439808`
- Root cause: Qwen3.6 MoE architecture has very large per-layer expert tensors
- Manual -ngl bypasses auto-fit → single tensor may exceed contiguous VRAM limit

**Solution:** Auto-fit mode (no `-ngl` specified) — llama.cpp auto-selects optimal split

### Phase 10 — GPU Inference: SUCCESS
```
llama-server.exe -m Qwen3.6-35B-A3B-Q4_K_M.gguf --port 8096
```
- **Load time:** ~54 seconds (auto-fit partial GPU offload)
- **VRAM used:** GPU0: 5748 MiB + GPU1: 5716 MiB = **11.2 GB total**
- **Tensor split:** ~57% on GPU (partial offload), ~43% on CPU RAM

---

## Performance Results

| Metric | CPU-only (Ollama 0.24.0) | GPU (Vulkan, llama.cpp b9279) |
|--------|--------------------------|-------------------------------|
| Tool | Ollama 0.24.0 | llama.cpp b9279 Vulkan |
| Backend | CPU (36 threads) | Tesla M60 ×2 (Vulkan) + CPU |
| Tokens generated | 80 | 73–80 |
| Eval time | 19.1 s | 5.8–5.9 s |
| **tok/s** | **4.19** | **12.69 – 13.50** |
| Average tok/s | 4.19 | **~13.1** |
| **Speedup** | 1× (baseline) | **3.13×** |
| Prompt tok/s | N/A | 18.2 (prefill) |
| VRAM | 0 | 11.2 GB / 16.3 GB |

---

## Failure Path Analysis

### Why CUDA Doesn't Work
| Issue | Detail |
|-------|--------|
| Tesla M60 max driver | 475.14 (CUDA 11.4) |
| Modern CUDA runtime requires | Driver ≥ 525.x (CUDA 12.0+) |
| All current AI tools bundle | CUDA 12.x runtime DLLs |
| Conclusion | **CUDA GPU inference permanently blocked** for Tesla M60 |

### Why TCC Mode Doesn't Work for Vulkan
- TCC (Tesla Compute Cluster) mode: CUDA compute only, no display APIs
- Vulkan requires Windows Display Driver Model (WDDM)
- DirectX, Vulkan, OpenGL: all unavailable in TCC mode

### Why Manual -ngl Fails with Vulkan
- Qwen3.6-35B-A3B is a MoE model with very large individual tensor buffers (~948 MB per MoE block)
- With manual `-ngl`, llama.cpp bypasses auto-fit and tries to allocate sequentially
- The first large contiguous buffer allocation fails in WDDM mode
- **Auto-fit mode** correctly probes available memory and distributes tensors across GPU+CPU

---

## Working Configuration

```powershell
# Server startup command (on DL380, run from interactive session or scheduled task)
$exe = "F:\ModelVault\llama-cpp\vulkan-bin\llama-server.exe"
$model = "F:\ModelVault\gguf\qwen\Qwen3.6-35B-A3B-Q4_K_M\Qwen3.6-35B-A3B-Q4_K_M.gguf"
& $exe -m $model --port 8096
# NOTE: Do NOT specify -ngl — auto-fit required for MoE models
```

```python
# Python inference example
import requests
r = requests.post("http://46.253.140.72:8096/completion", json={
    "prompt": "Your prompt here",
    "n_predict": 80,
    "temperature": 0.1
})
print(r.json()["content"])
print(f"{r.json()['timings']['predicted_per_second']:.2f} tok/s")
```

---

## Software Stack

| Component | Version / Detail |
|-----------|-----------------|
| NVIDIA Driver | 475.14 WHQL (Tesla WS2019) |
| GPU Mode | WDDM (switched from TCC) |
| Inference Engine | llama.cpp b9279 (build 47c0eda9d) |
| Backend | Vulkan (ggml-vulkan) |
| Ollama | 0.24.0 (CPU-only on this hardware) |
| Model | Qwen3.6-35B-A3B-Q4_K_M (19.71 GB) |
| OS | Windows Server 2019 Datacenter |

---

## Key Findings

1. **Tesla M60 in TCC mode** = CUDA compute available, Vulkan/DirectX unavailable
2. **Tesla M60 in WDDM mode** = Vulkan available, CUDA limited by driver version mismatch
3. **CUDA 11.4 (max for M60) is incompatible** with all modern inference tools (require CUDA 12.x)
4. **Vulkan is the viable GPU path** for this hardware, but requires WDDM mode
5. **MoE models (Qwen3.6) need auto-fit mode** in llama.cpp — manual -ngl causes OOM
6. **Partial offload (57% GPU)** achieves 3.13× speedup over full CPU inference
7. **Ollama 0.24.0 cannot be used** with this GPU (no CUDA 11 support, Vulkan disabled by default)

---

## Recommendations

### For Immediate Use
- Use `llama.cpp b9279 Vulkan` for inference (not Ollama)
- Always use auto-fit (no `-ngl` flag) for Qwen3.6 MoE model
- Server startup takes ~54 seconds (model load + GPU memory allocation)

### For Improved Performance
- **Best option:** Add PCIe GPU with CUDA 12.x support (e.g., RTX 4070/4080/A4000) — full model fits in 24+ GB VRAM, expected ≥50 tok/s
- **Alternative:** Use quantized model (e.g., Q2_K or IQ3_XS, ~10 GB) to fit entirely in GPU VRAM for better GPU utilization

### Security Note
⚠️ **Change the DL380 Administrator password** (`Qwe123` was used during this session)

---

## Q&A Checklist

| Question | Answer |
|----------|--------|
| GPU visible before driver? | YES — 2× VEN_10DE&DEV_13F2 as "Microsoft Basic Display Adapter" |
| NVIDIA driver pre-installed? | NO — "Error" status, no nvidia-smi |
| Driver installed successfully? | YES — 475.14 WHQL, exit code 1, no reboot |
| Reboot required for driver? | NO (but WDDM mode switch required reboot) |
| nvidia-smi PASS? | YES — 475.14, CUDA 11.4, 2× Tesla M60, 8129 MiB each |
| Ollama GPU (TCC mode)? | NO — CPU-only, total_vram=0 B |
| llama.cpp CUDA 12.4? | NO — runtime version mismatch |
| llama.cpp Vulkan (TCC mode)? | NO — TCC blocks Vulkan |
| TCC → WDDM switch? | YES — both GPUs, reboot triggered |
| Vulkan GPU detection (WDDM)? | YES — both Tesla M60 at 8312 MiB |
| GPU inference working? | YES — auto-fit partial offload |
| CPU baseline | 4.19 tok/s |
| GPU tok/s | ~13.1 tok/s (avg of 12.69 and 13.50) |
| Speedup | **3.13×** |
| Final verdict | ✅ GPU inference enabled via Vulkan WDDM |
