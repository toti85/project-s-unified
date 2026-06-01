# WINDOWS SUBSTRATE/AVAIL DA SETUP GUIDE

## STEP 1: Install LLVM with Clang for Windows

Run as Administrator in PowerShell:

```powershell
# Option A: Using Chocolatey (if installed)
choco install llvm -y

# Option B: Using pre-built LLVM installer
# Download and install from: https://github.com/llvm/llvm-project/releases
# Get Windows MSVC pre-built (e.g., LLVM-17.0.0-win64.exe)
# Extract to: C:\tools\llvm
```

**Verify Installation:**
```powershell
clang --version
clang-cl --version
```

If not in PATH, add manually:
```powershell
$llvm_path = "C:\Program Files\LLVM\bin"  # or C:\tools\llvm\bin
$env:PATH = "$llvm_path;$env:PATH"

# Verify
clang --version
```

---

## STEP 2: Verify MSVC Build Tools

Check for Visual Studio C++ tools:

```powershell
# Check for cl.exe (MSVC compiler)
where.exe cl.exe

# If not found, install via Visual Studio installer or:
# Download: https://visualstudio.microsoft.com/downloads/
# Install "Desktop development with C++" workload
```

Verify MSVC is in PATH:
```powershell
cl.exe /?
```

---

## STEP 3: Configure Rust Toolchain

```powershell
# Update Rust
rustup update

# Add wasm32 target (required for Substrate)
rustup target add wasm32-unknown-unknown

# Verify installation
rustc --print sysroot
rustup target list | Select-String wasm32-unknown-unknown
```

---

## STEP 4: Set Environment Variables for cc-rs

These tell the C/C++ compiler what to use:

```powershell
# Set C compiler to Clang
$env:CC = "clang-cl"
$env:CXX = "clang-cl"
$env:AR = "llvm-ar"

# Verify clang-cl works
clang-cl.exe /help | Select-Object -First 5
```

**Persist variables** (add to PowerShell profile):
```powershell
$profile_path = $PROFILE
if (!(Test-Path $profile_path)) {
    New-Item -ItemType File -Path $profile_path -Force
}

Add-Content -Path $profile_path -Value @"

# Avail DA Build Environment
`$env:CC = "clang-cl"
`$env:CXX = "clang-cl"
`$env:AR = "llvm-ar"
"@

# Reload profile
. $PROFILE
```

---

## STEP 5: Verify Rust WASM Support

```powershell
# Check WASM target
rustc --print target-spec-json wasm32-unknown-unknown | Select-Object -First 10

# Compile simple Rust → WASM test
cargo new --lib test_wasm
cd test_wasm
cargo build --target wasm32-unknown-unknown

cd ..
```

---

## STEP 6: Build da-runtime with std Feature

Navigate to project:

```powershell
cd "c:\1225\project_s_super_core\avail-da\avail"

# Clean previous builds
cargo clean

# Build runtime with std
cargo build -p da-runtime --features std --release 2>&1 | Select-Object -Last 50
```

**Expected output (no clang errors):**
```
Compiling blst v0.3.14
Compiling secp256k1-sys v0.9.2
...
Finished release [optimized] target(s) in XXs
```

---

## STEP 7: Run Target Dims Test

```powershell
cd "c:\1225\project_s_super_core\avail-da\avail"

# Run the PoC test (should compile and execute)
cargo test -p da-runtime test_target_dims_mismatch --features std --lib -- --nocapture 2>&1 | Select-Object -Last 100
```

**Expected output:**
- Test compiles successfully
- Artifact written to: `memory/output/target_dims_runtime_poc.json`

---

## TROUBLESHOOTING

### Error: "clang-cl: command not found"

**Solution:**
```powershell
# Find LLVM path
$llvm_bin = "C:\Program Files\LLVM\bin"
$env:PATH = "$llvm_bin;$env:PATH"

# Verify
clang-cl --version
```

### Error: "Failed to find tool. Is `clang` installed?"

**Solution:**
```powershell
# cc-rs looks for 'clang', not 'clang-cl'
# Create symlink or use full path

# Option 1: Symlink
cmd /c mklink "C:\Program Files\LLVM\bin\clang.exe" "C:\Program Files\LLVM\bin\clang-cl.exe"

# Option 2: Set CC to full path
$env:CC = "C:\Program Files\LLVM\bin\clang-cl.exe"
```

### Error: "Cannot find AR tool (llvm-ar)"

**Solution:**
```powershell
# Verify llvm-ar exists
Get-ChildItem -Path "C:\Program Files\LLVM\bin" -Filter "llvm-ar*"

# If missing, reinstall LLVM
# Or use alternative: ar.exe from MSVC
$env:AR = "C:\Program Files\LLVM\bin\llvm-ar.exe"
```

### WASM Build Still Fails

**Check build.rs dependency:**
```powershell
# The issue is in avail/runtime/build.rs which uses WasmBuilder
# If substrate-wasm-builder fails, ensure:

# 1. wasm32 target is installed
rustup target add wasm32-unknown-unknown

# 2. wasm-opt is available (usually auto-installed)
cargo install wasm-opt

# 3. Try clean rebuild
cargo clean
cargo build -p da-runtime --features std
```

---

## VERIFICATION CHECKLIST

- [ ] `clang --version` returns version
- [ ] `clang-cl --version` returns version
- [ ] `llvm-ar --version` returns version
- [ ] `cl.exe /?` returns MSVC help
- [ ] `rustc --print sysroot` shows Rust path
- [ ] `rustup target list | Select-String wasm32` shows installed
- [ ] `cargo build -p da-runtime --features std` completes without C compiler errors
- [ ] `cargo test -p da-runtime test_target_dims_mismatch` compiles and runs
- [ ] `memory/output/target_dims_runtime_poc.json` is created with valid JSON

---

## FINAL TEST

```powershell
cd "c:\1225\project_s_super_core\avail-da\avail"

# Full build + test cycle
Write-Host "Building da-runtime..."
cargo build -p da-runtime --features std 2>&1 | Select-String "Finished|error"

Write-Host "Running target_dims test..."
cargo test -p da-runtime test_target_dims_mismatch --features std --lib -- --nocapture 2>&1 | Select-String "test result|target_dims"

Write-Host "Checking artifact..."
Get-Content "c:\1225\project_s_super_core\memory\output\target_dims_runtime_poc.json" | ConvertFrom-Json | Select-Object result, error
```

**Expected output:**
```
Finished: ✓
test result: ✓
artifact: ✓
```
