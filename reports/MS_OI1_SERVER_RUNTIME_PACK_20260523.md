# MS-OI1: Server Runtime Pack

**Date:** 2026-05-24
**Agent:** Cline
**Purpose:** Minimal runtime pack for DL380 server deployment

---

## Target Location

`C:\ProjectS-ServerRuntimePack\` on DL380 (46.253.140.72)

---

## Files to Include

### Core Documents
| File | Source | Purpose |
|------|--------|---------|
| `self_state.json` | `C:\ProjectS-Unified\self_state.json` | System state, 33 milestones, 6 risks |
| `PROJECT_S_OVERVIEW.md` | `C:\ProjectS-Unified\PROJECT_S_OVERVIEW.md` | AI agent orientation doc |
| `PROJECT_S_STATUS_AND_JOURNAL.md` | `C:\ProjectS-Unified\PROJECT_S_STATUS_AND_JOURNAL.md` | Session journal v2.7 |
| `PROJECT_S_FOUNDATION.md` | `C:\ProjectS-Unified\PROJECT_S_FOUNDATION.md` | Immutable principles |

### Configuration
| File | Source | Purpose |
|------|--------|---------|
| `.env` | `C:\ProjectS-Unified\.env` | API keys (OpenRouter, etc.) |
| `config/` | `C:\ProjectS-Unified\config\` | models.yaml, risk.yaml, etc. |

### Interactive Layer
| File | Source | Purpose |
|------|--------|---------|
| `interactive_layer/` | `C:\ProjectS-Unified\interactive_layer\` | Web UI + API server |

### Core Code
| File | Source | Purpose |
|------|--------|---------|
| `src/core/super_intelligent_ai.py` | SAI main | Primary Doer pipeline |
| `src/core/meta/meta_controller.py` | MetaController | Multi-iteration goal execution |
| `src/core/evaluator.py` | Evaluator | Output quality gate |
| `tools/tools/registry/smart_orchestrator.py` | Orchestrator | Tool selection + synthesis |
| `tools/tools/registry/` | All tools | 15 registered tools |

### ModelVault Notes
| File | Source | Purpose |
|------|--------|---------|
| `MODELVAULT_NOTES_DL380_20260522.md` | `reports/` | Model deployment guide |

### Reports Index
| File | Source | Purpose |
|------|--------|---------|
| `MS_OQ1_E_DIRECT_STRUCTURE_FINAL_VALIDATION_20260523.md` | GAP_031 validation |
| `MS_OQ1_DOC_SYNC_REPORT_20260523.md` | Doc sync record |
| `MS_OI1_NETWORK_INVENTORY_AND_REMOTE_STRATEGY_20260523.md` | Network inventory |
| `MS_OI1_SERVER_RUNTIME_PACK_20260523.md` | This file |
| `BGE_M3_EMBEDDING_ACTIVATION_VERDICT_20260522.md` | BGE-M3 smoke test |
| `LOCAL_CLINE_QWEN25_CODER_14B_BENCHMARK_20260522.md` | Coder benchmark |

---

## Files to EXCLUDE

| Category | Reason |
|----------|--------|
| `memory/intelligence/meta_evidence.jsonl` | 104 MB, write-only log |
| `browser*` | Browser profiles, caches |
| `audits/` | Bounty hunting (separate workspace) |
| `archive/`, `ARCHIVE_VERSIONS/` | Historical archives |
| `*.exe` installers | BlueStacks, Delta APKs |
| `*.apk` files | Android packages |
| `*.zip` files | Large archives |
| `logs/` | Old logs |
| `tests/` | Test files (can be regenerated) |
| `*_test*.py` | Test scripts |
| `debug_*.py` | Debug scripts |
| `*_results.json` | Old test results |

---

## Model Startup Notes

### Qwen3.6-35B (Reasoning/Survival Model)
```powershell
# On DL380:
F:\ModelVault\scripts\start_qwen36_llama_server_vulkan.ps1
# Port: 8096 (llama-server) / 8097 (Cline proxy)
# VRAM: ~12-13 GB
# Speed: ~12-14 tok/s
```

### Qwen2.5-Coder-14B (Local Cline Small-Task Model)
```powershell
# On DL380:
F:\ModelVault\scripts\start_qwen25_coder_14b_vulkan.ps1
# Port: 8098
# VRAM: ~9.5 GB
# Speed: ~10-12.5 tok/s
# Context: 4096 tokens
```

### BGE-M3 (Embedding/RAG Model)
```powershell
# On DL380:
F:\ModelVault\scripts\start_bge_m3_embedding_server.ps1
# Port: 8099
# CPU-only (no GPU layers)
# Latency: ~50-80ms per embedding
```

---

## Estimated Size

| Category | Size |
|----------|------|
| Core docs | ~50 KB |
| Config | ~10 KB |
| Interactive Layer | ~200 KB |
| Core code | ~500 KB |
| Reports | ~100 KB |
| **Total** | **~1 MB** |

---

*End of Server Runtime Pack specification.*