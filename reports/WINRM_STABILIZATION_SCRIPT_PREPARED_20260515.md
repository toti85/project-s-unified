# WinRM Stabilization Script Prepared

**Date:** 2026-05-17 ~20:22 UTC+3
**Type:** Manual WinRM stabilization for new DL380 server
**Target:** 192.168.1.180 (new HP ProLiant DL380 Gen9, Windows Server 2019)

---

## A. Script Path

```
C:\ProjectS-Unified\scripts\stabilize_winrm_on_new_server.ps1
```

The script will be copied to the new server and executed from there via RDP.

---

## B. Exact Manual Instructions for Toti

### Step 1: RDP to the new server

1. On the **DEV machine**, press `Win + R`
2. Type `mstsc` and press Enter
3. In the Remote Desktop Connection dialog:
   - **Computer:** `46.253.140.72`
   - **Port:** `77` (if not pre-filled, type `46.253.140.72:77`)
4. Click **Connect**
5. When prompted for credentials:
   - **Username:** `Administrator`
   - **Password:** `Qwe123`
6. Click **OK**
7. If certificate warning appears: check "Don't ask me again..." and click **Yes**

### Step 2: Copy the script to the new server

Once RDP session is open:

1. Copy the script file to the new server:
   ```powershell
   # From the DEV machine, before connecting via RDP, copy:
   Copy-Item -Path "C:\ProjectS-Unified\scripts\stabilize_winrm_on_new_server.ps1" `
             -Destination "C:\stabilize_winrm_on_new_server.ps1" `
             -ToSession (New-PSSession -ComputerName 46.253.140.72 -Port 77 -Credential (Get-Credential) -SessionOption (New-PSSessionOption -ProxyServer))
   ```
   
   **OR** (simpler): Open Notepad on the DEV machine, paste the script content, save via RDP drag-and-drop or copy-paste to `C:\stabilize_winrm_on_new_server.ps1` on the new server.

### Step 3: Run the script as Administrator

1. In the RDP session, right-click the **Start button**
2. Select **Windows PowerShell (Admin)** or **Terminal (Admin)**
3. If prompted by UAC, click **Yes**
4. Run:
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   C:\stabilize_winrm_on_new_server.ps1
   ```
5. Wait for the script to complete (should take ~10-30 seconds)

---

## C. What Output/Report Toti Should Send Back

### On-screen output to screenshot/copy:

Toti should copy the **entire console output** from PowerShell and paste it into a text file, or take a screenshot showing:

1. The **hostname** at the top
2. The **IPv4 addresses** listed
3. The **WinRM service status** (should show "Running")
4. The **Test-NetConnection localhost -Port 5985** result (should say "OK (OPEN)")
5. The **WinRM bound listeners** section (should show a listener on port 5985)

### Local report file:

The script creates a local report on the new server at:
```
C:\ProjectS\WINRM_STABILIZATION_REPORT_20260515.txt
```

Toti should copy this file back to the DEV machine. The easiest way:
- In RDP session, open File Explorer and navigate to `C:\ProjectS\`
- Copy the `.txt` file to the Desktop
- Drag/copy it from the DEV machine to the RDP session

---

## D. After Toti Runs It — External Tests for Cline

Once Toti confirms the script completed successfully, Cline should run these tests from the DEV machine:

### Test 1: TCP reachability to external WinRM port
```powershell
Test-NetConnection 46.253.140.72 -Port 15985
```
**Expected:** `TcpTestSucceeded : True`

### Test 2: TCP reachability to internal WinRM port
```powershell
Test-NetConnection 192.168.1.180 -Port 5985
```
**Expected:** `TcpTestSucceeded : True`

### Test 3: Authenticated WinRM command via external endpoint
```powershell
Invoke-Command `
  -ComputerName 46.253.140.72 `
  -Port 15985 `
  -Credential (Get-Credential) `
  -ScriptBlock {
    hostname
    $env:COMPUTERNAME
    Get-Date
  }
```
**Expected:** Returns the hostname `WIN-DG0NK5UH3L5` (or whatever it is at that point) and the current date/time.

### Test 4: If Test 3 fails due to TrustedHosts
```powershell
# Check current TrustedHosts
Get-Item WSMan:\localhost\Client\TrustedHosts

# Add the public IP if needed
$current = Get-Item WSMan:\localhost\Client\TrustedHosts -ErrorAction SilentlyContinue
if ($current) {
    Set-Item WSMan:\localhost\Client\TrustedHosts -Value ("$(($current.Value) -replace ',$',''),46.253.140.72" -replace ',,',',')
} else {
    Set-Item WSMan:\localhost\Client\TrustedHosts -Value "46.253.140.72"
}
```

Then re-run Test 3.

---

## Script Safety Guarantees

| Constraint | Status |
|------------|--------|
| No hostname rename | ✅ Not in script |
| No reboot | ✅ Not in script |
| No software installation | ✅ Not in script |
| No HTTPS WinRM | ✅ Not in script |
| Safety check for old server (192.168.1.88) | ✅ Aborts if detected |
| Network profile set to Private | ✅ Only for active adapters |
| WinRM service set to Automatic + Running | ✅ |
| Firewall rules enabled | ✅ |

---

## Prerequisites for Toti

1. **RDP access must work** — Port 77 forward is confirmed OPEN
2. **Administrator credentials** — Username: `Administrator`, Password: `Qwe123`
3. **PowerShell execution policy** — Script uses `-ExecutionPolicy Bypass` for the process scope only
4. **Admin rights in RDP session** — Must run PowerShell as Administrator

---

**Report generated:** 2026-05-17 ~20:22 UTC+3
**Status:** Script ready for manual execution by Toti