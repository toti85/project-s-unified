#!/usr/bin/env python3
"""
PROJECT-S SUPERINTELLIGENT AI - STARTUP SCRIPT
=====================================================
Betartja a COPILOT_RULES.md dokumentációt
Entry point: super_intelligent_launcher.py
"""

import subprocess
import sys
from pathlib import Path

def print_header():
    print("\n" + "="*70)
    print("PROJECT-S SUPERINTELLIGENT AI v0.1")
    print("="*70)

def check_project_structure():
    """Verify project structure matches documentation"""
    print("\n[CHECK] Project structure verification...")
    
    required_paths = [
        "super_intelligent_launcher.py",
        "tests/TEST_D_META_LEARNING_PROOF.py",
        "tests/TEST_E_REGRESSION_LEARNING_PROOF.py",
        "src/core/super_intelligent_ai.py",
        "tools/tools/registry/",
        "integrations/ai_models/",
        "config/",
        "docs/COPILOT_RULES.md"
    ]
    
    base = Path(__file__).parent
    missing = []
    
    for path in required_paths:
        full_path = base / path
        if not full_path.exists():
            missing.append(path)
            print(f"  [WARN] Missing: {path}")
        else:
            print(f"  [OK] Found: {path}")
    
    if missing:
        print(f"\n[WARN] {len(missing)} path(s) missing but continuing...")
    else:
        print("\n[OK] All required paths found!")
    
    return len(missing) == 0

def start_launcher():
    """Start the SuperIntelligentAI launcher"""
    print("\n[START] Initializing SuperIntelligentAI...")
    print("-"*70)
    
    try:
        result = subprocess.run(
            [sys.executable, "super_intelligent_launcher.py", "--smoke"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Check for PASS in output
        if "PASS" in result.stdout:
            print("[OK] SuperIntelligentAI initialized successfully!")
            return True
        elif "FAIL" in result.stdout:
            print("[FAIL] SuperIntelligentAI initialization failed!")
            print(result.stdout)
            return False
        else:
            # Show last few lines
            lines = result.stdout.split('\n')
            for line in lines[-5:]:
                if line.strip():
                    print(f"  {line}")
            return "SuperIntelligentAI initialized" in result.stdout
            
    except subprocess.TimeoutExpired:
        print("[ERROR] Launcher timeout!")
        return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

def run_tests():
    """Run TEST_D and TEST_E as per documentation"""
    print("\n[TESTS] Running meta-learning and regression tests...")
    print("-"*70)
    
    tests = [
        ("TEST_D", "tests/TEST_D_META_LEARNING_PROOF.py", "META-LEARNING"),
        ("TEST_E", "tests/TEST_E_REGRESSION_LEARNING_PROOF.py", "REGRESSION LEARNING")
    ]
    
    results = {}
    
    for test_name, test_path, description in tests:
        print(f"\n[{test_name}] {description}...")
        
        try:
            result = subprocess.run(
                [sys.executable, test_path],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=Path(__file__).parent
            )
            
            # Check for PASS
            if "PASS" in result.stdout:
                print(f"  [OK] {test_name} PASSED")
                results[test_name] = True
            else:
                print(f"  [FAIL] {test_name} did not pass")
                results[test_name] = False
                # Show relevant output
                for line in result.stdout.split('\n')[-10:]:
                    if line.strip() and ('PASS' in line or 'FAIL' in line):
                        print(f"    {line}")
        
        except subprocess.TimeoutExpired:
            print(f"  [TIMEOUT] {test_name} exceeded 120s")
            results[test_name] = False
        except Exception as e:
            print(f"  [ERROR] {test_name}: {e}")
            results[test_name] = False
    
    return results

def show_available_interfaces():
    """Show available user interfaces"""
    print("\n[INTERFACES] Available task interfaces:")
    print("-"*70)
    print("  1. feladat.py    - Direct task assignment (command-line)")
    print("  2. task.py       - Interactive task interface")
    print("\nUsage:")
    print('  python feladat.py "Hozz letre egy JSON-t az elerheto toolok listajarol"')
    print("  python task.py   (interactive menu)")

def show_status_report(launcher_ok, test_results):
    """Show final status report"""
    print("\n" + "="*70)
    print("PROJECT STATUS REPORT")
    print("="*70)
    
    print("\n[LAUNCHER] SuperIntelligentAI:")
    print(f"  Status: {'OK' if launcher_ok else 'FAILED'}")
    
    print("\n[TESTS] Learning Proofs:")
    for test, passed in test_results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {test}: {status}")
    
    all_passed = launcher_ok and all(test_results.values())
    
    print("\n" + "="*70)
    if all_passed:
        print("[READY] PROJECT-S is ready for use!")
        print("\nYou can now:")
        print("  1. Run tasks: python feladat.py \"your task\"")
        print("  2. Use interactive mode: python task.py")
        print("  3. Check memory/output/ for results")
    else:
        print("[WARNING] Some checks failed, but system is operational")
    
    print("="*70 + "\n")
    
    return all_passed

def main():
    print_header()
    
    # Check structure
    structure_ok = check_project_structure()
    
    # Start launcher
    launcher_ok = start_launcher()
    
    # Run tests
    test_results = run_tests()
    
    # Show status
    ready = show_status_report(launcher_ok, test_results)
    
    return 0 if ready else 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n[STOP] Startup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FATAL] {e}")
        sys.exit(1)
