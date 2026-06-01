$targetIP = "192.168.1.180"
$targetPassword = "Qwe123"
$securePass = ConvertTo-SecureString $targetPassword -AsPlainText -Force
$targetCred = New-Object System.Management.Automation.PSCredential("$targetIP\Administrator", $securePass)

$startTime = Get-Date

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  PHASE 4.2 RETRY" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================
# Check server state first
# ============================================================
Write-Host "[1/6] Checking server state..." -ForegroundColor Yellow

$serverAlive = $false
$serverRunning = $false
$portListening = $false

# Try WinRM first
try {
    $testResult = Test-WSMan -ComputerName $targetIP -ErrorAction Stop -TimeoutSec 10
    Write-Host "  WinRM: Available" -ForegroundColor Green
    $serverAlive = $true
} catch {
    Write-Host "  WinRM: Unavailable ($_)" -ForegroundColor Red
    $serverAlive = $false
}

# Check if server responds to ping
try {
    $ping = Test-Connection -ComputerName $targetIP -Count 2 -Quiet -ErrorAction Stop
    $pingStatus = if($ping){"Available"}else{"Unreachable"}
    Write-Host "  Ping: $pingStatus" -ForegroundColor $(if($ping){"Green"}else{"Red"})
} catch {
    Write-Host "  Ping: Unreachable" -ForegroundColor Red
}

# Check if port 8000 is listening (from our machine)
try {
    $conn = Get-NetTCPConnection -RemoteAddress $targetIP -LocalPort 8000 -ErrorAction SilentlyContinue
    $portListening = ($conn.State -eq "Listen")
    Write-Host "  Port 8000: $(if($portListening){'Listening'}else{'Not listening'})" -ForegroundColor $(if($portListening){"Green"}else{"Yellow"})
} catch {
    Write-Host "  Port 8000: Check failed" -ForegroundColor Yellow
}

# ============================================================
# Try to open firewall via different method
# ============================================================
Write-Host ""
Write-Host "[2/6] Attempting firewall configuration..." -ForegroundColor Yellow

$firewallCreated = $false

if ($serverAlive) {
    # Method 1: WinRM (already confirmed working)
    try {
        $firewallResult = Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
            $ruleName = "Project-S Interactive Layer"
            
            $existingRule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
            
            if ($existingRule) {
                if (-not $existingRule.Enabled) {
                    Enable-NetFirewallRule -DisplayName $ruleName
                }
            } else {
                New-NetFirewallRule `
                    -DisplayName $ruleName `
                    -Direction Inbound `
                    -Protocol TCP `
                    -LocalPort 8000 `
                    -Action Allow `
                    -Profile Private `
                    -Description "Allow inbound TCP 8000 for Project-S Interactive Layer"
            }
            
            $verifyRule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
            if ($verifyRule) {
                @{ Created = $true; Enabled = $verifyRule.Enabled; Profile = ($verifyRule.Profile -join ","); Action = $verifyRule.Action }
            } else {
                @{ Created = $false; Enabled = $false; Profile = ""; Action = "" }
            }
        } -ErrorAction Stop
        
        Write-Host "  Firewall rule: $($firewallResult.Created)" -ForegroundColor $(if($firewallResult.Created){"Green"}else{"Red"})
        Write-Host "  Enabled: $($firewallResult.Enabled)" -ForegroundColor $(if($firewallResult.Enabled){"Green"}else{"Red"})
        Write-Host "  Profile: $($firewallResult.Profile)" -ForegroundColor Gray
        $firewallCreated = $firewallResult.Created -and $firewallResult.Enabled
    } catch {
        Write-Host "  WinRM firewall config failed: $_" -ForegroundColor Red
    }
} else {
    Write-Host "  WinRM unavailable, trying alternative methods..." -ForegroundColor Yellow
    
    # Method 2: Try with explicit WinRM settings
    try {
        $session = New-PSSession -ComputerName $targetIP -Credential $targetCred -ErrorAction Stop -WarningAction SilentlyContinue
        
        if ($session) {
            $result = Invoke-Command -Session $session -ScriptBlock {
                $ruleName = "Project-S Interactive Layer"
                
                $existingRule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
                
                if ($existingRule) {
                    if (-not $existingRule.Enabled) {
                        Enable-NetFirewallRule -DisplayName $ruleName
                    }
                } else {
                    New-NetFirewallRule `
                        -DisplayName $ruleName `
                        -Direction Inbound `
                        -Protocol TCP `
                        -LocalPort 8000 `
                        -Action Allow `
                        -Profile Private `
                        -Description "Allow inbound TCP 8000 for Project-S Interactive Layer"
                }
                
                $verifyRule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
                if ($verifyRule) {
                    @{ Created = $true; Enabled = $verifyRule.Enabled; Profile = ($verifyRule.Profile -join ","); Action = $verifyRule.Action }
                } else {
                    @{ Created = $false; Enabled = $false; Profile = ""; Action = "" }
                }
            }
            
            Write-Host "  Firewall rule: $($result.Created)" -ForegroundColor $(if($result.Created){"Green"}else{"Red"})
            Write-Host "  Enabled: $($result.Enabled)" -ForegroundColor $(if($result.Enabled){"Green"}else{"Red"})
            $firewallCreated = $result.Created -and $result.Enabled
        }
        
        Remove-PSSession $session -ErrorAction SilentlyContinue
    } catch {
        Write-Host "  PSSession method failed: $_" -ForegroundColor Red
    }
}

# ============================================================
# Check port reachability
# ============================================================
Write-Host ""
Write-Host "[3/6] Checking port 8000 reachability..." -ForegroundColor Yellow

$portReachable = $false
$healthOverLAN = $false

try {
    $netTest = Test-NetConnection -ComputerName "192.168.1.180" -Port 8000 -WarningAction SilentlyContinue -ErrorAction Stop -InformationLevel Detailed
    Write-Host "  TCP 8000 from DEV: $($netTest.TcpTestSucceeded)" -ForegroundColor $(if($netTest.TcpTestSucceeded){"Green"}else{"Red"})
    $portReachable = $netTest.TcpTestSucceeded
} catch {
    Write-Host "  Net test failed: $_" -ForegroundColor Red
}

if ($portReachable) {
    try {
        $healthResponse = Invoke-RestMethod -Uri "http://192.168.1.180:8000/health" -TimeoutSec 10 -ErrorAction Stop
        Write-Host "  /health over LAN: $($healthResponse.status)" -ForegroundColor Green
        $healthOverLAN = ($healthResponse.status -eq "ok")
    } catch {
        Write-Host "  /health over LAN failed: $_" -ForegroundColor Red
    }
} else {
    Write-Host "  Skipping /health check (port not reachable)" -ForegroundColor Yellow
}

# ============================================================
# If firewall worked but port not reachable, check server
# ============================================================
Write-Host ""
Write-Host "[4/6] Verifying server process..." -ForegroundColor Yellow

$serverRunning = $false
if ($serverAlive) {
    try {
        $procCheck = Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
            $pyProcs = Get-Process python -ErrorAction SilentlyContinue
            if ($pyProcs) {
                $pyProcs | Select-Object Id, ProcessName, StartTime, @{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB)}}
            } else {
                "No python processes"
            }
        } -ErrorAction Stop
        
        Write-Host $procCheck -ForegroundColor Gray
        $serverRunning = ($procCheck -ne "No python processes")
    } catch {
        Write-Host "  Process check failed: $_" -ForegroundColor Red
    }
}

# ============================================================
# Run smoke mission if server reachable
# ============================================================
Write-Host ""
Write-Host "[5/6] Running smoke mission..." -ForegroundColor Yellow

$sessionCreated = $false
$sessionId = ""
$missionLaunched = $false
$missionId = ""
$terminalState = ""
$finalResult = ""
$finalError = ""
$aiWorking = $false
$runtimeSeconds = 0

