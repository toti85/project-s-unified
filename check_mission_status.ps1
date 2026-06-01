$extIP = "46.253.140.72"
$extPort = 15985
$securePass = ConvertTo-SecureString "Qwe123" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential("Administrator", $securePass)

$s = New-PSSession -ComputerName $extIP -Port $extPort -Credential $cred -ErrorAction Stop

Invoke-Command -Session $s -ScriptBlock {
    Write-Host "=== Server Status ===" -ForegroundColor Cyan
    $pyProcs = Get-Process python -ErrorAction SilentlyContinue
    Write-Host ("Python processes: " + $pyProcs.Count)
    
    $port8000 = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
    Write-Host ("Port 8000: " + (if($port8000){'LISTENING'}else{'NOT LISTENING'}))
    
    $healthOk = $false
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -ErrorAction Stop
        if ($resp.StatusCode -eq 200) { $healthOk = $true }
    } catch {}
    Write-Host ("/health: " + (if($healthOk){'OK'}else{'FAIL'}))
    
    Write-Host ""
    Write-Host "=== Mission Status ===" -ForegroundColor Cyan
    $status = python -c "
import sqlite3
conn = sqlite3.connect(r'C:\ProjectS\project-s-code\interactive_layer_data\interactive.db')
row = conn.execute('SELECT mission_id, state, state_history, progress, error, result FROM missions WHERE mission_id = ' + chr(39) + '07ee2be9-1bf5-40a0-bae9-ff99f249c6d4' + chr(39)).fetchone()
if row:
    print('mission_id:', row[0])
    print('state:', row[1])
    print('progress:', row[3])
    print('error:', row[4])
    print('state_history:', row[2])
    if row[5]:
        result = row[5]
        if len(result) > 500:
            print('result:', result[:500] + '...')
        else:
            print('result:', result)
else:
    print('Mission not found')
" 2>&1 | Out-String
    Write-Host $status
} -ErrorAction Stop

Remove-PSSession $s