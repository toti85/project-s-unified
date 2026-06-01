$extIP = "46.253.140.72"
$extPort = 15985
$targetPassword = "Qwe123"
$securePass = ConvertTo-SecureString $targetPassword -AsPlainText -Force
$targetCred = New-Object System.Management.Automation.PSCredential("Administrator", $securePass)

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  PHASE 4.2.2: FIX FK ISSUE + TEST" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check if the issue is the foreign key constraint
Write-Host "[1/3] Testing session creation with 'toti' user (default)..." -ForegroundColor Yellow
try {
    $session = New-PSSession -ComputerName $extIP -Port $extPort -Credential $targetCred -ErrorAction Stop

    $testResult = Invoke-Command -Session $session -ScriptBlock {
        $codePath = "C:\ProjectS\project-s-code"

        # Kill existing server
        $existing = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
        if ($existing) {
            Stop-Process -Id $existing.OwningProcess -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 3
        }

        # Start server with debug logging
        $logFile = "C:\ProjectS\project-s-code\server_debug2.log"
        $process = Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "interactive_layer.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "debug" -WorkingDirectory $codePath -PassThru -RedirectStandardOutput "C:\ProjectS\server_stdout2.log" -RedirectStandardError $logFile

        Start-Sleep -Seconds 10

        # Check health
        $healthOk = $false
        try {
            $resp = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -ErrorAction Stop
            if ($resp.StatusCode -eq 200) { $healthOk = $true }
        } catch {}

        $result = @{ HealthOk = $healthOk }

        if ($healthOk) {
            # Test 1: Create session with 'toti' (default user that exists)
            try {
                $body1 = @{ user_id = "toti" } | ConvertTo-Json -Compress
                $resp1 = Invoke-RestMethod -Uri "http://localhost:8000/api/sessions" -Method Post -ContentType "application/json" -Body $body1 -TimeoutSec 10
                $result.SessionToti = "OK: $($resp1.session_id)"
                $result.SessionTotiId = $resp1.session_id
            } catch {
                $result.SessionToti = "FAILED: $($_.Exception.Message)"
            }

            # Test 2: Create session with 'diag_test' (non-existent user)
            try {
                $body2 = @{ user_id = "diag_test" } | ConvertTo-Json -Compress
                $resp2 = Invoke-RestMethod -Uri "http://localhost:8000/api/sessions" -Method Post -ContentType "application/json" -Body $body2 -TimeoutSec 10
                $result.SessionDiag = "OK: $($resp2.session_id)"
                $result.SessionDiagId = $resp2.session_id
            } catch {
                $result.SessionDiag = "FAILED: $($_.Exception.Message)"
            }

            # Read server error log
            if (Test-Path $logFile) {
                $result.ServerLog = Get-Content $logFile -Raw
            }
            if (Test-Path "C:\ProjectS\server_stdout2.log") {
                $result.ServerStdout = Get-Content "C:\ProjectS\server_stdout2.log" -Raw
            }
        }

        $result
    } -ErrorAction Stop

    Write-Host "  Health: $($testResult.HealthOk)" -ForegroundColor $(if($testResult.HealthOk){"Green"}else{"Red"})
    Write-Host "  Session with 'toti': $($testResult.SessionToti)" -ForegroundColor $(if($testResult.SessionToti -match "OK"){"Green"}else{"Red"})
    Write-Host "  Session with 'diag_test': $($testResult.SessionDiag)" -ForegroundColor $(if($testResult.SessionDiag -match "OK"){"Green"}else{"Red"})

    if ($testResult.ServerLog) {
        Write-Host ""
        Write-Host "=== SERVER LOG ===" -ForegroundColor Cyan
        Write-Host $testResult.ServerLog -ForegroundColor Red
    }
    if ($testResult.ServerStdout) {
        Write-Host ""
        Write-Host "=== SERVER STDOUT ===" -ForegroundColor Cyan
        Write-Host $testResult.ServerStdout -ForegroundColor Gray
    }

    Remove-PSSession $session -ErrorAction SilentlyContinue
} catch {
    Write-Host "  Test failed: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  FIX AND TEST COMPLETE" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan