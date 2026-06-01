$extIP = "46.253.140.72"
$extPort = 15985
$securePass = ConvertTo-SecureString "Qwe123" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential("Administrator", $securePass)

$s = New-PSSession -ComputerName $extIP -Port $extPort -Credential $cred -ErrorAction Stop

Invoke-Command -Session $s -ScriptBlock {
    Write-Host "=== Server Status ===" -ForegroundColor Cyan
    $pyProcs = Get-Process python -ErrorAction SilentlyContinue
    Write-Host ("Python processes: " + (if($pyProcs){$pyProcs.Count}else{0}))
    
    $port8000 = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
    Write-Host ("Port 8000: " + (if($port8000){'LISTENING'}else{'NOT LISTENING'}))
    
    $healthOk = $false
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -ErrorAction Stop
        if ($resp.StatusCode -eq 200) { $healthOk = $true }
    } catch {}
    Write-Host ("/health: " + (if($healthOk){'OK'}else{'FAIL'}))
    
    Write-Host ""
    Write-Host "=== Server Crash Log ===" -ForegroundColor Cyan
    $logFile = "C:\ProjectS\reports\SERVER_PHASE_4_3B_RUNTIME_CRASH_LOG_20260518.txt"
    if (Test-Path $logFile) {
        $content = Get-Content $logFile -Raw
        Write-Host $content
    } else {
        Write-Host "Log file not found"
    }
    
    Write-Host ""
    Write-Host "=== Server Stdout Log ===" -ForegroundColor Cyan
    $stdoutFile = "C:\ProjectS\reports\SERVER_PHASE_4_3B_STDOUT_20260518.txt"
    if (Test-Path $stdoutFile) {
        $content = Get-Content $stdoutFile -Raw
        Write-Host $content
    } else {
        Write-Host "Stdout file not found"
    }
    
    # Check latest server log
    Write-Host ""
    Write-Host "=== Latest Server Log ===" -ForegroundColor Cyan
    $latestLog = Get-ChildItem "C:\ProjectS" -Filter "*.log" -Recurse -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($latestLog) {
        Write-Host ("File: " + $latestLog.FullName)
        $content = Get-Content $latestLog.FullName -Tail 50 -ErrorAction SilentlyContinue
        Write-Host $content
    }
} -ErrorAction Stop

Remove-PSSession $s