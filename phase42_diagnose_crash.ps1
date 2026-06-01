$extIP = "46.253.140.72"
$extPort = 15985
$targetPassword = "Qwe123"
$securePass = ConvertTo-SecureString $targetPassword -AsPlainText -Force
$targetCred = New-Object System.Management.Automation.PSCredential("Administrator", $securePass)

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  PHASE 4.2.1: DIAGNOSE SERVER CRASH" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check if server is currently running
Write-Host "[1/4] Checking server state..." -ForegroundColor Yellow
try {
    $session = New-PSSession -ComputerName $extIP -Port $extPort -Credential $targetCred -ErrorAction Stop

    $state = Invoke-Command -Session $session -ScriptBlock {
        $pyProcs = Get-Process python -ErrorAction SilentlyContinue
        $port8000 = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue

        @{
            PythonProcs = if($pyProcs) { $pyProcs.Count } else { 0 }
            Port8000 = if($port8000) { $true } else { $false }
        }
    } -ErrorAction Stop

    Write-Host "  Python processes: $($state.PythonProcs)" -ForegroundColor $(if($state.PythonProcs -gt 0){"Green"}else{"Yellow"})
    Write-Host "  Port 8000 listening: $($state.Port8000)" -ForegroundColor $(if($state.Port8000){"Green"}else{"Yellow"})

    Remove-PSSession $session -ErrorAction SilentlyContinue
} catch {
    Write-Host "  WinRM check failed: $_" -ForegroundColor Red
}

# Step 2: Check server logs
Write-Host ""
Write-Host "[2/4] Checking server logs..." -ForegroundColor Yellow
try {
    $session = New-PSSession -ComputerName $extIP -Port $extPort -Credential $targetCred -ErrorAction Stop

    $logs = Invoke-Command -Session $session -ScriptBlock {
        $logPath = "C:\ProjectS\project-s-code\logs"
        if (Test-Path $logPath) {
            $logFiles = Get-ChildItem $logPath -Filter "*.log" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 3
            foreach ($log in $logFiles) {
                Write-Host ("=== " + $log.Name + " ===")
                Get-Content $log.FullName -Tail 50
                Write-Host ""
            }
        } else {
            Write-Host "No logs directory found"
        }

        # Also check for any .log files in the project root
        $rootLogs = Get-ChildItem "C:\ProjectS\project-s-code" -Filter "*.log" -ErrorAction SilentlyContinue
        foreach ($log in $rootLogs) {
            Write-Host ("=== ROOT: " + $log.Name + " ===")
            Get-Content $log.FullName -Tail 30
            Write-Host ""
        }
    } -ErrorAction Stop

    Remove-PSSession $session -ErrorAction SilentlyContinue
} catch {
    Write-Host "  Log check failed: $_" -ForegroundColor Red
}

# Step 3: Check sai_runner.py for missing dependencies
Write-Host ""
Write-Host "[3/4] Checking sai_runner.py for imports..." -ForegroundColor Yellow
try {
    $session = New-PSSession -ComputerName $extIP -Port $extPort -Credential $targetCred -ErrorAction Stop

    $imports = Invoke-Command -Session $session -ScriptBlock {
        $saiPath = "C:\ProjectS\project-s-code\interactive_layer\sai_runner.py"
        if (Test-Path $saiPath) {
            $content = Get-Content $saiPath -Raw
            $importLines = $content | Select-String -Pattern "^(import |from )" | ForEach-Object { $_.Line.Trim() }
            Write-Host "Import statements in sai_runner.py:"
            foreach ($line in $importLines) {
                Write-Host "  $line"
            }
        } else {
            Write-Host "sai_runner.py not found"
        }

        # Check for missing optional imports
        Write-Host ""
        Write-Host "Checking Python package availability..."
        $packages = @("openai", "anthropic", "aiohttp", "requests", "browser_use", "selenium", "playwright")
        foreach ($pkg in $packages) {
            try {
                $cmd = 'python -c "import ' + $pkg + '; print(' + "'" + 'OK' + "'" + ')"'
                $result = Invoke-Expression $cmd 2>&1 | Out-String
                Write-Host ("  " + $pkg + ": " + $result.Trim()) -ForegroundColor Green
            } catch {
                Write-Host ("  " + $pkg + ": NOT FOUND") -ForegroundColor Red
            }
        }
    } -ErrorAction Stop

    Remove-PSSession $session -ErrorAction SilentlyContinue
} catch {
    Write-Host "  Import check failed: $_" -ForegroundColor Red
}

# Step 4: Start server and run a simple mission to capture error
Write-Host ""
Write-Host "[4/4] Running diagnostic mission with full error capture..." -ForegroundColor Yellow
try {
    $session = New-PSSession -ComputerName $extIP -Port $extPort -Credential $targetCred -ErrorAction Stop

    $diagResult = Invoke-Command -Session $session -ScriptBlock {
        $codePath = "C:\ProjectS\project-s-code"

        # Kill any existing server
        $existing = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
        if ($existing) {
            Stop-Process -Id $existing.OwningProcess -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 3
        }

        # Start server with output redirected
        $logFile = "C:\ProjectS\project-s-code\server_debug.log"
        $process = Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "interactive_layer.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "debug" -WorkingDirectory $codePath -PassThru -RedirectStandardOutput "C:\ProjectS\server_stdout.log" -RedirectStandardError $logFile

        Start-Sleep -Seconds 10

        # Check if server is running
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

        $result = @{
            IsRunning = $isRunning
            PortListening = $portListening
            HealthOk = $healthOk
        }

        # If server is up, try a simple mission
        if ($healthOk) {
            try {
                # Create session
                $sessionBody = @{ user_id = "diag_test" } | ConvertTo-Json -Compress
                $sessionResp = Invoke-RestMethod -Uri "http://localhost:8000/api/sessions" -Method Post -ContentType "application/json" -Body $sessionBody -TimeoutSec 10
                $sessionId = $sessionResp.session_id

                # Launch a very simple mission (no AI, just test infrastructure)
                $missionBody = @{
                    session_id = $sessionId
                    user_id = "diag_test"
                    task = "Hello world test"
                } | ConvertTo-Json -Compress

                $missionResp = Invoke-RestMethod -Uri "http://localhost:8000/api/missions" -Method Post -ContentType "application/json" -Body $missionBody -TimeoutSec 10
                $missionId = $missionResp.mission_id
                $result.MissionId = $missionId

                # Wait a bit then check status
                Start-Sleep -Seconds 5

                $statusResp = Invoke-RestMethod -Uri "http://localhost:8000/api/missions/$missionId/status" -TimeoutSec 10 -ErrorAction Stop
                $result.MissionState = $statusResp.state
                $result.MissionError = if($statusResp.error) { $statusResp.error } else { "" }

                # Read server output for errors
                Start-Sleep -Seconds 5
                if (Test-Path $logFile) {
                    $result.ServerError = Get-Content $logFile -Raw
                }
                if (Test-Path "C:\ProjectS\server_stdout.log") {
                    $result.ServerStdout = Get-Content "C:\ProjectS\server_stdout.log" -Raw
                }
            } catch {
                $result.MissionError = $_.Exception.Message
                # Still read server output
                if (Test-Path $logFile) {
                    $result.ServerError = Get-Content $logFile -Raw
                }
                if (Test-Path "C:\ProjectS\server_stdout.log") {
                    $result.ServerStdout = Get-Content "C:\ProjectS\server_stdout.log" -Raw
                }
            }
        }

        $result
    } -ErrorAction Stop

    Write-Host "  Server running: $($diagResult.IsRunning)" -ForegroundColor $(if($diagResult.IsRunning){"Green"}else{"Red"})
    Write-Host "  Port 8000: $($diagResult.PortListening)" -ForegroundColor $(if($diagResult.PortListening){"Green"}else{"Red"})
    Write-Host "  Health: $($diagResult.HealthOk)" -ForegroundColor $(if($diagResult.HealthOk){"Green"}else{"Red"})
    Write-Host "  Mission ID: $($diagResult.MissionId)" -ForegroundColor Gray
    Write-Host "  Mission state: $($diagResult.MissionState)" -ForegroundColor Gray
    Write-Host "  Mission error: $($diagResult.MissionError)" -ForegroundColor Red

    if ($diagResult.ServerError) {
        Write-Host ""
        Write-Host "=== SERVER STDERR ===" -ForegroundColor Cyan
        Write-Host $diagResult.ServerError -ForegroundColor Red
    }
    if ($diagResult.ServerStdout) {
        Write-Host ""
        Write-Host "=== SERVER STDOUT ===" -ForegroundColor Cyan
        Write-Host $diagResult.ServerStdout -ForegroundColor Gray
    }

    Remove-PSSession $session -ErrorAction SilentlyContinue
} catch {
    Write-Host "  Diagnostic mission failed: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  DIAGNOSTIC COMPLETE" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan