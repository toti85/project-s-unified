#!/usr/bin/env python
"""Demonstrate file editing through direct tool access."""

import asyncio
from tools.tools.implementations.file_tools import FileWriteTool, FileReadTool

async def demo_editing():
    """Demo file editing capabilities."""
    
    print("="*80)
    print("FILE EDITING DEMO")
    print("="*80)
    print()
    
    file_path = "demo_edit.txt"
    
    # Step 1: Create initial file
    print("1. CREATING FILE")
    print("-" * 80)
    writer = FileWriteTool()
    
    initial_content = """Project Status Report
=====================

Project: AI System
Date: 2026-01-16
Status: Development

Features:
- Orchestrator: FIXED
- Mock tools: REMOVED
- Meta layer: ENABLED
"""
    
    result = await writer.execute(path=file_path, content=initial_content)
    print(f"Created: {result.get('path')}")
    print(f"Size: {result.get('size')} bytes")
    print()
    
    # Step 2: Read the file
    print("2. READING FILE")
    print("-" * 80)
    reader = FileReadTool()
    read_result = await reader.execute(path=file_path)
    print(f"Content:\n{read_result.get('content', '')[:300]}")
    print()
    
    # Step 3: Edit/Append to file
    print("3. EDITING FILE (APPEND)")
    print("-" * 80)
    updated_content = initial_content + """

Updates:
- File operations: WORKING
- Create: YES
- Edit: YES
- Browser automation: YES

System Status: PRODUCTION READY
"""
    
    edit_result = await writer.execute(path=file_path, content=updated_content)
    print(f"Updated: {edit_result.get('path')}")
    print(f"New size: {edit_result.get('size')} bytes")
    print()
    
    # Step 4: Verify changes
    print("4. VERIFYING CHANGES")
    print("-" * 80)
    verify_result = await reader.execute(path=file_path)
    content = verify_result.get('content', '')
    print(f"File now contains {len(content)} characters")
    print(f"Last line: {content.split(chr(10))[-1]}")
    print()
    
    print("="*80)
    print("File operations demo complete!")
    print(f"Demo file: {file_path}")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(demo_editing())
