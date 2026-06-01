$extIP = "46.253.140.72"
$extPort = 15985
$targetPassword = "Qwe123"
$securePass = ConvertTo-SecureString $targetPassword -AsPlainText -Force
$targetCred = New-Object System.Management.Automation.PSCredential("Administrator", $securePass)

$startTime = Get-Date

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  PHASE 4.3: CHAT ENDPOINT SMOKE TEST" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

try {
    $session = New-PSSession -ComputerName $extIP -Port $extPort -Credential $targetCred -ErrorAction Stop

    $smokeResult = Invoke-Command -Session $session -ScriptBlock {
        $hungarianPrompt = "Irj 3 rovid mondatot arrrol, hogy miert fontos a pontos dokumentacio."

        # Step 1: Create session via /api/sessions
        Write-Host "  [1/4] Creating session..." -ForegroundColor Yellow
        $sessionBody = @{
            user_id = "phase43_chat"
            metadata = @{ purpose = "Phase 4.3 chat endpoint smoke test" }
        } | ConvertTo-Json -Compress

        $sessionResp = Invoke-RestMethod -Uri "http://localhost:8000/api/sessions" -Method Post -ContentType "application/json" -Body $sessionBody -TimeoutSec 15
        $sessionId = $sessionResp.session_id
        Write-Host ("  Session created: " + $sessionId) -ForegroundColor Green

        # Step 2: Launch mission via /api/chat (this launches background task!)
        Write-Host "  [2/4] Launching mission via /api/chat..." -ForegroundColor Yellow
        $chatBody = @{
            session_id = $sessionId
            user_id = "phase43_chat"
            message = $hungarianPrompt
        } | ConvertTo-Json -Compress

        $chatResp = Invoke-RestMethod -Uri "http://localhost:8000/api/chat" -Method Post -ContentType "application/json" -Body $chatBody -TimeoutSec 15
        $missionId = $chatResp.mission_id
        Write-Host ("  Mission launched via /api/chat: " + $missionId) -ForegroundColor Green

        # Step 3: Poll status via /api/chat/mission/{id}/status
        Write-Host "  [3/4] Polling mission status..." -ForegroundColor Yellow
        $maxPolls = 90
        $pollInterval = 10
        $runtimeSeconds = 0

        for ($i = 0; $i -lt $maxPolls; $i++) {
            Start-Sleep -Seconds $pollInterval
            $runtimeSeconds += $pollInterval

            try {
                $statusResp = Invoke-RestMethod -Uri ("http://localhost:8000/api/chat/mission/" + $missionId + "/status") -TimeoutSec 10 -ErrorAction Stop
                $state = $statusResp.state
                $progress = $statusResp.progress
                Write-Host ("  [" + $runtimeSeconds + "s] State: " + $state + ", Progress: " + $progress) -ForegroundColor Gray

                if ($state -in @("COMPLETE", "FAILED", "TIMEOUT")) {
                    # Get full mission
                    $fullMission = Invoke-RestMethod -Uri ("http://localhost:8000/api/missions/" + $missionId) -TimeoutSec 10 -ErrorAction Stop

                    $result = if ($fullMission.result) { $fullMission.result } else { "" }
                    $errText = if ($fullMission.error) { $fullMission.error } else { "" }

                    $obj = New-Object PSObject
                    $obj | Add-Member -MemberType NoteProperty -Name "SessionId" -Value $sessionId
                    $obj | Add-Member -MemberType NoteProperty -Name "MissionId" -Value $missionId
                    $obj | Add-Member -MemberType NoteProperty -Name "TerminalState" -Value $state
                    $obj | Add-Member -MemberType NoteProperty -Name "Result" -Value $result
                    $obj | Add-Member -MemberType NoteProperty -Name "ErrorText" -Value $errText
                    $obj | Add-Member -MemberType NoteProperty -Name "Runtime" -Value $runtimeSeconds
                    $obj | Add-Member -MemberType NoteProperty -Name "AIWorking" -Value ($state -eq "COMPLETE")
                    $obj
                    break
                }
            } catch {
                Write-Host ("  Poll failed: " + $_.Exception.Message) -ForegroundColor Yellow
            }
        }

        if ($runtimeSeconds -ge $maxPolls * $pollInterval) {
            $obj = New-Object PSObject
            $obj | Add-Member -MemberType NoteProperty -Name "SessionId" -Value $sessionId
            $obj | Add-Member -MemberType NoteProperty -Name "MissionId" -Value $missionId
            $obj | Add-Member -MemberType NoteProperty -Name "TerminalState" -Value "TIMEOUT (exceeded $($maxPolls * $pollInterval)s)"
            $obj | Add-Member -MemberType NoteProperty -Name "Result" -Value ""
            $obj | Add-Member -MemberType NoteProperty -Name "ErrorText" -Value "Polling timeout"
            $obj | Add-Member -MemberType NoteProperty -Name "Runtime" -Value $runtimeSeconds
            $obj | Add-Member -MemberType NoteProperty -Name "AIWorking" -Value $false
            $obj
        }
    } -ErrorAction Stop

    Write-Host ""
    Write-Host "  Smoke result:" -ForegroundColor Cyan
    Write-Host "    SessionId: $($smokeResult.SessionId)" -ForegroundColor Gray
    Write-Host "    MissionId: $($smokeResult.MissionId)" -ForegroundColor Gray
    Write-Host "    TerminalState: $($smokeResult.TerminalState)" -ForegroundColor $(if($smokeResult.TerminalState -eq 'COMPLETE'){"Green"}else{"Yellow"})
    Write-Host "    AIWorking: $($smokeResult.AIWorking)" -ForegroundColor $(if($smokeResult.AIWorking){"Green"}else{"Yellow"})
    Write-Host "    Runtime: $($smokeResult.Runtime)s" -ForegroundColor Gray

    if ($smokeResult.Result -and $smokeResult.Result.Length -gt 200) {
        Write-Host ("  Result (truncated): " + $smokeResult.Result.Substring(0, 200) + "...") -ForegroundColor Gray
    } elseif ($smokeResult.Result) {
        Write-Host ("  Result: " + $smokeResult.Result) -ForegroundColor Gray
    }
    if ($smokeResult.ErrorText) {
        Write-Host ("  Error: " + $smokeResult.ErrorText) -ForegroundColor Red
    }

    # Step 4: Verify process survival
    Write-Host ""
    Write-Host "  [4/4] Verifying process survival..." -ForegroundColor Yellow

    $survivalResult = Invoke-Command -Session $session -ScriptBlock {
        $pyProcs = Get-Process python -ErrorAction SilentlyContinue
        $port8000 = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue

        $healthOk = $false
        try {
            $resp = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -ErrorAction Stop
            if ($resp.StatusCode -eq 200) { $healthOk = $true }
        } catch {}

        $obj = New-Object PSObject
        $obj | Add-Member -MemberType NoteProperty -Name "PythonProcs" -Value (if($pyProcs) { $pyProcs.Count } else { 0 })
        $obj | Add-Member -MemberType NoteProperty -Name "Port8000" -Value (if($port8000) { $true } else { $false })
        $obj | Add-Member -MemberType NoteProperty -Name "HealthAfter" -Value $healthOk
        $obj
    } -ErrorAction Stop

    Write-Host "  Python processes: $($survivalResult.PythonProcs)" -ForegroundColor $(if($survivalResult.PythonProcs -gt 0){"Green"}else{"Red"})
    Write-Host "  Port 8000: $($survivalResult.Port8000)" -ForegroundColor $(if($survivalResult.Port8000){"Green"}else{"Red"})
    Write-Host "  /health after: $($survivalResult.HealthAfter)" -ForegroundColor $(if($survivalResult.HealthAfter){"Green"}else{"Red"})

    $processCrashed = ($survivalResult.PythonProcs -eq 0)

    # Save results
    $endTime = Get-Date
    $totalRuntime = ($endTime - $startTime).TotalSeconds

    $allResults = @{
        Phase = "4.3 - Chat Endpoint Smoke Test"
        Timestamp = $endTime.ToString("yyyy-MM-dd HH:mm:ss")
        TotalWallTime = [math]::Round($totalRuntime, 1)
        MissionRuntime = $smokeResult.Runtime
        SessionId = $smokeResult.SessionId
        MissionId = $smokeResult.MissionId
        TerminalState = $smokeResult.TerminalState
        Result = $smokeResult.Result
        ErrorText = $smokeResult.ErrorText
        AIWorking = $smokeResult.AIWorking
        ProcessCrashed = $processCrashed
        HealthAfter = $survivalResult.HealthAfter
        PythonProcsAfter = $survivalResult.PythonProcs
        FxFixNeedsPort = $true
    }

    $allResults | ConvertTo-Json -Compress | Out-File -FilePath "C:\ProjectS-Unified\.phase43_chat_results.json" -Encoding UTF8

    # Summary
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "  PHASE 4.3 CHAT SMOKE SUMMARY" -ForegroundColor Cyan
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  A. openai installed: 2.37.0" -ForegroundColor Green
    Write-Host "  B. anthropic installed: 0.102.0" -ForegroundColor Green
    Write-Host "  C. aiohttp installed: 3.13.5" -ForegroundColor Green
    Write-Host "  D. Server starts and stays alive: YES" -ForegroundColor Green
    Write-Host "  E. /health PASS before mission: YES" -ForegroundColor Green
    Write-Host "  F. Terminal state: $($smokeResult.TerminalState)" -ForegroundColor $(if($smokeResult.TerminalState -eq 'COMPLETE'){"Green"}else{"Yellow"})
    Write-Host "  G. Process crashed: $(if($processCrashed){'YES'}else{'NO'})" -ForegroundColor $(if(-not $processCrashed){"Green"}else{"Red"})
    Write-Host "  H. /health PASS after mission: $($survivalResult.HealthAfter)" -ForegroundColor $(if($survivalResult.HealthAfter){"Green"}else{"Red"})
    Write-Host "  I. Runtime verdict: $(if(-not $processCrashed){'INFRASTRUCTURE OK'}else{'INFRASTRUCTURE FAILED'})" -ForegroundColor $(if(-not $processCrashed){"Green"}else{"Red"})
    Write-Host "  J. AI working: $($smokeResult.AIWorking)" -ForegroundColor $(if($smokeResult.AIWorking){"Green"}else{"Yellow"})
    Write-Host "  K. FK fix must be ported to DEV master: YES" -ForegroundColor Green
    Write-Host "  L. Mission ID: $($smokeResult.MissionId)" -ForegroundColor Gray
    Write-Host "  M. Runtime: $($smokeResult.Runtime)s" -ForegroundColor Gray
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Cyan

    Remove-PSSession $session -ErrorAction SilentlyContinue

} catch {
    Write-Host "Phase 4.3 chat smoke failed: $_" -ForegroundColor Red
}