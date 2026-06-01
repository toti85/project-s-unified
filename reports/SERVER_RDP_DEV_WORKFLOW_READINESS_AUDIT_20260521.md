# SERVER RDP / DEV Workflow Readiness Audit

**Date:** 2026-05-21 15:55 UTC+3  
**Type:** AUDIT ONLY — No modifications made  
**Scope:** Assess SHAYANSKA-DL380 readiness as future RDP-based Project-S development environment  
**Auditor:** Cline (automated audit from DEV machine)

---

## 1. Executive Verdict

**A. Is DL380 ready today for occasional RDP inspection?** YES (with caveats)  
**B. Is DL380 ready today as primary Project-S dev environment?** NO  
**C. What is missing?** See Section 5  
**D. Recommended next step:** Keep DEV canonical, prepare local LLM first, revisit RDP dev workflow later

---

## 2. Pre-Run Environment Verification

### 2.1 Current Machines

| Property | DEV Machine (Canonical) | DL380 (Server/Staging) |
|----------|------------------------|------------------------|
| Hostname | DESKTOP-VAR2T1H | SHAYANSKA-DL380 |
| OS | Windows 10 (10.0.26200) | Windows Server (unknown exact version) |
| Architecture | AMD64 | AMD64 (DL380 hardware) |
| Python | 3.11.9 | Unknown (not verified remotely) |
| pip | 25.0.1 | Unknown |
| Git | 2.54.0 | Unknown |
| Node.js | 22.16.0 | Unknown |
| PowerShell | 5.1 | Unknown |
| VS Code | Not installed (Cline used via IDE) | Unknown |
| NVIDIA GPU | Quadro P2000 (driver 573.71) | Unknown |
| Project-S Path | C:\ProjectS-Unified | C:\ProjectS\project-s-code (staging) |

### 2.2 Connectivity

| Test | Result |
|------|--------|
| Ping DL380 | ✅ REACHABLE |
| RDP port 3389 | ✅ OPEN |
| WinRM remote execution | ❌ NOT TRUSTED (ServerNotTrusted error) |
| External WinRM (previous) | ✅ Works (from prior audit) |

---

## 3. RDP / Remote Access Assessment

### 3.1 RDP Status

- **RDP enabled on DL380:** YES (port 3389 is open and accepting connections)
- **RDP reachable on LAN:** YES (verified via Test-NetConnection)
- **RDP on DEV machine:** DISABLED (fDenyTSConnections = 1)

### 3.2 External RDP Plan

| Option | Assessment |
|--------|------------|
| Direct port forward (3389→3389) | ❌ NOT RECOMMENDED — RDP is a high-value target for brute-force attacks |
| VPN (WireGuard/OpenVPN) | ✅ RECOMMENDED — secure tunnel, then RDP over VPN |
| No external exposure | ✅ SAFEST — RDP only on LAN |

### 3.3 WinRM Status

- **External WinRM:** Previously confirmed working (from earlier audit)
- **LAN WinRM from DEV:** NOT TRUSTED — requires `Set-Item WSMan:\localhost\Client\TrustedHosts` or HTTPS/Kerberos
- **Mitigation:** Add DL380 to TrustedHosts on DEV machine if remote PowerShell needed

### 3.4 Security Note

⚠️ **Do NOT expose RDP directly to the internet** unless explicitly approved later with:
- Strong password policy
- Network-level authentication (NLA)
- Fail2Ban equivalent for Windows
- VPN tunnel as primary access method

---

## 4. Development Environment Inventory

### 4.1 DEV Machine (Canonical Master)

| Tool | Version | Status |
|------|---------|--------|
| Python | 3.11.9 | ✅ |
| pip | 25.0.1 | ✅ |
| Git | 2.54.0 | ✅ |
| Node.js | 22.16.0 | ✅ |
| PowerShell | 5.1 | ✅ |
| NVIDIA GPU | Quadro P2000 | ✅ (local LLM capable) |
| VS Code | Not installed | ⚠️ (Cline works via IDE integration) |
| Cline | Available | ✅ |

