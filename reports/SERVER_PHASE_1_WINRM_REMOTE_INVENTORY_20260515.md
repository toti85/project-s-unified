# Server Phase 1 — WinRM Remote Inventory

**Date:** 2026-05-15 ~14:47 UTC+3
**Type:** Read-only host OS inventory via PowerShell Remoting
**Target:** 192.168.1.180 (new HP ProLiant DL380 Gen9)
**Credentials:** Administrator (password provided by user)

---

## 1. Executive Verdict

**WinRM remote shell: SUCCESS** — PowerShell Remoting session established to 192.168.1.180 using Administrator credentials. Full read-only inventory collected.

**Connection path:**
- Dev machine (192.168.1.161) → WinRM HTTP (5985) → 192.168.1.180
- TrustedHosts configured via `winrm set winrm/config/client`
- Network profile set to Private (required for WinRM firewall exception)

---

## 2. Connection Details

| Item | Value |
|------|-------|
| Target IP | 192.168.1.180 |
| Target MAC | F4:03:43:3E:C6:80 (NIC 1) |
| WinRM Port | 5985 TCP (HTTP) |
| Auth Method | Basic + Kerberos + Negotiate |
| TrustedHosts | 192.168.1.180 (configured via winrm.cmd) |
| Network Profile | Private (changed from Public) |
| WinRM Service | Running (started via Start-Service) |

---

## 3. Host Identity and OS

| Item | Value |
|------|-------|
| **Hostname** | WIN-DG0NK5UH3L5 |
| **OS Caption** | Microsoft Windows Server 2019 Datacenter |
| **OS Version** | 10.0.17763 (Build 17763) |
| **Last Boot** | 2026-05-15 11:19:22 |
| **Uptime** | 0.1 days (~3 hours) |
| **PowerShell Version** | 5.1.17763.1490 |

**Note:** The hostname `WIN-DG0NK5UH3L5` is the default Windows Server computer name — this strongly suggests the Windows Server 2019 image has **never been renamed** and may be a fresh/unused installation.

---

## 4. Hardware Inventory

| Item | Value |
|------|-------|
| **CPU Model** | Intel(R) Xeon(R) CPU E5-2699 v3 @ 2.30GHz |
| **CPU Count** | 2 physical processors |
| **CPU Threads** | 72 logical processors (36 cores per CPU, hyperthreading) |
| **Total RAM** | 127.9 GB |
| **Drives** | C: 1461.2 GB free; F: 447 GB free |

**Hardware verification:**
- CPU matches expected DL380 Gen9 configuration (dual Xeon E5-2699 v3 = 18 cores/36 threads each = 72 threads total) ✓
- RAM matches expected 128 GB DDR4 ✓
- Two drives detected: C: (system, ~1.5 TB NVMe) and F: (~450 GB)

---

## 5. Storage Inventory

| Drive | Free Space | Notes |
|-------|------------|-------|
| C: | 1461.2 GB | System drive, likely NVMe |
| F: | 447 GB | Secondary drive, possibly RAID or separate disk |

---

## 6. Network State

| Item | Value |
|------|-------|
| **Adapter** | HPE Ethernet 1Gb 4-port 331i Adapter #2 |
| **IP Address** | 192.168.1.180 |
| **DNS Servers** | 192.168.1.88, 8.8.8.8 |
| **NIC Count** | 4 physical ports (only 1 active with IP) |

**DNS clue:** Primary DNS is `192.168.1.88` — this is the same IP as the old Windows Server 2012 R2 production machine. The new server's DNS configuration may have inherited this from DHCP or a previous configuration.

---

## 7. Remote Management State

| Service | Status |
|---------|--------|
| **WinRM (5985)** | **OPEN** — confirmed working, inventory collected |
| **RDP (3389)** | **DISABLED** — `fDenyTSConnections = 1` |
| **SSH (22)** | Not installed |
| **WinRM HTTPS (5986)** | Not configured |

---

## 8. Developer Runtime Readiness

| Runtime | Present? | Notes |
|---------|----------|-------|
| **Python** | **NO** | Not found in standard paths or PATH |
| **Git** | **NO** | Not found in PATH |
| **NVIDIA (nvidia-smi)** | **NO** | Not in PATH — drivers likely not installed |

**Assessment:** The server is a **bare Windows Server 2019 installation** with no development runtimes installed. This is expected for a fresh server image.

---

## 9. What Can Now Be Done Remotely

1. **PowerShell remoting** — Full remote command execution via WinRM (5985)
2. **Software installation** — Install Python, Git, NVIDIA drivers remotely
3. **RDP enablement** — Enable Remote Desktop for interactive access
4. **Windows updates** — Run `WindowsUpdate` remotely
5. **Network configuration** — Assign static IP, configure DNS, bond NICs
6. **Storage management** — Initialize F: drive, create volumes, configure RAID

---

## 10. Exact Recommended Next Action

**Step 1 — Enable RDP for easier future access:**
```powershell
Invoke-Command -ComputerName 192.168.1.180 -Credential (Get-Credential) -ScriptBlock {
    Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -name "fDenyTSConnections" -value 0
    Enable-NetFirewallRule -DisplayGroup "Remote Desktop"
    Write-Host "RDP enabled"
}
```

**Step 2 — Install Python (for Project-S Python services):**
```powershell
Invoke-Command -ComputerName 192.168.1.180 -Credential (Get-Credential) -ScriptBlock {
    # Download and install Python 3.12
    Invoke-WebRequest "https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe" -OutFile "C:\python-installer.exe"
    Start-Process "C:\python-installer.exe" -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait
    Write-Host "Python installed"
}
```

**Step 3 — Install NVIDIA drivers (for Tesla M60):**
```powershell
# Download and install NVIDIA driver for Maxwell GM204 (Tesla M60)
# Note: Tesla M60 requires datacenter driver, not GeForce
```

**Step 4 — Install Git:**
```powershell
Invoke-Command -ComputerName 192.168.1.180 -Credential (Get-Credential) -ScriptBlock {
    winget install Git.Git
}
```

---

## Appendix A: Configuration Steps Taken

1. **VS Code reopened as Administrator** — IsAdmin: True confirmed
2. **Network profile changed** — Public → Private (required for WinRM firewall exception)
3. **WinRM service started** — `Start-Service WinRM`
4. **WinRM quickconfig** — Firewall exception + LocalAccountTokenFilterPolicy configured
5. **TrustedHosts configured** — `winrm set winrm/config/client "@{TrustedHosts=\"192.168.1.180\"}"`
6. **Remote inventory collected** — `Invoke-Command` with Administrator credentials

---

**Készítette:** Cline
**Dátum:** 2026-05-15
**Verzió:** v1.0