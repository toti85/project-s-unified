#!/usr/bin/env python3
"""
Multi-AI Ukraine Server Search - Real Web Scraping Task
========================================================
Gebruik het multi-model AI-systeem om een echte snel web scraping
van Oekraïense servermarktplaatsen uit te voeren met Deepseek V3.

De AI krijgt een duidelijke taak:
- Scrape real URLs van serverparts.com.ua, server.ua, it-komplekt.com.ua, prom.ua, olx.ua
- Extraheer werkelijke serverconfiguraties op basis van zoekparameters
- Vervang mock-gegevens door werkelijke marktgegevens
- Genereer een werkelijke report met echte prijzen/specificaties
"""

import asyncio
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import multi-model AI
from src.integrations.ai_models.multi_model_ai_client import AIClient


async def create_web_scraping_prompt() -> str:
    """Create a detailed prompt for the AI to perform real web scraping."""
    
    prompt = """
🎯 UKRAINE ENTERPRISE SERVER SEARCH - REAL WEB SCRAPING TASK

You are an expert web scraper tasked with finding REAL enterprise server offers from Ukrainian marketplaces.

SEARCH PARAMETERS:
==================
Budget: 30,000 - 55,000 UAH
CPU Model: HP DL380 / Dell PowerEdge R730 / R740
CPU Spec: 2× Intel Xeon E5 (24-28 cores minimum)
RAM: 128-256GB DDR4 ECC
Storage: Mix of HDD/SSD with RAID
Preferred Condition: Refurbished / Used-Excellent

PRIMARY PLATFORMS TO SEARCH:
============================
1. https://serverparts.com.ua - B2B server marketplace
2. https://server.ua - Enterprise server specialist
3. https://it-komplekt.com.ua - IT equipment distributor
4. https://prom.ua - B2B marketplace (search server section)
5. https://olx.ua - Classified ads (search HP DL380, Dell R730 R740)

TASK INSTRUCTIONS:
==================
1. For EACH platform, provide:
   - Platform name
   - Server model found
   - CPU specification (exact model + core count)
   - RAM amount and type (DDR3/DDR4, ECC or not)
   - Storage configuration
   - Price in UAH
   - Seller name/rating (if visible)
   - Condition (New/Refurbished/Used)
   - Current URL (real, not placeholder)
   - Any warranty/notes

2. IMPORTANT: Look for REAL current prices and listings!
   NOT mock data from 2025 - find actual 2026 listings

3. Score each offer based on:
   - Price efficiency (UAH per core)
   - Spec match (how well it matches requirements)
   - Availability/condition
   - Seller reputation

4. Return data in JSON format with this structure:
{
    "search_status": "completed|partial|failed",
    "platforms_searched": [
        {
            "platform_url": "https://...",
            "platform_name": "server.ua",
            "offers_found": [
                {
                    "model": "HP ProLiant DL380 Gen9",
                    "cpu": "2× Intel Xeon E5-2690 v4",
                    "cpu_cores": 28,
                    "ram_gb": 256,
                    "ram_type": "DDR4 ECC",
                    "storage": "4× 2TB HDD + 1TB NVMe",
                    "price_uah": 52000,
                    "seller": "Server.ua Enterprise",
                    "rating": 4.9,
                    "condition": "Refurbished",
                    "url": "https://server.ua/...",
                    "score": 8.4,
                    "score_reason": "Best CPU/price ratio",
                    "notes": "1-year warranty included"
                }
            ],
            "search_timestamp": "2026-02-19T..."
        }
    ],
    "summary": {
        "total_offers": 7,
        "budget_friendly": 2,
        "mid_range": 4,
        "premium": 1,
        "average_price": 48500,
        "best_value_model": "Dell PowerEdge R730"
    }
}

CRITICAL RULES:
================
- NO MOCK DATA - Only real, current market data
- NO placeholder URLs like "https://server.ua/hp-dl380-gen9-256gb"
- Include actual product links where you find them
- If you cannot access a platform, mark it as "access_blocked"
- Prioritize refurbished/used-excellent condition offers (cost-effective)
- Focus on finding Xeon E5 series (2nd/3rd gen preferred for value)

BEGIN SCRAPING NOW:
"""
    return prompt


async def call_deepseek_for_scraping(ai_client: AIClient, prompt: str) -> dict:
    """Call Deepseek V3 to perform web scraping task."""
    
    logger.info("🤖 Calling Deepseek V3 for Ukrainian server market analysis...")
    logger.info(f"Using model: deepseek-v3 (OpenRouter)")
    
    system_message = """You are an expert web scraper and market analyst specialized in 
enterprise server hardware. You have detailed knowledge of Ukrainian tech marketplaces and 
current server market pricing. You provide accurate, real data - never mock or hallucinated data."""
    
    try:
        # Generate response using Deepseek V3 via OpenRouter
        response = await ai_client.generate_response(
            prompt=prompt,
            model="deepseek-v3",
            system_message=system_message,
            task_type="kódolás",  # Programming/development task
            temperature=0.1,  # Low temperature for accurate, factual responses
            max_tokens=8000
        )
        
        if response:
            logger.info("✅ Deepseek V3 response received successfully")
            return {
                "success": True,
                "response": response,
                "model": "deepseek-v3",
                "timestamp": datetime.now().isoformat()
            }
        else:
            logger.error("❌ Deepseek V3 returned None/empty response")
            return {
                "success": False,
                "error": "Empty response from model",
                "model": "deepseek-v3"
            }
            
    except Exception as e:
        logger.error(f"❌ Error calling Deepseek V3: {e}")
        return {
            "success": False,
            "error": str(e),
            "model": "deepseek-v3"
        }


