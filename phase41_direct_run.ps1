$targetIP = "192.168.1.180"
$targetPassword = "Qwe123"
$securePass = ConvertTo-SecureString $targetPassword -AsPlainText -Force
$targetCred = New-Object System.Management.Automation.PSCredential("$targetIP\Administrator", $securePass)

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  PHASE 4.1: DIRECT SERVER RUN" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Run server directly and capture ALL output
Write-Host "[1/3] Running server directly on server..." -ForegroundColor Yellow

$runScript = @'
import sys
import os

os.environ["PYTHONIOENCODING"] = "utf-8"
os.chdir(r"C:\ProjectS\project-s-code")

print("=== Direct Server Run ===", flush=True)
print(f"Python: {sys.version}", flush=True)
print(f"CWD: {os.getcwd()}", flush=True)

# Try importing the module that start_server uses
try:
    print("Importing uvicorn...", flush=True)
    import uvicorn
    print(f"uvicorn version: {uvicorn.__version__}", flush=True)
except Exception as e:
    print(f"uvicorn import FAILED: {e}", flush=True)
    sys.exit(1)

try:
    print("Importing interactive_layer.main...", flush=True)
    from interactive_layer.main import app
    print("app imported successfully", flush=True)
except Exception as e:
    print(f"app import FAILED: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("Starting uvicorn on 0.0.0.0:8000...", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
except Exception as e:
    print(f"uvicorn.run FAILED: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)
'@

try {
    $runOutput = Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
        $scriptContent = $using:runScript
        $tempScript = "C:\ProjectS\phase41_direct_run.py"
        Set-Content -Path $tempScript -Value $scriptContent -Encoding UTF8
        
        # Run with python and capture ALL output including stderr
        $process = Start-Process -FilePath "python" -ArgumentList $tempScript -PassThru -RedirectStandardOutput "C:\ProjectS\phase41_stdout.txt" -RedirectStandardError "C:\ProjectS\phase41_stderr.txt"
        
        # Wait for process to exit or run for 30 seconds
        $exited = $process.WaitForExit(30000)
        
        $result = @{
            Exited = $exited
            PID = $process.Id
            ExitCode = if($exited) { $process.ExitCode } else { "still running" }
        }
        
        # Read output files
        if (Test-Path "C:\ProjectS\phase41_stdout.txt") {
            $result.Stdout = Get-Content "C:\ProjectS\phase41_stdout.txt" -Raw
        }
        if (Test-Path "C:\ProjectS\phase41_stderr.txt") {
            $result.Stderr = Get-Content "C:\ProjectS\phase41_stderr.txt" -Raw
        }
        
        # Clean up temp files
        Remove-Item "C:\ProjectS\phase41_stdout.txt" -ErrorAction SilentlyContinue
        Remove-Item "C:\ProjectS\phase41_stderr.txt" -ErrorAction SilentlyContinue
        Remove-Item $tempScript -ErrorAction SilentlyContinue
        
        $result
    }
    
    Write-Host ""
    Write-Host "=== STDOUT ===" -ForegroundColor Cyan
    Write-Host $runOutput.Stdout -ForegroundColor Gray
    Write-Host ""
    Write-Host "=== STDERR ===" -ForegroundColor Cyan
    Write-Host $runOutput.Stderr -ForegroundColor Red
    Write-Host ""
    Write-Host "Process exited: $($runOutput.Exited)" -ForegroundColor $(if($runOutput.Exited){"Yellow"}else{"Green"})
    Write-Host "Exit code: $($runOutput.ExitCode)" -ForegroundColor Gray
    
    $crashOutput = $runOutput.Stderr
    if (-not $crashOutput) { $crashOutput = $runOutput.Stdout }
} catch {
    Write-Host "  Direct run failed: $_" -ForegroundColor Red
    $crashOutput = $_.ToString()
}

# Task 2: Diagnose
Write-Host ""
Write-Host "[2/3] Diagnosing..." -ForegroundColor Yellow

$rootCause = "unknown"
if ($crashOutput -match "ModuleNotFoundError: No module named '(\w+)'") {
    $missingModule = $matches[1]
    Write-Host "  Missing module: $missingModule" -ForegroundColor Yellow
    $rootCause = "missing_dependency"
} elseif ($crashOutput -match "ImportError:") {
    Write-Host "  Import error" -ForegroundColor Yellow
    $rootCause = "import_error"
} elseif ($crashOutput -match "SyntaxError:") {
    Write-Host "  Syntax error" -ForegroundColor Yellow
    $rootCause = "syntax_error"
} elseif ($crashOutput -match "OSError.*[Ww]indow|OSError.*[Cc]onnect|Address.*[Aa]lready") {
    Write-Host "  Port/address issue" -ForegroundColor Yellow
    $rootCause = "port_issue"
} else {
    Write-Host "  Output captured but no clear error pattern" -ForegroundColor Yellow
    Write-Host "  Last 200 chars of output:" -ForegroundColor Gray
    Write-Host ($crashOutput.Substring([Math]::Max(0, $crashOutput.Length - 200))) -ForegroundColor Gray
}

Write-Host "  Root cause: $rootCause" -ForegroundColor $(if($rootCause -ne "unknown"){"Yellow"}else{"Red"})

# Task 3: Start server properly and test
Write-Host ""
Write-Host "[3/3] Starting server properly..." -ForegroundColor Yellow

try {
    $startResult = Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
        $codePath = "C:\ProjectS\project-s-code"
        
        # Kill any existing python processes on port 8000
        $existing = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
        if ($existing) {
            Write-Host "  Killing existing process on port 8000" -ForegroundColor Yellow
            Stop-Process -Id $existing.OwningProcess -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
        }
        
        # Start server using python -m uvicorn (more reliable)
        $process = Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "interactive_layer.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info" -WorkingDirectory $codePath -PassThru -WindowStyle Normal
        
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
    Phase = "4.1 - Direct Server Run"
    CrashOutput = $crashOutput
    RootCause = $rootCause
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
Write-Host "  A. Crash output captured: YES" -ForegroundColor Green
Write-Host "  B. Root cause: $rootCause" -ForegroundColor $(if($rootCause -ne "unknown"){"Yellow"}else{"Red"})
Write-Host "  C. Server running: $(if($serverRunning){'YES'}else{'NO'})" -ForegroundColor $(if($serverRunning){"Green"}else{"Red"})
Write-Host "  D. /health PASS: $(if($healthPass){'YES'}else{'NO'})" -ForegroundColor $(if($healthPass){"Green"}else{"Red"})
Write-Host "  E. Port 8000 from DEV: $(if($portFromDev){'YES'}else{'NO'})" -ForegroundColor $(if($portFromDev){"Green"}else{"Red"})
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan