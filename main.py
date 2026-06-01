#!/usr/bin/env python3
"""
Project-S Unified Main Entry Point
-----------------------------------
Single consolidated codebase running from project_s_super_core/
Built on True Golden Age foundations (929+959+585 lines)

- Clean modern architecture
- Smart Tool Orchestration 
- Enhanced Workflow Engine with LangGraph
- Advanced Decision Routing
- Multi-Model AI Integration
- Strategic AI Overlay (non-invasive)
"""

import logging
import asyncio
import sys
import time
from pathlib import Path
from datetime import datetime

# Load .env file so API keys (OPENROUTER_API_KEY etc.) are in os.environ
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=Path(__file__).parent / '.env', override=False)
except ImportError:
    pass  # python-dotenv not installed, rely on shell environment

# **FIX FOR WINDOWS UNICODE ISSUES**: Configure stdout encoding for emoji  
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except:
        pass

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Import AgentLoop for autonomous task processing
from core.agent.agent_loop import AgentLoop

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def display_banner():
    """Display the Project-S unified banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║              PROJECT-S UNIFIED SYSTEM                      ║
║        Single Consolidated Codebase (project_s_super_core)  ║
╠══════════════════════════════════════════════════════════════╣
║  🏛️  Golden Age Foundation (929+959+585 lines)            ║
║  🧠  Smart Tool Orchestrator (929 lines)                  ║
║  ⚡  Enhanced Workflow Engine (959 lines)                ║  
║  🎯  Advanced Decision Router (585 lines)                ║
║  🤖  Multi-Model AI Integration                          ║
║  📊  Learning System (404K+ events)                      ║
║  🎞️  Strategic AI Overlay                                ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

async def initialize_golden_age_components():
    """Initialize the True Golden Age components."""
    startup_start = time.time()
    logger.info("🏛️ Initializing True Golden Age components...")
    
    components_status = {
        "smart_orchestrator": False,
        "workflow_engine": False, 
        "decision_router": False,
        "multi_model_client": False,
        "cognitive_core": False
    }
    
    # Try to initialize Smart Tool Orchestrator
    try:
        from tools.registry import SmartToolOrchestrator, SMART_ORCHESTRATOR_AVAILABLE
        if SMART_ORCHESTRATOR_AVAILABLE:
            orchestrator = SmartToolOrchestrator()
            components_status["smart_orchestrator"] = True
            logger.info("✅ Smart Tool Orchestrator (929 lines) - LOADED")
        else:
            logger.warning("⚠️  Smart Tool Orchestrator - NOT AVAILABLE")
    except Exception as e:
        logger.debug(f"Smart Tool Orchestrator init info: {e}")
    
    # Try to initialize Cognitive Core  
    try:
        from core.cognitive import CognitiveCore
        cognitive_core = CognitiveCore()
        components_status["cognitive_core"] = True
        logger.info("✅ Cognitive Core (fixed version) - LOADED")
    except Exception as e:
        logger.debug(f"Cognitive Core init info: {e}")
    
    # Try to initialize Workflow Engine
    try:
        from core.orchestration import WORKFLOW_ENGINE_AVAILABLE
        if WORKFLOW_ENGINE_AVAILABLE:
            components_status["workflow_engine"] = True
            logger.info("✅ Enhanced Workflow Engine (959 lines) - LOADED")
        else:
            logger.debug("Workflow Engine - NOT AVAILABLE")
    except Exception as e:
        logger.debug(f"Workflow Engine init info: {e}")
    
    # Try to initialize Decision Router
    try:
        from integrations.decision_routing.base_router import DecisionRouterRegistry
        registry = DecisionRouterRegistry()
        components_status["decision_router"] = True
        logger.info("✅ Advanced Decision Router (585 lines) - LOADED")
    except Exception as e:
        logger.debug(f"Decision Router init info: {e}")
        
    # Try to initialize Multi-Model Client
    try:
        from integrations.ai_models.multi_model_ai_client import AIClient
        client = AIClient()
        models = client.list_available_models()
        components_status["multi_model_client"] = True
        logger.info(f"✅ Multi-Model AI Client - LOADED ({len(models)} models available)")
    except Exception as e:
        logger.debug(f"Multi-Model Client init info: {e}")
    
    # Summary
    loaded_count = sum(components_status.values())
    total_count = len(components_status)
    startup_time = time.time() - startup_start
    
    logger.info(f"🎯 Golden Age Components Status: {loaded_count}/{total_count} loaded")
    
    if loaded_count == total_count:
        logger.info("🎉 ALL True Golden Age components successfully loaded!")
        logger.info(f"⏱️  Startup time: {startup_time:.2f} seconds")
        return True
    elif loaded_count > 0:
        logger.info(f"⚡ Partial Golden Age system available ({loaded_count}/{total_count} components)")
        logger.info(f"⏱️  Startup time: {startup_time:.2f} seconds")
        return True
    else:
        logger.error("💥 No Golden Age components could be loaded")
        return False

async def main():
    """Main entry point."""
    try:
        display_banner()
        logger.info("🚀 Starting Project-S Unified System...")
        logger.info(f"📂 Working directory: {Path.cwd()}")
        
        # Initialize components
        success = await initialize_golden_age_components()
        
        if success:
            logger.info("✅ Project-S system initialization successful!")
            
            # Initialize Knowledge Layer
            try:
                from knowledge.knowledge_manager import KnowledgeManager
                km = KnowledgeManager()
                health = km.health_check()
                if health["state_readable"]:
                    km.update_state("meta.last_startup", datetime.now().isoformat())
                    logger.info(f"✅ Knowledge Layer initialized (state: {km.get_state('system.status')})")
                else:
                    logger.warning("⚠️  Knowledge Layer: state file not readable")
            except Exception as e:
                logger.warning(f"⚠️  Knowledge Layer initialization failed: {e}")
            
            logger.info("🎬 System ready for operations")
            
            # Show active status
            try:
                from integrations.ai_models.multi_model_ai_client import AIClient
                client = AIClient()
                models = client.list_available_models()
                providers = set(m.get("provider") for m in models)
                logger.info(f"📊 Available providers: {', '.join(sorted(providers))}")
                logger.info(f"📊 Available models: {len(models)}")
            except:
                pass
            
            # ════════════════════════════════════════════════════════════════
            # START AUTONOMOUS AGENT LOOP
            # ════════════════════════════════════════════════════════════════
            logger.info("🤖 Starting Autonomous Agent Loop...")
            logger.info("📂 Agent will monitor tasks/inbox/ every 5 seconds for .txt files")
            
            agent_loop = AgentLoop()
            await agent_loop.run()
            
            return 0
        else:
            logger.warning("⚠️  System partial initialization - some components unavailable")
            return 1
            
    except KeyboardInterrupt:
        logger.info("\n👋 System shutdown requested")
        return 130
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