### 4.2 DL380 (Server/Staging)

| Tool | Version | Status |
|------|---------|--------|
| Python | Unknown | ❓ (needs verification) |
| pip | Unknown | ❓ |
| Git | Unknown | ❓ |
| Node.js | Unknown | ❓ |
| PowerShell | Unknown | ❓ |
| NVIDIA GPU | Unknown | ❓ |
| VS Code | Unknown | ❓ |
| Cline | Unknown | ❓ |
| Project-S staging | C:\ProjectS\project-s-code | ✅ EXISTS |

**Note:** Remote PowerShell execution was blocked (WinRM not trusted), so DL380 tool versions could not be verified remotely. Manual RDP session needed for full inventory.

---

## 5. Workspace Separation Design

### 5.1 Proposed Future Layout

```
C:\ProjectS\
├── project-s-code\        # current staging copy (NOT canonical)
├── runtime\               # running services, processes
│   ├── interactive_layer\
│   ├── logs\
│   └── data\
├── logs\                  # server logs (separate from project logs)
│   ├── uvicorn\
│   ├── sai_runner\
│   └── system\
├── reports\               # server-side reports
├── local_models\          # local LLM models (if deployed)
│   ├── llama\
│   └── mistral\
└── dev_workspace\         # ONLY if server dev is approved later
    └── ProjectS-Unified\  # mirror of DEV canonical
```

### 5.2 Important Rule

⚠️ **The server staging copy (C:\ProjectS\project-s-code) must NOT become canonical master.**

