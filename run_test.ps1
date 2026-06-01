$extIP = "46.253.140.72"
$extPort = 15985
$securePass = ConvertTo-SecureString "Qwe123" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential("Administrator", $securePass)

$sess = New-PSSession -ComputerName $extIP -Port $extPort -Credential $cred -ErrorAction Stop

Write-Host "=== Step 1: Kill existing processes ===" -ForegroundColor Cyan
Invoke-Command -Session $sess -ScriptBlock {
    taskkill /F /IM python.exe /T 2>&1 | Out-String
    Start-Sleep -Seconds 3
}

Write-Host "=== Step 2: Start server in background ===" -ForegroundColor Cyan
$serverProc = Invoke-Command -Session $sess -ScriptBlock {
    $envVars = [System.Environment]::GetEnvironmentVariables()
    $envVars["PYTHONUNBUFFERED"] = "1"
    
    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = "python"
    $startInfo.Arguments = "-u C:\ProjectS\project-s-code\interactive_layer\start_server.py"
    $startInfo.WorkingDirectory = "C:\ProjectS\project-s-code"
    $startInfo.UseShellExecute = $false
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $startInfo.CreateNoWindow = $true
    
    $proc = [System.Diagnostics.Process]::Start($startInfo)
    $proc.Id
}
Write-Host "  Server PID: $serverProc"

Write-Host "=== Step 3: Wait for server ===" -ForegroundColor Cyan
$ready = $false
for ($i = 0; $i -lt 15; $i++) {
    Start-Sleep -Seconds 2
    try {
        $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
        if ($resp.StatusCode -eq 200) {
            Write-Host "  Server ready after $($i * 2)s" -ForegroundColor Green
            $ready = $true
            break
        }
    } catch {
        Write-Host "  Waiting... attempt $($i+1)" -ForegroundColor Yellow
    }
}

if ($ready) {
    Write-Host "=== Step 4: Run validation ===" -ForegroundColor Cyan
    $valOutput = Invoke-Command -Session $sess -ScriptBlock {
        $env:PYTHONPATH = "C:\ProjectS\project-s-code"
        $result = python C:\ProjectS\full_gap030_validation.py 2>&1
        $result -join "`n"
    }
    Write-Host $valOutput
} else {
    Write-Host "Server failed to start!" -ForegroundColor Red
}

Write-Host "=== Step 5: Check results ===" -ForegroundColor Cyan
$check = Invoke-Command -Session $sess -ScriptBlock {
    if (Test-Path 'C:\ProjectS\gap030_results.json') {
        Get-Content 'C:\ProjectS\gap030_results.json' -Raw
    } else {
        "No results file"
    }
}
Write-Host $check

Remove-PSSession $sess