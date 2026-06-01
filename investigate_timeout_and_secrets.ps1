$extIP = "46.253.140.72"
$extPort = 15985
$securePass = ConvertTo-SecureString "Qwe123" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential("Administrator", $securePass)

$s = New-PSSession -ComputerName $extIP -Port $extPort -Credential $cred -ErrorAction Stop

Invoke-Command -Session $s -ScriptBlock {
    Write-Host "=== 1. Mission Final State in SQLite ===" -ForegroundColor Cyan
    $dbPath = "C:\ProjectS\project-s-code\interactive_layer_data\interactive.db"
    if (Test-Path $dbPath) {
        $result = python -c "
import sqlite3
conn = sqlite3.connect(r'$dbPath')
row = conn.execute('SELECT mission_id, state, state_history, progress, error, result, updated_at FROM missions WHERE mission_id = ' + chr(39) + '07ee2be9-1bf5-40a0-bae9-ff99f249c6d4' + chr(39)).fetchone()
if row:
    print('mission_id:', row[0])
    print('state:', row[1])
    print('progress:', row[3])
    print('error:', row[4])
    print('updated_at:', row[6])
    print('state_history:', row[2])
    if row[5]:
        r = row[5]
        print('result_length:', len(r))
        if len(r) > 200:
            print('result_preview:', r[:200])
        else:
            print('result:', r)
else:
    print('Mission not found in database')
" 2>&1 | Out-String
        Write-Host $result
    } else {
        Write-Host "Database not found"
    }

    Write-Host ""
    Write-Host "=== 2. All Missions in Database ===" -ForegroundColor Cyan
    $result = python -c "
import sqlite3
conn = sqlite3.connect(r'$dbPath')
rows = conn.execute('SELECT mission_id, state, progress, updated_at FROM missions ORDER BY updated_at DESC').fetchall()
for r in rows:
    print(r[0], '|', r[1], '|', r[2], '|', r[3])
" 2>&1 | Out-String
    Write-Host $result

    Write-Host ""
    Write-Host "=== 3. Configured Mission Timeout ===" -ForegroundColor Cyan
    $saiRunner = "C:\ProjectS\project-s-code\interactive_layer\sai_runner.py"
    if (Test-Path $saiRunner) {
        $content = Get-Content $saiRunner -Raw
        $match = $content | Select-String "DEFAULT_TIMEOUT|timeout.*="
        if ($match) {
            Write-Host "Found timeout config:"
            Write-Host $match.Line
        }
        # Also check for timeout constant
        $match2 = $content | Select-String "DEFAULT_TIMEOUT\s*="
        if ($match2) {
            Write-Host "DEFAULT_TIMEOUT constant: $($match2.Line)"
        }
    }

    Write-Host ""
    Write-Host "=== 4. Check for API Key in Local Logs ===" -ForegroundColor Cyan
    $localLogFiles = @(
        "C:\ProjectS-Unified\server_crash_log.txt",
        "C:\ProjectS-Unified\server_stdout_log.txt",
        "C:\ProjectS-Unified\.phase43b_results.json",
        "C:\ProjectS-Unified\.phase43_chat_results.json",
        "C:\ProjectS-Unified\.phase43_results.json"
    )
    foreach ($logFile in $localLogFiles) {
        if (Test-Path $logFile) {
            Write-Host ("Checking: " + $logFile)
            $content = Get-Content $logFile -Raw
            if ($content -match 'sk-or-v1-') {
                Write-Host "  WARNING: API key found in this file!" -ForegroundColor Red
            } else {
                Write-Host "  OK: No API key found" -ForegroundColor Green
            }
        }
    }

    Write-Host ""
    Write-Host "=== 5. Check Scripts for API Key Printing ===" -ForegroundColor Cyan
    $scriptFiles = @(
        "C:\ProjectS-Unified\phase43_deploy_key_and_retry.ps1",
        "C:\ProjectS-Unified\phase43_chat_smoke.ps1",
        "C:\ProjectS-Unified\phase43b_crash_traceback.ps1",
        "C:\ProjectS-Unified\check_env_full.ps1",
        "C:\ProjectS-Unified\check_dotenv_load.ps1"
    )
    foreach ($scriptFile in $scriptFiles) {
        if (Test-Path $scriptFile) {
            Write-Host ("Checking: " + $scriptFile)
            $content = Get-Content $scriptFile -Raw
            # Check if script prints the actual key value
            if ($content -match 'Write-Host.*\$.*Key|Write-Host.*key.*value|Write-Host.*api.*key.*=') {
                Write-Host "  WARNING: May print API key value" -ForegroundColor Yellow
            } else {
                Write-Host "  OK: No direct key printing detected" -ForegroundColor Green
            }
        }
    }
} -ErrorAction Stop

Remove-PSSession $s