- DEV machine (C:\ProjectS-Unified) remains the single source of truth
- Server receives deployments from DEV via Git or file sync
- Any future server-side development goes in `dev_workspace\` only

---

## 6. Risk Assessment

### 6.1 Risk Matrix

| # | Risk | Severity | Likelihood | Mitigation |
|---|------|----------|------------|------------|
| 1 | **DEV/Server divergence** | HIGH | HIGH | Single canonical repo on DEV; server receives deployments only; Git-based sync |
| 2 | **Cline history split** | MEDIUM | MEDIUM | Keep Cline sessions on DEV; server sessions are read-only/audit only |
| 3 | **Secrets/env drift** | HIGH | MEDIUM | Use `.env.example` as template; never commit secrets; sync `.env` via secure channel |
| 4 | **Dependency drift** | MEDIUM | MEDIUM | Pin dependencies in `requirements.txt`; use `pip freeze` for reproducibility |
| 5 | **RDP latency** | LOW | MEDIUM | Use wired LAN connection; optimize RDP settings for performance |
| 6 | **External access security** | CRITICAL | LOW (if no exposure) | No direct RDP exposure; VPN required; strong passwords; NLA enabled |
| 7 | **Backup/versioning** | HIGH | MEDIUM | Git on DEV is primary backup; server has no independent backup strategy yet |

### 6.2 Detailed Mitigations

**Risk 1: DEV/Server Divergence**
- Use Git as the single source of truth
- Server pulls from DEV repo, never pushes
- Regular sync schedule (e.g., daily or per-release)
- Version tags for deployments

**Risk 2: Cline History Split**
- Primary Cline sessions on DEV machine
- Server Cline sessions for monitoring/audit only
- Document server-side changes in DEV issue tracker

**Risk 3: Secrets/Env Drift**
- `.env` files are NOT committed to Git
- Use `.env.example` as template
- Sync secrets via encrypted channel (e.g., SSH, manual copy)
- Audit secrets regularly

**Risk 4: Dependency Drift**
- Maintain `requirements.txt` with pinned versions
- Use virtual environments on both machines
- Test deployments on staging before production

**Risk 5: RDP Latency**
- Use wired Ethernet connection
- Adjust RDP quality settings (prioritize performance over visuals)
- Consider VS Code Remote SSH as alternative

**Risk 6: External Access Security**
- NO direct RDP port forwarding
- VPN tunnel (WireGuard recommended)
- Network-level authentication (NLA)
- Strong password policy (16+ characters)
- Regular security audits

**Risk 7: Backup/Versioning**
- Git on DEV is primary backup
- Consider off-site backup (e.g., GitHub private repo)
- Server data backup strategy needed (logs, database)
- Regular backup verification

---

## 7. Recommendation

### 7.1 Current State

| Question | Answer |
|----------|--------|
| A. DL380 ready for occasional RDP inspection? | **YES** — RDP port open, LAN accessible |
| B. DL380 ready as primary Project-S dev environment? | **NO** — toolchain not verified, WinRM blocked, no VS Code/Cline confirmed |
| C. What is missing? | See below |
| D. Recommended next step | Keep DEV canonical |

### 7.2 What is Missing for Full Dev Readiness

1. **Toolchain verification** — Python, Git, Node.js versions on DL380 need confirmation
2. **VS Code + Cline installation** — not confirmed on server
3. **WinRM trust configuration** — needed for remote management
4. **Git repository setup** — server needs proper Git clone/sync from DEV
5. **Virtual environment setup** — isolated Python environment on server
6. **Backup strategy** — server-side data backup plan
7. **VPN setup** — for secure external access (if needed)
8. **Local LLM infrastructure** — GPU verification, model deployment

### 7.3 Recommended Next Steps (Priority Order)

1. **Keep DEV machine as canonical master** — no change to current workflow
2. **Use DL380 for staging/runtime only** — current role remains appropriate
3. **Prepare local LLM on DEV first** — Quadro P2000 is available for local inference
4. **Occasional RDP inspection** — use RDP for server monitoring when needed
5. **Revisit RDP dev workflow later** — after local LLM is stable and server toolchain is verified

### 7.4 When to Reconsider

Reconsider making DL380 a primary dev environment when:
- DEV machine hardware is insufficient for development needs
- Local LLM requires more GPU resources than Quadro P2000 provides
- Team collaboration requires shared development environment
- DEV machine availability is unreliable

---

## 8. Return Values

| Question | Answer |
|----------|--------|
| A. DL380 ready for occasional RDP inspection? | **YES** |
| B. DL380 ready as primary Project-S dev environment? | **NO** |
| C. What is missing? | Toolchain verification, VS Code/Cline, WinRM trust, Git sync, backup strategy, VPN |
| D. Recommended next step | **Keep DEV canonical, prepare local LLM first, revisit RDP dev workflow later** |
| E. RDP enabled on DL380? | **YES** (port 3389 open) |
| F. RDP reachable on LAN? | **YES** |
| G. External RDP recommended? | **NO** (VPN required) |
| H. WinRM from DEV to DL380? | **NOT TRUSTED** (needs configuration) |
| I. DEV machine hostname | **DESKTOP-VAR2T1H** |
| J. Server hostname | **SHAYANSKA-DL380** |
| K. Server staging path | **C:\ProjectS\project-s-code** (EXISTS) |
| L. Security risk level | **LOW** (no external exposure currently) |

---

## Appendix A: Commands Used in Audit

```powershell
# Hostname and OS info
python -c "import platform; print(platform.node(), platform.system(), platform.version())"

# Ping test
Test-Connection -ComputerName SHAYANSKA-DL380 -Count 1 -Quiet

# RDP port check
Test-NetConnection -ComputerName SHAYANSKA-DL380 -Port 3389

# WinRM remote execution (FAILED - not trusted)
Invoke-Command -ComputerName SHAYANSKA-DL380 -ScriptBlock { ... }

# Local DEV environment
python --version; pip --version; git --version; node --version
$psversiontable.PSVersion
nvidia-smi --query-gpu=name,driver_version --format=csv,noheader

# RDP enabled check
Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server" -Name "fDenyTSConnections"
```

---

**END OF AUDIT REPORT**