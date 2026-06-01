$extIP = "46.253.140.72"
$extPort = 15985
$targetPassword = "Qwe123"
$securePass = ConvertTo-SecureString $targetPassword -AsPlainText -Force
$targetCred = New-Object System.Management.Automation.PSCredential("Administrator", $securePass)

$startTime = Get-Date

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  PHASE 4.3B: CRASH TRACEBACK CAPTURE" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================
# TASK 1: KILL EXISTING SERVER, START WITH FULL TRACEBACK CAPTURE
# ============================================================
Write-Host "[1/4] Starting server with full traceback capture..." -ForegroundColor Yellow

try {
    $session = New-PSSession -ComputerName $extIP -Port $extPort -Credential $targetCred -ErrorAction Stop

    $startResult = Invoke-Command -Session $session -ScriptBlock {
        $codePath = "C:\ProjectS\project-s-code"
        $logDir = "C:\ProjectS\reports"
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null

        $serverLog = "C:\ProjectS\reports\SERVER_PHASE_4_3B_RUNTIME_CRASH_LOG_20260518.txt"
        $stdoutLog = "C:\ProjectS\reports\SERVER_PHASE_4_3B_STDOUT_20260518.txt"

        # Kill existing server
        $existing = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
        if ($existing) {
            Stop-Process -Id $existing.OwningProcess -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 3
        }

        # Clear old logs
        if (Test-Path $serverLog) { Remove-Item $serverLog -Force }
        if (Test-Path $stdoutLog) { Remove-Item $stdoutLog -Force }

        # Start server - capture both stdout and stderr to separate files
        $process = Start-Process -FilePath "python" -ArgumentList "-u", "-m", "uvicorn", "interactive_layer.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "debug" -WorkingDirectory $codePath -PassThru -RedirectStandardOutput $stdoutLog -RedirectStandardError $serverLog

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
            Pid = $process.Id
        }
    } -ErrorAction Stop

    Write-Host "  Process running: $($startResult.IsRunning)" -ForegroundColor $(if($startResult.IsRunning){"Green"}else{"Red"})
    Write-Host "  /health: $($startResult.HealthOk)" -ForegroundColor $(if($startResult.HealthOk){"Green"}else{"Red"})
    Write-Host "  PID: $($startResult.Pid)" -ForegroundColor Gray
    Write-Host "  Log file: C:\ProjectS\reports\SERVER_PHASE_4_3B_RUNTIME_CRASH_LOG_20260518.txt" -ForegroundColor Gray

    # ============================================================
    # TASK 2: RUN SMOKE MISSION WITH DETAILED OUTPUT
    # ============================================================
    Write-Host ""
    Write-Host "[2/4] Running smoke mission..." -ForegroundColor Yellow

    $hungarianPrompt = "Irj 3 rovid mondatot arrrol, hogy miert fontos a pontos dokumentacio."

    $smokeResult = Invoke-Command -Session $session -ScriptBlock {
        $hungarianPrompt = $using:hungarianPrompt

        # Create session
        Write-Host "  Creating session..." -ForegroundColor Yellow
        try {
            $sessionBody = @{
                user_id = "phase43b_trace"
                metadata = @{ purpose = "Phase 4.3B crash traceback" }
            } | ConvertTo-Json -Compress

            $sessionResp = Invoke-RestMethod -Uri "http://localhost:8000/api/sessions" -Method Post -ContentType "application/json" -Body $sessionBody -TimeoutSec 15
            $sessionId = $sessionResp.session_id
            Write-Host ("  Session created: " + $sessionId) -ForegroundColor Green
        } catch {
            Write-Host ("  Session creation FAILED: " + $_.Exception.Message) -ForegroundColor Red
            $sessionId = ""
        }

        if ([string]::IsNullOrEmpty($sessionId)) {
            $result = New-Object PSObject
            $result | Add-Member -MemberType NoteProperty -Name "SessionId" -Value ""
            $result | Add-Member -MemberType NoteProperty -Name "MissionId" -Value ""
            $result | Add-Member -MemberType NoteProperty -Name "Error" -Value "Session creation failed"
            $result
            return
        }

        # Launch mission
        Write-Host "  Launching mission..." -ForegroundColor Yellow
        try {
            $missionBody = @{
                session_id = $sessionId
                user_id = "phase43b_trace"
                task = $hungarianPrompt
            } | ConvertTo-Json -Compress

            $missionResp = Invoke-RestMethod -Uri "http://localhost:8000/api/missions" -Method Post -ContentType "application/json" -Body $missionBody -TimeoutSec 15
            $missionId = $missionResp.mission_id
            Write-Host ("  Mission launched: " + $missionId) -ForegroundColor Green
        } catch {
            Write-Host ("  Mission launch FAILED: " + $_.Exception.Message) -ForegroundColor Red
            $missionId = ""
        }

        if ([string]::IsNullOrEmpty($missionId)) {
            $result = New-Object PSObject
            $result | Add-Member -MemberType NoteProperty -Name "SessionId" -Value $sessionId
            $result | Add-Member -MemberType NoteProperty -Name "MissionId" -Value ""
            $result | Add-Member -MemberType NoteProperty -Name "Error" -Value "Mission launch failed"
            $result
            return
        }

        # Poll status
        $maxPolls = 90
        $pollInterval = 10
        $runtimeSeconds = 0

        for ($i = 0; $i -lt $maxPolls; $i++) {
            Start-Sleep -Seconds $pollInterval
            $runtimeSeconds += $pollInterval

            try {
                $statusResp = Invoke-RestMethod -Uri ("http://localhost:8000/api/missions/" + $missionId + "/status") -TimeoutSec 10 -ErrorAction Stop
                $state = $statusResp.state
                $progress = $statusResp.progress
                Write-Host ("  [" + $runtimeSeconds + "s] State: " + $state + ", Progress: " + $progress) -ForegroundColor Gray

                if ($state -in @("COMPLETE", "FAILED", "TIMEOUT")) {
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
    Write-Host "    Error: $($smokeResult.Error)" -ForegroundColor Red
    Write-Host "    TerminalState: $($smokeResult.TerminalState)" -ForegroundColor Gray
    Write-Host "    AIWorking: $($smokeResult.AIWorking)" -ForegroundColor Gray

    # ============================================================
    # TASK 3: CAPTURE SERVER CRASH TRACEBACK
    # ============================================================
    Write-Host ""
    Write-Host "[3/4] Capturing server crash traceback..." -ForegroundColor Yellow

    $traceback = Invoke-Command -Session $session -ScriptBlock {
        $serverLog = "C:\ProjectS\reports\SERVER_PHASE_4_3B_RUNTIME_CRASH_LOG_20260518.txt"
        $stdoutLog = "C:\ProjectS\reports\SERVER_PHASE_4_3B_STDOUT_20260518.txt"

        $serverLogContent = ""
        $stdoutContent = ""

        if (Test-Path $serverLog) {
            $serverLogContent = Get-Content $serverLog -Raw
        }
        if (Test-Path $stdoutLog) {
            $stdoutContent = Get-Content $stdoutLog -Raw
        }

        # Check if server is still alive
        $pyProcs = Get-Process python -ErrorAction SilentlyContinue
        $port8000 = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue

        $healthOk = $false
        try {
            $resp = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -ErrorAction Stop
            if ($resp.StatusCode -eq 200) { $healthOk = $true }
        } catch {}

        $obj = New-Object PSObject
        $obj | Add-Member -MemberType NoteProperty -Name "ServerLog" -Value $serverLogContent
        $obj | Add-Member -MemberType NoteProperty -Name "StdoutLog" -Value $stdoutContent
        $obj | Add-Member -MemberType NoteProperty -Name "PythonProcs" -Value (if($pyProcs) { $pyProcs.Count } else { 0 })
        $obj | Add-Member -MemberType NoteProperty -Name "Port8000" -Value (if($port8000) { $true } else { $false })
        $obj | Add-Member -MemberType NoteProperty -Name "HealthAfter" -Value $healthOk
        $obj
    } -ErrorAction Stop

    Write-Host "  Server log lines: $($traceback.ServerLog.Split("`n").Count)" -ForegroundColor Gray
    Write-Host "  Python processes: $($traceback.PythonProcs)" -ForegroundColor $(if($traceback.PythonProcs -gt 0){"Green"}else{"Red"})
    Write-Host "  Port 8000: $($traceback.Port8000)" -ForegroundColor $(if($traceback.Port8000){"Green"}else{"Red"})
    Write-Host "  /health after: $($traceback.HealthAfter)" -ForegroundColor $(if($traceback.HealthAfter){"Green"}else{"Red"})

    # Save server log locally
    $traceback.ServerLog | Out-File -FilePath "C:\ProjectS-Unified\server_crash_log.txt" -Encoding UTF8
    $traceback.StdoutLog | Out-File -FilePath "C:\ProjectS-Unified\server_stdout_log.txt" -Encoding UTF8

    Write-Host ""
    Write-Host "  === SERVER STDERR LOG ===" -ForegroundColor Cyan
    Write-Host $traceback.ServerLog -ForegroundColor Red
    Write-Host ""
    Write-Host "  === SERVER STDOUT LOG ===" -ForegroundColor Cyan
    Write-Host $traceback.StdoutLog -ForegroundColor Gray

    # ============================================================
    # TASK 4: SAVE RESULTS
    # ============================================================
    Write-Host ""
    Write-Host "[4/4] Saving results..." -ForegroundColor Yellow

    $endTime = Get-Date
    $totalRuntime = ($endTime - $startTime).TotalSeconds

    $allResults = @{
        Phase = "4.3B - Crash Traceback Capture"
        Timestamp = $endTime.ToString("yyyy-MM-dd HH:mm:ss")
        TotalWallTime = [math]::Round($totalRuntime, 1)
        ServerCrashedDuringMission = ($traceback.PythonProcs -eq 0)
        ServerLogLines = $traceback.ServerLog.Split("`n").Count
        ServerLogContent = $traceback.ServerLog
        StdoutLogContent = $traceback.StdoutLog
        PythonProcsAfter = $traceback.PythonProcs
        Port8000After = $traceback.Port8000
        HealthAfter = $traceback.HealthAfter
        SmokeSessionId = $smokeResult.SessionId
        SmokeMissionId = $smokeResult.MissionId
        SmokeError = $smokeResult.Error
        SmokeTerminalState = $smokeResult.TerminalState
        SmokeAIWorking = $smokeResult.AIWorking
    }

    $allResults | ConvertTo-Json -Compress | Out-File -FilePath "C:\ProjectS-Unified\.phase43b_results.json" -Encoding UTF8

    # ============================================================
    # GENERATE REPORT
    # ============================================================
    Write-Host ""
    Write-Host "Generating report..." -ForegroundColor Yellow

    $serverCrashed = ($traceback.PythonProcs -eq 0)
    $hasTraceback = ($traceback.ServerLog -match "Traceback")
    $rootCause = "UNKNOWN"
    if ($traceback.ServerLog -match "ModuleNotFoundError") {
        $rootCause = "MISSING PYTHON MODULE"
    } elseif ($traceback.ServerLog -match "ImportError") {
        $rootCause = "MISSING PYTHON PACKAGE"
    } elseif ($traceback.ServerLog -match "SyntaxError") {
        $rootCause = "PYTHON SYNTAX ERROR"
    } elseif ($traceback.ServerLog -match "AttributeError") {
        $rootCause = "CODE BUG - ATTRIBUTE ERROR"
    } elseif ($traceback.ServerLog -match "KeyError") {
        $rootCause = "CODE BUG - KEY ERROR"
    } elseif ($traceback.ServerLog -match "TypeError") {
        $rootCause = "CODE BUG - TYPE ERROR"
    } elseif ($traceback.ServerLog -match "FileNotFoundError") {
        $rootCause = "MISSING FILE"
    } elseif ($hasTraceback) {
        $rootCause = "UNHANDLED EXCEPTION"
    }

    $reportContent = @"
# SERVER PHASE 4.3B - SMOKE MISSION CRASH ROOT CAUSE ANALYSIS

**Date:** 2026-05-18
**Target Server:** SHAYANSKA-DL380 (46.253.140.72:15985)
**Project Path:** C:\ProjectS\project-s-code

---

## A. DID THE SERVER PROCESS CRASH DURING MISSION?

**Answer: $(if($serverCrashed){'YES'}else{'NO'})**

$(if($serverCrashed){
    "The Python process count dropped to 0 after the smoke mission was launched, indicating a full process crash."
} else {
    "The Python process is still alive ($($traceback.PythonProcs) processes found)."
})

---

## B. EXACT TRACEBACK SUMMARY

### Server STDERR Log:
```
$($traceback.ServerLog)
```

### Server STDOUT Log:
```
$($traceback.StdoutLog)
```

---

## C. ROOT CAUSE CATEGORY

**Category: $rootCause**

---

## D. ANY PACKAGE INSTALLED AS SURGICAL FIX?

No packages were installed during Phase 4.3B. The fix attempt would depend on the root cause identified above.

---

## E. WHY WERE SESSION/MISSION OUTPUTS BLANK?

**Root cause:** The Write-Host commands inside the remote PowerShell session were executing, but the output was not visible in the local terminal because:

1. Invoke-RestMethod returns a PSCustomObject, not a string
2. The sessionResp.session_id property might not exist on the returned object
3. Write-Host output inside Invoke-Command -ScriptBlock may not display correctly locally
4. The actual API responses were likely successful (check server log above)

---

## F. SERVER SMOKE MISSION NOW PASSES?

**Answer: $(if($smokeResult.TerminalState -eq 'COMPLETE'){'YES'}elseif($smokeResult.TerminalState -match 'FAILED|ERROR|CRASH'){'NO - Server crashed'}else{'INCONCLUSIVE'})**

- Terminal state: $($smokeResult.TerminalState)
- Error: $($smokeResult.Error)
- AI working: $($smokeResult.AIWorking)

---

## G. NEXT RECOMMENDED STEP

$(if($traceback.ServerLog -match "No module named '(.+)'") {
    "Install missing package: pip install $($matches[1])"
} elseif($traceback.ServerLog -match "super_intelligent_ai") {
    "The crash occurs in src/core/super_intelligent_ai.py. Check imports and dependencies of this module."
} else {
    "Review the server log above and apply the appropriate fix."
})
"@

    $reportContent | Out-File -FilePath "C:\ProjectS-Unified\reports\SERVER_PHASE_4_3B_SMOKE_MISSION_CRASH_ROOT_CAUSE_20260518.md" -Encoding UTF8
    Write-Host "Report saved to: reports/SERVER_PHASE_4_3B_SMOKE_MISSION_CRASH_ROOT_CAUSE_20260518.md" -ForegroundColor Green

    Remove-PSSession $session -ErrorAction SilentlyContinue

} catch {
    Write-Host "Phase 4.3B failed: $_" -ForegroundColor Red
}