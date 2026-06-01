$extIP = "46.253.140.72"
$extPort = 15985
$targetPassword = "Qwe123"
$securePass = ConvertTo-SecureString $targetPassword -AsPlainText -Force
$targetCred = New-Object System.Management.Automation.PSCredential("Administrator", $securePass)

$startTime = Get-Date

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  PHASE 4.3: AI DEPS + SAI SMOKE RETRY" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================
# TASK 1: INSTALL MISSING AI PROVIDER PACKAGES
# ============================================================
Write-Host "[1/5] Installing AI provider packages..." -ForegroundColor Yellow

$openaiVersion = ""
$anthropicVersion = ""
$aiohttpVersion = ""

try {
    $session = New-PSSession -ComputerName $extIP -Port $extPort -Credential $targetCred -ErrorAction Stop

    $installResult = Invoke-Command -Session $session -ScriptBlock {
        Write-Host "Installing openai, anthropic, aiohttp..."
        $out = pip install openai anthropic aiohttp 2>&1 | Out-String
        Write-Host $out

        # Capture versions
        $ov = python -c "import openai; print(openai.__version__)" 2>&1 | Out-String
        $av = python -c "import anthropic; print(anthropic.__version__)" 2>&1 | Out-String
        $aio = python -c "import aiohttp; print(aiohttp.__version__)" 2>&1 | Out-String

        @{
            InstallOutput = $out
            OpenAI = $ov.Trim()
            Anthropic = $av.Trim()
            Aiohttp = $aio.Trim()
        }
    } -ErrorAction Stop

    $openaiVersion = $installResult.OpenAI
    $anthropicVersion = $installResult.Anthropic
    $aiohttpVersion = $installResult.Aiohttp

    Write-Host "  openai: $openaiVersion" -ForegroundColor Green
    Write-Host "  anthropic: $anthropicVersion" -ForegroundColor Green
    Write-Host "  aiohttp: $aiohttpVersion" -ForegroundColor Green

    Remove-PSSession $session -ErrorAction SilentlyContinue
} catch {
    Write-Host "  Install failed: $_" -ForegroundColor Red
}

# ============================================================
# TASK 2: RESTART INTERACTIVE LAYER
# ============================================================
Write-Host ""
Write-Host "[2/5] Restarting Interactive Layer..." -ForegroundColor Yellow

$serverStarts = $false
$healthBefore = $false

try {
    $session = New-PSSession -ComputerName $extIP -Port $extPort -Credential $targetCred -ErrorAction Stop

    $restartResult = Invoke-Command -Session $session -ScriptBlock {
        $codePath = "C:\ProjectS\project-s-code"

        # Kill existing server
        $existing = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
        if ($existing) {
            Stop-Process -Id $existing.OwningProcess -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 3
        }

        # Start server
        $logFile = "C:\ProjectS\project-s-code\server_phase43.log"
        $process = Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "interactive_layer.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info" -WorkingDirectory $codePath -PassThru -RedirectStandardOutput "C:\ProjectS\server_stdout43.log" -RedirectStandardError $logFile

        Start-Sleep -Seconds 10

        $process.Refresh()
        $isRunning = $process.HasExited -eq $false

        $healthOk = $false
        try {
            $resp = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -ErrorAction Stop
            if ($resp.StatusCode -eq 200) { $healthOk = $true }
        } catch {}

        @{
            IsRunning = $isRunning
            HealthOk = $healthOk
        }
    } -ErrorAction Stop

    $serverStarts = $restartResult.IsRunning
    $healthBefore = $restartResult.HealthOk

    Write-Host "  Process running: $serverStarts" -ForegroundColor $(if($serverStarts){"Green"}else{"Red"})
    Write-Host "  /health before mission: $healthBefore" -ForegroundColor $(if($healthBefore){"Green"}else{"Red"})

    Remove-PSSession $session -ErrorAction SilentlyContinue
} catch {
    Write-Host "  Restart failed: $_" -ForegroundColor Red
}

# ============================================================
# TASK 3: RETRY REAL SERVER-SIDE SMOKE MISSION
# ============================================================
Write-Host ""
Write-Host "[3/5] Running server-side smoke mission..." -ForegroundColor Yellow

$sessionCreated = $false
$sessionId = ""
$missionLaunched = $false
$missionId = ""
$terminalState = ""
$finalResult = ""
$finalError = ""
$aiWorking = $false
$runtimeSeconds = 0
$processCrashed = $false

