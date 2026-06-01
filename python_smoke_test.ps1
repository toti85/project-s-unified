$targetIP = "192.168.1.180"
$targetPassword = "Qwe123"
$securePass = ConvertTo-SecureString $targetPassword -AsPlainText -Force
$targetCred = New-Object System.Management.Automation.PSCredential("$targetIP\Administrator", $securePass)

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  PYTHON IMPORT SMOKE TESTS" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Run Python smoke tests on the server
$smokeTestScript = @'
import sys
import os

print("=== Python Environment ===" )
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print(f"Platform: {sys.platform}")
print(f"Working directory: {os.getcwd()}")
print()

# Check if Project-S files exist
project_path = r"C:\ProjectS\project-s-code"
print(f"=== Checking Project-S path: {project_path} ===")

if os.path.exists(project_path):
    print(f"Path exists: YES")
    # List top-level items
    items = os.listdir(project_path)
    print(f"Top-level items ({len(items)}):")
    for item in sorted(items):
        full = os.path.join(project_path, item)
        prefix = "DIR " if os.path.isdir(full) else "FILE"
        print(f"  [{prefix}] {item}")
else:
    print(f"Path exists: NO")

print()
print("=== Key File Checks ===")

key_files = [
    "PROJECT_S_OVERVIEW.md",
    "DECISIONS.md",
    "COMPONENT_INVENTORY.md",
    "config/CI_GATE_CONFIG.md",
    "ai_interactive.py",
    "ai_no_meta.py",
    "ai_web_scraping.py",
    "src/core/super_intelligent_ai.py",
    "src/core/async_execution_test.py",
    "interactive_layer/interactive_task.py",
    "interactive_layer/static/ui.html",
    "self_state.json",
    "memory/telemetry/executions.jsonl",
]

for f in key_files:
    full = os.path.join(project_path, f)
    if os.path.exists(full):
        size = os.path.getsize(full)
        print(f"  [OK] {f} ({size} bytes)")
    else:
        print(f"  [MISSING] {f}")

print()
print("=== Python Import Tests ===")

import_tests = [
    ("sys", "Standard library"),
    ("os", "Standard library"),
    ("json", "Standard library"),
    ("pathlib", "Standard library"),
    ("importlib", "Standard library"),
]

for module, desc in import_tests:
    try:
        __import__(module)
        print(f"  [OK] {module} - {desc}")
    except ImportError as e:
        print(f"  [FAIL] {module} - {e}")

print()
print("=== Project-S Module Checks ===")

# Add project path to sys.path
sys.path.insert(0, project_path)

project_modules = [
    "ai_interactive",
    "ai_no_meta",
    "ai_web_scraping",
]

for mod in project_modules:
    try:
        __import__(mod)
        print(f"  [OK] import {mod}")
        # Clean up from sys.modules
        if mod in sys.modules:
            del sys.modules[mod]
    except ImportError as e:
        print(f"  [FAIL] import {mod} - {e}")
    except Exception as e:
        print(f"  [WARN] import {mod} - {type(e).__name__}: {e}")

print()
print("=== Directory Structure Validation ===")

required_dirs = [
    "src",
    "src/core",
    "interactive_layer",
    "interactive_layer/static",
    "config",
    "memory",
    "memory/telemetry",
    "reports",
    "golden",
]

for d in required_dirs:
    full = os.path.join(project_path, d)
    exists = os.path.exists(full)
    is_dir = os.path.isdir(full) if exists else False
    status = "OK" if exists and is_dir else "MISSING"
    color = "green" if status == "OK" else "red"
    print(f"  [{status}] {d}")

print()
print("=== File Count ===")
total_files = 0
total_size = 0
for root, dirs, files in os.walk(project_path):
    for f in files:
        fp = os.path.join(root, f)
        if os.path.exists(fp):
            try:
                total_files += 1
                total_size += os.path.getsize(fp)
            except:
                pass

print(f"  Total files: {total_files}")
print(f"  Total size: {total_size / (1024*1024):.2f} MB")

print()
print("=== SMOKE TEST COMPLETE ===")
'@

# Write and execute the Python script on the server
$tempScript = "C:\ProjectS\server_smoke_test.py"

Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
    $scriptContent = $using:smokeTestScript
    $tempScript = "C:\ProjectS\server_smoke_test.py"
    
    # Write the script
    Set-Content -Path $tempScript -Value $scriptContent -Encoding UTF8
    
    # Execute it
    Write-Host "=== Running Python smoke tests on server ===" -ForegroundColor Cyan
    python $tempScript 2>&1
    
    # Clean up
    Remove-Item $tempScript -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  SMOKE TESTS COMPLETE" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan