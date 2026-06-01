$ErrorActionPreference = "Continue"
$baseURL = "http://127.0.0.1:8000"
$dbPath = "C:\ProjectS-Unified\interactive_layer_data\interactive.db"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  GAP_030 DEV LIVE GLOBAL TIMEOUT VALIDATION" -ForegroundColor Cyan
Write-Host "  Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# ─── Step 0: Patch DEFAULT_TIMEOUT to 30s and restart server ───
Write-Host "`n[0/7] Patching DEFAULT_TIMEOUT to 30s and restarting server..." -ForegroundColor Yellow

# Patch sai_runner.py
$saiRunnerPath = "C:\ProjectS-Unified\interactive_layer\sai_runner.py"
$content = Get-Content $saiRunnerPath -Raw
$content = $content -replace 'DEFAULT_TIMEOUT = 600', 'DEFAULT_TIMEOUT = 30'
Set-Content $saiRunnerPath $content -NoNewline
Write-Host "  Patched DEFAULT_TIMEOUT to 30 in sai_runner.py" -ForegroundColor Green

# Kill existing server
$procs = Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -eq "" -and (Get-Process -Id $_.Id -ErrorAction SilentlyContinue) }
Write-Host "  Killing existing Python processes..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 3

# Start server
Write-Host "  Starting server with patched code..." -ForegroundColor Yellow
$proc = Start-Process python -ArgumentList "interactive_layer/start_server.py" -PassThru -WindowStyle Hidden
Write-Host "  Server started (PID: $($proc.Id))" -ForegroundColor Green

# Wait for server
Write-Host "  Waiting for server..." -ForegroundColor Yellow
$ready = $false
for ($i = 0; $i -lt 15; $i++) {
    Start-Sleep -Seconds 2
    try {
        $resp = Invoke-WebRequest -Uri "$baseURL/health" -TimeoutSec 3 -UseBasicParsing
        if ($resp.StatusCode -eq 200) {
            Write-Host "  Server ready after $($i * 2)s" -ForegroundColor Green
            $ready = $true
            break
        }
    } catch {}
}

if (-not $ready) {
    Write-Host "  Server failed to start!" -ForegroundColor Red
    exit 1
}

# ─── Step 1: Health check before test ──────────────────────────
Write-Host "`n[1/7] Health check BEFORE test..." -ForegroundColor Yellow
try {
    $resp = Invoke-WebRequest -Uri "$baseURL/health" -TimeoutSec 5 -UseBasicParsing
    $healthBefore = $resp.StatusCode -eq 200
    Write-Host "  Health: PASS ($($resp.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "  Health: FAIL — $_" -ForegroundColor Red
    $healthBefore = $false
}

# ─── Step 2: Create test mission ───────────────────────────────
Write-Host "`n[2/7] Creating test mission (timeout=30s)..." -ForegroundColor Yellow

# Get or create a session
try {
    $sessions = Invoke-RestMethod -Uri "$baseURL/api/sessions" -UseBasicParsing
    $session = $sessions | Where-Object { $_.user_id -eq "toti" } | Select-Object -First 1
    if (-not $session) {
        $createBody = @{user_id="toti"; metadata=@{name="GAP_030_live_test"}} | ConvertTo-Json -Compress
        $resp = Invoke-WebRequest -Uri "$baseURL/api/sessions" -Method POST -ContentType "application/json" -Body $createBody -TimeoutSec 10 -UseBasicParsing
        $session = ($resp.Content | ConvertFrom-Json)
    }
    $sessionId = $session.session_id
    Write-Host "  Session: $sessionId" -ForegroundColor Green
} catch {
    Write-Host "  Session creation FAIL: $_" -ForegroundColor Red
    $sessionId = $null
}

