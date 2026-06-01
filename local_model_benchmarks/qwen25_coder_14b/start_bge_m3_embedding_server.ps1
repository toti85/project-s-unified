<#
.SYNOPSIS
    Start BGE-M3 embedding model server on port 8099 (CPU-only, llama.cpp Vulkan).

.DESCRIPTION
    Starts llama-server in embedding mode for BGE-M3.
    CPU-only by default to preserve Tesla M60 VRAM for Qwen models.
    Provides OpenAI-compatible /v1/embeddings endpoint.

.PARAMETER NThreads
    Number of CPU threads (default: 8, reasonable for 36-core DL380).
#>
param(
    [int]$NThreads = 8
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# === PATHS ===
$LLAMA_SERVER = "F:\ModelVault\llama-cpp\vulkan-bin\llama-server.exe"
$MODEL_FILE   = "F:\ModelVault\gguf\embedding\bge-m3\bge-m3-Q4_K_M.gguf"
$LOG_DIR      = "F:\ModelVault\logs"
$PORT         = 8099
$TIMESTAMP    = (Get-Date -Format "yyyyMMdd_HHmmss")
$LOG_FILE     = "$LOG_DIR\bge_m3_embedding_$TIMESTAMP.log"
$ERR_FILE     = "$LOG_DIR\bge_m3_embedding_$TIMESTAMP.err"

Write-Host "=========================================="
Write-Host "  BGE-M3 Embedding Server Startup"
Write-Host "  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "=========================================="

# === PRE-FLIGHT CHECKS ===
Write-Host ""
Write-Host "[1] Pre-flight checks..."

if (-not (Test-Path $LLAMA_SERVER)) {
    Write-Host "ERROR: llama-server.exe not found at $LLAMA_SERVER" -ForegroundColor Red
    exit 1
}
Write-Host "    llama-server.exe: OK"

if (-not (Test-Path $MODEL_FILE)) {
    Write-Host "ERROR: BGE-M3 model not found at $MODEL_FILE" -ForegroundColor Red
    Write-Host "       Download it first: Start-BitsTransfer from gpustack/bge-m3-GGUF on HuggingFace"
    exit 1
}
$modelSizeMB = [math]::Round((Get-Item $MODEL_FILE).Length / 1MB, 1)
Write-Host "    Model: OK ($modelSizeMB MB)"

if ($modelSizeMB -lt 300) {
    Write-Host "ERROR: Model file too small ($modelSizeMB MB) — likely corrupt download" -ForegroundColor Red
    exit 1
}

New-Item -Path $LOG_DIR -ItemType Directory -Force | Out-Null
Write-Host "    Log dir: OK"

# === KILL EXISTING PROCESS ON PORT 8099 ===
Write-Host ""
Write-Host "[2] Clearing port $PORT..."
$existing = Get-NetTCPConnection -LocalPort $PORT -State Listen -ErrorAction SilentlyContinue
if ($existing) {
    $pid = $existing[0].OwningProcess
    Write-Host "    Found PID $pid on port $PORT — stopping..."
    Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    Start-Sleep 2
}
Write-Host "    Port $PORT: clear"

# === FIREWALL RULE ===
Write-Host ""
Write-Host "[3] Firewall rule for port $PORT..."
$ruleName = "llama-embedding-8099"
if (-not (Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Protocol TCP `
        -LocalPort $PORT -Action Allow -Profile Any | Out-Null
    Write-Host "    Created: $ruleName"
} else {
    Write-Host "    Exists: $ruleName"
}

# === START SERVER ===
Write-Host ""
Write-Host "[4] Starting llama-server (embedding mode, CPU-only, $NThreads threads)..."
Write-Host "    Port: $PORT"
Write-Host "    Model: $MODEL_FILE"
Write-Host "    Log: $LOG_FILE"

$args = @(
    "-m", $MODEL_FILE,
    "--port", $PORT,
    "--host", "0.0.0.0",
    "--embedding",
    "--threads", $NThreads,
    "--ctx-size", "8192",
    "-ngl", "0"        # CPU-only: no GPU layers — preserves VRAM for Qwen models
)

$p = Start-Process `
    -FilePath $LLAMA_SERVER `
    -ArgumentList $args `
    -RedirectStandardOutput $LOG_FILE `
    -RedirectStandardError $ERR_FILE `
    -PassThru `
    -NoNewWindow

Write-Host "    PID: $($p.Id)"

# === WAIT FOR READY ===
Write-Host ""
Write-Host "[5] Waiting for server ready (max 30s)..."
$ready = $false
for ($i = 0; $i -lt 15; $i++) {
    Start-Sleep 2
    $errContent = Get-Content $ERR_FILE -ErrorAction SilentlyContinue
    if ($errContent -match "server is listening|listening on") {
        $ready = $true
        Write-Host "    READY after $($i*2+2)s"
        break
    }
    if ($i -eq 4) {
        Write-Host "    Still loading model..." 
    }
}

if (-not $ready) {
    Write-Host "WARNING: 'listening' signal not found in 30s — server may still be loading"
}

# === FINAL STATUS ===
Write-Host ""
Write-Host "[6] Status check..."
$port_check = Get-NetTCPConnection -LocalPort $PORT -State Listen -ErrorAction SilentlyContinue
if ($port_check) {
    Write-Host "    Port $PORT: LISTENING (PID=$($port_check[0].OwningProcess))" -ForegroundColor Green
} else {
    Write-Host "    Port $PORT: NOT listening yet" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "--- Last log lines ---"
Get-Content $ERR_FILE -Tail 5 -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "==========================================" 
Write-Host "  Endpoint: http://127.0.0.1:$PORT/v1/embeddings"
Write-Host "  Test: POST { 'model': 'bge-m3', 'input': 'hello world' }"
Write-Host "=========================================="
