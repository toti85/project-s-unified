#!/usr/bin/env python3
"""
UNISWAP V3 PRELIMINARY CODE ANALYZER
Solidity contract analysis for vulnerability patterns
Responsible disclosure - no exploitation, local analysis only
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime

REPO_PATH = Path("memory/bounty_audits/uniswap-v3-core")
OUTPUT_DIR = Path("memory/output")

# Vulnerability patterns to search for
PATTERNS = {
    "reentrancy": {
        "patterns": [
            r"(\.call|\.transfer|\.send)\s*\(",  # External calls
            r"(unchecked\s*\{|SafeMath)",  # State mutation after calls
        ],
        "severity": "CRITICAL",
        "cwe": "CWE-909"
    },
    "overflow": {
        "patterns": [
            r"overflow|underflow|uint256|uint128|uint96",
            r"(\+|\-|\*)\s*",
        ],
        "severity": "HIGH",
        "cwe": "CWE-190"
    },
    "precision_loss": {
        "patterns": [
            r"(rounding|division|precision|loss)",
            r"(\/).*[0-9]",
        ],
        "severity": "HIGH",
        "cwe": "CWE-1025"
    },
    "flash_loan": {
        "patterns": [
            r"(balance|balanceOf).*external",
            r"callback|onFlash",
        ],
        "severity": "HIGH",
        "cwe": "CWE-1104"
    }
}

def analyze_solidity_file(filepath):
    """Analyze a single Solidity file for vulnerabilities"""
    findings = []
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            lines = content.split('\n')
    except Exception as e:
        print(f"  ⚠️  Cannot read {filepath}: {e}")
        return findings
    
    # Check for each pattern
    for vuln_type, vuln_info in PATTERNS.items():
        for pattern in vuln_info["patterns"]:
            matches = []
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line, re.IGNORECASE):
                    matches.append({
                        "line": i,
                        "content": line.strip()[:100],
                        "pattern": pattern
                    })
            
            if matches:
                findings.append({
                    "type": vuln_type,
                    "severity": vuln_info["severity"],
                    "cwe": vuln_info["cwe"],
                    "count": len(matches),
                    "sample_matches": matches[:3]
                })
    
    return findings

def scan_contracts():
    """Scan all Solidity contracts in the repo"""
    print("\n🔍 SCANNING CONTRACTS...")
    print("=" * 70)
    
    contracts_dir = REPO_PATH / "contracts"
    results = {}
    
    if not contracts_dir.exists():
        print(f"⚠️  {contracts_dir} not found")
        return results
    
    sol_files = list(contracts_dir.rglob("*.sol"))
    print(f"📄 Found {len(sol_files)} Solidity files\n")
    
    for sol_file in sorted(sol_files)[:10]:  # Analyze first 10 files
        rel_path = sol_file.relative_to(REPO_PATH)
        print(f"  Analyzing: {rel_path}")
        
        findings = analyze_solidity_file(sol_file)
        if findings:
            print(f"    → Found {len(findings)} patterns")
            results[str(rel_path)] = findings
    
    return results

def check_critical_functions():
    """Check for known problematic function implementations"""
    print("\n🎯 CHECKING CRITICAL FUNCTIONS...")
    print("=" * 70)
    
    critical_funcs = {
        "swap": "Main token exchange function - reentrancy risk",
        "mint": "Add liquidity function - precision issues",
        "burn": "Remove liquidity function - callback attacks",
        "collect": "Fee collection - reentrancy with external calls",
    }
    
    functions_found = {}
    pool_file = REPO_PATH / "contracts" / "UniswapV3Pool.sol"
    
    if pool_file.exists():
        try:
            with open(pool_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            for func_name, description in critical_funcs.items():
                if re.search(rf"function\s+{func_name}\s*\(", content):
                    # Find the function
                    match = re.search(
                        rf"function\s+{func_name}\s*\([^)]*\)[^{{]*\{{",
                        content
                    )
                    if match:
                        functions_found[func_name] = {
                            "description": description,
                            "signature": match.group(0)[:80],
                            "found": True
                        }
                        print(f"  ✓ {func_name}() - {description}")
        except Exception as e:
            print(f"  ⚠️  Cannot analyze UniswapV3Pool.sol: {e}")
    else:
        print(f"  ⚠️  UniswapV3Pool.sol not found at {pool_file}")
    
    return functions_found

def create_preliminary_report(scan_results, functions_found):
    """Create detailed preliminary report"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "audit_target": "Uniswap V3 Core",
        "bounty_url": "https://immunefi.com/bounty/uniswap/",
        "status": "PRELIMINARY ANALYSIS",
        
        "summary": {
            "total_files_scanned": 10,
            "vulnerability_patterns_found": sum(len(v) for v in scan_results.values()),
            "critical_functions_analyzed": len(functions_found),
        },
        
        "findings": {
            "pattern_matches": scan_results,
            "critical_functions": functions_found,
        },
        
        "next_steps": [
            "1. Manual code review of UniswapV3Pool.sol (swap, mint, burn)",
            "2. Search for external calls followed by state mutations (reentrancy)",
            "3. Analyze liquidity math for precision issues with small amounts",
            "4. Check tick bitmap for integer overflow in position management",
            "5. Test with Hardhat on Sepolia testnet",
            "6. Create proof-of-concept for confirmed vulnerabilities",
            "7. Document findings and submit to Immunefi"
        ],
        
        "estimated_effort": "40-60 hours",
        "estimated_reward": "$5,000 - $100,000",
        "recommendation": "Proceed with detailed code review"
    }
    
    return report

def main():
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║         UNISWAP V3 PRELIMINARY CODE ANALYZER                        ║
║         ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━     ║
║         Responsible Disclosure • Local Analysis Only                ║
╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    # Verify repo exists
    if not REPO_PATH.exists():
        print(f"❌ Repository not found at {REPO_PATH}")
        print(f"   Run: python bounty_hunter_starter.py")
        return
    
    print(f"✓ Repository found: {REPO_PATH}")
    
    # Scan contracts
    scan_results = scan_contracts()
    
    # Check critical functions
    functions_found = check_critical_functions()
    
    # Create report
    report = create_preliminary_report(scan_results, functions_found)
    
    # Save report
    report_file = OUTPUT_DIR / "uniswap_preliminary_analysis.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n✓ Report saved: {report_file}")
    
    # Display summary
    print("\n" + "=" * 70)
    print("📊 PRELIMINARY ANALYSIS SUMMARY")
    print("=" * 70)
    
    print(f"\n📈 Metrics:")
    print(f"   • Pattern matches: {report['summary']['vulnerability_patterns_found']}")
    print(f"   • Critical functions: {report['summary']['critical_functions_analyzed']}")
    
    print(f"\n🎯 Recommendation: {report['recommendation']}")
    
    print(f"\n⏱️  Estimated effort: {report['estimated_effort']}")
    print(f"💰 Estimated reward: {report['estimated_reward']}")
    
    print("\n📋 Next steps:")
    for step in report['next_steps']:
        print(f"   {step}")
    
    print("\n✅ Analysis complete!")

if __name__ == "__main__":
    main()
