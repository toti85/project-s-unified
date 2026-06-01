# Cline Local Model Compatibility Test Plan
**Date:** 2026-05-21  
**Status:** PENDING EXECUTION — requires Qwen3.6 activation on DL380 first  
**Depends on:** MODEL_VAULT_QWEN36_SERVER_QUICKSTART_20260521.md

---

## Overview

Test whether VS Code Cline can use the local Qwen3.6-35B-A3B endpoint hosted on SHAYANSKA-DL380.  
This is compatibility testing only. The main Cline workflow remains on cloud API until explicitly approved.

**Infrastructure facts confirmed on 2026-05-21:**
- Ollama installed on DEV at `C:\Users\Admin\AppData\Local\Programs\Ollama\ollama.exe`
- No llama-server or LM Studio on DEV PATH
- DEV C: has only 14.2 GB free → model must run on DL380 (192.168.1.180)
- DL380 reachable on LAN via WinRM and RDP

---

## Phase A — Detect Active Serving Method

After the vault quickstart completes, determine which server is running on DL380.  
Run these detection commands **from DL380** (via WinRM or RDP terminal):

```powershell
# A1 — Ollama running?
Get-Process ollama -EA SilentlyContinue | Select-Object Name, Id
Invoke-RestMethod http://localhost:11434/api/tags -EA SilentlyContinue | ConvertTo-Json -Depth 3

# A2 — llama-server running?
Get-Process llama-server -EA SilentlyContinue | Select-Object Name, Id
Invoke-RestMethod http://localhost:8080/v1/models -EA SilentlyContinue | ConvertTo-Json

# A3 — LM Studio server running?
Get-Process "LM Studio" -EA SilentlyContinue | Select-Object Name, Id
Invoke-RestMethod http://localhost:1234/v1/models -EA SilentlyContinue | ConvertTo-Json

# A4 — What model is loaded?
# If Ollama:
ollama list

# If llama.cpp server:
# Check the process command line for --model path
Get-WmiObject Win32_Process | Where-Object { $_.Name -match "llama" } | Select-Object Name, CommandLine
```

**Decision matrix:**

| If active | Endpoint URL | Cline provider to use |
|-----------|-------------|----------------------|
| Ollama | `http://192.168.1.180:11434` | **Ollama** |
| llama-server | `http://192.168.1.180:8080/v1` | **OpenAI Compatible** |
| LM Studio | `http://192.168.1.180:1234/v1` | **LM Studio** or **OpenAI Compatible** |

---

## Phase B — Firewall / Port Check

From DEV machine, verify the DL380 port is accessible before configuring Cline:

```powershell
# Run from DEV
$dl380 = "192.168.1.180"

# Test all candidate ports
@(11434, 8080, 8081, 1234) | ForEach-Object {
    $r = Test-NetConnection -ComputerName $dl380 -Port $_ -WarningAction SilentlyContinue
    [PSCustomObject]@{ Port = $_; Open = $r.TcpTestSucceeded }
} | Format-Table -AutoSize

# If port is open, do HTTP probe:
# For Ollama:
Invoke-RestMethod "http://${dl380}:11434/api/tags" -TimeoutSec 10

# For llama.cpp:
Invoke-RestMethod "http://${dl380}:8080/v1/models" -TimeoutSec 10
```

**If port is blocked:** On DL380, add firewall exception:
```powershell
# On DL380 — run via WinRM or RDP
New-NetFirewallRule -DisplayName "Local LLM Ollama" -Direction Inbound -Protocol TCP -LocalPort 11434 -Action Allow -Profile Private
New-NetFirewallRule -DisplayName "Local LLM llama.cpp" -Direction Inbound -Protocol TCP -LocalPort 8080 -Action Allow -Profile Private
```

---

## Phase C — Model Info Probe

Retrieve the model's declared capabilities before connecting Cline.

### C1 — If Ollama

```powershell
# From DEV or DL380
$ep = "http://192.168.1.180:11434"

# List models
Invoke-RestMethod "$ep/api/tags" | ConvertTo-Json -Depth 5

# Get model details (context window, family, etc.)
$body = @{ name = "qwen3.6:35b-a3b-q4_k_m" } | ConvertTo-Json
Invoke-RestMethod "$ep/api/show" -Method POST -Body $body -ContentType "application/json" | ConvertTo-Json -Depth 5
```

**Key field to record:** `context_length` from model info.  
Qwen3.6-35B-A3B expected context: up to **128K tokens** (architecture limit), practical default ~8K-32K in Ollama.

### C2 — If llama.cpp server

```powershell
$ep = "http://192.168.1.180:8080"

# OpenAI-compatible list
Invoke-RestMethod "$ep/v1/models" | ConvertTo-Json -Depth 3

# Chat completions test (raw)
$body = @{
    model = "qwen3.6"
    messages = @(@{ role = "user"; content = "ping" })
    max_tokens = 20
} | ConvertTo-Json -Depth 4
Invoke-RestMethod "$ep/v1/chat/completions" -Method POST -Body $body -ContentType "application/json"
```

---

## Phase D — Configure Cline Provider

### D1 — Cline settings location

Cline stores its active API config in VS Code settings. Open:  
**VS Code → Settings (Ctrl+,) → search "cline" → "Cline: Api Provider"**

Or edit directly:  
`C:\Users\Admin\AppData\Roaming\Code\User\settings.json`

### D2 — Provider configuration snippets

**Option A: Ollama provider (preferred if Ollama is active)**
```json
{
  "cline.apiProvider": "ollama",
  "cline.ollamaBaseUrl": "http://192.168.1.180:11434",
  "cline.ollamaApiModelId": "qwen3.6:35b-a3b-q4_k_m"
}
```

**Option B: OpenAI Compatible (for llama.cpp or LM Studio)**
```json
{
  "cline.apiProvider": "openai-native",
  "cline.openAiNativeApiKey": "not-needed",
  "cline.openAiBaseUrl": "http://192.168.1.180:8080/v1",
  "cline.openAiModelId": "qwen3.6"
}
```

**Option C: LM Studio provider**
```json
{
  "cline.apiProvider": "lmstudio",
  "cline.lmStudioBaseUrl": "http://192.168.1.180:1234",
  "cline.lmStudioModelId": "qwen3.6-35b-a3b-q4_k_m"
}
```

### D3 — Fallback: OpenAI Compatible with Ollama backend

If the Ollama provider in Cline doesn't support remote endpoints, use the OpenAI-compatible path which Ollama also exposes:
```json
{
  "cline.apiProvider": "openai-native",
  "cline.openAiNativeApiKey": "ollama",
  "cline.openAiBaseUrl": "http://192.168.1.180:11434/v1",
  "cline.openAiModelId": "qwen3.6:35b-a3b-q4_k_m"
}
```
Ollama exposes `/v1/chat/completions` at port 11434 compatible with OpenAI clients.

### D4 — Context window hint for Cline

Cline may need a manual context window override for newer models:
```json
{
  "cline.modelMaxTokens": 32768,
  "cline.modelMaxOutputTokens": 4096
}
```

---

## Phase E — Connectivity Smoke Test (Pre-Cline)

Before opening Cline, verify the endpoint works with a raw HTTP test from DEV:

```powershell
# E1 — Ollama path
$t0 = Get-Date
$body = @{
    model  = "qwen3.6:35b-a3b-q4_k_m"
    prompt = "Respond in one word: OK"
    stream = $false
} | ConvertTo-Json
$r = Invoke-RestMethod "http://192.168.1.180:11434/api/generate" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 120
$elapsed = (Get-Date) - $t0
Write-Host "Response: $($r.response)"
Write-Host "Elapsed: $($elapsed.TotalSeconds)s"
Write-Host "GPU used: $($r.model)" # Ollama response includes eval stats

# E2 — OpenAI-compatible path
$t0 = Get-Date
$body = @{
    model    = "qwen3.6"
    messages = @(@{ role = "user"; content = "Respond in one word: OK" })
    max_tokens = 10
} | ConvertTo-Json -Depth 4
$r = Invoke-RestMethod "http://192.168.1.180:8080/v1/chat/completions" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 120
$elapsed = (Get-Date) - $t0
Write-Host "Response: $($r.choices[0].message.content)"
Write-Host "Elapsed: $($elapsed.TotalSeconds)s"
```

**Record:** response text, latency in seconds, whether it completed.

---

## Phase F — Cline Compatibility Test Tasks

### F1 — Test Task: Read File + Explain + Propose

Target file (small, safe): `interactive_layer/response_polish.py`

**Cline prompt to use:**
```
Read the file interactive_layer/response_polish.py.
1. In 2–3 sentences, explain what this file does.
2. Propose ONE small, harmless improvement to the code style or documentation.
Do not make any changes. Just explain and propose.
```

