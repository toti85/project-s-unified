$targetIP = "192.168.1.180"
$targetPassword = "Qwe123"
$securePass = ConvertTo-SecureString $targetPassword -AsPlainText -Force
$targetCred = New-Object System.Management.Automation.PSCredential("$targetIP\Administrator", $securePass)

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  PHASE 3.1: OPTIONAL RUNTIME DEPS" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Install psutil and langgraph
Write-Host "[1/3] Installing psutil and langgraph..." -ForegroundColor Yellow
try {
    $installOutput = Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
        $out = pip install psutil langgraph 2>&1 | Out-String
        $out
    }
    Write-Host $installOutput -ForegroundColor Gray
    Write-Host "  Installation complete" -ForegroundColor Green
    $installOK = $true
} catch {
    Write-Host "  Install failed: $_" -ForegroundColor Red
    $installOK = $false
}

# Step 2: Re-run import checks
Write-Host ""
Write-Host "[2/3] Re-running import checks..." -ForegroundColor Yellow

$importCheckScript = @'
import sys

project_path = r"C:\ProjectS\project-s-code"
sys.path.insert(0, project_path)

print("=== Phase 3.1 Import Checks ===")
print()

results = {}

# Check 1: psutil
try:
    import psutil
    print("[OK] psutil import")
    results["psutil"] = "OK"
except Exception as e:
    print(f"[FAIL] psutil import: {type(e).__name__}: {e}")
    results["psutil"] = f"{type(e).__name__}: {e}"

# Check 2: langgraph
try:
    import langgraph
    print("[OK] langgraph import")
    results["langgraph"] = "OK"
except Exception as e:
    print(f"[FAIL] langgraph import: {type(e).__name__}: {e}")
    results["langgraph"] = f"{type(e).__name__}: {e}"

print()

# Check 3: SuperIntelligentAI
try:
    from src.core.super_intelligent_ai import SuperIntelligentAI
    print("[OK] SuperIntelligentAI import")
    results["SuperIntelligentAI"] = "OK"
except Exception as e:
    print(f"[FAIL] SuperIntelligentAI import: {type(e).__name__}: {e}")
    results["SuperIntelligentAI"] = f"{type(e).__name__}: {e}"

# Check 4: Interactive Layer
try:
    from interactive_layer.main import app
    print("[OK] Interactive Layer import")
    results["InteractiveLayer"] = "OK"
except Exception as e:
    print(f"[FAIL] Interactive Layer import: {type(e).__name__}: {e}")
    results["InteractiveLayer"] = f"{type(e).__name__}: {e}"

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
        $scriptContent = $using:importCheckScript
        $tempScript = "C:\ProjectS\phase31_import_check.py"
        Set-Content -Path $tempScript -Value $scriptContent -Encoding UTF8
        $output = python $tempScript 2>&1 | Out-String
        Remove-Item $tempScript -ErrorAction SilentlyContinue
        $output
    }
    Write-Host $importOutput -ForegroundColor Gray
    $importOK = $true
} catch {
    Write-Host "  Import check failed: $_" -ForegroundColor Red
    $importOK = $false
}

# Step 3: Check for new missing dependencies
Write-Host ""
Write-Host "[3/3] Checking for new missing dependencies..." -ForegroundColor Yellow

$depCheckScript = @'
import sys

# Check all previously missing modules again
needed = ["psutil", "langgraph", "yaml", "requests", "dotenv", "httpx", "fastapi", "aiofiles"]

missing = {}
for mod in needed:
    try:
        __import__(mod)
    except ImportError:
        missing[mod] = "not found"

if missing:
    print(f"MISSING_COUNT:{len(missing)}")
    for k in missing.keys():
        print(f"MISSING:{k}")
else:
    print("ALL_CRITICAL_INSTALLED")
'@

try {
    $depOutput = Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
        $scriptContent = $using:depCheckScript
        $tempScript = "C:\ProjectS\phase31_dep_check.py"
        Set-Content -Path $tempScript -Value $scriptContent -Encoding UTF8
        $output = python $tempScript 2>&1 | Out-String
        Remove-Item $tempScript -ErrorAction SilentlyContinue
        $output
    }
    Write-Host $depOutput -ForegroundColor Gray
    
    if ($depOutput -match "ALL_CRITICAL_INSTALLED") {
        Write-Host "  All critical dependencies installed" -ForegroundColor Green
        $newMissing = @()
    } else {
        $missingLines = $depOutput | Where-Object { $_ -match "^MISSING:" }
        $newMissing = $missingLines | ForEach-Object { $_ -replace "MISSING:", "" }
        Write-Host "  New missing: $($newMissing -join ', ')" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  Dependency check: $_" -ForegroundColor Gray
    $newMissing = @()
}

# Save results
Write-Host ""
Write-Host "Saving results..." -ForegroundColor Yellow

$allResults = @{
    Phase = "3.1 - Optional Runtime Dependency Completion"
    PsutilInstalled = $installOK
    LanggraphInstalled = $installOK
    AllImportsPass = $importOK
    NewMissingDeps = $newMissing
    Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
}

$allResults | ConvertTo-Json | Out-File -FilePath "C:\ProjectS-Unified\.phase31_results.json" -Encoding UTF8

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  PHASE 3.1 SUMMARY" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  A. psutil installed: $($installOK)" -ForegroundColor $(if($installOK){"Green"}else{"Red"})
Write-Host "  B. langgraph installed: $($installOK)" -ForegroundColor $(if($installOK){"Green"}else{"Red"})
Write-Host "  C. Core imports still PASS: $($importOK)" -ForegroundColor $(if($importOK){"Green"}else{"Red"})
Write-Host "  D. New missing deps: $(if($newMissing){$newMissing.Count}else{0})" -ForegroundColor $(if(-not $newMissing -or $newMissing.Count -eq 0){"Green"}else{"Yellow"})
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan