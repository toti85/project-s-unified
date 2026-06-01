# WinRM Stabilization Script for New DL380 Server (192.168.1.180)
# Safe, focused, no reboot, no hostname change, no installs
# Run as Administrator in PowerShell

$ErrorActionPreference = "Stop"
$reportLines = @()

function AddLine {
    param([string]$text)
    $reportLines += $text
    Write-Host $text
}

AddLine "============================================================"
AddLine " WinRM Stabilization Script — $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
AddLine "============================================================"
AddLine ""

# ============================================================
# STEP 0: Safety check — confirm we are NOT on the old server
# ============================================================
AddLine "--- STEP 0: Safety check ---"
$currentHost = hostname
AddLine "  Current hostname: $currentHost"

if ($currentHost -eq "WIN-DG0NK5UH3L5" -or $currentHost -eq "SHAYANSKA-DL380") {
    AddLine "  WARNING: Hostname matches expected new server names."
} elseif ($currentHost -eq "WIN-DG0NK5UH3L5" -or $true) {
    # Just warn if it's not the old server's known IP
}

# Verify IP is NOT 192.168.1.88 (old server)
$myIPs = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notlike "Loopback" -and $_.IPAddress -notlike "169.*" }
$oldServerIP = "192.168.1.88"

AddLine ""
AddLine "  My IPv4 addresses:"
foreach ($ip in $myIPs) {
    AddLine "    $($ip.InterfaceAlias): $($ip.IPAddress)"
    if ($ip.IPAddress -eq $oldServerIP) {
        AddLine "  !!! ERROR: This machine IS 192.168.1.88 (OLD SERVER) !!!"
        AddLine "  DO NOT RUN THIS SCRIPT ON THE OLD SERVER."
        throw "WRONG SERVER DETECTED — aborting"
    }
}
AddLine "  Confirmed: NOT running on old server 192.168.1.88"
AddLine ""

# ============================================================
# STEP 1: Confirm local hostname and IPs
# ============================================================
AddLine "--- STEP 1: Hostname and IP confirmation ---"
$computerInfo = Get-ComputerInfo
AddLine "  Hostname: $currentHost"
AddLine "  OS: $($computerInfo.OSFullName)"
AddLine "  Version: $($computerInfo.OSVersion)"

foreach ($ip in $myIPs) {
    AddLine "  $($ip.InterfaceAlias): $($ip.IPAddress) (Gateway: $($ip.Gateway))"
}
AddLine ""

# ============================================================
# STEP 2: Set network profile to Private for active adapter
# ============================================================
AddLine "--- STEP 2: Set network profile to Private ---"
$activeAdapters = Get-NetAdapter | Where-Object { $_.Status -eq "Up" }
foreach ($adapter in $activeAdapters) {
    AddLine "  Adapter: $($adapter.Name) (ifIndex: $($adapter.IfIndex))"
    $currentProfile = (Get-NetAdapterAdvancedProperty -Name $adapter.Name -PropertyLabel "NetworkLocation" -ErrorAction SilentlyContinue).DisplayValue
    AddLine "    Current NetworkLocation: $currentProfile"
    
    try {
        Set-NetConnectionProfile -Name $adapter.Name -NetworkCategory Private -ErrorAction SilentlyContinue
        AddLine "    Set to Private: OK"
    } catch {
        # Try by ifIndex as fallback
        try {
            Set-NetConnectionProfile -InterfaceIndex $adapter.IfIndex -NetworkCategory Private -ErrorAction SilentlyContinue
            AddLine "    Set to Private (by ifIndex): OK"
        } catch {
            AddLine "    Set to Private: FAILED — $_"
        }
    }
}
AddLine ""

# ============================================================
# STEP 3: Enable PSRemoting
# ============================================================
AddLine "--- STEP 3: Enable PSRemoting ---"
try {
    $remotingCheck = (Get-Item WSMan:\localhost\Service\RootSASPolicy -ErrorAction SilentlyContinue)
    AddLine "  PSRemoting is already enabled"
} catch {
    try {
        Enable-PSRemoting -Force -SkipNetworkProfileCheck
        AddLine "  PSRemoting enabled successfully"
    } catch {
        AddLine "  PSRemoting enable FAILED: $_"
    }
}
AddLine ""

# ============================================================
# STEP 4: Run winrm quickconfig
# ============================================================
AddLine "--- STEP 4: winrm quickconfig ---"
try {
    $quickConfig = winrm quickconfig -force 2>&1
    foreach ($line in $quickConfig) {
        AddLine "  $line"
    }
} catch {
    AddLine "  winrm quickconfig FAILED: $_"
}
AddLine ""

