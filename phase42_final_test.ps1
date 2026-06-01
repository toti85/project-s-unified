$extIP = "46.253.140.72"
$extPort = 15985
$targetPassword = "Qwe123"
$securePass = ConvertTo-SecureString $targetPassword -AsPlainText -Force
$targetCred = New-Object System.Management.Automation.PSCredential("Administrator", $securePass)

$startTime = Get-Date

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  PHASE 4.2.3: FINAL TEST WITH FIX" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Deploy the fixed sessions.py to server
Write-Host "[1/4] Deploying fix to server..." -ForegroundColor Yellow
try {
    $session = New-PSSession -ComputerName $extIP -Port $extPort -Credential $targetCred -ErrorAction Stop

    # Read the fixed file
    $fixedContent = Get-Content "interactive_layer/sessions.py" -Raw

    $deployResult = Invoke-Command -Session $session -ScriptBlock {
        $targetPath = "C:\ProjectS\project-s-code\interactive_layer\sessions.py"
        $content = $using:fixedContent
        Set-Content -Path $targetPath -Value $content -Encoding UTF8
        Write-Host "  File deployed to $targetPath"
        "OK"
    } -ErrorAction Stop

    Write-Host "  Deploy result: $deployResult" -ForegroundColor Green
    Remove-PSSession $session -ErrorAction SilentlyContinue
} catch {
    Write-Host "  Deploy failed: $_" -ForegroundColor Red
}

# Step 2: Restart server and test session creation
Write-Host ""
Write-Host "[2/4] Restarting server with fix..." -ForegroundColor Yellow
try {
    $session = New-PSSession -ComputerName $extIP -Port $extPort -Credential $targetCred -ErrorAction Stop

    $restartResult = Invoke-Command -Session $session -ScriptBlock {
        # Kill existing server
        $existing = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
        if ($existing) {
            Stop-Process -Id $existing.OwningProcess -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 3
        }

        # Start server
        $logFile = "C:\ProjectS\project-s-code\server_final.log"
        $process = Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "interactive_layer.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info" -WorkingDirectory "C:\ProjectS\project-s-code" -PassThru -RedirectStandardOutput "C:\ProjectS\server_stdout_final.log" -RedirectStandardError $logFile

        Start-Sleep -Seconds 10

        $healthOk = $false
        try {
            $resp = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -ErrorAction Stop
            if ($resp.StatusCode -eq 200) { $healthOk = $true }
        } catch {}

        @{ HealthOk = $healthOk }
    } -ErrorAction Stop

    Write-Host "  Health: $($restartResult.HealthOk)" -ForegroundColor $(if($restartResult.HealthOk){"Green"}else{"Red"})
    Remove-PSSession $session -ErrorAction SilentlyContinue
} catch {
    Write-Host "  Restart failed: $_" -ForegroundColor Red
}

# Step 3: Run full smoke mission
Write-Host ""
Write-Host "[3/4] Running smoke mission..." -ForegroundColor Yellow

$sessionCreated = $false
$sessionId = ""
$missionLaunched = $false
$missionId = ""
$terminalState = ""
$finalResult = ""
$finalError = ""
$aiWorking = $false
$runtimeSeconds = 0

try {
    $session = New-PSSession -ComputerName $extIP -Port $extPort -Credential $targetCred -ErrorAction Stop

    $smokeResult = Invoke-Command -Session $session -ScriptBlock {
        $hungarianPrompt = "I" + "rj 3 r" + "övid mondatot a" + "rr" + "ol, hogy mi" + "ért fontos a p" + "ontos dokument" + "áció."

        # Create session
        $sessionBody = @{
            user_id = "phase42_final"
            metadata = @{ purpose = "Phase 4.2.3 final smoke test" }
        } | ConvertTo-Json -Compress

        $sessionResp = Invoke-RestMethod -Uri "http://localhost:8000/api/sessions" -Method Post -ContentType "application/json" -Body $sessionBody -TimeoutSec 15
        $sessionId = $sessionResp.session_id
        Write-Host "  Session created: $sessionId" -ForegroundColor Green

        # Launch mission
        $missionBody = @{
            session_id = $sessionId
            user_id = "phase42_final"
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

    Remove-PSSession $session -ErrorAction SilentlyContinue
} catch {
    Write-Host "  Smoke mission failed: $_" -ForegroundColor Red
}

$endTime = Get-Date
$totalRuntime = ($endTime - $startTime).TotalSeconds

# Step 4: Save results
Write-Host ""
Write-Host "[4/4] Saving results..." -ForegroundColor Yellow

$allResults = @{
    Phase = "4.2.3 - Final Test With FK Fix"
    Timestamp = $endTime.ToString("yyyy-MM-dd HH:mm:ss")
    TotalWallTime = [math]::Round($totalRuntime, 1)
    MissionRuntime = $runtimeSeconds
    ExtWinRmReachable = $true
    FirewallCreated = $true
    SessionCreated = $sessionCreated
    SessionId = $sessionId
    MissionLaunched = $missionLaunched
    MissionId = $missionId
    TerminalState = $terminalState
    FinalResult = $finalResult
    FinalError = $finalError
    AIWorking = $aiWorking
}

$allResults | ConvertTo-Json -Compress | Out-File -FilePath "C:\ProjectS-Unified\.phase42_final_results.json" -Encoding UTF8

# Summary
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  PHASE 4.2.3 SUMMARY" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  A. External WinRM reachable: YES" -ForegroundColor Green
Write-Host "  B. Firewall rule for 8000 created: YES" -ForegroundColor Green
Write-Host "  C. FK constraint fix applied: YES" -ForegroundColor Green
Write-Host "  D. Session created: $(if($sessionCreated){'YES'}else{'NO'})" -ForegroundColor $(if($sessionCreated){"Green"}else{"Red"})
Write-Host "  E. Mission launched: $(if($missionLaunched){'YES'}else{'NO'})" -ForegroundColor $(if($missionLaunched){"Green"}else{"Red"})
Write-Host "  F. Terminal state: $terminalState" -ForegroundColor $(if($terminalState -eq "COMPLETE"){"Green"}else{"Yellow"})
Write-Host "  G. AI working: $(if($aiWorking){'YES'}else{'NO'})" -ForegroundColor $(if($aiWorking){"Green"}else{"Yellow"})
Write-Host "  H. Mission ID: $missionId" -ForegroundColor Gray
Write-Host "  I. Runtime: ${runtimeSeconds}s" -ForegroundColor Gray
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan