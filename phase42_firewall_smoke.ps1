$targetIP = "192.168.1.180"
$targetPassword = "Qwe123"
$securePass = ConvertTo-SecureString $targetPassword -AsPlainText -Force
$targetCred = New-Object System.Management.Automation.PSCredential("$targetIP\Administrator", $securePass)

$startTime = Get-Date

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  PHASE 4.2: FIREWALL + FIRST SMOKE MISSION" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================
# TASK 1: OPEN TCP 8000 ON PRIVATE PROFILE
# ============================================================
Write-Host "[1/5] Opening firewall rule for TCP 8000..." -ForegroundColor Yellow

$firewallRuleName = "Project-S Interactive Layer"
try {
    $firewallResult = Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
        $ruleName = "Project-S Interactive Layer"
        
        # Check if rule already exists
        $existingRule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
        
        if ($existingRule) {
            # Enable if disabled
            if (-not $existingRule.Enabled) {
                Enable-NetFirewallRule -DisplayName $ruleName
                Write-Host "  Rule re-enabled"
            } else {
                Write-Host "  Rule already exists and enabled"
            }
        } else {
            # Create new rule
            New-NetFirewallRule `
                -DisplayName $ruleName `
                -Direction Inbound `
                -Protocol TCP `
                -LocalPort 8000 `
                -Action Allow `
                -Profile Private `
                -Description "Allow inbound TCP 8000 for Project-S Interactive Layer"
            Write-Host "  Rule created"
        }
        
        # Verify
        $verifyRule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
        if ($verifyRule) {
            @{
                Created = $true
                Enabled = $verifyRule.Enabled
                Profile = ($verifyRule.Profile -join ",")
                Action = $verifyRule.Action
            }
        } else {
            @{ Created = $false; Enabled = $false; Profile = ""; Action = "" }
        }
    }
    
    Write-Host "  Firewall rule: $($firewallResult.Created)" -ForegroundColor $(if($firewallResult.Created){"Green"}else{"Red"})
    Write-Host "  Enabled: $($firewallResult.Enabled)" -ForegroundColor $(if($firewallResult.Enabled){"Green"}else{"Red"})
    Write-Host "  Profile: $($firewallResult.Profile)" -ForegroundColor Gray
    Write-Host "  Action: $($firewallResult.Action)" -ForegroundColor Gray
    
    $firewallCreated = $firewallResult.Created -and $firewallResult.Enabled
} catch {
    Write-Host "  Firewall creation failed: $_" -ForegroundColor Red
    $firewallCreated = $false
}

# ============================================================
# TASK 2: VERIFY REACHABILITY FROM DEV
# ============================================================
Write-Host ""
Write-Host "[2/5] Verifying reachability from DEV..." -ForegroundColor Yellow

$portReachable = $false
$healthOverLAN = $false

try {
    $netTest = Test-NetConnection -ComputerName "192.168.1.180" -Port 8000 -WarningAction SilentlyContinue -ErrorAction Stop
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
    Write-Host "  Skipping /health over LAN (port not reachable)" -ForegroundColor Yellow
}

# ============================================================
# TASK 3: FIRST REAL SERVER-SIDE SMOKE MISSION
# ============================================================
Write-Host ""
Write-Host "[3/5] Creating smoke session..." -ForegroundColor Yellow

$sessionCreated = $false
$sessionId = ""

if ($healthOverLAN) {
    try {
        $sessionBody = @{
            user_id = "phase42_smoke"
            metadata = @{
                purpose = "Phase 4.2 infrastructure smoke test"
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
} else {
    Write-Host "  Skipping session creation (health check failed)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[4/5] Submitting smoke mission..." -ForegroundColor Yellow

$missionLaunched = $false
$missionId = ""
$missionState = ""
$missionResult = ""
$missionError = ""
$aiWorking = $false

if ($sessionCreated) {
    $hungarianPrompt = "Írj 3 r" + "övid mondatot arról, hogy mi" + "ért fontos a p" + "ontos dokument" + "áció."
    
    try {
        $missionBody = @{
            session_id = $sessionId
            user_id = "phase42_smoke"
            task = $hungarianPrompt
        } | ConvertTo-Json -Compress
        
        $missionResponse = Invoke-RestMethod `
            -Uri "http://192.168.1.180:8000/api/missions" `
            -Method Post `
            -ContentType "application/json" `
            -Body $missionBody `
            -TimeoutSec 15
        
        $missionId = $missionResponse.mission_id
        $missionState = $missionResponse.state
        Write-Host "  Mission launched: $missionId (state: $missionState)" -ForegroundColor Green
        $missionLaunched = $true
    } catch {
        Write-Host "  Mission launch failed: $_" -ForegroundColor Red
    }
} else {
    Write-Host "  Skipping mission launch (session not created)" -ForegroundColor Yellow
}