**What to record:**
- Did Cline start the task? (yes/no)
- Did Cline read the file successfully? (yes/no)
- Did the model produce a coherent explanation? (yes/no)
- Was the Hungarian language handled correctly? (yes/partial/no)
- Did Cline complete without error? (yes/no)
- Total latency from task start to completion (seconds)
- Any truncation, hang, or timeout? (yes/no)

### F2 — Test Task: Hungarian Language Smoke

**Cline prompt:**
```
Írj 3 rövid magyar mondatot arról, miért hasznos egy lokális AI modell a Project-S számára.
```

This is the canonical Project-S local LLM smoke prompt.

**Pass criteria:**
- Response is in Hungarian
- 3 sentences produced
- Grammatically coherent
- No hallucinated HTML, code, or role-play artifacts

### F3 — Context Window Stress (optional, only if F1+F2 pass)

**Cline prompt:**
```
Read ALL files in the interactive_layer/ directory and summarize the overall architecture in 5 bullet points.
```

This sends a larger context. If Cline fails with a context limit error, record the error message.

---

## Phase G — Metrics to Collect

| Metric | How to measure | Target |
|--------|---------------|--------|
| First-token latency | Time from send to first streaming token | < 10s |
| Full response latency (F1) | Time to complete read+explain task | < 90s |
| Tokens/second | From Ollama eval_duration or llama.cpp stats | ≥ 5 tok/s (usable) |
| GPU utilization | nvidia-smi on DL380 during inference | GPU > 0% = GPU used |
| VRAM used | nvidia-smi during inference | Record MB used |
| Completion rate | Out of 3 tasks: how many complete | 3/3 = reliable |
| Context handled | Largest prompt completed without truncation | ≥ 4096 tokens |
| Hungarian accuracy | F2 task: are all 3 sentences in HU | 3/3 |

---

## Phase H — Pass / Fail Criteria

### PASS — Usable for Project-S development

All of the following:
- [ ] Endpoint reachable from DEV without VPN
- [ ] Raw HTTP smoke test responds within 60s
- [ ] Cline F1 task completes (read + explain) without error
- [ ] Cline F2 task produces Hungarian output
- [ ] Tokens/second ≥ 5
- [ ] GPU is used (not CPU-only; CPU-only at 35B is unusably slow)

### PARTIAL — Usable for occasional tasks only

- Endpoint works but latency > 60s/response
- CPU-only mode (tokens/sec < 2)
- Context limit below 8192 tokens

### FAIL — Not viable

- Port blocked from DEV
- Cline cannot authenticate/connect
- Model crashes or produces incoherent output
- Tokens/sec < 1 (implies CPU-only on 35B params)

---

## Phase I — Configuration Rollback

**After testing is complete, restore Cline to the original API provider:**

```json
// Restore in VS Code settings.json — undo Phase D changes
// Remove or revert any cline.apiProvider changes made during this test
```

Do not commit local-model Cline settings to any shared config until the model is proven stable.

---

## Phase J — Execution Checklist

- [ ] J1: Vault quickstart complete (DL380 password entered, model downloaded)
- [ ] J2: Serving method confirmed (Ollama / llama.cpp / LM Studio)
- [ ] J3: DL380 port accessible from DEV (Phase B)
- [ ] J4: Raw HTTP smoke test passes (Phase E)
- [ ] J5: Cline provider configured (Phase D, correct option)
- [ ] J6: Cline F1 task executed and recorded
- [ ] J7: Cline F2 task executed and recorded
- [ ] J8: GPU usage confirmed via nvidia-smi
- [ ] J9: Metrics table completed (Phase G)
- [ ] J10: Pass/fail verdict recorded
- [ ] J11: Cline config restored to cloud API (Phase I)

---

## Results Section (fill in after execution)

| Question | Answer |
|----------|--------|
| 1. Active serving method | ___ |
| 2. Endpoint URL | ___ |
| 3. Model name (as seen by Cline) | ___ |
| 4. Context window supported | ___ |
| 5a. Ollama provider works? | ___ |
| 5b. OpenAI Compatible works? | ___ |
| 5c. LM Studio works? | ___ |
| 6. F1 task (read+explain) | PASS / FAIL / PARTIAL |
| 6. F2 task (Hungarian) | PASS / FAIL |
| 7a. First-token latency | ___s |
| 7b. Full F1 latency | ___s |
| 7c. Tokens/second | ___ tok/s |
| 8. GPU used? | yes / no / unknown |
| 9. VRAM used | ___ MB |
| 10. Overall verdict | PASS / PARTIAL / FAIL |
| 11. Usable for Project-S dev? | yes / partial / no |
| 12. Recommended next step | ___ |
