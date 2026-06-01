"""
REAL-WORLD TASKS - Live Demonstration
======================================

Run this to see the full system in action:
- Meta path execution
- Browser automation (PRIMARY path with API)
- File creation
- Evidence logging
- Tool orchestration

Tasks are real and generate actual output files.
"""

import asyncio
import sys
import json
import os
from pathlib import Path
from datetime import datetime

# UTF-8 encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace') if hasattr(sys.stdout, 'reconfigure') else None
sys.path.insert(0, str(Path(__file__).parent))


async def task_1_analyze_directory():
    """TASK 1: Analyze project structure and create summary"""
    
    print("\n" + "="*80)
    print("TASK 1: Analyze Project Structure")
    print("="*80)
    
    from src.core.super_intelligent_ai import SuperIntelligentAI
    
    task = """
    Analyze the src/ directory structure in this project.
    Create a summary:
    1. List all Python modules found
    2. Count the total lines of code (estimate)
    3. Identify core components
    
    Then save the analysis to: memory/intelligence/project_analysis.md
    """
    
    print(f"\n📋 Task: {task.strip()}\n")
    
    ai = SuperIntelligentAI(use_meta_controller=True)
    
    result = await asyncio.wait_for(
        ai.execute_intelligent_task(task, use_meta_controller=True),
        timeout=120.0
    )
    
    print(f"\n✅ Result: {result.get('success', False)}")
    print(f"📄 Output:\n{str(result.get('output', ''))[:500]}...")
    
    # Check if file was created
    analysis_file = Path("memory/intelligence/project_analysis.md")
    if analysis_file.exists():
        print(f"\n✅ File created: {analysis_file}")
        print(f"   Size: {analysis_file.stat().st_size} bytes")
    
    return result


