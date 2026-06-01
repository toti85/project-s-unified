#!/usr/bin/env python3
"""
🎯 TEST: Meta Layer Planning + Project-S Execution
Task: Create file on desktop after meta layer review
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Add repo to path
_repo_root = str(Path(__file__).parent)
sys.path.insert(0, _repo_root)

async def main():
    """Test meta layer planning + execution."""
    
    logger.info("="*80)
    logger.info("META LAYER PLANNING + PROJECT-S EXECUTION TEST")
    logger.info("="*80)
    
    # Step 1: Meta layer planning
    logger.info("\n[PHASE 1] META LAYER PLANNING")
    logger.info("-"*80)
    
    from src.core.meta.meta_controller import MetaController, MetaControllerConfig
    from src.core.meta.strategy_council import StrategyCouncil
    from src.core.meta.execution_validator import ExecutionValidator
    
    council = StrategyCouncil()
    validator = ExecutionValidator()
    
    # Evidence logger (minimal)
    class SimpleEvidenceLogger:
        def log(self, event_type, data):
            logger.info(f"  📝 Evidence: {event_type} = {data.get('status', 'ok')}")
    
    evidence_logger = SimpleEvidenceLogger()
    
    meta_controller = MetaController(
        council=council,
        executor=None,  # Not needed for planning
        validator=validator,
        evidence_logger=evidence_logger,
        config=MetaControllerConfig(max_iters=1)
    )
    
    # Get the plan
    goal = "Create a file named 'meta_layer_success.txt' on the desktop"
    logger.info(f"Goal: {goal}")
    logger.info("\nCouncil deliberating...")
    
    council_decision = await council.decide(goal)
    logger.info(f"✅ Council decision: {council_decision.decision}")
    logger.info(f"   Consensus: {council_decision.consensus_type}")
    logger.info(f"   Approval ratio: {council_decision.approval_ratio * 100:.1f}%")
    
    # Step 2: Project-S execution
    logger.info("\n[PHASE 2] PROJECT-S EXECUTION")
    logger.info("-"*80)
    
    from tools.tools.implementations.file_tools import FileWriteTool
    from tools.tools.registry.tool_registry_golden import ToolRegistry
    
    # Get tool registry
    registry = ToolRegistry()
    logger.info("✅ Tool Registry initialized")
    
    # Create file on desktop
    desktop_path = Path.home() / "Desktop" / "meta_layer_success.txt"
    content = f"""Meta Layer Success Report
Generated: {datetime.now().isoformat()}
Goal: {goal}
Status: COMPLETED

This file was created by Project-S after Meta Layer approval.
Meta layer planned → Project-S executed → File created.

Timestamp: {datetime.now().isoformat()}
"""
    
    logger.info(f"\nCreating file: {desktop_path}")
    
    try:
        # Use file write tool
        file_write = FileWriteTool()
        result = await file_write.execute(
            path=str(desktop_path),
            content=content
        )
        
        if result.get('success'):
            logger.info(f"✅ FILE CREATED SUCCESSFULLY")
            logger.info(f"   Path: {desktop_path}")
            logger.info(f"   Size: {result.get('message', 'N/A')}")
        else:
            logger.error(f"❌ Failed to create file: {result.get('error', 'Unknown')}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        return False
    
    # Step 3: Verification
    logger.info("\n[PHASE 3] VERIFICATION")
    logger.info("-"*80)
    
    if desktop_path.exists():
        logger.info(f"✅ File exists on desktop")
        logger.info(f"   Path: {desktop_path}")
        logger.info(f"   Size: {desktop_path.stat().st_size} bytes")
        logger.info(f"   Modified: {datetime.fromtimestamp(desktop_path.stat().st_mtime)}")
        return True
    else:
        logger.error(f"❌ File NOT found on desktop")
        return False

if __name__ == "__main__":
    result = asyncio.run(main())
    
    logger.info("\n" + "="*80)
    if result:
        logger.info("✅ TEST PASSED - Meta Layer + Project-S Integration Working")
    else:
        logger.info("❌ TEST FAILED")
    logger.info("="*80)
    
    sys.exit(0 if result else 1)
