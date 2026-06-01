#!/usr/bin/env python3
"""Quick test of AgentLoop import and initialization"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

print("[1] Testing AgentLoop import...")
try:
    from core.agent.agent_loop import AgentLoop
    print("    ✓ AgentLoop imported successfully")
except Exception as e:
    print(f"    ✗ Failed to import: {e}")
    sys.exit(1)

print("[2] Creating AgentLoop instance...")
try:
    agent = AgentLoop()
    print(f"    ✓ AgentLoop instance created")
    print(f"    - Monitoring: {agent.inbox_dir}")
    print(f"    - Logging to: {Path(__file__).parent / 'logs' / 'agent_loop.log'}")
except Exception as e:
    print(f"    ✗ Failed to initialize: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("[3] Checking components...")
try:
    print(f"    - AI Client: {'✓' if agent.ai_client else '✗'}")
    print(f"    - Cognitive Core: {'✓' if agent.cognitive_core else '✗'}")
    print(f"    - Tool Orchestrator: {'✓' if agent.tool_orchestrator else '✗'}")
    print(f"    - Evaluator: {'✓' if agent.evaluator else '✗'}")
except Exception as e:
    print(f"    ✗ Component check failed: {e}")

print("")
print("[RESULT] AgentLoop is ready for async.run(agent_loop.run())")
