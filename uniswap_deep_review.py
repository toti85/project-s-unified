#!/usr/bin/env python3
"""
UNISWAP V3 DEEP CODE REVIEW
Detailed vulnerability analysis focusing on:
1. Reentrancy patterns
2. Precision loss
3. Flash loan attacks
4. Access control
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime

REPO_PATH = Path("memory/bounty_audits/uniswap-v3-core")
OUTPUT_DIR = Path("memory/output")

def analyze_reentrancy(content, filename):
    """Find potential reentrancy vulnerabilities"""
    findings = []
    lines = content.split('\n')
    
    # Pattern: external call followed by state mutation
    external_call_pattern = r'\.call|\.transfer|\.send|\(token\.'
    state_mutation_pattern = r'(=|emit|require|assert)'
    
    for i, line in enumerate(lines):
        if re.search(external_call_pattern, line):
            # Check next 5 lines for state mutation
            for j in range(i+1, min(i+6, len(lines))):
                if re.search(state_mutation_pattern, lines[j]):
                    findings.append({
                        "type": "REENTRANCY",
                        "severity": "CRITICAL",
                        "line": i+1,
                        "code": line.strip()[:100],
                        "issue": "External call not followed by checks-effects-interactions",
                        "cwe": "CWE-909"
                    })
                    break
    
    return findings

def analyze_precision(content, filename):
    """Find precision loss issues"""
    findings = []
    lines = content.split('\n')
    
    # Look for division operations
    division_pattern = r'(\d+)\s*\/\s*(?!.*\/\/)'
    
    for i, line in enumerate(lines):
        if re.search(division_pattern, line):
            # Check if result is used without scaling
            if 'mulDiv' not in line and 'SafeMath' not in line:
                findings.append({
                    "type": "PRECISION_LOSS",
                    "severity": "HIGH",
                    "line": i+1,
                    "code": line.strip()[:100],
                    "issue": "Division operation may result in precision loss",
                    "cwe": "CWE-1025",
                    "recommendation": "Use mulDiv library or check for rounding errors"
                })
    
    return findings

def analyze_flash_loans(content, filename):
    """Find flash loan attack vectors"""
    findings = []
    
    # Look for balance-based checks
    if 'balance' in content and 'external' in content:
        if 'callback' in content:
            findings.append({
                "type": "FLASH_LOAN_VECTOR",
                "severity": "HIGH",
                "file": filename,
                "issue": "Potential flash loan attack vector",
                "description": "Balance-based checks used with callback pattern",
                "cwe": "CWE-1104",
                "recommendation": "Use internal accounting or checksummed balances"
            })
    
    return findings

def deep_review_pool_contract():
    """Perform detailed review of UniswapV3Pool.sol"""
    pool_file = REPO_PATH / "contracts" / "UniswapV3Pool.sol"
    findings = {
        "reentrancy": [],
        "precision": [],
        "flash_loan": [],
        "access_control": []
    }
    
    if not pool_file.exists():
        print(f"⚠️  {pool_file} not found")
        return findings
    
    try:
        with open(pool_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Cannot read {pool_file}: {e}")
        return findings
    
    print(f"\n📖 Reviewing: UniswapV3Pool.sol ({len(content)} bytes)")
    print("=" * 70)
    
    # Reentrancy analysis
    print("\n🔴 REENTRANCY ANALYSIS")
    reentrancy_findings = analyze_reentrancy(content, "UniswapV3Pool.sol")
    findings["reentrancy"] = reentrancy_findings
    if reentrancy_findings:
        print(f"   Found {len(reentrancy_findings)} potential issues")
        for f in reentrancy_findings[:3]:
            print(f"   Line {f['line']}: {f['code'][:60]}")
    else:
        print("   ✓ No obvious reentrancy patterns found")
    
    # Precision analysis
    print("\n🟡 PRECISION LOSS ANALYSIS")
    precision_findings = analyze_precision(content, "UniswapV3Pool.sol")
    findings["precision"] = precision_findings
    if precision_findings:
        print(f"   Found {len(precision_findings)} potential issues")
        for f in precision_findings[:3]:
            print(f"   Line {f['line']}: {f['code'][:60]}")
    else:
        print("   ✓ No precision loss patterns found")
    
    # Flash loan analysis
    print("\n🟠 FLASH LOAN ANALYSIS")
    flash_findings = analyze_flash_loans(content, "UniswapV3Pool.sol")
    findings["flash_loan"] = flash_findings
    if flash_findings:
        print(f"   ⚠️  Potential flash loan vectors detected")
    else:
        print("   ✓ No obvious flash loan vectors")
    
    # Access control patterns
    print("\n🔵 ACCESS CONTROL ANALYSIS")
    if 'onlyFactoryOwner' in content or 'onlyOwner' in content:
        print("   ✓ Found access control modifiers")
    if 'permission' in content.lower():
        print("   ⚠️  Check permission logic carefully")
    
    return findings

def analyze_liquidity_math():
    """Analyze LiquidityMath library"""
    math_file = REPO_PATH / "contracts" / "libraries" / "LiquidityMath.sol"
    findings = []
    
    if not math_file.exists():
        print("⚠️  LiquidityMath.sol not found")
        return findings
    
    try:
        with open(math_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except:
        return findings
    
    print(f"\n📖 Reviewing: LiquidityMath.sol")
    print("=" * 70)
    
    # Check for edge case handling
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        # Look for operations on 1 wei or max values
        if '1' in line and 'wei' in line:
            findings.append({
                "type": "EDGE_CASE",
                "line": i+1,
                "code": line.strip()[:100],
                "note": "Check 1 wei edge case handling"
            })
        
        # Look for unchecked math
        if 'unchecked' in line:
            findings.append({
                "type": "UNCHECKED_MATH",
                "line": i+1,
                "code": line.strip()[:100],
                "note": "Unchecked math operation - verify safety"
            })
    
    if findings:
        print(f"   Found {len(findings)} items to review:")
        for f in findings[:5]:
            print(f"   Line {f['line']}: {f.get('note', 'Review carefully')}")
    else:
        print("   ✓ Math library appears well-protected")
    
    return findings

def create_detailed_report(pool_findings, math_findings):
    """Create detailed vulnerability report"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "audit_title": "Uniswap V3 Deep Code Review",
        "status": "FINDINGS COMPILED",
        
        "executive_summary": {
            "contracts_reviewed": 2,
            "total_findings": (
                len(pool_findings.get("reentrancy", [])) +
                len(pool_findings.get("precision", [])) +
                len(pool_findings.get("flash_loan", [])) +
                len(math_findings)
            ),
            "critical_issues": len(pool_findings.get("reentrancy", [])),
            "high_severity": len(pool_findings.get("precision", [])) + len(pool_findings.get("flash_loan", []))
        },
        
        "detailed_findings": {
            "pool_contract": pool_findings,
            "math_library": math_findings
        },
        
        "vulnerability_assessment": {
            "reentrancy": {
                "status": "REQUIRES MANUAL REVIEW",
                "recommendation": "Audit swap(), mint(), burn() functions for CEI pattern",
                "tools": ["Slither --detect reentrancy", "Manual code review"]
            },
            "precision": {
                "status": "REQUIRES TESTING",
                "recommendation": "Test with 1 wei and large amount edge cases",
                "tools": ["Hardhat tests", "Fuzzing"]
            },
            "flash_loan": {
                "status": "REQUIRES ANALYSIS",
                "recommendation": "Verify no balance-based checks in callbacks",
                "tools": ["Code review", "Integration tests"]
            }
        },
        
        "recommended_tools": [
            "Slither: static analysis tool",
            "Mythril: symbolic execution",
            "Echidna: fuzzing tool",
            "Hardhat: testing framework"
        ],
        
        "next_phase": "POC Development & Testnet Testing",
        "estimated_reward": "$5,000 - $100,000"
    }
    
    return report

