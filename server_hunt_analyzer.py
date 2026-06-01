#!/usr/bin/env python3
"""
🎯 SERVER HUNT AI ANALYZER
=========================
DeepSeek V3 powered deal analysis and negotiation strategy generator

Reads server hunt JSON data and provides:
- Deal ranking & value assessment
- Market trend analysis
- Negotiation recommendations
- Risk analysis
- Portfolio recommendations (if buying multiple)

Usage:
    1. Run: python server_hunt_scraper.py (generates JSON)
    2. Run: python server_hunt_analyzer.py (analyzes data)
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] 🤖 %(message)s'
)
logger = logging.getLogger(__name__)

class ServerHuntAnalyzer:
    """AI-powered analyzer for server deal recommendations"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_API_KEY') or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("⚠️  Set OPENROUTER_API_KEY or OPENAI_API_KEY environment variable!")
        
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "deepseek/deepseek-chat"
        self.output_dir = Path.home() / "Desktop"
        
        logger.info("✅ ServerHuntAnalyzer initialized")
        logger.info(f"   Model: {self.model}")
        logger.info(f"   API: OpenRouter")
    
    def _find_latest_hunt_data(self) -> Optional[Path]:
        """Find the most recent server hunt JSON file"""
        hunt_files = list(self.output_dir.glob("server_hunt_data_*.json"))
        
        if not hunt_files:
            raise FileNotFoundError(
                "❌ No server hunt data found!\n"
                "   Run: python server_hunt_scraper.py first"
            )
        
        latest = max(hunt_files, key=lambda p: p.stat().st_mtime)
        logger.info(f"📂 Found hunt data: {latest.name}")
        return latest
    
    def _load_hunt_data(self, json_file: Path) -> dict:
        """Load server hunt data from JSON"""
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"   Loaded {len(data.get('offers', []))} offers")
        return data
    
    def _prepare_analysis_prompt(self, hunt_data: dict) -> str:
        """Prepare detailed prompt for AI analysis"""
        
        offers = hunt_data.get('offers', [])
        
        # Format offers for prompt
        offers_text = ""
        for i, offer in enumerate(offers[:10], 1):  # Top 10
            offers_text += f"""
{i}. {offer['server_model']} ({offer['platform']})
   CPU: {offer['cpu_cores']} cores
   RAM: {offer['ram_gb']} GB
   Price: {offer['price_uah_estimated']:,.0f} UAH
   Score: {offer['score']:.0f}
   URL: {offer['url']}"""
        
        prompt = f"""
You are an expert enterprise IT procurement specialist with 15+ years of experience buying used/refurbished servers.

HUNTING CAMPAIGN DATA:
======================
Campaign Date: {datetime.now().strftime('%Y-%m-%d')}

TARGET SPECS:
- Model: HP DL380 G8/G9 or Dell R730/R740
- CPU: 20-28 cores (preferably Xeon E5 v2)
- RAM: 64-128 GB DDR3/DDR4
- Price Target: < 40,000 UAH (ideal)
- Form: 2U (GPU-ready)
- Condition: Used/Refurbished acceptable

OFFERS FOUND:
{offers_text}

Please provide:

1. **DEAL ANALYSIS** (for top 3 offers)
   - Value for money assessment
   - CPU/RAM efficiency score
   - Price fairness evaluation
   - Red flags (if any)

2. **MARKET INSIGHTS**
   - Current market pricing trends
   - Availability of required specs
   - Currency/location considerations

3. **NEGOTIATION PLAYBOOK**
   - 3 opening offers for each top deal
   - Counter-negotiation strategies
   - Bundling opportunities (if multiple units)
   - Payment/shipping leverage points

4. **RISK ASSESSMENT**
   - Specific risks for each platform
   - Health check recommendations
   - Warranty considerations
   - Hidden cost warnings

5. **FINAL RECOMMENDATIONS**
   - Ranking: Best value, Backup, Budget option
   - Exact opening price to propose
   - Which specs to test upon receipt
   - Timeline (how urgent to buy)

6. **PORTFOLIO STRATEGY**
   - If buying 2-3 units: Recommended mix
   - Vendor diversification strategy
   - Bulk purchase discount estimates
   - Phased buying vs. immediate approach

Use your expert knowledge of server markets, Ukrainian pricing, and procurement tactics.
Be specific with numbers and actionable advice.
"""
        
        return prompt
    
    async def call_ai_analysis(self, prompt: str) -> str:
        """Call DeepSeek AI for analysis"""
        logger.info("🤔 Sending hunt data to DeepSeek V3 for analysis...")
        logger.info(f"   Prompt size: {len(prompt)} chars")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://project-s-agent.local",
            "X-Title": "Project-S Server Hunter"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": """You are a world-class enterprise IT procurement specialist.
