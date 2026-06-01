$targetIP = "192.168.1.180"
$targetPassword = "Qwe123"
$securePass = ConvertTo-SecureString $targetPassword -AsPlainText -Force
$targetCred = New-Object System.Management.Automation.PSCredential("$targetIP\Administrator", $securePass)

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  EXTERNAL WINRM READINESS DIAGNOSIS" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# ============================================
# PART 1: SERVER-SIDE CHECKS
# ============================================
Write-Host "=== PART 1: SERVER-SIDE CHECKS ===" -ForegroundColor Yellow
Write-Host ""

$serverChecks = Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
    $results = @{}
    
    # 1. WinRM service status
    $winrmService = Get-Service -Name WinRM -ErrorAction SilentlyContinue
    $results.WinRMServiceStatus = if($winrmService){$winrmService.Status}else{"NOT FOUND"}
    $results.WinRMStartupType = if($winrmService){$winrmService.StartType}else{"N/A"}
    
    # 2. WinRM listeners
    try {
        $listeners = winrm enumerate winrm/config/listener 2>&1
        $results.WinRMListeners = $listeners
        $results.WinRMListenersCount = ($listeners | Select-String "ListenAddress").Count
    } catch {
        $results.WinRMListeners = $_.ToString()
        $results.WinRMListenersCount = 0
    }
    
    # 3. Port 5985 listening
    try {
        $listening = Get-NetTCPConnection -LocalPort 5985 -State Listen -ErrorAction Stop
        $results.Port5985Listening = $true
        $results.Port5985Process = (Get-Process -Id $listening.OwningProcess -ErrorAction SilentlyContinue).ProcessName
    } catch {
        $results.Port5985Listening = $false
        $results.Port5985Process = "N/A"
    }
    
    # 4. Firewall rules
    try {
        $fwRules = Get-NetFirewallRule -DisplayGroup "Windows Remote Management" -ErrorAction SilentlyContinue
        $fwEnabled = ($fwRules | Where-Object {$_.Enabled -eq "True"}).Count
        $results.FirewallRules = $fwRules | Select-Object DisplayName, Enabled, Profile | ConvertTo-Json -Compress
        $results.FirewallEnabledCount = $fwEnabled
        $results.FirewallTotalCount = ($fwRules | Measure-Object).Count
    } catch {
        $results.FirewallEnabledCount = 0
        $results.FirewallTotalCount = 0
        $results.FirewallError = $_.ToString()
    }
    
    # 5. Network profile
    try {
        $netProfile = Get-NetConnectionProfile -ErrorAction SilentlyContinue
        $results.NetworkName = $netProfile.Name
        $results.NetworkProfile = $netProfile.NetworkCategory
        $results.NetworkInterface = $netProfile.InterfaceDescription
        $results.IPv4Address = (Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | Where-Object {$_.InterfaceAlias -eq $netProfile.InterfaceAlias}).IPAddress
    } catch {
        $results.NetworkError = $_.ToString()
    }
    
    # 6. LocalAccountTokenFilterPolicy
    $tokenPolicy = Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" -Name LocalAccountTokenFilterPolicy -ErrorAction SilentlyContinue
    $results.LocalAccountTokenFilterPolicy = if($tokenPolicy){$tokenPolicy.LocalAccountTokenFilterPolicy}else{"NOT SET (defaults to 0)"}
    
    # 7. Current LAN IP
    $ipConfig = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | Where-Object {$_.PrefixOrigin -ne "WellKnown"}
    $results.ServerIPs = ($ipConfig | Where-Object {$_.IPAddress -like "192.168.*"}).IPAddress -join ", "
    $results.DefaultGateway = ($ipConfig | ForEach-Object { (Get-NetRoute -DestinationPrefix "0.0.0.0/0" -ErrorAction SilentlyContinue | Select-Object -First 1).NextHop })
    
    $results
}

Write-Host "  1. WinRM Service:" -ForegroundColor White
Write-Host "     Status: $($serverChecks.WinRMServiceStatus)" -ForegroundColor $(if($serverChecks.WinRMServiceStatus -eq "Running"){"Green"}else{"Red"})
Write-Host "     Startup: $($serverChecks.WinRMStartupType)" -ForegroundColor $(if($serverChecks.WinRMStartupType -eq 2){"Green"}else{"Red"})

Write-Host "  2. WinRM Listeners:" -ForegroundColor White
Write-Host "     Count: $($serverChecks.WinRMListenersCount)" -ForegroundColor $(if($serverChecks.WinRMListenersCount -gt 0){"Green"}else{"Red"})
$serverChecks.WinRMListeners -split "`n" | Where-Object {$_ -match "ListenAddress|Port|Hostname"} | ForEach-Object { Write-Host "     $_" -ForegroundColor Gray }

