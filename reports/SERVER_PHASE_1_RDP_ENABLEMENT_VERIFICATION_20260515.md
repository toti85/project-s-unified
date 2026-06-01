# Server Phase 1 — RDP Enablement Verification

**Date:** 2026-05-15 ~14:56 UTC+3
**Type:** Remote RDP enablement via WinRM + port verification
**Target:** 192.168.1.180 (new HP ProLiant DL380 Gen9)

---

## 1. Exact Commands Used

### Step 1: Check RDP state BEFORE changes
```powershell
Invoke-Command -ComputerName 192.168.1.180 -Credential $cred -ScriptBlock {
    $rdpKey = Get-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server'
    $fDeny = $rdpKey.fDenyTSConnections
    $fwRules = Get-NetFirewallRule -DisplayGroup "Remote Desktop"
}
```

### Step 2: Enable RDP registry key
```powershell
Invoke-Command -ComputerName 192.168.1.180 -Credential $cred -ScriptBlock {
    Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' `
        -name "fDenyTSConnections" -value 0
}
```

### Step 3: Enable RDP firewall rules
```powershell
Invoke-Command -ComputerName 192.168.1.180 -Credential $cred -ScriptBlock {
    Enable-NetFirewallRule -DisplayGroup "Remote Desktop"
}
```

### Step 4: Verify RDP state AFTER changes
```powershell
Invoke-Command -ComputerName 192.168.1.180 -Credential $cred -ScriptBlock {
    $rdpKey = Get-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server'
    $fDeny = $rdpKey.fDenyTSConnections
    $fwRules = Get-NetFirewallRule -DisplayGroup "Remote Desktop"
}
```

### Step 5: Test RDP port reachability from DEV machine
```powershell
$tcp = New-Object System.Net.Sockets.TcpClient
$tcp.BeginConnect("192.168.1.180", 3389, $null, $null)
# Result: Connected = true
```

---

## 2. RDP Registry State Before/After

| State | fDenyTSConnections | Value Meaning |
|-------|-------------------|---------------|
| **BEFORE** | 1 | RDP DISABLED (deny all connections) |
| **AFTER** | 0 | RDP ENABLED (allow connections) |

---

## 3. Firewall Rule State

| State | Total Rules | Enabled |
|-------|-------------|---------|
| **BEFORE** | 3 | 0/3 (all disabled) |
| **AFTER** | 3 | 3/3 (all enabled) |

**Rules in "Remote Desktop" display group:**
- Remote Desktop - User Mode (TCP 3389)
- Remote Desktop - Port 3389 (TCP 3389)
- Remote Desktop - User Mode (UDP 3389)

---

## 4. TCP 3389 Reachability Result

**Port 3389 on 192.168.1.180: OPEN** — RDP connection established successfully from DEV machine (192.168.1.161).

---

## 5. Final Verdict

**RDP STATUS: READY**

Remote Desktop is now enabled on the new DL380 Gen9 server at 192.168.1.180.

---

## 6. Exact Next Action for Toti

**To connect via RDP from the dev machine:**

1. Press `Win + R` on the dev machine
2. Type `mstsc` and press Enter
3. In the Remote Desktop Connection dialog:
   - Computer: `192.168.1.180`
   - Click Connect
4. When prompted for credentials:
   - Username: `Administrator`
   - Password: `Qwe123`
5. Click OK
6. If certificate warning appears, check "Don't ask me again for connections to this computer" and click Yes

**Alternatively, from PowerShell:**
```powershell
Start-Process mstsc -ArgumentList "/v:192.168.1.180"
```

---

## Appendix A: Configuration Summary

| Item | Before | After |
|------|--------|-------|
| fDenyTSConnections | 1 | 0 |
| RDP Firewall Rules | 0/3 enabled | 3/3 enabled |
| Port 3389 | CLOSED | OPEN |
| RDP Access | DENIED | ALLOWED |

**Changes made:**
1. Registry: `HKLM:\System\CurrentControlSet\Control\Terminal Server\fDenyTSConnections` set to 0
2. Firewall: All 3 "Remote Desktop" display group rules enabled
3. No reboot required — changes took effect immediately

**No changes made:**
- No user accounts modified
- No network settings changed
- No unrelated firewall rules touched
- No software installed
- No reboot performed
- Old server 192.168.1.88 untouched