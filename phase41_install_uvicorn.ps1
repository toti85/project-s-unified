$targetIP = "192.168.1.180"
$targetPassword = "Qwe123"
$securePass = ConvertTo-SecureString $targetPassword -AsPlainText -Force
$targetCred = New-Object System.Management.Automation.PSCredential("$targetIP\Administrator", $securePass)

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  PHASE 4.1: INSTALL UVICORN" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Install uvicorn
Write-Host "[1/3] Installing uvicorn..." -ForegroundColor Yellow
try {
    $installOutput = Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
        $out = pip install uvicorn 2>&1 | Out-String
        $out
    }
    Write-Host $installOutput -ForegroundColor Gray
    Write-Host "  uvicorn installed" -ForegroundColor Green
} catch {
    Write-Host "  Install failed: $_" -ForegroundColor Red
}

# Verify
Write-Host ""
Write-Host "[2/3] Verifying uvicorn..." -ForegroundColor Yellow
try {
    $verifyOutput = Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
        $out = python -c "import uvicorn; print(f'uvicorn {uvicorn.__version__} OK')" 2>&1 | Out-String
        $out
    }
    Write-Host $verifyOutput -ForegroundColor Green
} catch {
    Write-Host "  Verify failed: $_" -ForegroundColor Red
}

# Start server
Write-Host ""
Write-Host "[3/3] Starting server..." -ForegroundColor Yellow
try {
    $startResult = Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
        $codePath = "C:\ProjectS\project-s-code"
        
        # Start server using python -m uvicorn
        $process = Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "interactive_layer.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info" -WorkingDirectory $codePath -PassThru -WindowStyle Hidden
        
        # Wait for server to start
        Start-Sleep -Seconds 20
        
        # Check status
        $process.Refresh()
        $isRunning = $process.HasExited -eq $false
        
        $portListening = $false
        try {
            $conn = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction Stop
            if ($conn) { $portListening = $true }
        } catch {}
        
        $healthOk = $false
        $healthContent = ""
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                $healthOk = $true
                $healthContent = $response.Content
            }
        } catch {}
        
        @{
            IsRunning = $isRunning
            PortListening = $portListening
            HealthOk = $healthOk
            HealthContent = $healthContent
        }
    }
    
    Write-Host "  Process running: $($startResult.IsRunning)" -ForegroundColor $(if($startResult.IsRunning){"Green"}else{"Red"})
    Write-Host "  Port 8000 listening: $($startResult.PortListening)" -ForegroundColor $(if($startResult.PortListening){"Green"}else{"Red"})
    Write-Host "  Health OK: $($startResult.HealthOk)" -ForegroundColor $(if($startResult.HealthOk){"Green"}else{"Red"})
    if ($startResult.HealthContent) {
        Write-Host "  Health response: $($startResult.HealthContent)" -ForegroundColor Gray
    }
    
    $serverRunning = $startResult.IsRunning
    $healthPass = $startResult.HealthOk
    $portListening = $startResult.PortListening
} catch {
    Write-Host "  Server start failed: $_" -ForegroundColor Red
    $serverRunning = $false
    $healthPass = $false
    $portListening = $false
}

# Check from DEV
Write-Host ""
Write-Host "Checking from DEV machine..." -ForegroundColor Cyan
try {
    $netTest = Test-NetConnection -ComputerName "192.168.1.180" -Port 8000 -WarningAction SilentlyContinue -ErrorAction Stop
    Write-Host "  TCP 8000 from DEV: $($netTest.TcpTestSucceeded)" -ForegroundColor $(if($netTest.TcpTestSucceeded){"Green"}else{"Red"})
    $portFromDev = $netTest.TcpTestSucceeded
} catch {
    Write-Host "  Net test failed: $_" -ForegroundColor Red
    $portFromDev = $false
}

# Save results
Write-Host ""
Write-Host "Saving results..." -ForegroundColor Yellow

$allResults = @{
    Phase = "4.1 - Install uvicorn + Server Start"
    RootCause = "missing_dependency"
    MissingPackage = "uvicorn"
    ServerRunning = $serverRunning
    HealthPass = $healthPass
    PortListening = $portListening
    PortFromDev = $portFromDev
    Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
}

$allResults | ConvertTo-Json | Out-File -FilePath "C:\ProjectS-Unified\.phase41_results.json" -Encoding UTF8

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  PHASE 4.1 SUMMARY" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  A. Root cause: uvicorn not installed" -ForegroundColor Yellow
Write-Host "  B. Fix applied: pip install uvicorn" -ForegroundColor Green
Write-Host "  C. Server running: $(if($serverRunning){'YES'}else{'NO'})" -ForegroundColor $(if($serverRunning){"Green"}else{"Red"})
Write-Host "  D. /health PASS: $(if($healthPass){'YES'}else{'NO'})" -ForegroundColor $(if($healthPass){"Green"}else{"Red"})
Write-Host "  E. Port 8000 from DEV: $(if($portFromDev){'YES'}else{'NO'})" -ForegroundColor $(if($portFromDev){"Green"}else{"Red"})
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan