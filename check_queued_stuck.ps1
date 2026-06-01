$extIP = "46.253.140.72"
$extPort = 15985
$securePass = ConvertTo-SecureString "Qwe123" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential("Administrator", $securePass)

$s = New-PSSession -ComputerName $extIP -Port $extPort -Credential $cred -ErrorAction Stop

Invoke-Command -Session $s -ScriptBlock {
    Write-Host "=== Checking server logs ===" -ForegroundColor Cyan
    
    # Check all log files
    $logPaths = @(
        "C:\ProjectS\reports\SERVER_PHASE_4_3B_RUNTIME_CRASH_LOG_20260518.txt",
        "C:\ProjectS\reports\SERVER_PHASE_4_3B_STDOUT_20260518.txt",
        "C:\ProjectS\project-s-code\server_phase43_v2.log",
        "C:\ProjectS\project-s-code\server_phase43.log",
        "C:\ProjectS\project-s-code\server_debug.log",
        "C:\ProjectS\project-s-code\server_debug2.log",
        "C:\ProjectS\server_debug.log",
        "C:\ProjectS\server_debug2.log",
        "C:\ProjectS\server_final.log",
        "C:\ProjectS\server_stdout.log",
        "C:\ProjectS\server_stdout2.log",
        "C:\ProjectS\server_stdout_final.log",
        "C:\ProjectS\server_stdout43.log",
        "C:\ProjectS\server_stdout43_v2.log"
    )
    
    foreach ($logPath in $logPaths) {
        if (Test-Path $logPath) {
            Write-Host ("=== " + $logPath + " ===") -ForegroundColor Yellow
            $content = Get-Content $logPath -Raw
            Write-Host $content
            Write-Host ""
        }
    }
    
    # Check if server is still alive
    Write-Host "=== Server Status ===" -ForegroundColor Cyan
    $pyProcs = Get-Process python -ErrorAction SilentlyContinue
    Write-Host "Python processes: $(if($pyProcs){$pyProcs.Count}else{0})"
    
    $port8000 = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
    Write-Host "Port 8000: $(if($port8000){'LISTENING'}else{'NOT LISTENING'})"
    
    $healthOk = $false
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -ErrorAction Stop
        if ($resp.StatusCode -eq 200) { $healthOk = $true }
    } catch {}
    Write-Host "/health: $(if($healthOk){'OK'}else{'FAIL'})"
    
    # Check the mission state in the database
    Write-Host ""
    Write-Host "=== Mission State ===" -ForegroundColor Cyan
    $dbPath = "C:\ProjectS\project-s-code\interactive_layer_data\interactive.db"
    if (Test-Path $dbPath) {
        $mission = python -c "
import sqlite3
import json
conn = sqlite3.connect(r'$dbPath')
row = conn.execute('SELECT mission_id, state, state_history, error, updated_at FROM missions WHERE mission_id = ' + chr(39) + '6bab48af-acfc-48ec-8542-8f38dc11af2c' + chr(39)).fetchone()
if row:
    print('mission_id:', row[0])
    print('state:', row[1])
    print('state_history:', row[2])
    print('error:', row[3])
    print('updated_at:', row[4])
else:
    print('Mission not found in database')
" 2>&1 | Out-String
        Write-Host $mission
    } else {
        Write-Host "Database not found at $dbPath"
    }
} -ErrorAction Stop

Remove-PSSession $s