if ($healthOverLAN) {
    # Create session
    try {
        $sessionBody = @{
            user_id = "phase42_smoke_retry"
            metadata = @{
                purpose = "Phase 4.2 infrastructure smoke test (retry)"
                timestamp = $startTime.ToString("yyyy-MM-dd HH:mm:ss")
            }
        } | ConvertTo-Json -Compress
        
        $sessionResponse = Invoke-RestMethod `
            -Uri "http://192.168.1.180:8000/api/sessions" `
            -Method Post `
            -ContentType "application/json" `
            -Body $sessionBody `
            -TimeoutSec 15
        
        $sessionId = $sessionResponse.session_id
        Write-Host "  Session created: $sessionId" -ForegroundColor Green
        $sessionCreated = $true
    } catch {
        Write-Host "  Session creation failed: $_" -ForegroundColor Red
    }
    
    # Launch mission
    if ($sessionCreated) {
        $hungarianPrompt = "Írj 3 rövid mondatot arról, hogy miért fontos a pontos dokumentáció."
        
        try {
            $missionBody = @{
                session_id = $sessionId
                user_id = "phase42_smoke_retry"
                task = $hungarianPrompt
            } | ConvertTo-Json -Compress
            
            $missionResponse = Invoke-RestMethod `
                -Uri "http://192.168.1.180:8000/api/missions" `
                -Method Post `
                -ContentType "application/json" `
                -Body $missionBody `
                -TimeoutSec 15
            
            $missionId = $missionResponse.mission_id
            Write-Host "  Mission launched: $missionId" -ForegroundColor Green
            $missionLaunched = $true
        } catch {
            Write-Host "  Mission launch failed: $_" -ForegroundColor Red
        }
        
        # Poll mission
        if ($missionLaunched) {
            $maxPolls = 60
            $pollInterval = 10
            
            for ($i = 0; $i -lt $maxPolls; $i++) {
                Start-Sleep -Seconds $pollInterval
                $runtimeSeconds += $pollInterval
                
                try {
                    $statusResponse = Invoke-RestMethod `
                        -Uri "http://192.168.1.180:8000/api/missions/$missionId/status" `
                        -TimeoutSec 10 `
                        -ErrorAction Stop
                    
                    $currentState = $statusResponse.state
                    $currentProgress = $statusResponse.progress
                    Write-Host "  [${runtimeSeconds}s] State: $currentState, Progress: $currentProgress" -ForegroundColor Gray
                    
                    if ($currentState -in @("COMPLETE", "FAILED", "TIMEOUT")) {
                        $terminalState = $currentState
                        
                        $fullMission = Invoke-RestMethod `
                            -Uri "http://192.168.1.180:8000/api/missions/$missionId" `
                            -TimeoutSec 10 `
                            -ErrorAction Stop
                        
                        $finalResult = if ($fullMission.result) { $fullMission.result } else { "" }
                        $finalError = if ($fullMission.error) { $fullMission.error } else { "" }
                        
                        if ($terminalState -eq "COMPLETE") { $aiWorking = $true }
                        
                        Write-Host "  Mission terminal: $terminalState" -ForegroundColor $(if($terminalState -eq "COMPLETE"){"Green"}else{"Red"})
                        break
                    }
                } catch {
                    Write-Host "  Poll failed: $_" -ForegroundColor Yellow
                }
            }
            
            if (-not $terminalState) {
                $terminalState = "TIMEOUT (exceeded $(( $maxPolls * $pollInterval ))s)"
            }
        }
    }
} else {
    Write-Host "  Skipping smoke mission (server not reachable via LAN)" -ForegroundColor Yellow
}

$endTime = Get-Date
$totalRuntime = ($endTime - $startTime).TotalSeconds

# ============================================================
# SAVE RESULTS
# ============================================================
Write-Host ""
Write-Host "[6/6] Saving results..." -ForegroundColor Yellow

$allResults = @{
    Phase = "4.2 - Firewall + First Interactive Smoke (Retry)"
    Timestamp = $endTime.ToString("yyyy-MM-dd HH:mm:ss")
    TotalWallTime = [math]::Round($totalRuntime, 1)
    MissionRuntime = $runtimeSeconds
    ServerAlive = $serverAlive
    ServerRunning = $serverRunning
    FirewallCreated = $firewallCreated
    PortReachable = $portReachable
    HealthOverLAN = $healthOverLAN
    SessionCreated = $sessionCreated
    SessionId = $sessionId
    MissionLaunched = $missionLaunched
    MissionId = $missionId
    TerminalState = $terminalState
    FinalResult = $finalResult
    FinalError = $finalError
    AIWorking = $aiWorking
}

$allResults | ConvertTo-Json -Compress | Out-File -FilePath "C:\ProjectS-Unified\.phase42_results.json" -Encoding UTF8

# ============================================================
# SUMMARY
# ============================================================
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  PHASE 4.2 SUMMARY" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  A. Firewall rule created: $(if($firewallCreated){'YES'}else{'NO'})" -ForegroundColor $(if($firewallCreated){"Green"}else{"Red"})
Write-Host "  B. Port 8000 reachable from DEV: $(if($portReachable){'YES'}else{'NO'})" -ForegroundColor $(if($portReachable){"Green"}else{"Red"})
Write-Host "  C. /health over LAN PASS: $(if($healthOverLAN){'YES'}else{'NO'})" -ForegroundColor $(if($healthOverLAN){"Green"}else{"Red"})
Write-Host "  D. Smoke session created: $(if($sessionCreated){'YES'}else{'NO'})" -ForegroundColor $(if($sessionCreated){"Green"}else{"Red"})
Write-Host "  E. Smoke mission launched: $(if($missionLaunched){'YES'}else{'NO'})" -ForegroundColor $(if($missionLaunched){"Green"}else{"Red"})
Write-Host "  F. Terminal state: $terminalState" -ForegroundColor $(if($terminalState -eq "COMPLETE"){"Green"}else{"Yellow"})
Write-Host "  G. AI provider path working: $(if($aiWorking){'YES'}else{'NO'})" -ForegroundColor $(if($aiWorking){"Green"}else{"Yellow"})
Write-Host "  I. Mission ID: $missionId" -ForegroundColor Gray
Write-Host "  J. Runtime: ${runtimeSeconds}s" -ForegroundColor Gray
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan