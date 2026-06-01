$extIP = "46.253.140.72"
$extPort = 15985
$targetPassword = "Qwe123"
$securePass = ConvertTo-SecureString $targetPassword -AsPlainText -Force
$targetCred = New-Object System.Management.Automation.PSCredential("Administrator", $securePass)

$newApiKey = "[REDACTED - EXPOSED KEY REMOVED]"

$startTime = Get-Date

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  PHASE 4.3: DEPLOY NEW API KEY + RETRY" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================
# TASK 1: DEPLOY NEW API KEY
# ============================================================
Write-Host "[1/4] Deploying new OPENROUTER_API_KEY..." -ForegroundColor Yellow

$keyDeployed = $false
try {
    $session = New-PSSession -ComputerName $extIP -Port $extPort -Credential $targetCred -ErrorAction Stop

    $deployResult = Invoke-Command -Session $session -ScriptBlock {
        $envPath = "C:\ProjectS\project-s-code\.env"
        $newKey = $using:newApiKey

        # Read current .env
        $content = Get-Content $envPath -Raw

        # Replace the OPENROUTER_API_KEY line
        $updatedContent = $content -replace '(?m)^OPENROUTER_API_KEY=.*', "OPENROUTER_API_KEY=$newKey"

        if ($updatedContent -eq $content) {
            # Key wasn't present, append it
            if ($content -and -not $content.EndsWith("`n")) {
                $updatedContent = $content + "`n" + "OPENROUTER_API_KEY=$newKey"
            } else {
                $updatedContent = "OPENROUTER_API_KEY=$newKey"
            }
        }

        Set-Content -Path $envPath -Value $updatedContent -Encoding UTF8 -NoNewline

        # Verify
        $verifyContent = Get-Content $envPath -Raw
        $match = $verifyContent | Select-String "OPENROUTER_API_KEY=(.*)"
        if ($match) {
            $keyLen = ($match.Matches[0].Groups[1].Value).Length
            Write-Host "  Key deployed, length=$keyLen"
            @{ Deployed = $true; Length = $keyLen }
        } else {
            Write-Host "  Key NOT found after deploy"
            @{ Deployed = $false; Length = 0 }
        }
    } -ErrorAction Stop

    $keyDeployed = $deployResult.Deployed
    Write-Host "  Deployed: $keyDeployed" -ForegroundColor $(if($keyDeployed){"Green"}else{"Red"})

    Remove-PSSession $session -ErrorAction SilentlyContinue
} catch {
    Write-Host "  Deploy failed: $_" -ForegroundColor Red
}

# ============================================================
# TASK 2: VERIFY PYTHON CAN LOAD THE KEY
# ============================================================
Write-Host ""
Write-Host "[2/4] Verifying Python can load the key..." -ForegroundColor Yellow

$keyLoads = $false
try {
    $session = New-PSSession -ComputerName $extIP -Port $extPort -Credential $targetCred -ErrorAction Stop

    $loadResult = Invoke-Command -Session $session -ScriptBlock {
        $codePath = "C:\ProjectS\project-s-code"
        $test = python -c "
import os
from dotenv import load_dotenv
load_dotenv(r'$codePath\.env')
v = os.getenv('OPENROUTER_API_KEY', '')
print('loaded=' + ('YES' if v else 'NO') + ' len=' + str(len(v)))
" 2>&1 | Out-String
        Write-Host $test
        @{ Loaded = ($test -match 'loaded=YES') }
    } -ErrorAction Stop

    $keyLoads = $loadResult.Loaded
    Write-Host "  Python loads key: $keyLoads" -ForegroundColor $(if($keyLoads){"Green"}else{"Red"})

    Remove-PSSession $session -ErrorAction SilentlyContinue
} catch {
    Write-Host "  Load test failed: $_" -ForegroundColor Red
}

# ============================================================
# TASK 3: RESTART SERVER WITH CORRECT KEY
# ============================================================
Write-Host ""
Write-Host "[3/4] Restarting server..." -ForegroundColor Yellow

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
        $logFile = "C:\ProjectS\project-s-code\server_phase43_v2.log"
        $process = Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "interactive_layer.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info" -WorkingDirectory $codePath -PassThru -RedirectStandardOutput "C:\ProjectS\server_stdout43_v2.log" -RedirectStandardError $logFile

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
    Write-Host "  /health: $healthBefore" -ForegroundColor $(if($healthBefore){"Green"}else{"Red"})

    Remove-PSSession $session -ErrorAction SilentlyContinue
} catch {
    Write-Host "  Restart failed: $_" -ForegroundColor Red
}

# ============================================================
# TASK 4: RUN SMOKE MISSION
# ============================================================
Write-Host ""
Write-Host "[4/4] Running smoke mission..." -ForegroundColor Yellow

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
$healthAfter = $false

try {
    $session = New-PSSession -ComputerName $extIP -Port $extPort -Credential $targetCred -ErrorAction Stop

    $smokeResult = Invoke-Command -Session $session -ScriptBlock {
        $hungarianPrompt = "I" + "rj 3 r" + "Г¶vid mondatot a" + "rr" + "ol, hogy mi" + "Г©rt fontos a p" + "ontos dokument" + "ГЎciГі."

        # Create session
        $sessionBody = @{
            user_id = "phase43_retry"
            metadata = @{ purpose = "Phase 4.3 API key retry" }
        } | ConvertTo-Json -Compress

        $sessionResp = Invoke-RestMethod -Uri "http://localhost:8000/api/sessions" -Method Post -ContentType "application/json" -Body $sessionBody -TimeoutSec 15
        $sessionId = $sessionResp.session_id
        Write-Host "  Session created: $sessionId" -ForegroundColor Green

        # Launch mission
        $missionBody = @{
            session_id = $sessionId
            user_id = "phase43_retry"
            task = $hungarianPrompt
        } | ConvertTo-Json -Compress

        $missionResp = Invoke-RestMethod -Uri "http://localhost:8000/api/missions" -Method Post -ContentType "application/json" -Body $missionBody -TimeoutSec 15
        $missionId = $missionResp.mission_id
        Write-Host "  Mission launched: $missionId" -ForegroundColor Green

        # Poll status
        $maxPolls = 90
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

    # Verify process survival
    Write-Host ""
    Write-Host "  Verifying process survival..." -ForegroundColor Yellow

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
    Write-Host "  /health after: $($survivalResult.HealthAfter)" -ForegroundColor $(if($survivalResult.HealthAfter){"Green"}else{"Red"})

    $processCrashed = -not ($survivalResult.PythonProcs -gt 0)
    $healthAfter = $survivalResult.HealthAfter

    Remove-PSSession $session -ErrorAction SilentlyContinue
} catch {
    Write-Host "  Smoke mission failed: $_" -ForegroundColor Red
    $processCrashed = $true
}

$endTime = Get-Date
$totalRuntime = ($endTime - $startTime).TotalSeconds

# ============================================================
# SAVE RESULTS
# ============================================================
Write-Host ""
Write-Host "[5/5] Saving results..." -ForegroundColor Yellow

$allResults = @{
    Phase = "4.3 - Deploy New API Key + SAI Smoke Retry"
    Timestamp = $endTime.ToString("yyyy-MM-dd HH:mm:ss")
    TotalWallTime = [math]::Round($totalRuntime, 1)
    MissionRuntime = $runtimeSeconds
    KeyDeployed = $keyDeployed
    KeyLoadsInPython = $keyLoads
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
    HealthAfter = $healthAfter
    FxFixNeedsPort = $true
}

$allResults | ConvertTo-Json -Compress | Out-File -FilePath "C:\ProjectS-Unified\.phase43_retry_results.json" -Encoding UTF8

# Summary
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  PHASE 4.3 RETRY SUMMARY" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  A. Key deployed: $(if($keyDeployed){'YES'}else{'NO'})" -ForegroundColor $(if($keyDeployed){"Green"}else{"Red"})
Write-Host "  B. Python loads key: $(if($keyLoads){'YES'}else{'NO'})" -ForegroundColor $(if($keyLoads){"Green"}else{"Red"})
Write-Host "  C. Server starts: $(if($serverStarts){'YES'}else{'NO'})" -ForegroundColor $(if($serverStarts){"Green"}else{"Red"})
Write-Host "  D. /health before: $(if($healthBefore){'YES'}else{'NO'})" -ForegroundColor $(if($healthBefore){"Green"}else{"Red"})
Write-Host "  E. Session created: $(if($sessionCreated){'YES'}else{'NO'})" -ForegroundColor $(if($sessionCreated){"Green"}else{"Red"})
Write-Host "  F. Mission launched: $(if($missionLaunched){'YES'}else{'NO'})" -ForegroundColor $(if($missionLaunched){"Green"}else{"Red"})
Write-Host "  G. Terminal state: $terminalState" -ForegroundColor $(if($terminalState -eq "COMPLETE"){"Green"}else{"Yellow"})
Write-Host "  H. Process crashed: $(if($processCrashed){'YES'}else{'NO'})" -ForegroundColor $(if(-not $processCrashed){"Green"}else{"Red"})
Write-Host "  I. /health after: $(if($healthAfter){'YES'}else{'NO'})" -ForegroundColor $(if($healthAfter){"Green"}else{"Red"})
Write-Host "  J. AI working: $(if($aiWorking){'YES'}else{'NO'})" -ForegroundColor $(if($aiWorking){"Green"}else{"Yellow"})
Write-Host "  K. FK fix needs porting: YES" -ForegroundColor Green
Write-Host "  L. Mission ID: $missionId" -ForegroundColor Gray
Write-Host "  M. Runtime: ${runtimeSeconds}s" -ForegroundColor Gray
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