try {
    $session = New-PSSession -ComputerName $extIP -Port $extPort -Credential $targetCred -ErrorAction Stop

    $smokeResult = Invoke-Command -Session $session -ScriptBlock {
        $hungarianPrompt = "I" + "rj 3 r" + "övid mondatot a" + "rr" + "ol, hogy mi" + "ért fontos a p" + "ontos dokument" + "áció."

        # Create session
        $sessionBody = @{
            user_id = "phase43_smoke"
            metadata = @{ purpose = "Phase 4.3 AI deps smoke test" }
        } | ConvertTo-Json -Compress

        $sessionResp = Invoke-RestMethod -Uri "http://localhost:8000/api/sessions" -Method Post -ContentType "application/json" -Body $sessionBody -TimeoutSec 15
        $sessionId = $sessionResp.session_id
        Write-Host "  Session created: $sessionId" -ForegroundColor Green

        # Launch mission
        $missionBody = @{
            session_id = $sessionId
            user_id = "phase43_smoke"
            task = $hungarianPrompt
        } | ConvertTo-Json -Compress

        $missionResp = Invoke-RestMethod -Uri "http://localhost:8000/api/missions" -Method Post -ContentType "application/json" -Body $missionBody -TimeoutSec 15
        $missionId = $missionResp.mission_id
        Write-Host "  Mission launched: $missionId" -ForegroundColor Green

        # Poll status
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
                Write-Host "  [${runtimeSeconds}s] State: $state, Progress: $progress" -ForegroundColor Gray

                if ($state -in @("COMPLETE", "FAILED", "TIMEOUT")) {
                    $fullMission = Invoke-RestMethod -Uri "http://localhost:8000/api/missions/$missionId" -TimeoutSec 10 -ErrorAction Stop

                    $result = if ($fullMission.result) { $fullMission.result } else { "" }
                    $errText = if ($fullMission.error) { $fullMission.error } else { "" }

                    @{
                        SessionId = $sessionId
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
                SessionId = $sessionId
                MissionId = $missionId
                TerminalState = "TIMEOUT (exceeded $($maxPolls * $pollInterval)s)"
                Result = ""
                ErrorText = "Polling timeout"
                Runtime = $runtimeSeconds
                AIWorking = $false
            }
        }
    } -ErrorAction Stop

    $sessionId = $smokeResult.SessionId
    $missionId = $smokeResult.MissionId
    $terminalState = $smokeResult.TerminalState
    $finalResult = $smokeResult.Result
    $finalError = $smokeResult.ErrorText
    $runtimeSeconds = $smokeResult.Runtime
    $aiWorking = $smokeResult.AIWorking

    Write-Host "  Terminal state: $terminalState" -ForegroundColor $(if($terminalState -eq "COMPLETE"){"Green"}else{"Yellow"})
    Write-Host "  Runtime: ${runtimeSeconds}s" -ForegroundColor Gray
    Write-Host "  AI working: $aiWorking" -ForegroundColor $(if($aiWorking){"Green"}else{"Yellow"})

    if ($finalResult -and $finalResult.Length -gt 200) {
        Write-Host "  Result (truncated): $($finalResult.Substring(0, 200))..." -ForegroundColor Gray
    } elseif ($finalResult) {
        Write-Host "  Result: $finalResult" -ForegroundColor Gray
    }
    if ($finalError) {
        Write-Host "  Error: $finalError" -ForegroundColor Red
    }

    $sessionCreated = $true
    $missionLaunched = $true

    # ============================================================
    # TASK 4: VERIFY PROCESS SURVIVAL
    # ============================================================
    Write-Host ""
    Write-Host "[4/5] Verifying process survival..." -ForegroundColor Yellow

    $survivalResult = Invoke-Command -Session $session -ScriptBlock {
        $pyProcs = Get-Process python -ErrorAction SilentlyContinue
        $port8000 = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue

        $healthOk = $false
        try {
            $resp = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -ErrorAction Stop
            if ($resp.StatusCode -eq 200) { $healthOk = $true }
        } catch {}

        @{
            PythonProcs = if($pyProcs) { $pyProcs.Count } else { 0 }
            Port8000 = if($port8000) { $true } else { $false }
            HealthAfter = $healthOk
        }
    } -ErrorAction Stop

    Write-Host "  Python processes: $($survivalResult.PythonProcs)" -ForegroundColor $(if($survivalResult.PythonProcs -gt 0){"Green"}else{"Red"})
    Write-Host "  Port 8000: $($survivalResult.Port8000)" -ForegroundColor $(if($survivalResult.Port8000){"Green"}else{"Red"})
    Write-Host "  /health after mission: $($survivalResult.HealthAfter)" -ForegroundColor $(if($survivalResult.HealthAfter){"Green"}else{"Red"})

    $processCrashed = -not $survivalResult.PythonProcs -gt 0

    Remove-PSSession $session -ErrorAction SilentlyContinue
} catch {
    Write-Host "  Smoke mission failed: $_" -ForegroundColor Red
    $processCrashed = $true
}