# Poll mission status
Write-Host ""
Write-Host "[5/5] Polling mission status..." -ForegroundColor Yellow

$terminalState = ""
$finalResult = ""
$finalError = ""
$runtimeSeconds = 0
$maxPolls = 60
$pollInterval = 10

if ($missionLaunched) {
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
            Write-Host "  [$runtime`s] State: $currentState, Progress: $currentProgress" -ForegroundColor Gray
            
            if ($currentState -in @("COMPLETE", "FAILED", "TIMEOUT")) {
                $terminalState = $currentState
                $missionState = $currentState
                
                # Get full mission details for result
                $fullMission = Invoke-RestMethod `
                    -Uri "http://192.168.1.180:8000/api/missions/$missionId" `
                    -TimeoutSec 10 `
                    -ErrorAction Stop
                
                $finalResult = if ($fullMission.result) { $fullMission.result } else { "" }
                $finalError = if ($fullMission.error) { $fullMission.error } else { "" }
                
                if ($terminalState -eq "COMPLETE") {
                    $aiWorking = $true
                } elseif ($terminalState -eq "FAILED") {
                    # Check if it's a runtime/crash error vs AI error
                    if ($finalError -match "crash|traceback|ModuleNotFound|ImportError|OSError") {
                        $aiWorking = $false
                    } else {
                        $aiWorking = $false
                    }
                }
                
                Write-Host "  Mission terminal: $terminalState" -ForegroundColor $(if($terminalState -eq "COMPLETE"){"Green"}else{"Red"})
                break
            }
        } catch {
            Write-Host "  Poll failed at attempt $($i+1): $_" -ForegroundColor Yellow
        }
    }
    
    if (-not $terminalState) {
        $terminalState = "TIMEOUT (exceeded $($maxPolls * $pollInterval)s)"
        Write-Host "  Mission timed out after $($maxPolls * $pollInterval) seconds" -ForegroundColor Yellow
    }
}

$endTime = Get-Date
$totalRuntime = ($endTime - $startTime).TotalSeconds

# ============================================================
# SAVE RESULTS
# ============================================================
Write-Host ""
Write-Host "Saving results..." -ForegroundColor Yellow

$allResults = @{
    Phase = "4.2 - Firewall + First Interactive Smoke"
    Timestamp = $endTime.ToString("yyyy-MM-dd HH:mm:ss")
    TotalWallTime = [math]::Round($totalRuntime, 1)
    MissionRuntime = $runtimeSeconds
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
    MissingDependencyCrash = -not $aiWorking -and (-not $finalError -or $finalError -notmatch "crash|traceback|ModuleNotFound|ImportError")
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
Write-Host "  G. Missing dependency/crash: $(if($allResults.MissingDependencyCrash){'YES'}else{'NO'})" -ForegroundColor $(if($allResults.MissingDependencyCrash){"Red"}else{"Green"})
Write-Host "  H. AI provider path working: $(if($aiWorking){'YES'}else{'NO'})" -ForegroundColor $(if($aiWorking){"Green"}else{"Yellow"})
Write-Host "  I. Mission ID: $missionId" -ForegroundColor Gray
Write-Host "  J. Runtime: ${runtimeSeconds}s" -ForegroundColor Gray
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan