# Windows C Compiler Blocker - Build Environment Issue

**Date:** 2025 (Current Session)
**Status:** BLOCKING - Cannot proceed with Avail DA build without C compiler
**System:** Windows (MSVC only, no MinGW)

## Problem Summary

The Avail DA codebase requires cryptography libraries (blst, arkworks, dusk-plonk) that contain C code and need compilation via a C compiler. The Windows system is missing all C compilers:

- ✗ MSVC (`cl.exe`) - NOT installed
- ✗ LLVM clang-cl - NOT installed
- ✗ MinGW gcc - NOT installed

Rust's bundled LLVM tools (`llvm-ar.exe`, `llc.exe`, `opt.exe`) are **backend/optimization tools only**, NOT C compilers.

### Error Expected
```
error: Microsoft Visual C++ build tools not found
note: run `rustup update msvc` or install MSVC build tools
```

or

```
error: trying to build a library with C dependency blst
error: C compiler not found
```

## Why LLVM Tools Aren't Enough

Rust toolchain includes:
- `llvm-ar.exe` - Static library archiver (backend)
- `llc.exe` - LLVM IR compiler (backend)
- `opt.exe` - IR optimizer (backend)
- `rust-lld.exe` - Linker (backend)

Missing:
- `clang-cl.exe` - C compiler (frontend) ← **REQUIRED**
- `clang.exe` - C compiler (frontend) ← **REQUIRED**

The `cc` crate (used by blst build script) expects a C compiler executable in PATH.

## Solutions (In Order of Recommendation)

### Option 1: Install Visual Studio Build Tools (RECOMMENDED)
- **Size:** ~2GB download, 5-10GB installed
- **Time:** 10-15 minutes
- **Result:** Full MSVC toolchain, official Microsoft support
- **Command:** Download from https://visualstudio.microsoft.com/downloads/
  - Select "Build Tools for Visual Studio 2022"
  - Install "Desktop development with C++"

**After installation, verify:**
```powershell
cl /?  # Should show cl.exe version
rustup update msvc  # Update Rust MSVC support
```

### Option 2: Install LLVM with clang-cl
- **Size:** ~1GB download, 3-5GB installed
- **Time:** 5-10 minutes
- **Result:** clang-cl.exe available, but less integrated
- **Command:** Download from https://releases.llvm.org/download.html
  - Select LLVM 17 or 18 for Windows (x64)
  - Install to C:\Program Files\LLVM
  - Add C:\Program Files\LLVM\bin to PATH

**After installation, verify:**
```powershell
clang-cl /?  # Should show clang-cl version
```

### Option 3: Install MinGW-w64 (Minimal)
- **Size:** ~500MB
- **Time:** 5 minutes
- **Note:** Requires configuration, may have compatibility issues
- **Command:** 
  - Download from https://www.mingw-w64.org/
  - Install to C:\mingw-w64
  - Add C:\mingw-w64\bin to PATH

## Current Environment State

**Installed:**
- Rust: stable-x86_64-pc-windows-msvc
- Cargo: Available
- LLVM tools: Partial (backend only)

**Missing:**
- C compiler (cl.exe, clang-cl, gcc)
- MSVC runtime
- Build environment

## Impact on Build

Without a C compiler:
- ✗ `cargo build -p da-runtime --features std` will fail
- ✗ `cargo build -p da-runtime --target wasm32-unknown-unknown` will fail
- ✓ Pure Rust crates will build fine
- ✗ Any crate with C dependencies (blst, arkworks, etc.) will fail

## Next Steps

1. Choose installation option (1, 2, or 3)
2. Install selected C compiler/build tools
3. Verify with `cl /?` or `clang-cl /?`
4. Update Rust: `rustup update msvc`
5. Run: `cargo build -p da-runtime --features std`

## Related Documentation

- Avail DA Target Dims Audit: [AVAIL_DA_TARGET_DIMS_SECURITY_AUDIT.md](AVAIL_DA_TARGET_DIMS_SECURITY_AUDIT.md)
- Previous Setup Attempt: [WINDOWS_SUBSTRATE_SETUP.md](WINDOWS_SUBSTRATE_SETUP.md)
- LLVM Workaround (Obsolete): [WINDOWS_LLVM_WORKAROUND.md](WINDOWS_LLVM_WORKAROUND.md)

## Conclusion

The Rust-bundled LLVM tools are insufficient for building C/C++ dependencies. A proper C compiler (MSVC, clang-cl, or gcc) must be installed separately. Option 1 (Visual Studio Build Tools) is recommended as the most compatible and reliable choice for Windows Rust development.