async def task_2_fetch_and_analyze_url():
    """TASK 2: Fetch and analyze a web page"""
    
    print("\n" + "="*80)
    print("TASK 2: Fetch and Analyze Web Page")
    print("="*80)
    
    from src.core.super_intelligent_ai import SuperIntelligentAI
    from tools.tools.implementations.simple_browser_tool import SimpleBrowserTool
    
    # Direct browser tool test first
    print("\n🌐 Testing browser.open_url adapter...")
    browser_tool = SimpleBrowserTool()
    
    browser_result = await browser_tool.execute(
        url="https://example.com",
        extract_text=True,
        max_length=500,
        use_browser=True  # Try PRIMARY (Playwright)
    )
    
    print(f"   ok: {browser_result['ok']}")
    print(f"   status_code: {browser_result['status_code']}")
    print(f"   title: {browser_result['title']}")
    print(f"   extracted: {len(browser_result.get('extracted', ''))} chars")
    
    # Now use Meta controller to do something with it
    task = """
    Use the browser.open_url tool to fetch https://www.w3schools.com/html/html_intro.asp
    
    Analyze the page and create a learning guide:
    1. What is the main topic?
    2. Extract 3-5 key points
    3. Save as: memory/intelligence/html_learning_guide.txt
    """
    
    print(f"\n📋 Task: Use browser tool in Meta path\n")
    
    ai = SuperIntelligentAI(use_meta_controller=True)
    
    result = await asyncio.wait_for(
        ai.execute_intelligent_task(task, use_meta_controller=True),
        timeout=120.0
    )
    
    print(f"\n✅ Result: {result.get('success', False)}")
    
    # Check if learning guide was created
    guide_file = Path("memory/intelligence/html_learning_guide.txt")
    if guide_file.exists():
        print(f"\n✅ File created: {guide_file}")
        with open(guide_file, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()[:300]
            print(f"   Content preview:\n{content}...")
    
    return result


async def task_3_create_report():
    """TASK 3: Create a comprehensive report"""
    
    print("\n" + "="*80)
    print("TASK 3: Create Comprehensive Report")
    print("="*80)
    
    from src.core.super_intelligent_ai import SuperIntelligentAI
    
    task = """
    Create a comprehensive report about this AI system.
    
    Include:
    1. System capabilities overview
    2. Main components (Meta path, Tool registry, Browser automation)
    3. How browser adapter pattern works
    4. Example usage scenarios
    
    Format as markdown and save to: memory/intelligence/system_report.md
    """
    
    print(f"\n📋 Task: Generate system report\n")
    
    ai = SuperIntelligentAI(use_meta_controller=True)
    
    result = await asyncio.wait_for(
        ai.execute_intelligent_task(task, use_meta_controller=True),
        timeout=120.0
    )
    
    print(f"\n✅ Result: {result.get('success', False)}")
    
    # Check file
    report_file = Path("memory/intelligence/system_report.md")
    if report_file.exists():
        print(f"\n✅ File created: {report_file}")
        print(f"   Size: {report_file.stat().st_size} bytes")
        with open(report_file, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()[:300]
            print(f"   Preview:\n{content}...")
    
    return result


async def task_4_check_evidence():
    """TASK 4: Review evidence logging"""
    
    print("\n" + "="*80)
    print("TASK 4: Evidence Logging Analysis")
    print("="*80)
    
    evidence_file = Path("memory/intelligence/meta_evidence.jsonl")
    
    if not evidence_file.exists():
        print("❌ Evidence file not found")
        return
    
    # Count events by type
    event_counts = {}
    total_events = 0
    
    with open(evidence_file, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            if line.strip():
                try:
                    event = json.loads(line)
                    event_type = event.get('event_type', 'unknown')
                    event_counts[event_type] = event_counts.get(event_type, 0) + 1
                    total_events += 1
                except json.JSONDecodeError:
                    pass
    
    print(f"\n📊 Evidence Statistics:")
    print(f"   Total events: {total_events}")
    print(f"\n   Event breakdown:")
    for event_type, count in sorted(event_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"     • {event_type}: {count}")
    
    # Show recent goals
    goals = {}
    with open(evidence_file, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            if line.strip():
                try:
                    event = json.loads(line)
                    if event.get('event_type') == 'goal_completed':
                        goal_id = event.get('data', {}).get('goal_id')
                        status = event.get('data', {}).get('status')
                        if goal_id and status:
                            goals[goal_id] = status
                except json.JSONDecodeError:
                    pass
    
    if goals:
        print(f"\n   Recent completed goals:")
        for goal_id, status in list(goals.items())[-5:]:
            print(f"     • {goal_id}: {status}")


async def main():
    """Run all real-world tasks"""
    
    print("\n" + "="*80)
    print("PROJECT-S REAL-WORLD TASK EXECUTION")
    print("="*80)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nThis demonstration will:")
    print("  • Execute tasks using the Meta controller")
    print("  • Use browser automation (Playwright + API or HTTP fallback)")
    print("  • Create files in memory/intelligence/")
    print("  • Log all evidence to meta_evidence.jsonl")
    print("  • Show tool orchestration in action")
    
    try:
        # Task 1: Analyze directory
        print("\n" + "🔄 "*40)
        await task_1_analyze_directory()
        
        # Task 2: Browser + Web analysis
        print("\n" + "🔄 "*40)
        await task_2_fetch_and_analyze_url()
        
        # Task 3: Create report
        print("\n" + "🔄 "*40)
        await task_3_create_report()
        
        # Task 4: Review evidence
        print("\n" + "🔄 "*40)
        await task_4_check_evidence()
        
        # Summary
        print("\n" + "="*80)
        print("✅ ALL REAL-WORLD TASKS COMPLETED")
        print("="*80)
        print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # List created files
        print("\n📁 Created Files:")
        output_dir = Path("memory/intelligence")
        if output_dir.exists():
            for f in sorted(output_dir.glob("*.md")) + sorted(output_dir.glob("*.txt")):
                size = f.stat().st_size
                print(f"   • {f.name} ({size} bytes)")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
