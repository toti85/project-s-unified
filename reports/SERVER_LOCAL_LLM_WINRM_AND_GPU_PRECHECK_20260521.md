$secPwd = Read-Host -AsSecureString# SERVER LOCAL LLM — WinRM & GPU Precheck

**Date:** 2026-05-21 18:50 UTC+3
**Type:** INFRASTRUCTURE PRECHECK
**Scope:** WinRM trust fix + GPU check for SHAYANSKA-DL380

---

## A. TrustedHosts Fixed? **YES (already configured)**

Current TrustedHosts on DEV machine:
```
192.168.1.180,46.253.140.72
```

No changes needed — both LAN and external IPs already present.

## B. WinRM Invoke-Command Works? **PARTIAL**

| Test | Result |
|------|--------|
| `Test-WSMan 192.168.1.180` (LAN) | ✅ WORKS |
| `Test-WSMan 46.253.140.72` (external) | ❌ FAILS (firewall/network profile) |
| `Invoke-Command` without credential | ❌ ACCESS DENIED |
| `Invoke-Command` with credential | ⚠️ Requires interactive credential prompt (not available in automated context) |

**Finding:** WinRM trust is configured and Test-WSMan succeeds on LAN. However, `Invoke-Command` requires Administrator credentials, and the interactive credential prompt (`Get-Credential`) cannot be satisfied in this automated terminal context.

**To complete manually:**
```powershell
$cred = Get-Credential -UserName "Administrator"
Invoke-Command -ComputerName 192.168.1.180 -Credential $cred -ScriptBlock { hostname; nvidia-smi }
```

## C. nvidia-smi Works? **NOT VERIFIED**

Could not execute `nvidia-smi` remotely due to credential requirement.

## D. GPU Detected

**NOT VERIFIED** — requires manual WinRM session with credentials.

## E. Driver/CUDA Version

**NOT VERIFIED** — requires `nvidia-smi` output.

## F. Ready to Proceed to Ollama Install? **PARTIAL**

| Prerequisite | Status |
|-------------|--------|
| DL380 reachable on LAN | ✅ |
| RDP port 3389 open | ✅ |
| WinRM trust configured | ✅ |
| Test-WSMan works | ✅ |
| Invoke-Command with credentials | ⚠️ Manual step needed |
| GPU verified | ❓ Pending |
| NVIDIA driver verified | ❓ Pending |

**Recommendation:** Run the credential-based WinRM command manually to verify GPU, then proceed to Ollama install.

---

## Return Values

| Question | Answer |
|----------|--------|
| A. TrustedHosts fixed? | **YES** (already configured) |
| B. WinRM Invoke-Command works? | **PARTIAL** (Test-WSMan ✅, Invoke-Command needs credentials) |
| C. nvidia-smi works? | **NOT VERIFIED** |
| D. GPU detected | **NOT VERIFIED** |
| E. Driver/CUDA version | **NOT VERIFIED** |
| F. Ready to proceed to Ollama install? | **PARTIAL** — manual GPU verification needed first |