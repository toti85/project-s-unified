# PROJECT_S_SERVER_PHASE_BLUEPRINT_AND_LOCAL_INTELLIGENCE_ACTIVATION_20260515

**Date:** 2026-05-15  
**Status:** Strategic Blueprint & Technical Migration Plan  
**Target:** Project-S Server Phase (24/7 Local LLM + Python AI Service)

---

## 1. Executive Verdict — Primary Migration Strategy Recommendation

**Recommendation: Two-Stage Hybrid Migration (Windows-First Validation → Proxmox Isolation)**

Project-S should **not** immediately deploy Proxmox. The immediate priority is hardware driver maturity, local inference stability, and Python service persistence on the existing Windows Server 2019 image. 

**Strategy:**
1. **Phase 1 (Days 0–30):** Deploy directly on Windows Server 2019. Install NVIDIA drivers, configure `llama.cpp`/Ollama for local inference, and run the Python AI service via NSSM/systemd-like Windows services. Validate Tesla M60 VRAM constraints and model routing.
2. **Phase 2 (Day 30+):** Migrate to Proxmox VE. Virtualize the Factory Systems, Cognitive Core, AI Models, and Dream Mode into isolated VMs. Passthrough the Tesla M60 to the AI Models VM for dedicated GPU allocation.

This approach minimizes initial downtime, avoids hypervisor passthrough debugging during the critical first week, and allows Project-S to begin local inference immediately while preserving the long-term isolation architecture.

---

## 2. Current Project-S State — What Is Actually Ready To Move

Based on `self_state.json` and `PROJECT_S_OVERVIEW.md` (validated 2026-05-15):

| Component | Status | Notes |
|-----------|--------|-------|
| **Canonical Runtime** | `SuperIntelligentAI(use_meta_controller=True)` | Active. Routes through MetaController → Qwen3 235B planning → SmartToolOrchestrator → Evaluator → Witness/meta_evidence. |
| **AgentLoop** | Archived | Standalone MetaController dispatcher is dormant. |
| **Active Tools** | 15+ verified | DDGS web search live. Browser automation live. |
| **File I/O** | Fixed | `file_reader` dispatch (GAP_024) and `file_writer` path-corruption (GAP_025) resolved. |
| **Synthesis Default** | `Qwen3.6-35B-A3B` | Verified runtime synthesis default. |
| **State Management** | Restored | `self_state.json` validated. Gap state: 25 total / 24 resolved / 1 accepted / 0 active. |
| **Bridges** | Operational | `witness/bridges/organism_to_meta.py` (GAP_001), `witness/evidence_reader.py` (GAP_002), `witness/bridges/state_reader.py` (GAP_004) all resolved and read-only adapters functional. |
| **Sleeping Components** | Ready | MetaController, StrategyCouncil, ExecutionValidator, Organism (Observer/Prioritizer/Proposer). |

**Readiness Assessment:** The cognitive core, state bridges, and tool orchestration are production-stable and ready for server deployment. The primary gap is infrastructure routing (API vs. Local).

---

## 3. Server Reality Check — Component-by-Component Table for DL380 Gen9

| Component | Specification | Impact on Project-S |
|-----------|---------------|---------------------|
| **CPU** | 2x Xeon E5-2699 v3 (36 cores / 72 threads) | Excellent for Python async services, background state backups, and CPU-offloaded KV cache management. |
| **RAM** | 128 GB DDR4 ECC | Ample for OS, Python services, and large context windows. Can absorb VRAM bottlenecks via CPU offloading. |
| **GPU** | Tesla M60 (2x Maxwell GM204, 16 GB GDDR5 total; 2x 8 GB boards) | **Critical Constraint.** Maxwell architecture (SM 5.2). No NVLink. Effective VRAM per board is 8 GB. Requires careful quantization and CPU offloading for 35B-class models. |
| **Storage** | ~1.6 TB NVMe | High I/O throughput for rapid model loading, `meta_evidence.jsonl` streaming, and state persistence. |
| **PSU** | Dual PSU | Enables true 24/7 uptime without single-point power failure. |
| **OS** | Windows Server 2019 | Pre-installed. Requires driver updates and service management configuration. |

---

## 4. Migration Architecture Options — Compare Windows-first vs Proxmox-first vs Two-stage hybrid