Write-Host "  3. Port 5985:" -ForegroundColor White
Write-Host "     Listening: $($serverChecks.Port5985Listening)" -ForegroundColor $(if($serverChecks.Port5985Listening){"Green"}else{"Red"})
Write-Host "     Process: $($serverChecks.Port5985Process)" -ForegroundColor Gray

Write-Host "  4. Firewall Rules:" -ForegroundColor White
Write-Host "     Enabled/Total: $($serverChecks.FirewallEnabledCount)/$($serverChecks.FirewallTotalCount)" -ForegroundColor $(if($serverChecks.FirewallEnabledCount -gt 0){"Green"}else{"Red"})
if ($serverChecks.FirewallError) {
    Write-Host "     Error: $($serverChecks.FirewallError)" -ForegroundColor Red
}

Write-Host "  5. Network Profile:" -ForegroundColor White
Write-Host "     Name: $($serverChecks.NetworkName)" -ForegroundColor Gray
Write-Host "     Category: $($serverChecks.NetworkProfile)" -ForegroundColor $(if($serverChecks.NetworkProfile -eq "Private"){"Green"}else{"Yellow"})
Write-Host "     Interface: $($serverChecks.NetworkInterface)" -ForegroundColor Gray
Write-Host "     LAN IP: $($serverChecks.IPv4Address)" -ForegroundColor $(if($serverChecks.IPv4Address -like "*180"){"Green"}else{"Yellow"})

Write-Host "  6. LocalAccountTokenFilterPolicy:" -ForegroundColor White
Write-Host "     Value: $($serverChecks.LocalAccountTokenFilterPolicy)" -ForegroundColor $(if($serverChecks.LocalAccountTokenFilterPolicy -eq 1){"Green"}else{"Yellow"})

Write-Host "  7. Server LAN IPs:" -ForegroundColor White
Write-Host "     $($serverChecks.ServerIPs)" -ForegroundColor Gray

# Server-side verdict
$serverSidePass = ($serverChecks.WinRMServiceStatus -eq "Running") -and 
                  ($serverChecks.WinRMStartupType -eq 2) -and 
                  ($serverChecks.WinRMListenersCount -gt 0) -and 
                  ($serverChecks.Port5985Listening) -and 
                  ($serverChecks.FirewallEnabledCount -gt 0)

Write-Host ""
Write-Host "  SERVER-SIDE VERDICT: $(if($serverSidePass){'ALL PASS'}else{'ISSUES FOUND'})" -ForegroundColor $(if($serverSidePass){"Green"}else{"Red"})
Write-Host ""

# ============================================
# PART 2: DEV MACHINE LAN CHECKS
# ============================================
Write-Host "=== PART 2: DEV MACHINE LAN CHECKS ===" -ForegroundColor Yellow
Write-Host ""

# Test WinRM connectivity
$lanWinRMPass = $false
try {
    $testHostname = Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock { hostname } -ErrorAction Stop
    $ipLabel = $targetIP
    Write-Host "  Invoke-Command to ${ipLabel}: SUCCESS (hostname: $testHostname)" -ForegroundColor Green
    $lanWinRMPass = $true
} catch {
    Write-Host "  Invoke-Command to ${ipLabel}: FAILED - $_" -ForegroundColor Red
}

# Test TCP 5985 from DEV
try {
    $tcpTest = Test-NetConnection -ComputerName $targetIP -Port 5985 -WarningAction SilentlyContinue -ErrorAction Stop
    Write-Host "  Test-NetConnection 192.168.1.180:5985:" -ForegroundColor White
    Write-Host "     TcpTestSucceeded: $($tcpTest.TcpTestSucceeded)" -ForegroundColor $(if($tcpTest.TcpTestSucceeded){"Green"}else{"Red"})
    if (-not $tcpTest.TcpTestSucceeded) {
        $lanWinRMPass = $false
    }
} catch {
    Write-Host "  Test-NetConnection failed: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "  LAN WINRM VERDICT: $(if($lanWinRMPass){'PASS'}else{'FAIL'})" -ForegroundColor $(if($lanWinRMPass){"Green"}else{"Red"})
Write-Host ""

# ============================================
# PART 3: EXTERNAL FORWARD TEST
# ============================================
Write-Host "=== PART 3: EXTERNAL FORWARD TEST ===" -ForegroundColor Yellow
Write-Host "  Testing: Test-NetConnection 46.253.140.72 Port 15985" -ForegroundColor Gray
Write-Host ""

$externalReachable = $false
try {
    $extTest = Test-NetConnection -ComputerName "46.253.140.72" -Port 15985 -WarningAction SilentlyContinue -ErrorAction Stop
    Write-Host "  External TCP 46.253.140.72:15985:" -ForegroundColor White
    Write-Host "     TcpTestSucceeded: $($extTest.TcpTestSucceeded)" -ForegroundColor $(if($extTest.TcpTestSucceeded){"Green"}else{"Red"})
    Write-Host "     TracerouteHops: $($extTest.TracerouteHops.Count)" -ForegroundColor Gray
    $externalReachable = $extTest.TcpTestSucceeded
} catch {
    Write-Host "  External test failed: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "  EXTERNAL REACHABLE: $(if($externalReachable){'YES'}else{'NO'})" -ForegroundColor $(if($externalReachable){"Green"}else{"Red"})
Write-Host ""

# ============================================
# PART 4: CONCLUSION
# ============================================
Write-Host "=== PART 4: CONCLUSION ===" -ForegroundColor Yellow
Write-Host ""

$allResults = @{
    ServerSideWinRMCorrect = $serverSidePass
    LANWinRMPass = $lanWinRMPass
    ExternalReachable = $externalReachable
    ServerIP = $serverChecks.ServerIPs
    NetworkProfile = $serverChecks.NetworkProfile
    TokenFilterPolicy = $serverChecks.LocalAccountTokenFilterPolicy
}

# Determine most likely cause
if (-not $serverSidePass) {
    $likelyCause = "Server-side WinRM configuration issue"
    $likelyCauseDetail = "Check WinRM service status, startup type, listeners, or firewall rules on SHAYANSKA-DL380"
} elseif (-not $lanWinRMPass) {
    $likelyCause = "LAN connectivity issue"
    $likelyCauseDetail = "Check Windows Firewall on server, network profile (must be Private), or local firewall on DEV machine"
} elseif (-not $externalReachable) {
    $likelyCause = "Router/NAT/port-forward issue"
    $likelyCauseDetail = "Server WinRM is correct. Router must forward external TCP 15985 -> 192.168.1.180:5985"
} else {
    $likelyCause = "All checks passed"
    $likelyCauseDetail = "No issues found"
}

Write-Host "  A. Server-side WinRM fully correct: $(if($serverSidePass){'yes'}else{'no'})" -ForegroundColor $(if($serverSidePass){"Green"}else{"Red"})
Write-Host "  B. LAN WinRM still PASS: $(if($lanWinRMPass){'yes'}else{'no'})" -ForegroundColor $(if($lanWinRMPass){"Green"}else{"Red"})
Write-Host "  C. External 15985 reachable: $(if($externalReachable){'yes'}else{'no'})" -ForegroundColor $(if($externalReachable){"Green"}else{"Red"})
Write-Host "  D. Most likely remaining cause: $likelyCause" -ForegroundColor Yellow
Write-Host "     Detail: $likelyCauseDetail" -ForegroundColor Gray
Write-Host "  E. Exact next physical/router action:" -ForegroundColor Yellow

if (-not $externalReachable -and $serverSidePass -and $lanWinRMPass) {
    Write-Host "     1. Log into router (likely 192.168.1.1)" -ForegroundColor White
    Write-Host "     2. Create port forward rule:" -ForegroundColor White
    Write-Host "        Protocol: TCP" -ForegroundColor White
    Write-Host "        External Port: 15985" -ForegroundColor White
    Write-Host "        Internal IP: 192.168.1.180" -ForegroundColor White
    Write-Host "        Internal Port: 5985" -ForegroundColor White
    Write-Host "     3. Verify router WAN IP is 46.253.140.72" -ForegroundColor White
    Write-Host "     4. Test from DEV: Test-NetConnection 46.253.140.72 -Port 15985" -ForegroundColor White
} elseif (-not $serverSidePass) {
    Write-Host "     1. Fix server-side WinRM first (see server checks above)" -ForegroundColor White
} elseif (-not $lanWinRMPass) {
    Write-Host "     1. Enable Windows Firewall inbound rule for WinRM on server" -ForegroundColor White
    Write-Host "     2. Run on server: netsh advfirewall firewall set rule group='Windows Remote Management' new profile=yes" -ForegroundColor White
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  DIAGNOSIS COMPLETE" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# Save results for report
$allResults | ConvertTo-Json | Out-File -FilePath "C:\ProjectS-Unified\.winrm_diagnosis.json" -Encoding UTF8