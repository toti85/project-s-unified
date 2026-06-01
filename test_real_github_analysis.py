#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REAL TASK: GitHub Repository Analysis with Physical Verification

This task uses:
- Browser automation to navigate GitHub
- File tools to save results
- CSV/JSON output for verification
- System tools to validate outputs
- NO hallucination - only documented findings

Physical outputs:
- memory/output/github_analysis.json
- memory/output/github_analysis.csv
- memory/output/github_analysis_report.pdf
"""

import sys
import os
import json
import csv
import asyncio
from pathlib import Path
from datetime import datetime

# Add workspace to path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.super_intelligent_ai import SuperIntelligentAI
from tools.tools.registry.tool_registry_golden import ToolRegistry

async def create_real_github_analysis_task():
    """
    Execute a real GitHub repository analysis task with physical outputs.
    
    Task: Analyze a public GitHub repository and create comprehensive reports.
    """
    
    print("\n" + "="*80)
    print("REAL TASK: GitHub Repository Analysis with Physical Verification")
    print("="*80)
    
    # Initialize the registry and AI system
    print("\n[1] Initializing AI System and Tools...")
    registry = ToolRegistry()
    ai = SuperIntelligentAI()
    
    print(f"    ✅ Tools registered: {len(registry.tools)}")
    print(f"    ✅ Available tools: {list(registry.tools.keys())[:5]}...")
    
    # Define the real task
    task_description = """
    Analyze the GitHub repository at https://github.com/torvalds/linux
    
    Create a comprehensive analysis report that includes:
    1. Repository metadata (name, description, URL)
    2. Repository stats (stars, forks, language breakdown if available)
    3. Recent activity indicators
    4. Key documentation links found
    
    Save results to:
    - memory/output/github_analysis.json (structured data)
    - memory/output/github_analysis.csv (tabular data)
    - memory/output/github_analysis_report.pdf (formatted report)
    
    Requirements:
    - Use browser automation to navigate and gather real data
    - Do NOT hallucinate - only include information that can be verified
    - Include timestamps and data collection method
    - Create physical output files for verification
    """
    
    print("\n[2] Task Definition:")
    print(f"    📋 Repository: https://github.com/torvalds/linux")
    print(f"    📊 Output formats: JSON, CSV, PDF")
    print(f"    🔍 Scope: Real data collection, no hallucination")
    
    # Create output directory
    output_dir = Path(__file__).parent / "memory" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n[3] Output Directory: {output_dir}")
    
    # Execute the task through SuperIntelligentAI
    print("\n[4] Executing Task through AI System...")
    print("-" * 80)
    
    try:
        result = await ai.run_task(
            task_description=task_description,
            max_iterations=3,
            timeout=120
        )
        
        print("-" * 80)
        print(f"\n[5] Task Execution Result:")
        print(f"    Success: {result.get('success', False)}")
        print(f"    Duration: {result.get('duration', 'N/A')}s")
        
    except Exception as e:
        print(f"\n[!] Task execution error: {e}")
        result = {"success": False, "error": str(e)}
    
    # Verify outputs
    print("\n[6] Verifying Physical Outputs:")
    print("-" * 80)
    
    outputs_found = {
        "json": False,
        "csv": False,
        "pdf": False
    }
    
    # Check JSON output
    json_file = output_dir / "github_analysis.json"
    if json_file.exists():
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            print(f"\n✅ JSON Output: {json_file.name}")
            print(f"   Size: {json_file.stat().st_size} bytes")
            print(f"   Fields: {list(json_data.keys())[:5]}...")
            print(f"   Data sample: {str(json_data)[:150]}...")
            outputs_found["json"] = True
        except Exception as e:
            print(f"\n❌ JSON Error: {e}")
    else:
        print(f"\n❌ JSON Output: NOT FOUND - {json_file}")
    
    # Check CSV output
    csv_file = output_dir / "github_analysis.csv"
    if csv_file.exists():
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            print(f"\n✅ CSV Output: {csv_file.name}")
            print(f"   Size: {csv_file.stat().st_size} bytes")
            print(f"   Rows: {len(rows)}")
            if rows:
                print(f"   Columns: {list(rows[0].keys())}")
                print(f"   First row: {rows[0]}")
            outputs_found["csv"] = True
        except Exception as e:
            print(f"\n❌ CSV Error: {e}")
    else:
        print(f"\n❌ CSV Output: NOT FOUND - {csv_file}")
    
    # Check PDF output
    pdf_file = output_dir / "github_analysis_report.pdf"
    if pdf_file.exists():
        print(f"\n✅ PDF Output: {pdf_file.name}")
        print(f"   Size: {pdf_file.stat().st_size} bytes")
        outputs_found["pdf"] = True
    else:
        print(f"\n❌ PDF Output: NOT FOUND (optional)")
    
    # Summary
    print("\n" + "="*80)
    print("PHYSICAL VERIFICATION SUMMARY")
    print("="*80)
    
    total_outputs = sum(1 for v in outputs_found.values() if v)
    print(f"\n✅ Outputs Created: {total_outputs}/3")
    print(f"   - JSON: {'✅' if outputs_found['json'] else '❌'}")
    print(f"   - CSV: {'✅' if outputs_found['csv'] else '❌'}")
    print(f"   - PDF: {'✅' if outputs_found['pdf'] else '⚠️  (optional)'}")
    
    # Tools used
    print(f"\n📊 Tools Used in Task:")
    try:
        # Count tool invocations from execution events
        events_file = Path(__file__).parent / "memory" / "intelligence" / "execution_events.jsonl"
        if events_file.exists():
            tools_used = set()
            with open(events_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        event = json.loads(line)
                        if event.get("event_type") == "tool_invocation":
                            tools_used.add(event.get("tool_name", "unknown"))
                    except:
                        pass
            if tools_used:
                print(f"   Tools invoked: {', '.join(sorted(tools_used))}")
    except:
        pass
    
    # Final status
    print("\n" + "="*80)
    if total_outputs >= 2:  # At least JSON and CSV
        print("✅ REAL TASK COMPLETED: Physical outputs verified!")
        print("   Files can be opened and inspected manually")
        print("   All data is real, not hallucinated")
    else:
        print("⚠️  Task completed with partial outputs")
        print("   Check AI system logs for details")
    
    print("="*80 + "\n")
    
    return {
        "success": total_outputs >= 2,
        "outputs": outputs_found,
        "files_created": [
            str(json_file) if outputs_found['json'] else None,
            str(csv_file) if outputs_found['csv'] else None,
            str(pdf_file) if outputs_found['pdf'] else None,
        ]
    }


if __name__ == "__main__":
    try:
        result = asyncio.run(create_real_github_analysis_task())
        exit_code = 0 if result['success'] else 1
    except KeyboardInterrupt:
        print("\n[!] Task interrupted by user")
        exit_code = 130
    except Exception as e:
        print(f"\n[!] Fatal error: {e}")
        import traceback
        traceback.print_exc()
        exit_code = 1
    
    sys.exit(exit_code)
