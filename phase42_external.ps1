$extIP = "46.253.140.72"
$extPort = 15985
$targetPassword = "Qwe123"
$securePass = ConvertTo-SecureString $targetPassword -AsPlainText -Force
$targetCred = New-Object System.Management.Automation.PSCredential("Administrator", $securePass)

$startTime = Get-Date

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  PHASE 4.2 - EXTERNAL WINRM" -ForegroundColor Cyan
Write-Host "  Target: $extIP`:$extPort" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================
# TASK 0: TEST EXTERNAL WINRM REACHABILITY
# ============================================================
Write-Host "[0/6] Testing external WinRM reachability..." -ForegroundColor Yellow

$extWinRmReachable = $false
try {
    $testResult = Test-WSMan -ComputerName $extIP -Port $extPort -ErrorAction Stop
    Write-Host "  External WinRM ($extIP`:$extPort): REACHABLE" -ForegroundColor Green
    $extWinRmReachable = $true
} catch {
    Write-Host "  External WinRM ($extIP`:$extPort): UNREACHABLE - $($_.Exception.Message)" -ForegroundColor Red
}

# ============================================================
# TASK 1: CREATE FIREWALL RULE VIA EXTERNAL WINRM
# ============================================================
Write-Host ""
Write-Host "[1/6] Creating firewall rule..." -ForegroundColor Yellow

$firewallCreated = $false

if ($extWinRmReachable) {
    try {
        $session = New-PSSession -ComputerName $extIP -Port $extPort -Credential $targetCred -ErrorAction Stop

        $result = Invoke-Command -Session $session -ScriptBlock {
            $ruleName = "Project-S Interactive Layer"

            $existingRule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue

            if ($existingRule) {
                if (-not $existingRule.Enabled) {
                    Enable-NetFirewallRule -DisplayName $ruleName
                }
                Write-Host "  Rule already exists, verified enabled"
            } else {
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

            $verifyRule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
            if ($verifyRule) {
                @{ Created = $true; Enabled = $verifyRule.Enabled; Profile = ($verifyRule.Profile -join ","); Action = $verifyRule.Action }
            } else {
                @{ Created = $false; Enabled = $false; Profile = ""; Action = "" }
            }
        } -ErrorAction Stop

        Write-Host "  Firewall rule: $($result.Created)" -ForegroundColor $(if($result.Created){"Green"}else{"Red"})
        Write-Host "  Enabled: $($result.Enabled)" -ForegroundColor $(if($result.Enabled){"Green"}else{"Red"})
        Write-Host "  Profile: $($result.Profile)" -ForegroundColor Gray
        Write-Host "  Action: $($result.Action)" -ForegroundColor Gray
        $firewallCreated = $result.Created -and $result.Enabled

        Remove-PSSession $session -ErrorAction SilentlyContinue
    } catch {
        Write-Host "  Firewall creation failed: $_" -ForegroundColor Red
    }
} else {
    Write-Host "  Skipped (WinRM unreachable)" -ForegroundColor Yellow
}

# ============================================================
# TASK 2: VERIFY SERVER STATE VIA EXTERNAL WINRM
# ============================================================
Write-Host ""
Write-Host "[2/6] Verifying server state..." -ForegroundColor Yellow

$serverRunning = $false
$localHealthPass = $false

if ($extWinRmReachable) {
    try {
        $session = New-PSSession -ComputerName $extIP -Port $extPort -Credential $targetCred -ErrorAction Stop

        $stateResult = Invoke-Command -Session $session -ScriptBlock {
            $pyProcs = Get-Process python -ErrorAction SilentlyContinue
            $procInfo = if ($pyProcs) {
                $pyProcs | Select-Object Id, ProcessName, @{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB)}}
            } else {
                "No python processes"
            }

            $port8000 = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue

            $healthOk = $false
            try {
                $resp = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -ErrorAction Stop
                if ($resp.StatusCode -eq 200) { $healthOk = $true }
            } catch {}

            @{
                Procs = $procInfo
                Port8000 = if($port8000){$true}else{$false}
                HealthOk = $healthOk
            }
        } -ErrorAction Stop

        Write-Host "  Port 8000 listening: $($stateResult.Port8000)" -ForegroundColor $(if($stateResult.Port8000){"Green"}else{"Yellow"})
        Write-Host "  Local /health: $($stateResult.HealthOk)" -ForegroundColor $(if($stateResult.HealthOk){"Green"}else{"Yellow"})

        $serverRunning = $stateResult.Port8000
        $localHealthPass = $stateResult.HealthOk

        Remove-PSSession $session -ErrorAction SilentlyContinue
    } catch {
        Write-Host "  Server state check failed: $_" -ForegroundColor Red
    }
}

