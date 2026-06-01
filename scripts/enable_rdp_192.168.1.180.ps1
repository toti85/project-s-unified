# Server Phase 1 — Enable Remote Desktop on 192.168.1.180
# Read-only changes: enable RDP registry + firewall rules only

$targetIP = "192.168.1.180"
$password = ConvertTo-SecureString "Qwe123" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential ("$targetIP\Administrator", $password)

Write-Host "=== Enable Remote Desktop on $targetIP ===" -ForegroundColor Cyan
Write-Host "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Yellow
Write-Host ""

$rdpReady = $false

# Step 1: Check current RDP state BEFORE changes
Write-Host "--- Step 1: Current RDP State (BEFORE) ---" -ForegroundColor Green
try {
    $before = Invoke-Command -ComputerName $targetIP -Credential $cred -ScriptBlock {
        $rdpKey = Get-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -ErrorAction SilentlyContinue
        $fDeny = if ($rdpKey) { $rdpKey.fDenyTSConnections } else { "key not found" }

        $fwRules = Get-NetFirewallRule -DisplayGroup "Remote Desktop" -ErrorAction SilentlyContinue |
            Select-Object -ExpandProperty Enabled

        [PSCustomObject]@{
            fDenyTSConnections = $fDeny
            RDPFirewallRules = if ($fwRules.Count -gt 0) {
                "Count: $($fwRules.Count), Enabled: $($fwRules -join ', ')"
            } else { "No rules found" }
        }
    }
    Write-Host "  fDenyTSConnections: $($before.fDenyTSConnections)" -ForegroundColor Yellow
    Write-Host "  Firewall rules: $($before.RDPFirewallRules)" -ForegroundColor Yellow
} catch {
    Write-Host "  Error reading state: $_" -ForegroundColor Red
}
Write-Host ""

# Step 2: Enable RDP registry key
Write-Host "--- Step 2: Enabling RDP (registry) ---" -ForegroundColor Green
try {
    Invoke-Command -ComputerName $targetIP -Credential $cred -ScriptBlock {
        Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -name "fDenyTSConnections" -value 0
        Write-Host "  Registry set: fDenyTSConnections = 0" -ForegroundColor Green
    }
    Write-Host "  RDP registry enabled successfully" -ForegroundColor Green
} catch {
    Write-Host "  Error enabling RDP registry: $_" -ForegroundColor Red
}
Write-Host ""

# Step 3: Enable RDP firewall rules
Write-Host "--- Step 3: Enabling RDP Firewall rules ---" -ForegroundColor Green
try {
    Invoke-Command -ComputerName $targetIP -Credential $cred -ScriptBlock {
        Enable-NetFirewallRule -DisplayGroup "Remote Desktop" -ErrorAction SilentlyContinue
        $fwRules = Get-NetFirewallRule -DisplayGroup "Remote Desktop" -ErrorAction SilentlyContinue
        $enabledCount = ($fwRules | Where-Object { $_.Enabled -eq 'True' }).Count
        $totalCount = $fwRules.Count
        Write-Host "  Firewall rules: $enabledCount/$totalCount enabled" -ForegroundColor Green
    }
    Write-Host "  RDP firewall rules enabled successfully" -ForegroundColor Green
} catch {
    Write-Host "  Error enabling firewall rules: $_" -ForegroundColor Red
}
Write-Host ""

# Step 4: Verify RDP state AFTER changes
Write-Host "--- Step 4: Verify RDP State (AFTER) ---" -ForegroundColor Green
try {
    $after = Invoke-Command -ComputerName $targetIP -Credential $cred -ScriptBlock {
        $rdpKey = Get-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -ErrorAction SilentlyContinue
        $fDeny = if ($rdpKey) { $rdpKey.fDenyTSConnections } else { "key not found" }

        $fwRules = Get-NetFirewallRule -DisplayGroup "Remote Desktop" -ErrorAction SilentlyContinue
        $enabledCount = ($fwRules | Where-Object { $_.Enabled -eq 'True' }).Count
        $totalCount = $fwRules.Count

        [PSCustomObject]@{
            fDenyTSConnections = $fDeny
            RDPFirewallRules = "Count: $totalCount, Enabled: $enabledCount"
        }
    }
    $fDenyVal = $after.PSObject.Properties["fDenyTSConnections"].Value
    $fwVal = $after.PSObject.Properties["RDPFirewallRules"].Value
    $color = if ($fDenyVal -eq 0) { "Green" } else { "Red" }
    Write-Host "  fDenyTSConnections: $fDenyVal" -ForegroundColor $color
    Write-Host "  Firewall rules: $fwVal" -ForegroundColor $color
} catch {
    Write-Host "  Error verifying state: $_" -ForegroundColor Red
}
Write-Host ""

# Step 5: Test RDP port reachability from DEV machine
Write-Host "--- Step 5: Test RDP Port 3389 from DEV machine ---" -ForegroundColor Green
try {
    $tcp = New-Object System.Net.Sockets.TcpClient
    $result = $tcp.BeginConnect($targetIP, 3389, $null, $null)
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    while (!$result.IsCompleted) { Start-Sleep -Milliseconds 100; if ($sw.ElapsedMilliseconds -gt 5000) { break } }
    if ($tcp.Connected) {
        Write-Host "  Port 3389 on ${targetIP}: OPEN" -ForegroundColor Green
        $rdpReady = $true
    } else {
        Write-Host "  Port 3389 on ${targetIP}: CLOSED/timeout" -ForegroundColor Red
        $rdpReady = $false
    }
    $tcp.EndConnect($result)
    $tcp.Close()
} catch {
    Write-Host "  Port 3389 error: $_" -ForegroundColor Red
    $rdpReady = $false
}
Write-Host ""

# Final verdict
Write-Host "=== FINAL VERDICT ===" -ForegroundColor Cyan
if ($rdpReady) {
    Write-Host "RDP STATUS: READY" -ForegroundColor Green
    Write-Host "Next action: Run mstsc on the dev machine, connect to $targetIP" -ForegroundColor Green
} else {
    Write-Host "RDP STATUS: NOT READY" -ForegroundColor Red
    Write-Host "Check firewall rules and try again" -ForegroundColor Red
}
