$extIP = "46.253.140.72"
$extPort = 15985
$securePass = ConvertTo-SecureString "Qwe123" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential("Administrator", $securePass)

$sess = New-PSSession -ComputerName $extIP -Port $extPort -Credential $cred -ErrorAction Stop

Write-Host "=== Checking DB schema ===" -ForegroundColor Cyan
$schema = Invoke-Command -Session $sess -ScriptBlock {
    $py = @"
import sqlite3
conn = sqlite3.connect(r'C:\ProjectS\project-s-code\interactive_layer_data\interactive.db')
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
for t in tables:
    print(f"Table: {t[0]}")
    cols = conn.execute(f"PRAGMA table_info({t[0]})").fetchall()
    for c in cols:
        print(f"  {c[1]} ({c[2]}) pk={c[5]} notnull={c[3]}")
    fk = conn.execute(f"PRAGMA foreign_key_list({t[0]})").fetchall()
    for f in fk:
        print(f"  FK: {f[2]} -> {f[3]}.{f[4]}")
    print()
conn.close()
"@
    python -c $py 2>&1 | Out-String
}
Write-Host $schema

Write-Host "=== Testing API endpoints ===" -ForegroundColor Cyan
Write-Host "GET /api/chat (list missions):" -ForegroundColor Yellow
try {
    $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/chat" -UseBasicParsing
    Write-Host $resp.Content -ForegroundColor Green
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
}

Write-Host "`nGET /api/sessions (list sessions):" -ForegroundColor Yellow
try {
    $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/sessions" -UseBasicParsing
    Write-Host $resp.Content -ForegroundColor Green
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
}

Write-Host "`nPOST /api/sessions with empty body:" -ForegroundColor Yellow
try {
    $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/sessions" -Method POST -ContentType "application/json" -Body '{}' -UseBasicParsing
    Write-Host $resp.Content -ForegroundColor Green
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
}

Remove-PSSession $sess