$extIP = "46.253.140.72"
$extPort = 15985
$securePass = ConvertTo-SecureString "Qwe123" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential("Administrator", $securePass)

$sess = New-PSSession -ComputerName $extIP -Port $extPort -Credential $cred -ErrorAction Stop

Write-Host "=== Checking for results file ===" -ForegroundColor Cyan
$result = Invoke-Command -Session $sess -ScriptBlock {
    if (Test-Path 'C:\ProjectS\gap030_results.json') {
        Get-Content 'C:\ProjectS\gap030_results.json' -Raw
    } else {
        "No results file found"
    }
}
Write-Host $result

Write-Host "`n=== Checking for validation output ===" -ForegroundColor Cyan
$validation = Invoke-Command -Session $sess -ScriptBlock {
    if (Test-Path 'C:\ProjectS\validation_server.log') {
        Get-Content 'C:\ProjectS\validation_server.log' -Tail 50 -Raw
    } else {
        "No validation log found"
    }
}
Write-Host $validation

Write-Host "`n=== Checking running processes ===" -ForegroundColor Cyan
$procs = Invoke-Command -Session $sess -ScriptBlock {
    Get-Process python -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, StartTime | Format-Table -AutoSize | Out-String
}
Write-Host $procs

Write-Host "`n=== Checking last 10 missions ===" -ForegroundColor Cyan
$missions = Invoke-Command -Session $sess -ScriptBlock {
    $py = @"
import sqlite3
conn = sqlite3.connect(r'C:\ProjectS\project-s-code\interactive_layer_data\interactive.db')
rows = conn.execute('SELECT mission_id, state, progress, updated_at FROM missions ORDER BY updated_at DESC LIMIT 10').fetchall()
for r in rows:
    print(f'{r[0]} | {r[1]} | {r[2]} | {r[3]}')
conn.close()
"@
    python -c $py 2>&1 | Out-String
}
Write-Host $missions

Remove-PSSession $sess