You have deep expertise in:
- Server hardware specs and value
- International and local Ukrainian IT markets
- Negotiation tactics for bulk purchases
- Risk assessment for used/refurbished equipment
Provide specific, actionable, expert-level recommendations."""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.4,  # Balanced (not too creative, some reasoning)
            "max_tokens": 4000,
            "top_p": 0.95
        }
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                logger.info("📡 Calling OpenRouter API...")
                logger.info(f"   Endpoint: {self.base_url}/chat/completions")
                
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
                
                logger.info(f"✅ Analysis received ({len(analysis)} chars)")
                return analysis
        
        except Exception as e:
            logger.error(f"❌ API call failed: {e}")
            raise
    
    def _generate_final_report(self, hunt_data: dict, analysis: str) -> str:
        """Generate final comprehensive report"""
        
        offers = hunt_data.get('offers', [])
        top_offers = sorted(offers, key=lambda x: x.get('score', 0), reverse=True)[:3]
        
        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                  🎯 SERVER HUNT - AI ANALYSIS REPORT                       ║
║                                                                            ║
║               DeepSeek V3 Procurement Strategy Analysis                    ║
║                                                                            ║
║                    Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                     ║
╚════════════════════════════════════════════════════════════════════════════╝

🏆 EXECUTIVE SUMMARY:
=====================
Total Offers Analyzed: {len(offers)}
Platforms Searched: {len(set(o['platform'] for o in offers))}

Top Candidates:
"""
        
        for i, offer in enumerate(top_offers, 1):
            report += f"""
{i}. {offer['server_model']}
   - {offer['cpu_cores']} cores / {offer['ram_gb']} GB RAM
   - {offer['price_uah_estimated']:,.0f} UAH ({offer['platform']})
   - Value Score: {offer['score']:.0f}/1000
"""
        
        report += f"""

💡 DEEPSEEK V3 EXPERT ANALYSIS:
====================================

{analysis}


📊 QUICK REFERENCE TABLE - ALL OFFERS:
======================================
"""
        
        report += "Platform | Server | Cores/RAM | Price UAH | Score\n"
        report += "-" * 70 + "\n"
        
        for offer in sorted(offers, key=lambda x: x.get('score', 0), reverse=True):
            plat = offer['platform'][:15].ljust(15)
            model = offer['server_model'][:15].ljust(15)
            specs = f"{offer['cpu_cores']}c/{offer['ram_gb']}G".ljust(10)
            price = f"{offer['price_uah_estimated']:,.0f}".ljust(12)
            score = f"{offer['score']:.0f}".ljust(8)
            
            report += f"{plat} | {model} | {specs} | {price} | {score}\n"
        
        report += """

🎯 ACTION ITEMS:
===============
□ Contact top 3 sellers immediately (within 24h)
□ Request detailed technical specs for each unit
□ Ask about bulk discount opportunities (2+ units)
□ Negotiate based on AI-recommended opening price
□ Schedule technical inspection before payment
□ Verify system logs and SMART data for HDDs

⚠️ RISK MITIGATION:
===================
• Don't rely on single seller if buying multiple units
• Always test each server upon receipt
• Document any cosmetic damage for warranty claims
• Verify all fans included (common missing part)
• Check PSU health (common failure point)
• Ask about refurbishment date and any repairs

📞 TEMPLATE EMAILS:
===================
Opening inquiry (negotiate downward):
"Hi, I'm interested in [model]. What's your best price for [qty] units?
Can you offer a discount for bulk purchase? Would you consider [X% lower] for immediate payment?"

After receiving initial offer (if too high):
"Thanks for the quote. I'm seeing similar models at [lower price] on [platform].
Can you match that? Would you accept [offer amount]?"

Bulk negotiation (if buying 2+):
"I'm interested in purchasing multiple units. What's your best bulk rate?
Available for immediate payment if the pricing is right."

📖 MARKET INTELLIGENCE:
======================
- Ukrainian IT market heavily influenced by currency fluctuations
- Refurbished servers typically 20-30% cheaper than new
- Bulk buyers (2-3 units) often get additional 10-15% discount
- HP DL380 more expensive than equivalent Dell R730
- Used-no-warranty units can be 30-40% cheaper if condition good
"""
        
        return report
    
    async def run(self):
        """Execute complete analysis"""
        logger.info("\n" + "=" * 80)
        logger.info("🤖 SERVER HUNT AI ANALYSIS - STARTING")
        logger.info("=" * 80)
        
        try:
            # Find and load hunt data
            hunt_file = self._find_latest_hunt_data()
            hunt_data = self._load_hunt_data(hunt_file)
            
            # Prepare prompt
            logger.info("\n📝 Preparing analysis prompt...")
            prompt = self._prepare_analysis_prompt(hunt_data)
            logger.info(f"   Prompt prepared ({len(prompt)} chars)")
            
            # Call AI
            analysis = await self.call_ai_analysis(prompt)
            
            # Generate report
            logger.info("\n📋 Generating final report with AI insights...")
            report = self._generate_final_report(hunt_data, analysis)
            
            # Save report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = self.output_dir / f"server_hunt_analysis_{timestamp}.txt"
            
            logger.info(f"💾 Saving report to: {report_file}")
            
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            
            logger.info(f"✅ Report saved")
            
            # Summary
            logger.info("\n" + "=" * 80)
            logger.info("✅ AI ANALYSIS COMPLETE")
            logger.info("=" * 80)
            logger.info(f"\n📁 Analysis saved to Desktop:")
            logger.info(f"   {report_file.name}\n")
            
            return report_file
        
        except Exception as e:
            logger.error(f"\n❌ FATAL ERROR: {e}")
            import traceback
            traceback.print_exc()
            raise


async def main():
    """Main entry point"""
    try:
        analyzer = ServerHuntAnalyzer()
        report_file = await analyzer.run()
        return report_file
    except Exception as e:
        logger.error(f"Fatal: {e}")
        raise


if __name__ == "__main__":
    import asyncio
    
    try:
        report_file = asyncio.run(main())
        print(f"\n✅ Analysis complete!")
        print(f"   Report: {report_file}")
    except KeyboardInterrupt:
        print("\n⚠️  Analysis interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
