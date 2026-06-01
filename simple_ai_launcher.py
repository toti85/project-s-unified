#!/usr/bin/env python3
"""
SIMPLE AI LAUNCHER
=====================================
Standalone AI analysis script that analyzes scraped marketplace data

Features:
- Direct DeepSeek V3 API call (no Meta Layer)
- Reads JSON from simple_ukraine_server_search.py output
- Generates comprehensive market analysis
- Saves report to desktop

Usage:
    1. Run: python simple_ukraine_server_search.py  (generates JSON)
    2. Run: python simple_ai_launcher.py             (analyzes data)
    
Environment:
    Set OPENROUTER_API_KEY environment variable
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)-8s %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleAIAnalyzer:
    """Direct AI analyzer using OpenRouter API"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set!")
        
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "deepseek/deepseek-chat"  # Free tier DeepSeek
        self.output_dir = Path.home() / "Desktop"
        
        logger.info("✅ SimpleAIAnalyzer initialized")
        logger.info(f"   Model: {self.model}")
        logger.info(f"   API: OpenRouter")
    
    def load_scraped_data(self, json_file: Path) -> dict:
        """Load scraped data from JSON file"""
        logger.info(f"\n📂 Loading scraped data from: {json_file}")
        
        if not json_file.exists():
            raise FileNotFoundError(f"Scraped data file not found: {json_file}")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"✅ Loaded data for {len(data)} websites")
        
        # Summary
        total_chars = sum(
            d.get('page_text_length', 0) 
            for d in data.values() 
            if 'error' not in d
        )
        logger.info(f"   Total extracted: {total_chars:,} characters")
        
        return data
    
    def prepare_analysis_prompt(self, scraped_data: dict) -> str:
        """Prepare prompt for AI analysis"""
        
        # Format scraped data for prompt
        data_summary = ""
        for site, site_data in scraped_data.items():
            if 'error' in site_data:
                data_summary += f"\n❌ {site}: Error - {site_data['error']}"
            else:
                data_summary += f"\n✅ {site}:"
                data_summary += f"\n   URL: {site_data.get('url', 'N/A')}"
                data_summary += f"\n   Data length: {site_data.get('page_text_length', 0)} chars"
                data_summary += f"\n   Preview:\n{site_data.get('page_text_preview', 'N/A')[:500]}...\n"
        
        prompt = f"""
You are an expert Ukrainian IT market analyst specializing in server procurement and enterprise computing solutions.

TASK: Analyze the following scraped data from Ukrainian server marketplaces and provide:
1. Market Overview (available server models, price ranges)
2. Top 5 Recommendations (with prices in UAH)
3. Market Insights (trends, availability, negotiation potential)
4. Risk Assessment
5. Next Steps for Procurement

SCRAPED DATA FROM UKRAINIAN MARKETPLACES:
==========================================
{data_summary}

Provide a detailed, professional market analysis suitable for enterprise procurement decisions.
Format your response as a structured report with clear sections and bullet points.
Include specific prices, model names, and seller information where available from the data.
"""
        
        return prompt
    
    async def call_api(self, prompt: str) -> str:
        """Call OpenRouter API with DeepSeek"""
        logger.info("\n🤖 Calling OpenRouter DeepSeek API...")
        logger.info(f"   Prompt length: {len(prompt)} characters")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://project-s-agent.local",
            "X-Title": "Project-S Market Analyzer"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a professional IT market analyst with expertise in server procurement."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "temperature": 0.3,  # Lower temp for factual analysis
            "max_tokens": 3000,
            "top_p": 0.95
        }
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                logger.info(f"   Endpoint: {self.base_url}/chat/completions")
                logger.info("   Sending request...")
                
                start_time = datetime.now()
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                latency = (datetime.now() - start_time).total_seconds()
                
                logger.info(f"   Status: HTTP {response.status_code}")
                logger.info(f"   Latency: {latency:.1f}s")
                
                if response.status_code != 200:
                    raise Exception(f"API error: {response.status_code} - {response.text}")
                
                result = response.json()
                analysis = result['choices'][0]['message']['content']
                
                logger.info(f"✅ API Response received ({len(analysis)} chars)")
                
                return analysis
                
        except Exception as e:
            logger.error(f"❌ API call failed: {e}")
            raise
    
    def generate_report(self, prompt: str, analysis: str, scraped_data: dict) -> str:
        """Generate final report combining all data"""
        
        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║     UKRAINE ENTERPRISE SERVER MARKET ANALYSIS REPORT                       ║
║                                                                            ║
║     Analysis: DeepSeek V3 (OpenRouter)                                     ║
║     Scraped Data: Direct Playwright from 4 Ukrainian Marketplaces          ║
║                                                                            ║
║                           Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                           ║
╚════════════════════════════════════════════════════════════════════════════╝

🔍 DATA SOURCES:
================

Websites Scraped:
"""
        
        for site, data in scraped_data.items():
            if 'error' in data:
                report += f"  ❌ {site}: {data['error']}\n"
            else:
                chars = data.get('page_text_length', 0)
                report += f"  ✅ {site}: {chars:,} chars extracted\n"
        
        report += f"""

💡 DEEPSEEK V3 MARKET ANALYSIS:
===============================

{analysis}

📊 METADATA:
============
- Analysis Generated: {datetime.now()}
- AI Model: DeepSeek V3 (deepseek/deepseek-chat)
- API Provider: OpenRouter
- Temperature: 0.3 (factual mode)
- Data Source: Real marketplace scraping (Playwright)
- Data Processing: Standalone (no Meta Layer)

⚠️ METHODOLOGY NOTES:
====================
- All analysis based on real marketplace data
- Prices in UAH unless otherwise specified
- Data extracted from live Ukrainian server marketplaces
- Analysis reflects current market conditions at time of scraping

"""
        
        return report
    
    async def save_report(self, report: str) -> Path:
        """Save report to desktop"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"ukraine_server_analysis_{timestamp}.txt"
        
        logger.info(f"\n💾 Saving report to: {report_file}")
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"✅ Report saved ({len(report)} chars)")
        
        return report_file
    
    async def run(self, json_file: Path):
        """Execute full analysis pipeline"""
        logger.info("\n" + "=" * 80)
        logger.info("🤖 UKRAINE SERVER MARKET AI ANALYSIS (STANDALONE)")
        logger.info("=" * 80)
        
        try:
            # Load scraped data
            scraped_data = self.load_scraped_data(json_file)
            
            # Prepare prompt
            logger.info("\n📝 Preparing analysis prompt...")
            prompt = self.prepare_analysis_prompt(scraped_data)
            logger.info(f"   Prompt prepared ({len(prompt)} chars)")
            
            # Call AI
            analysis = await self.call_api(prompt)
            
            # Generate report
            logger.info("\n📋 Generating final report...")
            report = self.generate_report(prompt, analysis, scraped_data)
            
            # Save report
            report_file = await self.save_report(report)
            
            # Summary
            logger.info("\n" + "=" * 80)
            logger.info("✅ ANALYSIS COMPLETE")
            logger.info("=" * 80)
            logger.info(f"\n📁 Report saved to desktop:")
            logger.info(f"   {report_file}")
            
            return report_file
            
        except Exception as e:
            logger.error(f"\n❌ FATAL ERROR: {e}")
            import traceback
            traceback.print_exc()
            raise


async def find_latest_scraped_file() -> Path:
    """Find the most recent scraped data JSON file"""
    desktop = Path.home() / "Desktop"
    
    scraped_files = list(desktop.glob("ukraine_servers_scraped_*.json"))
    
    if not scraped_files:
        raise FileNotFoundError(
            "No scraped data file found on desktop!\n"
            "Run: python simple_ukraine_server_search.py first"
        )
    
    # Get most recent
    latest = max(scraped_files, key=lambda p: p.stat().st_mtime)
    logger.info(f"Found latest scraped file: {latest.name}")
    
    return latest


async def main():
    """Main entry point"""
    # Find scraped data
    try:
        json_file = await find_latest_scraped_file()
    except FileNotFoundError as e:
        logger.error(f"\n{e}")
        return None
    
    # Run analyzer
    analyzer = SimpleAIAnalyzer()
    report_file = await analyzer.run(json_file)
    
    return report_file


if __name__ == "__main__":
    import asyncio
    
    try:
        report_file = asyncio.run(main())
        if report_file:
            print(f"\n✅ Analysis complete! Report saved to:")
            print(f"   {report_file}")
    except KeyboardInterrupt:
        print("\n⚠️  Analysis interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)