| Architecture | Pros | Cons | Recommendation |
|--------------|------|------|----------------|
| **Windows-First** | Leverages existing image. Faster initial deployment. Easier CUDA/llama.cpp debugging. | Poor service isolation. Harder to manage VM boundaries. Windows Server 2019 EOL risks long-term. | **Use for Phase 1 (0-30 days)** |
| **Proxmox-First** | Strong isolation (Factory, Cognitive, AI, Sandbox). Better resource allocation. | High initial setup time. GPU passthrough debugging on Maxwell can be complex. Delays local LLM activation. | **Defer to Phase 2** |
| **Two-Stage Hybrid** | Combines rapid validation with long-term isolation. Minimizes downtime. | Requires data migration later. | **✅ RECOMMENDED** |

---

## 5. Recommended Phase Architecture — Concrete Target Architecture with Text Diagram

### Phase 1: Windows Server 2019 Host (Days 0–30)
```text
[Windows Server 2019 Host]
├── NVIDIA Driver + CUDA Toolkit (Maxwell SM 5.2 compatible)
├── Python 3.12+ Runtime
│   ├── FastAPI Async Service (Project-S Core)
│   ├── SmartToolOrchestrator + Evaluator
│   └── NSSM Service Manager (Persistence & Auto-restart)
├── Local LLM Inference Engine
│   ├── llama.cpp (Windows build)
│   └── Ollama (Optional, for lighter routing)
├── Tesla M60 (GPU Passthrough to llama.cpp)
└── State Persistence Layer
    ├── self_state.json
    ├── meta_evidence.jsonl
    └── Scheduled Backup Scripts (NVMe → External/Cloud)
```

### Phase 2: Proxmox VE Host (Day 30+)
```text
[Proxmox VE Host]
├── VM 1: Factory Systems (Isolated business-critical services)
├── VM 2: Project-S Cognitive Core (Python AI Service + Orchestrator)
├── VM 3: AI Models VM (GPU Passthrough → Tesla M60 → Local LLMs)
└── VM 4: Dream Mode (Sandbox experiments)
```

---

## 6. Local LLM Activation Strategy — Role Routing

| Role | Current Host | Target Host | Rationale |
|------|--------------|-------------|-----------|
| **Planning/Strategy** | API (Qwen3 235B) | **Stay API** | Requires high reasoning depth. VRAM constraints on M60 make local 35B planning unreliable for complex multi-step tasks. |
| **Synthesis/Execution** | API (Qwen3.6-35B-A3B) | **Move Local** | High volume, lower complexity. Local deployment reduces latency and API costs. |
| **Coding** | API | **Move Local** | `Qwen3-Coder-Next` (8B/14B) fits easily in 8GB VRAM. Fast, cheap, and highly effective for code generation. |
| **Evaluator/Witness** | API | **Move Local (Small)** | `Qwen3-8B` or `Qwen2.5-Coder` for fast, cheap verification of tool outputs and state consistency. |

**Routing Policy:** All synthesis, coding, and evaluation tasks route to local `llama.cpp`/Ollama. Planning and complex multi-agent coordination remain on the external API until local 35B inference proves stable over 72-hour continuous runs.

---

## 7. Qwen3.6 Local Feasibility Decision — Hard Answer with Evidence

**Decision:** `Qwen3.6-35B-A3B` is **feasible but constrained** on the Tesla M60. It will run via `llama.cpp` using extreme quantization and CPU offloading. Ollama support exists but is rough for multimodal GGUFs.

**Evidence:**
- `Qwen3.6-35B-A3B-MTP-GGUF` is available on Unsloth (`unsloth/Qwen3.6-35B-A3B-MTP-GGUF`).
- TurboQuant enables extreme KV cache quantization (`--ctk turbo3 -ctv turbo3`), reducing VRAM pressure (`https://github.com/ggml-org/llama.cpp/discussions/20969`).
- VRAM requirements for 35B-A3B quantized models are tight. Q4_K_M or Q4_K_XL can fit in 16GB total, but with only 8GB per board and no NVLink, the model must either use CPU offloading for the KV cache or run on a single board with heavy quantization (`https://www.knightli.com/en/2026/05/01/qwen3-6-local-vram-quantization-table/`).
- Tesla M60 (Maxwell SM 5.2) is still workable with `llama.cpp`, but `vLLM` support for Maxwell is deprecated/limited. `llama.cpp` is the only viable high-performance inference engine for this hardware in 2026.
- Ollama's `mmproj` integration for multimodal GGUFs is currently rough, requiring separate main + `mmproj.gguf` files (`https://ollama.com/batiai/qwen3.6-35b`).

**Our first local model experiment should be:** `Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf` via `llama.cpp`, configured with `--ctx-size 8192` and CPU offloading for the KV cache to bypass the 8GB per-board VRAM limit.