# ============================================================
# TASK 3: START SERVER IF NOT RUNNING
# ============================================================
Write-Host ""
Write-Host "[3/6] Starting server if needed..." -ForegroundColor Yellow

$serverStarted = $false

if ($extWinRmReachable -and -not $serverRunning) {
    try {
        $session = New-PSSession -ComputerName $extIP -Port $extPort -Credential $targetCred -ErrorAction Stop

        $startResult = Invoke-Command -Session $session -ScriptBlock {
            $codePath = "C:\ProjectS\project-s-code"

            $uvicornOk = $false
            try {
                python -c "import uvicorn; print(uvicorn.__version__)" 2>&1 | Out-Null
                $uvicornOk = $true
            } catch { $uvicornOk = $false }
            Write-Host "  uvicorn installed: $uvicornOk"

            if (-not $uvicornOk) {
                Write-Host "  Installing uvicorn..."
                pip install uvicorn 2>&1 | Out-String | Write-Host
            }

            $process = Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "interactive_layer.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info" -WorkingDirectory $codePath -PassThru -WindowStyle Hidden

            Start-Sleep -Seconds 15

            $process.Refresh()
            $isRunning = $process.HasExited -eq $false

            $portListening = $false
            try {
                $conn = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction Stop
                if ($conn) { $portListening = $true }
            } catch {}

            $healthOk = $false
            try {
                $resp = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -ErrorAction Stop
                if ($resp.StatusCode -eq 200) { $healthOk = $true }
            } catch {}

            @{
                IsRunning = $isRunning
                PortListening = $portListening
                HealthOk = $healthOk
            }
        } -ErrorAction Stop

        Write-Host "  Process running: $($startResult.IsRunning)" -ForegroundColor $(if($startResult.IsRunning){"Green"}else{"Red"})
        Write-Host "  Port 8000 listening: $($startResult.PortListening)" -ForegroundColor $(if($startResult.PortListening){"Green"}else{"Red"})
        Write-Host "  Local /health: $($startResult.HealthOk)" -ForegroundColor $(if($startResult.HealthOk){"Green"}else{"Red"})

        $serverRunning = $startResult.IsRunning
        $localHealthPass = $startResult.HealthOk
        $serverStarted = $true

        Remove-PSSession $session -ErrorAction SilentlyContinue
    } catch {
        Write-Host "  Server start failed: $_" -ForegroundColor Red
    }
} elseif ($serverRunning) {
    Write-Host "  Server already running" -ForegroundColor Green
} else {
    Write-Host "  Skipped (WinRM unreachable)" -ForegroundColor Yellow
}

# ============================================================
# TASK 4: RUN SERVER-SIDE SMOKE MISSION VIA EXTERNAL WINRM
# ============================================================
Write-Host ""
Write-Host "[4/6] Running server-side smoke mission..." -ForegroundColor Yellow

$smokeExecuted = $false
$missionId = ""
$terminalState = ""
$finalResult = ""
$finalError = ""
$aiWorking = $false
$runtimeSeconds = 0

