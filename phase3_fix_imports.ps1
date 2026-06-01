$targetIP = "192.168.1.180"
$targetPassword = "Qwe123"
$securePass = ConvertTo-SecureString $targetPassword -AsPlainText -Force
$targetCred = New-Object System.Management.Automation.PSCredential("$targetIP\Administrator", $securePass)

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  PHASE 3: FIX MISSING IMPORTS" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Install the 3 immediately missing dependencies
Write-Host "[1/3] Installing httpx, fastapi, aiofiles..." -ForegroundColor Yellow
try {
    $installOutput = Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
        $out = pip install httpx fastapi aiofiles 2>&1 | Out-String
        $out
    }
    Write-Host $installOutput -ForegroundColor Gray
    Write-Host "  Installation complete" -ForegroundColor Green
} catch {
    Write-Host "  Install failed: $_" -ForegroundColor Red
}

# Re-run import tests
Write-Host ""
Write-Host "[2/3] Re-running import tests..." -ForegroundColor Yellow

$importTestScript = @'
import sys
import os

project_path = r"C:\ProjectS\project-s-code"
sys.path.insert(0, project_path)

print("=== Import Smoke Tests (Retry) ===")
print(f"Python: {sys.version}")
print(f"Path: {project_path}")
print()

results = {}

# Test 1: SuperIntelligentAI
try:
    from src.core.super_intelligent_ai import SuperIntelligentAI
    print("[OK] SuperIntelligentAI import")
    results["SuperIntelligentAI"] = "OK"
except Exception as e:
    exc_type = type(e).__name__
    exc_msg = str(e)
    print(f"[FAIL] SuperIntelligentAI import: {exc_type}: {exc_msg}")
    results["SuperIntelligentAI"] = f"{exc_type}: {exc_msg}"

print()

# Test 2: Interactive Layer
try:
    from interactive_layer.main import app
    print("[OK] Interactive Layer import")
    results["InteractiveLayer"] = "OK"
except Exception as e:
    exc_type = type(e).__name__
    exc_msg = str(e)
    print(f"[FAIL] Interactive Layer import: {exc_type}: {exc_msg}")
    results["InteractiveLayer"] = f"{exc_type}: {exc_msg}"

print()

# Test 3: SmartToolOrchestrator
try:
    from tools.tools.registry.smart_orchestrator import SmartToolOrchestrator
    print("[OK] SmartToolOrchestrator import")
    results["SmartToolOrchestrator"] = "OK"
except Exception as e:
    exc_type = type(e).__name__
    exc_msg = str(e)
    print(f"[FAIL] SmartToolOrchestrator import: {exc_type}: {exc_msg}")
    results["SmartToolOrchestrator"] = f"{exc_type}: {exc_msg}"

print()
print("=== Summary ===")
ok_count = sum(1 for v in results.values() if v == "OK")
fail_count = len(results) - ok_count
print(f"  OK: {ok_count}, Failed: {fail_count}")
for name, status in results.items():
    print(f"  {name}: {status}")
'@

try {
    $importOutput = Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
        $scriptContent = $using:importTestScript
        $tempScript = "C:\ProjectS\phase3_import_retry.py"
        Set-Content -Path $tempScript -Value $scriptContent -Encoding UTF8
        $output = python $tempScript 2>&1 | Out-String
        Remove-Item $tempScript -ErrorAction SilentlyContinue
        $output
    }
    Write-Host $importOutput -ForegroundColor Gray
} catch {
    Write-Host "  Import test failed: $_" -ForegroundColor Red
}

# Save results
Write-Host ""
Write-Host "[3/3] Saving results..." -ForegroundColor Yellow

$allResults = @{
    Phase = "3 - Fix Missing Imports"
    Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
}

$allResults | ConvertTo-Json | Out-File -FilePath "C:\ProjectS-Unified\.phase3_retry_results.json" -Encoding UTF8

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  DONE" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan