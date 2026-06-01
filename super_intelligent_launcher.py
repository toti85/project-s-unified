#!/usr/bin/env python3
"""
Super Intelligent AI - Entry Point
"""

import asyncio
import sys
from pathlib import Path

# Setup paths for super_core structure
repo_root = Path(__file__).parent
sys.path.insert(0, str(repo_root / "src"))
sys.path.insert(0, str(repo_root))

from core.super_intelligent_ai import SuperIntelligentAI


async def main():
    """Initialize SuperIntelligentAI"""
    system = SuperIntelligentAI()
    print("SuperIntelligentAI initialized.")
    
    # Smoke test mode
    if len(sys.argv) > 1 and sys.argv[1] == "--smoke":
        try:
            # Check internal state without external calls
            status = system.get_intelligence_status()
            
            # Verify core components initialized
            assert status is not None, "Status unavailable"
            assert "intelligence_metrics" in status, "Missing metrics"
            assert "execution_stats" in status, "Missing stats"
            
            print("PASS")
            return 0
        except Exception as e:
            print(f"FAIL: {e}")
            return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