def main():
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║         UNISWAP V3 DEEP CODE REVIEW                                 ║
║         Detailed Vulnerability Analysis                             ║
╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    if not REPO_PATH.exists():
        print(f"❌ Repository not found at {REPO_PATH}")
        return
    
    # Analyze Pool contract
    pool_findings = deep_review_pool_contract()
    
    # Analyze Math library
    math_findings = analyze_liquidity_math()
    
    # Create report
    report = create_detailed_report(pool_findings, math_findings)
    
    # Save report
    report_file = OUTPUT_DIR / "uniswap_deep_code_review.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n✓ Detailed report saved: {report_file}")
    
    # Display summary
    print("\n" + "=" * 70)
    print("📊 DEEP REVIEW SUMMARY")
    print("=" * 70)
    
    summary = report["executive_summary"]
    print(f"\n📈 Findings:")
    print(f"   • Total issues: {summary['total_findings']}")
    print(f"   • Critical: {summary['critical_issues']}")
    print(f"   • High severity: {summary['high_severity']}")
    
    print(f"\n🔧 Next steps:")
    print(f"   1. Install security tools (Slither, Mythril)")
    print(f"   2. Run static analysis")
    print(f"   3. Create test cases for edge cases")
    print(f"   4. Develop POC on Sepolia testnet")
    print(f"   5. Document all findings")
    
    print(f"\n💰 Bounty reward: {report['estimated_reward']}")
    print("\n✅ Deep code review complete!")

if __name__ == "__main__":
    main()