$endTime = Get-Date
$totalRuntime = ($endTime - $startTime).TotalSeconds

# ============================================================
# TASK 5: SAVE RESULTS AND GENERATE REPORT
# ============================================================
Write-Host ""
Write-Host "[5/5] Saving results..." -ForegroundColor Yellow

$allResults = @{
    Phase = "4.3 - AI Provider Dependencies + SAI Smoke Retry"
    Timestamp = $endTime.ToString("yyyy-MM-dd HH:mm:ss")
    TotalWallTime = [math]::Round($totalRuntime, 1)
    MissionRuntime = $runtimeSeconds
    OpenAIInstalled = $openaiVersion
    AnthropicInstalled = $anthropicVersion
    AiohttpInstalled = $aiohttpVersion
    ServerStarts = $serverStarts
    HealthBefore = $healthBefore
    SessionCreated = $sessionCreated
    SessionId = $sessionId
    MissionLaunched = $missionLaunched
    MissionId = $missionId
    TerminalState = $terminalState
    FinalResult = $finalResult
    FinalError = $finalError
    AIWorking = $aiWorking
    ProcessCrashed = $processCrashed
    FxFixNeedsPort = $true
}

$allResults | ConvertTo-Json -Compress | Out-File -FilePath "C:\ProjectS-Unified\.phase43_results.json" -Encoding UTF8

# Summary
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  PHASE 4.3 SUMMARY" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  A. openai installed: $openaiVersion" -ForegroundColor $(if($openaiVersion){"Green"}else{"Red"})
Write-Host "  B. anthropic installed: $anthropicVersion" -ForegroundColor $(if($anthropicVersion){"Green"}else{"Red"})
Write-Host "  C. aiohttp installed: $aiohttpVersion" -ForegroundColor $(if($aiohttpVersion){"Green"}else{"Red"})
Write-Host "  D. Server starts and stays alive: $(if($serverStarts){'YES'}else{'NO'})" -ForegroundColor $(if($serverStarts){"Green"}else{"Red"})
Write-Host "  E. /health PASS before mission: $(if($healthBefore){'YES'}else{'NO'})" -ForegroundColor $(if($healthBefore){"Green"}else{"Red"})
Write-Host "  F. Terminal state: $terminalState" -ForegroundColor $(if($terminalState -eq "COMPLETE"){"Green"}else{"Yellow"})
Write-Host "  G. Process crashed: $(if($processCrashed){'YES'}else{'NO'})" -ForegroundColor $(if(-not $processCrashed){"Green"}else{"Red"})
Write-Host "  H. /health PASS after mission: $(if($survivalResult -and $survivalResult.HealthAfter){'YES'}else{'NO'})" -ForegroundColor $(if($survivalResult -and $survivalResult.HealthAfter){"Green"}else{"Yellow"})
Write-Host "  I. Runtime verdict: $(if(-not $processCrashed){'INFRASTRUCTURE OK'}else{'INFRASTRUCTURE FAILED'})" -ForegroundColor $(if(-not $processCrashed){"Green"}else{"Red"})
Write-Host "  J. AI working: $(if($aiWorking){'YES'}else{'NO'})" -ForegroundColor $(if($aiWorking){"Green"}else{"Yellow"})
Write-Host "  K. FK fix must be ported to DEV master: YES" -ForegroundColor Green
Write-Host "  L. Mission ID: $missionId" -ForegroundColor Gray
Write-Host "  M. Runtime: ${runtimeSeconds}s" -ForegroundColor Gray
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan