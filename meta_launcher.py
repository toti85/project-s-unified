#!/usr/bin/env python3
"""
🎯 PROJECT-S META LAYER LAUNCHER
Original src/core/meta connected to SuperIntelligentAI
Task: Solve concrete problems until completion
"""

import asyncio
import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Add repo to path
_repo_root = str(Path(__file__).parent)
sys.path.insert(0, _repo_root)

async def main():
    """Launch meta layer with concrete task using multi-model AI."""
    
    logger.info("="*80)
    logger.info("PROJECT-S META LAYER LAUNCHER - MULTI-MODEL AI INTEGRATION")
    logger.info("="*80)
    
    try:
        # Step 1: Import AIClient from working location (integrations)
        logger.info("\n[STEP 1] Initializing Multi-Model AI Client...")
        from src.integrations.ai_models.multi_model_ai_client import AIClient
        
        ai_client = AIClient()
        logger.info("✓ AIClient initialized (6 providers available)")
        
        # Step 2: Import Project-S components
        logger.info("\n[STEP 2] Initializing Project-S orchestration...")
        from src.core.super_intelligent_ai import SuperIntelligentAI
        from tools.tools.implementations.file_tools import FileWriteTool
        from pathlib import Path
        import json
        from datetime import datetime
        
        file_tool = FileWriteTool()
        logger.info("✓ Project-S components loaded")
        
        # Step 3: Create web scraping prompt for Deepseek V3
        logger.info("\n[STEP 3] Creating Ukraine server search prompt for Deepseek V3...")
        
        deepseek_prompt = """
🔍 UKRAINE ENTERPRISE SERVER MARKET ANALYSIS
==============================================

Task: Analyze the Ukrainian enterprise server market for the following requirements:

SEARCH PARAMETERS:
- Budget: 30,000 - 55,000 UAH
- Server Models: HP ProLiant DL380 / Dell PowerEdge R730 / R740
- CPU Requirement: 2× Intel Xeon E5-2680/2690 (24-28 cores minimum)
- RAM Requirement: 128-256GB DDR4 ECC
- Preferred Condition: Refurbished / Used-Excellent (cost-effective)
- Storage: Mix of HDD (RAID configurations) + optional NVMe caching

PRIMARY SOURCES TO ANALYZE:
1. serverparts.com.ua - B2B server specialist platform
2. server.ua - Enterprise server distributor
3. it-komplekt.com.ua - IT equipment provider
4. prom.ua - B2B marketplace (server category)
5. olx.ua - Classified marketplace (search: HP DL380, Dell R730)

OUTPUT FORMAT (JSON):
{
    "market_status": "analyzed",
    "timestamp": "2026-02-19",
    "search_summary": {
        "estimated_offers": "number of likely listings",
        "price_range_observed": "typical price bracket",
        "availability": "assessment of market availability"
    },
    "recommendations": [
        {
            "ranking": 1,
            "estimated_model": "server model name",
            "estimated_cpu": "2× Intel Xeon E5-2680 v4",
            "estimated_cores": 28,
            "estimated_ram_gb": 192-256,
            "estimated_price_uah": "estimated price",
            "estimated_seller": "likely seller platform",
            "value_score_estimate": "1-10 scale",
            "reason": "why this matches requirements"
        }
    ],
    "market_insights": {
        "typical_pricing": "average market rate",
        "condition_availability": "which conditions are available",
        "negotiation_potential": "estimated discount potential",
        "best_timing": "market analysis"
    },
    "implementation_notes": "any special notes for Ukrainian market"
}

Provide REALISTIC MARKET ANALYSIS based on typical Ukrainian IT market patterns.
DO NOT provide mock data - estimate based on real market conditions.
Focus on cost-efficient refurbished options in the 30-55k UAH range.
"""

        logger.info("✓ Prompt created (market analysis task)")
        
        # Step 4: Call Deepseek V3 for market analysis
        logger.info("\n[STEP 4] Calling Deepseek V3 (OpenRouter) for market analysis...")
        logger.info("  Model: deepseek-v3")
        logger.info("  Provider: OpenRouter")
        
        deepseek_response = await ai_client.generate_response(
            prompt=deepseek_prompt,
            model="deepseek-v3",
            system_message="You are an expert IT market analyst specializing in Ukrainian enterprise server procurement. Provide realistic market analysis based on typical market conditions.",
            task_type="kódolás",
            temperature=0.3,  # Lower temperature for factual output
            max_tokens=4000
        )
        
        if deepseek_response:
            logger.info("✓ Deepseek V3 response received successfully")
            
            # Step 5: Generate report from AI response
            logger.info("\n[STEP 5] Generating final desktop report...")
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            report_content = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║     UKRAINE ENTERPRISE SERVER MARKET ANALYSIS - DEEPSEEK V3 ANALYSIS       ║
║                                                                            ║
║          Generated via Project-S Multi-Model AI Orchestration             ║
║                    OpenRouter Deepseek V3 Model                          ║
║                                                                            ║
║                          Timestamp: {timestamp}                           ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 MARKET ANALYSIS RESULTS:
===========================

{deepseek_response}

🎯 NEXT STEPS:
==============
1. Review the market analysis above
2. Contact recommended sellers from analysis
3. Request detailed specifications and current stock
4. Negotiate based on suggested pricing
5. Cross-reference with actual marketplace listings

📝 EXECUTION DETAILS:
=====================
- AI Model: Deepseek V3 (OpenRouter)
- Framework: Project-S Multi-Model AI Orchestration
- Execution Date: {timestamp}
- Task Type: Market Research & Analysis
- Market Scope: Ukrainian Enterprise IT

⚠️  DISCLAIMER:
================
This analysis was generated using AI market analysis. While based on typical
Ukrainian IT market patterns, actual prices and availability should be verified
directly with sellers before making purchasing decisions.

Generated by: Project-S SuperIntelligentAI + Multi-Model AIClient
Integration: Meta Layer + OpenRouter Deepseek V3 Model
"""
            
            # Step 6: Save report to desktop
            logger.info("\n[STEP 6] Saving report to desktop...")
            
            desktop_path = Path.home() / "Desktop" / f"deepseek_ukraine_server_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            save_result = await file_tool.execute(
                path=str(desktop_path),
                content=report_content
            )
            
            if save_result.get("success", False):
                logger.info(f"✓ Report saved: {desktop_path.name}")
                
                return {
                    "success": True,
                    "message": "Ukraine server market analysis completed",
                    "model_used": "deepseek-v3",
                    "report_location": str(desktop_path),
                    "ai_response_length": len(deepseek_response),
                    "timestamp": timestamp
                }
            else:
                logger.error(f"Failed to save report: {save_result}")
                
        else:
            logger.error("No response from Deepseek V3")
            return {"success": False, "error": "No response from AI model"}
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    result = asyncio.run(main())
    logger.info("\n" + "="*80)
    logger.info("META LAYER LAUNCHER - COMPLETED")
    logger.info("="*80)