---

## 8. 72-Hour Server Activation Plan — 0-24h / 24-48h / 48-72h Concrete Steps

| Timeframe | Task | Success Criteria |
|-----------|------|------------------|
| **0-24h** | Hardware boot, Windows Server 2019 setup, NVIDIA driver installation for Tesla M60, verify CUDA toolkit compatibility. | `nvidia-smi` shows Tesla M60. CUDA 12.x toolkit installed. No driver conflicts. |
| **24-48h** | Install Python 3.12+, FastAPI, `llama.cpp` (Windows build), download `Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf`, run initial inference test. | `llama-server` starts. Token generation > 2 tok/s. VRAM usage < 7.5GB per board. |
| **48-72h** | Configure NSSM for Python AI service, set up state backup scripts, run integration test with existing Project-S tools. | Python service runs 24h without memory leaks. `self_state.json` updates correctly. Backup completes. |

---

## 9. First 7 Days of 24/7 Project-S Operation — Table of Daily/Nightly Jobs

| Day | Task | Frequency | Owner/Agent |
|-----|------|-----------|-------------|
| **1** | Service startup, health checks, GPU memory monitoring | Continuous | System/NSSM |
| **2** | Local LLM routing test (Synthesis → Local, Planning → API) | Hourly | SmartToolOrchestrator |
| **3** | State persistence backup (`self_state.json`, `meta_evidence.jsonl`) | Nightly | Scheduled Task |
| **4** | Tool integration verification (DDGS, Browser Automation) | Daily | ExecutionValidator |
| **5** | Performance benchmarking (Token throughput, latency) | Daily | MetaController |
| **6** | Failover testing (Simulate GPU crash, verify auto-restart) | Daily | System/NSSM |
| **7** | Full autonomous run simulation (End-to-end mission) | Daily | SuperIntelligentAI |

---

## 10. Risks, Failure Modes, and Anti-Patterns — Blunt List

1. **VRAM Exhaustion:** Tesla M60's 8GB per board limit will cause OOM crashes if KV cache is not offloaded to CPU. *Mitigation:* Use `--ctx-size 8192`, TurboQuant, and CPU offloading.
2. **Windows Server 2019 EOL:** Security risks long-term. *Mitigation:* Isolate from public internet, use firewall rules, migrate to Proxmox by Day 30.
3. **Proxmox Migration Complexity:** GPU passthrough debugging can cause days of downtime. *Mitigation:* Delay until local inference is stable.
4. **Over-Reliance on Local LLM for Planning:** 35B models on Maxwell will hallucinate on complex multi-step reasoning. *Mitigation:* Keep planning on API.
5. **Anti-Pattern:** Attempting to run 35B models on CPU fallback. *Result:* Token throughput drops to < 0.5 tok/s, breaking real-time agentic loops.

---

## 11. Decision Gates — Explicit Go/No-Go Criteria

| Gate | Criteria | Action |
|------|----------|--------|
| **Gate 1: Hardware** | Tesla M60 recognized by Windows, CUDA drivers installed, `nvidia-smi` functional. | Go to Phase 1. |
| **Gate 2: Inference** | `llama.cpp` runs `Qwen3.6-35B-A3B` Q4_K_XL with > 2 tok/s and < 7.5GB VRAM per board. | Go to Phase 1. |
| **Gate 3: Service** | Python AI service runs 24h without memory leaks or crashes. | Go to Phase 1. |
| **Gate 4: State** | `self_state.json` updates correctly, backups complete successfully. | Go to Phase 1. |
| **Gate 5: Proxmox** | Local inference stable for 30 days, no critical bugs. | Go to Phase 2 (Proxmox migration). |

---

## 12. Final Recommendation — 5 Concrete Points

1. **Choice:** Two-stage hybrid migration. Start on Windows Server 2019, migrate to Proxmox after 30 days.
2. **First Model:** `Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf` via `llama.cpp`, with CPU offloading for KV cache.
3. **Immediate Action:** Install NVIDIA drivers for Tesla M60 on Windows Server 2019 and verify CUDA compatibility.
4. **What NOT to Do:** Do not install Proxmox yet. Do not attempt to run 35B models on CPU fallback. Do not route planning tasks locally until 72-hour stability is proven.
5. **Highest-Leverage Next Action:** Deploy FastAPI + `llama.cpp` service and route synthesis/coding tasks locally to reduce latency and API costs immediately.

---

## 12.5. Server Phase 0 — iLO Read-Only Control VERIFIED (2026-05-15)

