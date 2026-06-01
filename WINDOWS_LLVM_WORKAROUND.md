# ALTERNATIVE: Use Rust-bundled LLVM Tools (No External Installation)

## Problem
System doesn't have clang installed and LLVM download failed. However, Rust includes LLVM tools.

## Solution
Configure cc-rs to use LLVM tools from Rust toolchain instead of system clang.

---

## STEP 1: Locate Rust's LLVM Tools

```powershell
# Find Rust sysroot
$sysroot = rustc --print sysroot
Write-Host "Rust sysroot: $sysroot"

# LLVM bin location
$llvm_bin = "$sysroot\lib\rustlib\x86_64-pc-windows-msvc\bin"
Write-Host "LLVM bin: $llvm_bin"

# Verify tools exist
Get-ChildItem -Path $llvm_bin -Filter "llvm*" | Select-Object -First 10
```

**Expected:**
```
llc.exe
llvm-ar.exe
llvm-as.exe
llvm-dis.exe
llvm-link.exe
llvm-nm.exe
llvm-objcopy.exe
llvm-objdump.exe
...
```

---

## STEP 2: Create Wrapper Scripts for cc-rs

CC-rs looks for `clang`, `clang-cl`, `ar`, etc. We create wrappers that redirect to Rust's LLVM tools.

```powershell
# Create scripts directory
$scripts_dir = "C:\avail-build-scripts"
New-Item -ItemType Directory -Path $scripts_dir -Force | Out-Null

# Get LLVM paths
$sysroot = rustc --print sysroot
$llvm_bin = "$sysroot\lib\rustlib\x86_64-pc-windows-msvc\bin"

Write-Host "Creating wrapper scripts in: $scripts_dir"
```

**Create clang-cl wrapper (clang-cl.cmd):**
```powershell
$clang_cl_wrapper = @"
@echo off
"$llvm_bin\clang-cl.exe" %*
"@

Set-Content -Path "$scripts_dir\clang-cl.cmd" -Value $clang_cl_wrapper
Write-Host "✓ Created: $scripts_dir\clang-cl.cmd"
```

**Create clang wrapper (clang.cmd):**
```powershell
$clang_wrapper = @"
@echo off
REM Redirect to clang-cl for Windows MSVC compilation
"$llvm_bin\clang-cl.exe" %*
"@

Set-Content -Path "$scripts_dir\clang.cmd" -Value $clang_wrapper
Write-Host "✓ Created: $scripts_dir\clang.cmd"
```

**Create llvm-ar wrapper (llvm-ar.cmd):**
```powershell
$ar_wrapper = @"
@echo off
"$llvm_bin\llvm-ar.exe" %*
"@

Set-Content -Path "$scripts_dir\llvm-ar.cmd" -Value $ar_wrapper
Write-Host "✓ Created: $scripts_dir\llvm-ar.cmd"
```

---

## STEP 3: Add to PATH and Configure Environment

```powershell
# Add scripts directory to PATH (before other tools)
$env:PATH = "$scripts_dir;$env:PATH"

# Configure cc-rs environment variables
$env:CC = "clang-cl"
$env:CXX = "clang-cl"  
$env:AR = "llvm-ar"

# Optional: CFLAGS for WASM target
$env:CFLAGS_wasm32_unknown_unknown = "-target wasm32"

# Verify scripts are callable
clang-cl --version 2>&1 | Select-Object -First 3
llvm-ar --version 2>&1 | Select-Object -First 3

Write-Host "✓ Environment configured"
```

---

## STEP 4: Persist Configuration (PowerShell Profile)

```powershell
# Add to PowerShell profile for persistence
$profile_content = @"

# ============================================
# Avail DA / Substrate Build Configuration
# ============================================

# Scripts directory with LLVM tool wrappers
`$avail_scripts = "C:\avail-build-scripts"
if (Test-Path `$avail_scripts) {
    `$env:PATH = "`$avail_scripts;`$env:PATH"
}

# Configure C compiler (using Rust-bundled LLVM)
`$env:CC = "clang-cl"
`$env:CXX = "clang-cl"
`$env:AR = "llvm-ar"

# Optional: Verbose output for debugging
# `$env:RUST_LOG = "debug"
"@

# Append to profile
Add-Content -Path $PROFILE -Value $profile_content -ErrorAction SilentlyContinue

Write-Host "✓ Profile updated: $PROFILE"
Write-Host "  Restart PowerShell to apply changes"
```

---

## STEP 5: Test Build

```powershell
# Full test cycle
cd "c:\1225\project_s_super_core\avail-da\avail"

Write-Host "Step 1: Clean build cache"
cargo clean

Write-Host "Step 2: Building da-runtime (this will use Rust LLVM tools)..."
$start = Get-Date
cargo build -p da-runtime --features std 2>&1 | Tee-Object -Variable build_log

$end = Get-Date
$duration = ($end - $start).TotalSeconds

# Check for success
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Build succeeded in $duration seconds" -ForegroundColor Green
    Write-Host "  Check: Compiling blst v0.3.14 (should NOT have clang errors)"
} else {
    Write-Host "✗ Build failed" -ForegroundColor Red
    $build_log | Select-String "error|clang" -Context 2
}
```

---

## STEP 6: Run PoC Test

```powershell
cd "c:\1225\project_s_super_core\avail-da\avail"

Write-Host "Running target_dims PoC test..."
cargo test -p da-runtime test_target_dims_mismatch --features std --lib -- --nocapture 2>&1 | Select-Object -Last 50

# Check for artifact
$artifact = "c:\1225\project_s_super_core\memory\output\target_dims_runtime_poc.json"
if (Test-Path $artifact) {
    Write-Host "✓ Artifact created" -ForegroundColor Green
    Get-Content $artifact | ConvertFrom-Json | Select-Object timestamp, result, error
} else {
    Write-Host "✗ Artifact not created" -ForegroundColor Red
}
```

---

## VERIFICATION CHECKLIST

```powershell
$checks = @{
    "Scripts dir exists" = (Test-Path "C:\avail-build-scripts")
    "clang-cl.cmd exists" = (Test-Path "C:\avail-build-scripts\clang-cl.cmd")
    "llvm-ar.cmd exists" = (Test-Path "C:\avail-build-scripts\llvm-ar.cmd")
    "clang-cl callable" = (!(!(clang-cl --version 2>$null)))
    "llvm-ar callable" = (!(!(llvm-ar --version 2>$null)))
}

Write-Host "Verification Results:" -ForegroundColor Cyan
foreach ($check in $checks.GetEnumerator()) {
    $status = if ($check.Value) { "✓" } else { "✗" }
    Write-Host "$status $($check.Key)"
}
```

---

## IF BUILD STILL FAILS

### Check 1: BLST Build
```powershell
cargo build -p blst 2>&1 | Select-String "error|clang"

# If still fails, try with native-only (no WASM)
# Remove the WASM build requirement temporarily
```

### Check 2: Secp256k1
```powershell
cargo build -p secp256k1-sys 2>&1 | Select-String "error|C compiler"
```

### Check 3: Verbose Output
```powershell
$env:RUST_LOG = "debug"
$env:CC_ENABLE_DEBUG_OUTPUT = "1"
cargo build -p da-runtime --features std 2>&1 | Select-String "Compiler|cc-rs|error"
```

---

## NOTES

- This approach uses **Rust's bundled LLVM**, avoiding external installation
- Wrapper scripts work for both native and WASM targets
- For WASM, clang-cl automatically recognizes wasm32 target
- No modification to project code required