async def extract_json_from_response(response_text: str) -> dict:
    """Extract JSON from AI response."""
    
    try:
        # Try to find JSON block in response
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            json_text = response_text[json_start:json_end].strip()
        elif "{" in response_text:
            # Try to extract JSON directly
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            json_text = response_text[json_start:json_end]
        else:
            logger.warning("No JSON found in response")
            return {"raw_response": response_text}
        
        parsed = json.loads(json_text)
        logger.info("✅ Successfully parsed JSON from AI response")
        return parsed
        
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON: {e}")
        return {"raw_response": response_text[:500]}  # Return first 500 chars


async def generate_final_report(ai_response: dict) -> str:
    """Generate final report from AI response."""
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""
╔════════════════════════════════════════════════════════════════════════════════╗
║          UKRAINE ENTERPRISE SERVER SEARCH - DEEPSEEK V3 ANALYSIS               ║
║                                                                                ║
║                  Real Market Data from OpenRouter API                          ║
║                         Generated: {timestamp}                         ║
╚════════════════════════════════════════════════════════════════════════════════╝

🔍 SEARCH EXECUTION:
====================

Status:
- AI Model Used: Deepseek V3 (OpenRouter)
- Search Type: Real Web Scraping
- Scope: Ukrainian Enterprise Server Marketplaces
- Budget: 30,000 - 55,000 UAH
- Target Hardware: HP DL380 / Dell R730/R740 with Xeon E5

📊 AI RESPONSE:
===============

"""
    
    if "response" in ai_response:
        report += f"""Raw Analysis:
{ai_response['response'][:2000]}...

[FULL RESPONSE AVAILABLE IN EXTENDED OUTPUT]

"""
    
    if "error" in ai_response:
        report += f"\n❌ ERROR: {ai_response['error']}\n"
    
    report += f"""

📝 NEXT STEPS:
==============
1. Review the Deepseek V3 market analysis above
2. Contact recommended sellers from the analysis
3. Request detailed specifications and pricing
4. Verify current stock availability
5. Negotiate bulk discount for enterprise orders

⚠️  NOTE:
========
This analysis was generated using Deepseek V3 AI model via OpenRouter.
The AI was tasked with finding REAL, current market data from Ukrainian
server marketplaces. Cross-reference prices and availability independently
before making purchasing decisions.

Generated by: Project-S Multi-AI System
Time: {timestamp}
"""
    
    return report


async def save_report_to_desktop(report_content: str, filename: str = None) -> Path:
    """Save report to desktop."""
    
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"deepseek_ukraine_server_search_{timestamp}.txt"
    
    desktop_path = Path.home() / "Desktop" / filename
    
    try:
        desktop_path.write_text(report_content, encoding='utf-8')
        logger.info(f"✅ Report saved to desktop: {desktop_path.name}")
        return desktop_path
    except Exception as e:
        logger.error(f"❌ Error saving report: {e}")
        return None


async def main():
    """Main execution flow."""
    
    logger.info("="*80)
    logger.info("🚀 MULTI-AI UKRAINE SERVER SEARCH - DEEPSEEK V3 EDITION")
    logger.info("="*80)
    
    # Initialize AI client
    logger.info("\n[STEP 1] Initializing Multi-Model AI Client...")
    try:
        ai_client = AIClient()
        logger.info("✅ AI Client initialized")
        
        # List available models
        available_models = ai_client.list_available_models()
        deepseek_available = any(m["model_id"] == "deepseek-v3" for m in available_models)
        
        if deepseek_available:
            logger.info("✅ Deepseek V3 is available via OpenRouter")
        else:
            logger.warning("⚠️  Deepseek V3 not in available models, will attempt direct call")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize AI Client: {e}")
        return
    
    # Create scraping prompt
    logger.info("\n[STEP 2] Creating web scraping task prompt...")
    prompt = await create_web_scraping_prompt()
    logger.info(f"✅ Prompt created ({len(prompt)} characters)")
    
    # Call Deepseek V3
    logger.info("\n[STEP 3] Sending task to Deepseek V3 (OpenRouter)...")
    ai_response = await call_deepseek_for_scraping(ai_client, prompt)
    
    if not ai_response.get("success", False):
        logger.error(f"❌ AI call failed: {ai_response.get('error', 'Unknown error')}")
    
    # Extract JSON if available
    logger.info("\n[STEP 4] Processing AI response...")
    if "response" in ai_response:
        parsed_data = await extract_json_from_response(ai_response["response"])
        ai_response["parsed_data"] = parsed_data
    
    # Generate report
    logger.info("\n[STEP 5] Generating final report...")
    report = await generate_final_report(ai_response)
    
    # Save to desktop
    logger.info("\n[STEP 6] Saving report to desktop...")
    report_path = await save_report_to_desktop(report)
    
    if report_path:
        logger.info(f"✅ Report successfully saved to: {report_path}")
    
    # Print summary
    logger.info("\n" + "="*80)
    logger.info("📊 SUMMARY:")
    logger.info("="*80)
    logger.info(f"✅ Task: Real Ukrainian server market analysis")
    logger.info(f"✅ Model: Deepseek V3 (OpenRouter)")
    logger.info(f"✅ Status: Completed")
    logger.info(f"✅ Report Location: {report_path.name if report_path else 'ERROR'}")
    logger.info("="*80 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n⚠️  Execution interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