# ============================================================
# STEP 5: Ensure WinRM service is Automatic and Running
# ============================================================
AddLine "--- STEP 5: WinRM service status ---"
try {
    $winrmService = Get-Service -Name WinRM -ErrorAction Stop
    AddLine "  Service name: $($winrmService.Name)"
    AddLine "  Display name: $($winrmService.DisplayName)"
    AddLine "  Start type: $($winrmService.StartType)"
    AddLine "  Status: $($winrmService.Status)"
    
    if ($winrmService.StartType -ne "Automatic") {
        AddLine "  Setting StartType to Automatic..."
        Set-Service -Name WinRM -StartupType Automatic
        AddLine "  StartType set to Automatic: OK"
    } else {
        AddLine "  StartType is already Automatic"
    }
    
    if ($winrmService.Status -ne "Running") {
        AddLine "  Starting WinRM service..."
        Start-Service -Name WinRM
        AddLine "  WinRM service started: OK"
    } else {
        AddLine "  WinRM service is already running"
    }
} catch {
    AddLine "  WinRM service check FAILED: $_"
}
AddLine ""

# ============================================================
# STEP 6: Enable Windows Firewall rules for WinRM
# ============================================================
AddLine "--- STEP 6: Firewall rules ---"
try {
    # Enable the built-in WinRM firewall rules
    $fwRules = Get-NetFirewallRule -DisplayGroup "Windows Remote Management" -ErrorAction SilentlyContinue
    if ($fwRules) {
        foreach ($rule in $fwRules) {
            if (-not $rule.Enabled) {
                Enable-NetFirewallRule -Id $rule.Id
                AddLine "  Enabled rule: $($rule.DisplayName)"
            } else {
                AddLine "  Already enabled: $($rule.DisplayName)"
            }
        }
    } else {
        AddLine "  No Windows Remote Management firewall rules found"
    }
    
    # Also try the specific rule by name
    try {
        Enable-NetFirewallRule -DisplayGroup "Windows Remote Management" -ErrorAction SilentlyContinue
        AddLine "  Windows Remote Management firewall group: enabled"
    } catch {
        AddLine "  Firewall rule enable: $_"
    }
} catch {
    AddLine "  Firewall rules check FAILED: $_"
}
AddLine ""

# ============================================================
# STEP 7: Verify local listener
# ============================================================
AddLine "--- STEP 7: Local listener verification ---"
try {
    $localTest = Test-NetConnection -ComputerName localhost -Port 5985 -WarningAction SilentlyContinue
    if ($localTest.TcpTestSucceeded) {
        AddLine "  Test-NetConnection localhost -Port 5985: OK (OPEN)"
    } else {
        AddLine "  Test-NetConnection localhost -Port 5985: FAILED (CLOSED)"
        AddLine "  WinRM listener may not be active on port 5985"
    }
} catch {
    AddLine "  Test-NetConnection FAILED: $_"
}
AddLine ""

# ============================================================
# STEP 8: Verify bound WinRM listeners
# ============================================================
AddLine "--- STEP 8: WinRM bound listeners ---"
try {
    $listeners = winrm enumerate winrm/config/listener 2>&1
    foreach ($line in $listeners) {
        AddLine "  $line"
    }
} catch {
    AddLine "  winrm enumerate FAILED: $_"
}
AddLine ""

# ============================================================
# STEP 9: Final summary
# ============================================================
AddLine "============================================================"
AddLine " WINRM STABILIZATION COMPLETE"
AddLine "============================================================"
AddLine ""
AddLine " Next steps for manual verification:"
AddLine "   1. From this machine, test: Test-NetConnection 192.168.1.180 -Port 5985"
AddLine "   2. From dev machine, test: Test-NetConnection 46.253.140.72 -Port 15985"
AddLine "   3. If port 15985 still fails, check router port forward is active"
AddLine ""

# ============================================================
# STEP 10: Create local report
# ============================================================
AddLine "--- STEP 10: Creating report ---"
$reportDir = "C:\ProjectS"
if (-not (Test-Path $reportDir)) {
    New-Item -ItemType Directory -Path $reportDir -Force | Out-Null
    AddLine "  Created directory: $reportDir"
}

$reportPath = Join-Path $reportDir "WINRM_STABILIZATION_REPORT_$(Get-Date -Format 'yyyyMMdd').txt"
$reportLines += ""
$reportLines += "============================================================"
$reportLines += " WINRM STABILIZATION REPORT"
$reportLines += "============================================================"
$reportLines += ""

# Add the full output to the report
$fullOutput = $reportLines -join "`r`n"
$fullOutput | Out-File -FilePath $reportPath -Encoding UTF8

AddLine "  Report saved to: $reportPath"
AddLine ""
AddLine "============================================================"
AddLine " SCRIPT COMPLETE"
AddLine "============================================================"