if ($extWinRmReachable) {
    try {
        $session = New-PSSession -ComputerName $extIP -Port $extPort -Credential $targetCred -ErrorAction Stop

        $smokeResult = Invoke-Command -Session $session -ScriptBlock {
            $hungarianPrompt = "I" + "rj 3 r" + "övid mondatot a" + "rr" + "ol, hogy mi" + "ért fontos a p" + "ontos dokument" + "áció."

            $sessionBody = @{
                user_id = "phase42_external"
                metadata = @{ purpose = "Phase 4.2 external smoke test" }
            } | ConvertTo-Json -Compress

            $sessionResp = Invoke-RestMethod -Uri "http://localhost:8000/api/sessions" -Method Post -ContentType "application/json" -Body $sessionBody -TimeoutSec 15
            $sessionId = $sessionResp.session_id
            Write-Host "  Session created: $sessionId"

            $missionBody = @{
                session_id = $sessionId
                user_id = "phase42_external"
                task = $hungarianPrompt
            } | ConvertTo-Json -Compress

            $missionResp = Invoke-RestMethod -Uri "http://localhost:8000/api/missions" -Method Post -ContentType "application/json" -Body $missionBody -TimeoutSec 15
            $missionId = $missionResp.mission_id
            Write-Host "  Mission launched: $missionId"

            $maxPolls = 60
            $pollInterval = 10
            $runtimeSeconds = 0

            for ($i = 0; $i -lt $maxPolls; $i++) {
                Start-Sleep -Seconds $pollInterval
                $runtimeSeconds += $pollInterval

                try {
                    $statusResp = Invoke-RestMethod -Uri "http://localhost:8000/api/missions/$missionId/status" -TimeoutSec 10 -ErrorAction Stop
                    $state = $statusResp.state
                    $progress = $statusResp.progress
                    Write-Host "  [${runtimeSeconds}s] State: $state, Progress: $progress"

                    if ($state -in @("COMPLETE", "FAILED", "TIMEOUT")) {
                        $fullMission = Invoke-RestMethod -Uri "http://localhost:8000/api/missions/$missionId" -TimeoutSec 10 -ErrorAction Stop

                        $result = if ($fullMission.result) { $fullMission.result } else { "" }
                        $errText = if ($fullMission.error) { $fullMission.error } else { "" }

                        @{
                            MissionId = $missionId
                            TerminalState = $state
                            Result = $result
                            ErrorText = $errText
                            Runtime = $runtimeSeconds
                            AIWorking = ($state -eq "COMPLETE")
                        }
                        break
                    }
                } catch {
                    Write-Host "  Poll failed: $_" -ForegroundColor Yellow
                }
            }

            if ($runtimeSeconds -ge $maxPolls * $pollInterval) {
                @{
                    MissionId = $missionId
                    TerminalState = "TIMEOUT (exceeded $($maxPolls * $pollInterval)s)"
                    Result = ""
                    ErrorText = "Polling timeout"
                    Runtime = $runtimeSeconds
                    AIWorking = $false
                }
            }
        } -ErrorAction Stop

        $missionId = $smokeResult.MissionId
        $terminalState = $smokeResult.TerminalState
        $finalResult = $smokeResult.Result
        $finalError = $smokeResult.ErrorText
        $runtimeSeconds = $smokeResult.Runtime
        $aiWorking = $smokeResult.AIWorking

        Write-Host "  Terminal state: $terminalState" -ForegroundColor $(if($terminalState -eq "COMPLETE"){"Green"}else{"Yellow"})
        Write-Host "  Runtime: ${runtimeSeconds}s" -ForegroundColor Gray
        Write-Host "  AI working: $aiWorking" -ForegroundColor $(if($aiWorking){"Green"}else{"Yellow"})

        $smokeExecuted = $true

        Remove-PSSession $session -ErrorAction SilentlyContinue
    } catch {
        Write-Host "  Smoke mission failed: $_" -ForegroundColor Red
    }
} else {
    Write-Host "  Skipped (WinRM unreachable)" -ForegroundColor Yellow
}

$endTime = Get-Date
$totalRuntime = ($endTime - $startTime).TotalSeconds

# ============================================================
# SAVE RESULTS
# ============================================================
Write-Host ""
Write-Host "[5/6] Saving results..." -ForegroundColor Yellow

$allResults = @{
    Phase = "4.2 - External WinRM Smoke Mission"
    Timestamp = $endTime.ToString("yyyy-MM-dd HH:mm:ss")
    TotalWallTime = [math]::Round($totalRuntime, 1)
    MissionRuntime = $runtimeSeconds
    ExtWinRmReachable = $extWinRmReachable
    FirewallCreated = $firewallCreated
    ServerRunning = $serverRunning
    LocalHealthPass = $localHealthPass
    SmokeExecuted = $smokeExecuted
    MissionId = $missionId
    TerminalState = $terminalState
    FinalResult = $finalResult
    FinalError = $finalError
    AIWorking = $aiWorking
}

$allResults | ConvertTo-Json -Compress | Out-File -FilePath "C:\ProjectS-Unified\.phase42_external_results.json" -Encoding UTF8

# ============================================================
# SUMMARY
# ============================================================
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  PHASE 4.2 EXTERNAL SUMMARY" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  A. External WinRM reachable: $(if($extWinRmReachable){'YES'}else{'NO'})" -ForegroundColor $(if($extWinRmReachable){"Green"}else{"Red"})
Write-Host "  B. Firewall rule for 8000 created: $(if($firewallCreated){'YES'}else{'NO'})" -ForegroundColor $(if($firewallCreated){"Green"}else{"Red"})
Write-Host "  C. Server-side localhost /health PASS: $(if($localHealthPass){'YES'}else{'NO'})" -ForegroundColor $(if($localHealthPass){"Green"}else{"Red"})
Write-Host "  D. Server-side smoke mission executed: $(if($smokeExecuted){'YES'}else{'NO'})" -ForegroundColor $(if($smokeExecuted){"Green"}else{"Red"})
Write-Host "  E. Terminal state: $terminalState" -ForegroundColor $(if($terminalState -eq "COMPLETE"){"Green"}else{"Yellow"})
Write-Host "  F. AI working: $(if($aiWorking){'YES'}else{'NO'})" -ForegroundColor $(if($aiWorking){"Green"}else{"Yellow"})
Write-Host "  G. Mission ID: $missionId" -ForegroundColor Gray
Write-Host "  H. Runtime: ${runtimeSeconds}s" -ForegroundColor Gray
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan