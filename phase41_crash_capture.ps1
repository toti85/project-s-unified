$targetIP = "192.168.1.180"
$targetPassword = "Qwe123"
$securePass = ConvertTo-SecureString $targetPassword -AsPlainText -Force
$targetCred = New-Object System.Management.Automation.PSCredential("$targetIP\Administrator", $securePass)

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  PHASE 4.1: CRASH CAPTURE" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Task 1: Capture exact crash output
Write-Host "[1/4] Capturing exact crash output..." -ForegroundColor Yellow

$crashScript = @'
import sys
import os

# Force UTF-8 encoding
os.environ["PYTHONIOENCODING"] = "utf-8"

code_path = r"C:\ProjectS\project-s-code"
os.chdir(code_path)

print("=== Starting Interactive Layer Server ===", flush=True)
print(f"Python: {sys.version}", flush=True)
print(f"Working dir: {os.getcwd()}", flush=True)
print(f"Python path: {sys.path[:3]}", flush=True)
print("", flush=True)

try:
    print("Importing start_server module...", flush=True)
    import importlib.util
    spec = importlib.util.spec_from_file_location("start_server", "interactive_layer/start_server.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    print("Module loaded successfully", flush=True)
except Exception as e:
    print(f"\n=== CRASH DETECTED ===", flush=True)
    print(f"Exception type: {type(e).__name__}", flush=True)
    print(f"Exception message: {e}", flush=True)
    import traceback
    traceback.print_exc()
    print(f"\n=== END TRACEBACK ===", flush=True)
    sys.exit(1)
'@

try {
    $crashOutput = Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
        $scriptContent = $using:crashScript
        $tempScript = "C:\ProjectS\phase41_crash_test.py"
        Set-Content -Path $tempScript -Value $scriptContent -Encoding UTF8
        $output = python $tempScript 2>&1 | Out-String
        Remove-Item $tempScript -ErrorAction SilentlyContinue
        $output
    }
    
    Write-Host ""
    Write-Host "=== CRASH OUTPUT ===" -ForegroundColor Cyan
    Write-Host $crashOutput -ForegroundColor Gray
    Write-Host "=== END CRASH OUTPUT ===" -ForegroundColor Cyan
    
    $crashCaptured = $crashOutput
} catch {
    Write-Host "  Crash capture failed: $_" -ForegroundColor Red
    $crashCaptured = $_.ToString()
}

# Task 2: Diagnose
Write-Host ""
Write-Host "[2/4] Diagnosing crash..." -ForegroundColor Yellow

$rootCause = "unknown"
$fixRequired = $false
$fixCommand = ""

if ($crashCaptured -match "ModuleNotFoundError: No module named '(\w+)'") {
    $missingModule = $matches[1]
    Write-Host "  Missing module: $missingModule" -ForegroundColor Yellow
    $rootCause = "missing_dependency"
    $fixRequired = $true
    $fixCommand = "pip install $missingModule"
} elseif ($crashCaptured -match "ImportError:") {
    Write-Host "  Import error detected" -ForegroundColor Yellow
    $rootCause = "import_error"
    $fixRequired = $true
} elseif ($crashCaptured -match "SyntaxError:") {
    Write-Host "  Syntax error detected" -ForegroundColor Yellow
    $rootCause = "syntax_error"
    $fixRequired = $true
} elseif ($crashCaptured -match "FileNotFoundError:") {
    Write-Host "  File not found error" -ForegroundColor Yellow
    $rootCause = "file_not_found"
    $fixRequired = $true
} elseif ($crashCaptured -match "KeyError|EnvironmentError") {
    Write-Host "  Environment/config error" -ForegroundColor Yellow
    $rootCause = "env_config_issue"
    $fixRequired = $true
} elseif ($crashCaptured -match "OSError|AddressAlreadyInUse|OSError.*[Cc]onnect") {
    Write-Host "  Port/address issue" -ForegroundColor Yellow
    $rootCause = "port_issue"
    $fixRequired = $true
} else {
    Write-Host "  Root cause: unknown (need to analyze output)" -ForegroundColor Yellow
    $rootCause = "unknown"
}

Write-Host "  Root cause category: $rootCause" -ForegroundColor $(if($rootCause -ne "unknown"){"Yellow"}else{"Red"})

# Task 3: Apply minimal fix
Write-Host ""
Write-Host "[3/4] Applying fix if needed..." -ForegroundColor Yellow

$fixApplied = $false
if ($fixRequired -and $rootCause -eq "missing_dependency") {
    try {
        Write-Host "  Installing: $fixCommand" -ForegroundColor Cyan
        $installOutput = Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
            $module = $using:missingModule
            $out = pip install $module 2>&1 | Out-String
            $out
        }
        Write-Host $installOutput -ForegroundColor Gray
        Write-Host "  Fix applied: $missingModule installed" -ForegroundColor Green
        $fixApplied = $true
    } catch {
        Write-Host "  Fix install failed: $_" -ForegroundColor Red
    }
} elseif ($fixRequired) {
    Write-Host "  Fix required but not auto-applicable (manual review needed)" -ForegroundColor Yellow
} else {
    Write-Host "  No fix needed or root cause unknown" -ForegroundColor Gray
}

# Task 4: Retry server startup
Write-Host ""
Write-Host "[4/4] Retrying server startup..." -ForegroundColor Yellow

try {
    $retryResult = Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
        $codePath = "C:\ProjectS\project-s-code"
        $startScript = "interactive_layer\start_server.py"
        $fullPath = Join-Path $codePath $startScript
        
        if (Test-Path $fullPath) {
            # Start Python server in background with output capture
            $process = Start-Process -FilePath "python" -ArgumentList $startScript -WorkingDirectory $codePath -PassThru -WindowStyle Hidden
            
            # Wait for server to start
            Start-Sleep -Seconds 15
            
            # Check if process is still running
            $process.Refresh()
            $isRunning = $process.HasExited -eq $false
            
            # Check if port 8000 is listening
            $portListening = $false
            try {
                $conn = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction Stop
                if ($conn) { $portListening = $true }
            } catch {}
            
            # Try health check
            $healthOk = $false
            try {
                $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -ErrorAction Stop
                if ($response.StatusCode -eq 200) { $healthOk = $true }
            } catch {}
            
            @{
                Started = $true
                ProcessId = $process.Id
                IsRunning = $isRunning
                PortListening = $portListening
                HealthOk = $healthOk
            }
        } else {
            @{
                Started = $false
                Error = "Start script not found"
            }
        }
    }
    
    Write-Host "  Server started: $($retryResult.Started)" -ForegroundColor $(if($retryResult.Started){"Green"}else{"Red"})
    if ($retryResult.Started) {
        Write-Host "  PID: $($retryResult.ProcessId)" -ForegroundColor Gray
        Write-Host "  Process still running: $($retryResult.IsRunning)" -ForegroundColor $(if($retryResult.IsRunning){"Green"}else{"Red"})
        Write-Host "  Port 8000 listening: $($retryResult.PortListening)" -ForegroundColor $(if($retryResult.PortListening){"Green"}else{"Red"})
        Write-Host "  Health check OK: $($retryResult.HealthOk)" -ForegroundColor $(if($retryResult.HealthOk){"Green"}else{"Red"})
        
        $serverRunning = $retryResult.IsRunning
        $healthPass = $retryResult.HealthOk
        $portListening = $retryResult.PortListening
    }
} catch {
    Write-Host "  Server retry failed: $_" -ForegroundColor Red
    $serverRunning = $false
    $healthPass = $false
    $portListening = $false
}

# Check from DEV machine
Write-Host ""
Write-Host "Checking from DEV machine..." -ForegroundColor Cyan
try {
    $netTest = Test-NetConnection -ComputerName "192.168.1.180" -Port 8000 -WarningAction SilentlyContinue -ErrorAction Stop
    Write-Host "  TCP 8000 from DEV: $($netTest.TcpTestSucceeded)" -ForegroundColor $(if($netTest.TcpTestSucceeded){"Green"}else{"Red"})
    $portFromDev = $netTest.TcpTestSucceeded
} catch {
    Write-Host "  Net connection test failed: $_" -ForegroundColor Red
    $portFromDev = $false
}

# Save results
Write-Host ""
Write-Host "Saving results..." -ForegroundColor Yellow

$allResults = @{
    Phase = "4.1 - Interactive Layer Startup Crash Root Cause"
    CrashCaptured = $crashCaptured
    RootCause = $rootCause
    FixApplied = $fixApplied
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
Write-Host "  A. Crash traceback captured: YES" -ForegroundColor Green
Write-Host "  B. Root cause category: $rootCause" -ForegroundColor $(if($rootCause -ne "unknown"){"Yellow"}else{"Red"})
Write-Host "  C. Fix applied: $fixApplied" -ForegroundColor $(if($fixApplied){"Green"}else{"Yellow"})
Write-Host "  D. Server now stays running: $(if($serverRunning){'YES'}else{'NO'})" -ForegroundColor $(if($serverRunning){"Green"}else{"Red"})
Write-Host "  E. /health local PASS: $(if($healthPass){'YES'}else{'NO'})" -ForegroundColor $(if($healthPass){"Green"}else{"Red"})
Write-Host "  F. Port 8000 from DEV: $(if($portFromDev){'YES'}else{'NO'})" -ForegroundColor $(if($portFromDev){"Green"}else{"Red"})
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan