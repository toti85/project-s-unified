$extIP = "46.253.140.72"
$extPort = 15985
$securePass = ConvertTo-SecureString "Qwe123" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential("Administrator", $securePass)

$s = New-PSSession -ComputerName $extIP -Port $extPort -Credential $cred -ErrorAction Stop

Write-Host "=== Running GAP_030 validation ===" -ForegroundColor Cyan

$validationOutput = Invoke-Command -Session $s -ScriptBlock {
    cd C:\ProjectS\project-s-code
    python validate_gap030_server.py 2>&1 | Out-String
}

Write-Host "`n=== VALIDATION OUTPUT ===" -ForegroundColor Cyan
Write-Host $validationOutput

# Check final state
Write-Host "`n=== Final states ===" -ForegroundColor Cyan
$finalState = Invoke-Command -Session $s -ScriptBlock {
    $script = @'
import sqlite3
conn = sqlite3.connect(r"C:\ProjectS\project-s-code\interactive_layer_data\interactive.db")
rows = conn.execute("SELECT mission_id, state, progress, error FROM missions ORDER BY updated_at DESC LIMIT 3").fetchall()
for r in rows:
    err = (r[3] or "")[:60]
    print(f"{r[0]} | {r[1]} | {r[2]} | {err}")
conn.close()
'@
    python -c $script 2>&1 | Out-String
}
Write-Host $finalState

# Health check
Write-Host "`n=== Health check ===" -ForegroundColor Cyan
try {
    $resp = Invoke-WebRequest -Uri "http://46.253.140.72:8000/health" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "PASS" -ForegroundColor Green
} catch {
    Write-Host "FAIL" -ForegroundColor Red
}

Remove-PSSession $s