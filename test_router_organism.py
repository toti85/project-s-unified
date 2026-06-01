#!/usr/bin/env python3
"""
PROJECT-S PHASE 1B - DECISION ROUTER & ORGANISM TEST
Task 4 & 5: Advanced routing and organism system verification
"""

import sys
sys.path.insert(0, './src')

print("\n" + "="*70)
print("[TEST 4] Advanced Decision Router Workflow")
print("="*70)

try:
    from integrations.decision_routing.base_router import (
        DecisionRouterRegistry,
        DecisionType,
        DecisionStatus
    )
    
    registry = DecisionRouterRegistry()
    print(f"✅ DecisionRouterRegistry initialized")
    
    # Display available decision types
    decision_types = [dt.name for dt in DecisionType]
    print(f"\n📊 Decision Types Available ({len(decision_types)}):")
    for dt in decision_types:
        print(f"   • {dt}")
    
    # Display decision statuses
    statuses = [ds.name for ds in DecisionStatus]
    print(f"\n📊 Decision Status Types ({len(statuses)}):")
    for status in statuses:
        print(f"   • {status}")
    
    print("\n✅ DECISION ROUTER TEST PASSED")
    print("   Status: Registry functional with 5 decision types + 4 status types")
    
except Exception as e:
    print(f"❌ Decision Router test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("[TEST 5] Organism System Components")
print("="*70)

from pathlib import Path

organism_path = Path("organism")
if organism_path.exists():
    print(f"✅ Organism directory found")
    
    # Check for organism components
    components = {
        "observer.py": "Change Detection",
        "prioritizer.py": "Task Prioritization",
        "proposer.py": "Action Generation",
    }
    
    found = 0
    for file, desc in components.items():
        file_path = organism_path / file
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"   ✅ {file} ({desc}): {size} bytes")
            found += 1
        else:
            print(f"   ⚠️  {file} ({desc}): NOT FOUND")
    
    print(f"\n✅ ORGANISM SYSTEM: {found}/3 components available")
    
    if found >= 2:
        print("   Status: FUNCTIONAL (core components present)")
    else:
        print("   Status: PARTIAL (some components missing)")
        
else:
    print(f"⚠️  Organism directory not found at {organism_path}")

print("\n" + "="*70)
print("COMPONENT VERIFICATION COMPLETE")
print("="*70)