if ($sessionId) {
    # Use a prompt that will trigger long AI execution
    $body = @{
        session_id = $sessionId
        message    = "Write a very detailed and comprehensive analysis of the history of mathematics from ancient times to the modern era. Include at least 20 paragraphs covering every major discovery, mathematician, and concept. Each paragraph should be detailed and thorough, including specific dates, names, and mathematical concepts. Be extremely verbose and detailed in your response."
        user_id    = "toti"
    } | ConvertTo-Json -Compress

    try {
        $resp = Invoke-WebRequest -Uri "$baseURL/api/chat" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 15 -UseBasicParsing
        $result = ($resp.Content | ConvertFrom-Json)
        $missionId = $result.mission_id
        Write-Host "  Mission: $missionId" -ForegroundColor Green
    } catch {
        Write-Host "  Mission creation FAIL: $_" -ForegroundColor Red
        $missionId = $null
    }

    # ─── Step 3: Poll mission status ─────────────────────────────
    if ($missionId) {
        Write-Host "`n[3/7] Polling mission status (max 90s, timeout=30s)..." -ForegroundColor Yellow
        $pollStart = Get-Date
        $finalState = "UNKNOWN"
        $count = 0
        $stateHistory = @()

        while ((Get-Date).Subtract($pollStart).TotalSeconds -lt 90) {
            Start-Sleep -Seconds 3
            $count++
            try {
                $resp = Invoke-WebRequest -Uri "$baseURL/api/chat/mission/$missionId/status" -TimeoutSec 5 -UseBasicParsing
                $status = ($resp.Content | ConvertFrom-Json)
                $state = $status.state
                $progress = $status.progress
                $elapsed = [int](Get-Date).Subtract($pollStart).TotalSeconds
                $line = "  [$count] [$elapsed s] $state (progress: $progress)"
                Write-Host $line -ForegroundColor Yellow
                $entry = "$state`|$progress`|$elapsed"
                $stateHistory += $entry
                $finalState = $state

                if ($state -in @("COMPLETE", "FAILED", "TIMEOUT")) {
                    Write-Host "  -> Terminal state reached: $state at ${elapsed}s" -ForegroundColor Green
                    break
                }
            } catch {
                Write-Host "  Poll error: $_" -ForegroundColor Red
            }
        }

        if ($finalState -eq "EXECUTING") {
            Write-Host "  -> Polling window expired. Final state: $finalState" -ForegroundColor Red
        }

        # ─── Step 4: Check SQLite ──────────────────────────────────
        Write-Host "`n[4/7] Checking SQLite DB..." -ForegroundColor Yellow
        $sqliteScript = @"
import sqlite3
conn = sqlite3.connect(r'$dbPath')
rows = conn.execute('SELECT mission_id, state, progress, error FROM missions WHERE mission_id=?', ('$missionId',)).fetchall()
if rows:
    for r in rows:
        print(f'  {r[0]} | {r[1]} | {r[2]} | {r[3] or \"(none)\"}')
else:
    print('  Mission not found in DB')
rows = conn.execute('SELECT mission_id, state, progress FROM missions ORDER BY updated_at DESC LIMIT 5').fetchall()
print('  Last 5 missions:')
for r in rows:
    print(f'    {r[0]} | {r[1]} | {r[2]}')
conn.close()
"@
        $sqliteScript | Out-File -FilePath 'C:\ProjectS-Unified\check_sqlite.py' -Encoding ascii
        $sqliteCheck = python C:\ProjectS-Unified\check_sqlite.py 2>&1
        Write-Host $sqliteCheck

        # ─── Step 5: Verify not stuck in EXECUTING ─────────────────
        Write-Host "`n[5/7] Stuck EXECUTING check..." -ForegroundColor Yellow
        $remainedExecuting = ($finalState -eq "EXECUTING")
        if ($remainedExecuting) {
            Write-Host "  REMAINED EXECUTING: YES (timeout may not have fired within 90s)" -ForegroundColor Red
        } else {
            Write-Host "  REMAINED EXECUTING: NO (reached terminal state: $finalState)" -ForegroundColor Green
        }

        # ─── Step 6: Health check after test ───────────────────────
        Write-Host "`n[6/7] Health check AFTER test..." -ForegroundColor Yellow
        try {
            $resp = Invoke-WebRequest -Uri "$baseURL/health" -TimeoutSec 5 -UseBasicParsing
            $healthAfter = $resp.StatusCode -eq 200
            Write-Host "  Health: PASS ($($resp.StatusCode))" -ForegroundColor Green
        } catch {
            Write-Host "  Health: FAIL" -ForegroundColor Red
            $healthAfter = $false
        }

        # ─── Step 7: Summary ───────────────────────────────────────
        Write-Host "`n[7/7] Summary:" -ForegroundColor Yellow
        Write-Host "  Mission ID:        $missionId" -ForegroundColor White
        Write-Host "  Timeout override:  30s" -ForegroundColor White
        Write-Host "  Final state:       $finalState" -ForegroundColor $(if ($finalState -eq "TIMEOUT") { "Green" } elseif ($finalState -eq "COMPLETE") { "Yellow" } else { "Red" })
        Write-Host "  Health before:     $healthBefore" -ForegroundColor $(if ($healthBefore) { "Green" } else { "Red" })
        Write-Host "  Health after:      $healthAfter" -ForegroundColor $(if ($healthAfter) { "Green" } else { "Red" })
        Write-Host "  Remained EXECUTING: $remainedExecuting" -ForegroundColor $(if ($remainedExecuting) { "Red" } else { "Green" })

        # Determine GAP_030 status
        $gap030Status = "ACTIVE"
        if ($finalState -eq "TIMEOUT" -and $healthAfter -and -not $remainedExecuting) {
            $gap030Status = "RESOLVED"
        } elseif ($finalState -eq "TIMEOUT") {
            $gap030Status = "PARTIAL"
        }

        Write-Host "  GAP_030 status:    $gap030Status" -ForegroundColor $(if ($gap030Status -eq "RESOLVED") { "Green" } elseif ($gap030Status -eq "PARTIAL") { "Yellow" } else { "Red" })

        # Save results for report
        $results = @{
            health_before          = $healthBefore
            timeout_override       = 30
            prompt_used            = "Write a very detailed and comprehensive analysis of the history of mathematics from ancient times to the modern era. Include at least 20 paragraphs..."
            mission_id             = $missionId
            final_state            = $finalState
            state_history          = $stateHistory
            remained_executing     = $remainedExecuting
            health_after           = $healthAfter
            gap030_status          = $gap030Status
            timestamp              = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
        } | ConvertTo-Json -Depth 10
        $results | Out-File -FilePath "C:\ProjectS-Unified\.gap030_live_results.json" -Encoding UTF8

        Write-Host "`n============================================================" -ForegroundColor Cyan
        Write-Host "  VALIDATION COMPLETE — Status: $gap030Status" -ForegroundColor $(if ($gap030Status -eq "RESOLVED") { "Green" } elseif ($gap030Status -eq "PARTIAL") { "Yellow" } else { "Red" })
        Write-Host "============================================================" -ForegroundColor Cyan
    }
} else {
    Write-Host "  No session/mission created — validation skipped" -ForegroundColor Red
}