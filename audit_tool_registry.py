#!/usr/bin/env python3
"""Audit tool registry for ghost tools"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

print("=" * 70)
print("TASK 1F: TOOL REGISTRY AUDIT")
print("=" * 70)

try:
    from core.tools.tool_registry_golden import ToolRegistry
    
    registry = ToolRegistry()
    
    print(f"\n📊 REGISTERED TOOLS: {len(registry.tools)}\n")
    
    # List all registered tool instances
    for name in sorted(registry.tools.keys()):
        tool = registry.tools[name]
        category = getattr(tool, 'category', 'unknown')
        print(f"  ✅ {name:40} (category: {category})")
    
    # Check for ghost tools (known issues)
    print(f"\n🔍 GHOST TOOL DETECTION:\n")
    
    ghost_tools = ["general_assistant", "browser_automation"]
    found_ghosts = []
    
    for ghost in ghost_tools:
        if ghost in registry.tools:
            print(f"  ❌ {ghost:40} - FOUND (should be removed)")
            found_ghosts.append(ghost)
        else:
            print(f"  ✅ {ghost:40} - not found (good)")
    
    print(f"\n{'⚠️  GHOST TOOLS FOUND: ' + str(len(found_ghosts)) if found_ghosts else '✅ NO GHOST TOOLS DETECTED'}")
    
    if found_ghosts:
        print(f"   Remove these tools:")
        for ghost in found_ghosts:
            print(f"   - {ghost}")
    
    # Summary
    print(f"\n📈 CATEGORIES:")
    for category, tools in sorted(registry.categories.items()):
        print(f"  • {category}: {', '.join(sorted(tools))}")
    
    print("\n" + "=" * 70)
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