**Status:** Phase 0 complete. iLO read-only access confirmed.

| Item | Value |
|------|-------|
| iLO Controller | `project_s/infrastructure/ilo_controller.py` (689 lines) |
| API | HPE iLO 4 Redfish v1 |
| Endpoint | `https://46.253.140.72:89` |
| Server Model | HP ProLiant DL380 Gen9 |
| Serial | CZ3733LABY |
| BIOS | P89 v3.40 (08/29/2024) |
| Power State | ON |
| Health | OK |
| Redirect Workaround | `192.168.1.89` → public endpoint (essential, exercised 3x) |
| Commands Issued | Read-only: connect, get_system_info, get_power_state, get_health_summary |
| Power Commands | Available (power_on, power_off, restart_server) but NOT exercised |

**Evidence:** `reports/NEW_DL380_ILO_READONLY_CONNECTIVITY_VERIFICATION_20260515.md`

**What this means for the blueprint:**
- The server is physically powered on and iLO is responsive
- The NAT redirect workaround is built into the iLO controller and will work for any future iLO operations
- Host OS LAN is NOT yet connected — the server's main network interface is offline
- Next prerequisite: Toti plugs in the normal server LAN cable → host OS reachability discovery (IP/RDP/SSH)
- Once host OS is reachable, the Phase 1 Windows Server deployment plan proceeds as written

**What is still unknown:**
- Host OS IP address (LAN not connected)
- Whether Windows Server 2019 is installed or needs imaging
- Whether the Tesla M60 is recognized by the host OS
- Whether the NVMe drives are initialized

---

## 13. Confirmed Facts vs Assumptions

| Category | Statement | Source/Status |
|----------|-----------|---------------|
| **Internal Confirmed** | `self_state.json` schema v0.1, gap state 25/24/0/1, components active/sleeping. | `self_state.json` (2026-05-15) |
| **Internal Confirmed** | `Qwen3.6-35B-A3B` is verified runtime synthesis default. | `PROJECT_S_OVERVIEW.md` |
| **Internal Confirmed** | GAP_001, GAP_002, GAP_004 resolved with read-only adapters. | `self_state.json` |
| **External Confirmed** | `Qwen3.6-35B-A3B-MTP-GGUF` available on Unsloth. | `https://unsloth.ai/docs/models/qwen3.6` |
| **External Confirmed** | TurboQuant enables extreme KV cache quantization. | `https://github.com/ggml-org/llama.cpp/discussions/20969` |
| **External Confirmed** | Ollama's `mmproj` integration for multimodal GGUFs is rough. | `https://ollama.com/batiai/qwen3.6-35b` |
| **External Confirmed** | Tesla M60 specs (2x Maxwell GM204, 16GB total, no NVLink). | Hardware context |
| **Phase 0 Verified** | iLO read-only control to DL380 Gen9 confirmed (2026-05-15). | `reports/NEW_DL380_ILO_READONLY_CONNECTIVITY_VERIFICATION_20260515.md` |
| **Strategic Assumption** | Windows Server 2019 is stable enough for 30-day validation phase. | Assumption |
| **Strategic Assumption** | Tesla M60 SM 5.2 is sufficient for `llama.cpp` inference without `vLLM`. | Assumption |
| **Strategic Assumption** | CPU offloading can compensate for 8GB per-board VRAM limit. | Assumption |

---

## 15. Sources

**Internal Documents:**
- `C:\ProjectS-Unified\self_state.json`
- `C:\ProjectS-Unified\PROJECT_S_OVERVIEW.md`
- `C:\ProjectS-Unified\project_s\infrastructure\ilo_controller.py`
- `C:\ProjectS-Unified\project_s\infrastructure\test_ilo_controller.py`

**External Research:**
- `https://unsloth.ai/docs/models/qwen3.5`
- `https://unsloth.ai/docs/models/qwen3.6`
- `https://github.com/ggml-org/llama.cpp/discussions/20969`
- `https://github.com/QwenLM/Qwen3.6`
- `https://qwen.readthedocs.io/en/latest/run_locally/llama.cpp.html`
- `https://www.knightli.com/en/2026/05/01/qwen3-6-local-vram-quantization-table/`
- `https://huggingface.co/unsloth/Qwen3-Coder-Next-GGUF`
- `https://ollama.com/batiai/qwen3.6-35b`

**iLO Verification Reports:**
- `reports/ILO_SCRIPT_RECOVERY_SEARCH_20260515.md`
- `reports/NEW_DL380_ILO_READONLY_CONNECTIVITY_VERIFICATION_20260515.md`
