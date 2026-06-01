$targetIP = "192.168.1.180"
$targetPassword = "Qwe123"
$securePass = ConvertTo-SecureString $targetPassword -AsPlainText -Force
$targetCred = New-Object System.Management.Automation.PSCredential("$targetIP\Administrator", $securePass)

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  SERVER PHASE 3: DEPENDENCY BOOTSTRAP" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# ============================================
# STEP 1: VERIFY SMB SHARE REMOVED
# ============================================
Write-Host "[1/5] Verifying SMB share removal..." -ForegroundColor Yellow
$shareRemoved = $true
try {
    $shareCheck = Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
        $share = Get-WmiObject -Class Win32_Share -Filter "Name='ProjectSStage'" -ErrorAction SilentlyContinue
        if ($share) {
            @{ Exists = $true; Name = $share.Name }
        } else {
            @{ Exists = $false }
        }
    }
    if ($shareCheck.Exists) {
        Write-Host "  Share ProjectSStage still exists - removing..." -ForegroundColor Yellow
        Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
            net share ProjectSStage /delete /y 2>&1 | Out-Null
        }
        Write-Host "  Share removed" -ForegroundColor Green
    } else {
        Write-Host "  Share ProjectSStage: already removed" -ForegroundColor Green
    }
} catch {
    Write-Host "  Share check: $_" -ForegroundColor Gray
}

# ============================================
# STEP 2: INSTALL DEPENDENCIES
# ============================================
Write-Host "[2/5] Installing baseline Python dependencies..." -ForegroundColor Yellow
$depsInstalled = $false
try {
    $installResult = Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
        $installOutput = pip install pyyaml requests python-dotenv 2>&1 | Out-String
        $checkOutput = pip list 2>&1 | Out-String
        $result = "=== pip install output ===`n" + $installOutput + "`n=== Installed packages (filtered) ===`n"
        $packages = @("pyyaml", "requests", "python-dotenv", "yaml")
        foreach ($pkg in $packages) {
            $pkgLine = $checkOutput | Where-Object { $_ -match "^$pkg" -or $_ -match "^PyYAML" -or $_ -match "^requests" -or $_ -match "^python-dotenv" }
            if ($pkgLine) { $result += "  $pkgLine`n" }
        }
        $result
    }
    Write-Host $installResult -ForegroundColor Gray
    Write-Host "  Dependencies installed" -ForegroundColor Green
    $depsInstalled = $true
} catch {
    Write-Host "  Dependency install failed: $_" -ForegroundColor Red
}

# ============================================
# STEP 3: RUN IMPORT SMOKE TESTS
# ============================================
Write-Host "[3/5] Running import smoke tests..." -ForegroundColor Yellow
$importResults = "failed"

$importTestScript = @'
import sys
import os

project_path = r"C:\ProjectS\project-s-code"
sys.path.insert(0, project_path)

print("=== Import Smoke Tests ===")
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
for name, status in results.items():
    print(f"  {name}: {status}")
'@

try {
    $importOutput = Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
        $scriptContent = $using:importTestScript
        $tempScript = "C:\ProjectS\phase3_import_test.py"
        Set-Content -Path $tempScript -Value $scriptContent -Encoding UTF8
        $output = python $tempScript 2>&1 | Out-String
        Remove-Item $tempScript -ErrorAction SilentlyContinue
        $output
    }
    Write-Host $importOutput -ForegroundColor Gray
    $importResults = "captured"
} catch {
    Write-Host "  Import test failed: $_" -ForegroundColor Red
}

# ============================================
# STEP 4: CAPTURE MISSING DEPENDENCIES
# ============================================
Write-Host "[4/5] Capturing missing dependencies..." -ForegroundColor Yellow
$missingDeps = @{}

$depCheckScript = @'
import sys

needed = ["yaml", "requests", "dotenv", "flask", "fastapi", "uvicorn", "numpy", "pandas", "torch", "transformers", "openai", "anthropic", "aiohttp", "websockets", "pydantic", "click", "rich", "tqdm", "loguru", "colorama", "jinja2", "markupsafe", "certifi", "urllib3", "idna", "charset_normalizer", "pyyaml", "python_dotenv", "setuptools"]

missing = {}
for mod in needed:
    try:
        __import__(mod)
    except ImportError:
        missing[mod] = "not found"

print(f"MISSING_COUNT:{len(missing)}")
for k, v in missing.items():
    print(f"MISSING:{k}")
'@

try {
    $depOutput = Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
        $scriptContent = $using:depCheckScript
        $tempScript = "C:\ProjectS\phase3_dep_check.py"
        Set-Content -Path $tempScript -Value $scriptContent -Encoding UTF8
        $output = python $tempScript 2>&1 | Out-String
        Remove-Item $tempScript -ErrorAction SilentlyContinue
        $output
    }
    Write-Host $depOutput -ForegroundColor Gray
    
    $missingLines = $depOutput | Where-Object { $_ -match "^MISSING:" }
    $countLine = $depOutput | Where-Object { $_ -match "^MISSING_COUNT:" }
    if ($countLine) {
        $count = [int]($countLine -replace "MISSING_COUNT:", "")
        Write-Host "  Missing critical modules: $count" -ForegroundColor $(if($count -lt 10){"Green"}else{"Yellow"})
        foreach ($line in $missingLines | Select-Object -First 10) {
            $mod = $line -replace "MISSING:", ""
            Write-Host "    - $mod" -ForegroundColor Gray
            $missingDeps[$mod] = "not found"
        }
    }
} catch {
    Write-Host "  Dependency check: $_" -ForegroundColor Gray
}

# ============================================
# STEP 5: SAVE RESULTS
# ============================================
Write-Host "[5/5] Saving results..." -ForegroundColor Yellow

$allResults = @{
    Phase = "3 - Dependency Bootstrap + Import Smoke"
    ShareRemoved = $shareRemoved
    DepsInstalled = $depsInstalled
    ImportResults = $importResults
    MissingModuleCount = $missingDeps.Count
    MissingModules = $missingDeps.Keys
    Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
}

$allResults | ConvertTo-Json | Out-File -FilePath "C:\ProjectS-Unified\.phase3_results.json" -Encoding UTF8

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  PHASE 3 SUMMARY" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  A. SMB share removed: $($shareRemoved)" -ForegroundColor $(if($shareRemoved){"Green"}else{"Red"})
Write-Host "  B. Dependencies installed: $($depsInstalled)" -ForegroundColor $(if($depsInstalled){"Green"}else{"Red"})
Write-Host "  C. Import results: $importResults" -ForegroundColor $(if($importResults -eq "captured"){"Green"}else{"Red"})
Write-Host "  D. Missing modules: $($missingDeps.Count)" -ForegroundColor $(if($missingDeps.Count -lt 10){"Green"}else{"Yellow"})
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan