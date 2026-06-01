#!/usr/bin/env python3
"""
🎯 SERVER HUNT MAESTRO
====================
Complete orchestration: Scraping → Data cleaning → AI analysis → Reporting

This is the MAIN ENTRY POINT for the entire server hunting campaign.

Usage:
    python server_hunt_maestro.py

What it does:
    1. ✅ Scrapes 10 platforms (Ukraine + International)
    2. ✅ Cleans and validates data
    3. ✅ Scores deals using multi-factor algorithm
    4. ✅ Generates scraper report
    5. ✅ Calls DeepSeek V3 for AI deal analysis
    6. ✅ Generates final recommendations
    7. ✅ Opens results on Desktop

EXPECTED OUTPUTS:
    - server_hunt_campaign_YYYYMMDD_HHMMSS.txt (scraper report)
    - server_hunt_data_YYYYMMDD_HHMMSS.json (structured data)
    - server_hunt_analysis_YYYYMMDD_HHMMSS.txt (AI analysis)
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] 🎯 %(message)s'
)
logger = logging.getLogger(__name__)


class ServerHuntMaestro:
    """Orchestrates complete server hunting campaign"""
    
    def __init__(self):
        self.workspace = Path("c:\\1225\\project_s_super_core")
        self.desktop = Path.home() / "Desktop"
        self.scraper_script = self.workspace / "server_hunt_scraper.py"
        self.analyzer_script = self.workspace / "server_hunt_analyzer.py"
        self.config_file = self.workspace / "server_hunt_config.yaml"
        
        logger.info("🎯 SERVER HUNT MAESTRO v1.0")
        logger.info("-" * 80)
        logger.info(f"Workspace: {self.workspace}")
        logger.info(f"Desktop: {self.desktop}")
        
        self._validate_files()
    
    def _validate_files(self):
        """Validate all required files exist"""
        required_files = {
            "Scraper": self.scraper_script,
            "Analyzer": self.analyzer_script,
            "Config": self.config_file
        }
        
        logger.info("\n📋 VALIDATING REQUIRED FILES:")
        for name, filepath in required_files.items():
            exists = "✅" if filepath.exists() else "❌"
            logger.info(f"   {exists} {name}: {filepath.name}")
            if not filepath.exists():
                raise FileNotFoundError(f"Missing: {filepath}")
        
        # Check API key
        api_key = os.getenv('OPENROUTER_API_KEY') or os.getenv('OPENAI_API_KEY')
        if api_key:
            key_preview = api_key[:10] + "..." if len(api_key) > 10 else api_key
            logger.info(f"   ✅ API Key: {key_preview}")
        else:
            logger.warning("   ⚠️  No API key found - Analyzer will fail")
            logger.info("      Set: OPENROUTER_API_KEY or OPENAI_API_KEY")
    
    async def run_scraper(self) -> Optional[Path]:
        """Execute server hunting scraper"""
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 1️⃣  - WEB SCRAPING")
        logger.info("=" * 80)
        
        try:
            logger.info("\n🌐 Starting browser automation...")
            logger.info("   Scraping 10 platforms (may take 5-15 minutes):")
            logger.info("   • OLX.ua (1/10)")
            logger.info("   • Prom.ua (2/10)")
            logger.info("   • serverparts.com.ua (3/10)")
            logger.info("   • server.ua (4/10)")
            logger.info("   • it-komplekt.com.ua (5/10)")
            logger.info("   • Rozetka (6/10)")
            logger.info("   • Facebook Marketplace UA (7/10)")
            logger.info("   • eBay Europe (8/10)")
            logger.info("   • ServerMonkey.com (9/10)")
            logger.info("   • Hetzner Auctions (10/10)")
            
            start_time = datetime.now()
            
            # Run scraper
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                str(self.scraper_script),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            elapsed = (datetime.now() - start_time).total_seconds()
            
            if process.returncode != 0:
                logger.error(f"❌ Scraper failed with code {process.returncode}")
                logger.error(f"   {stderr.decode()}")
                return None
            
            logger.info(f"\n✅ Scraping complete ({elapsed:.1f}s)")
            
            # Find generated JSON file
            json_files = sorted(self.desktop.glob("server_hunt_data_*.json"), reverse=True)
            if json_files:
                json_file = json_files[0]
                logger.info(f"   Data: {json_file.name}")
                
                # Load and report stats
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                offers = data.get('offers', [])
                logger.info(f"   Offers found: {len(offers)}")
                
                if offers:
                    avg_price = sum(o.get('price_uah_estimated', 0) for o in offers) / len(offers)
                    min_price = min(o.get('price_uah_estimated', float('inf')) for o in offers)
                    max_price = max(o.get('price_uah_estimated', 0) for o in offers)
                    
                    logger.info(f"   Price range: {min_price:,.0f} - {max_price:,.0f} UAH")
                    logger.info(f"   Average: {avg_price:,.0f} UAH")
                
                return json_file
            else:
                logger.error("❌ No JSON file generated")
                return None
        
        except Exception as e:
            logger.error(f"❌ Scraper error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def run_analyzer(self) -> Optional[Path]:
        """Execute AI analyzer"""
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 2️⃣  - AI ANALYSIS")
        logger.info("=" * 80)
        
        api_key = os.getenv('OPENROUTER_API_KEY') or os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.warning("\n⚠️  No API key configured")
            logger.warning("   Skipping AI analysis phase")
            logger.warning("\n   To enable:")
            logger.warning("   Set OPENROUTER_API_KEY or OPENAI_API_KEY environment variable")
            return None
        
        try:
            logger.info("\n🤖 Launching DeepSeek V3 analyzer...")
            logger.info("   Model: deepseek/deepseek-chat")
            logger.info("   API: OpenRouter")
            logger.info("   (This may take 2-3 minutes)")
            
            start_time = datetime.now()
            
            # Run analyzer
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                str(self.analyzer_script),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            elapsed = (datetime.now() - start_time).total_seconds()
            
            if process.returncode != 0:
                logger.error(f"❌ Analyzer failed with code {process.returncode}")
                logger.error(f"   {stderr.decode()}")
                return None
            
            logger.info(f"\n✅ AI analysis complete ({elapsed:.1f}s)")
            
            # Find generated report file
            report_files = sorted(self.desktop.glob("server_hunt_analysis_*.txt"), reverse=True)
            if report_files:
                report_file = report_files[0]
                logger.info(f"   Analysis: {report_file.name}")
                return report_file
            else:
                logger.error("❌ No report file generated")
                return None
        
        except Exception as e:
            logger.error(f"❌ Analyzer error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _open_results(self, scraper_report: Optional[Path], analysis_report: Optional[Path]):
        """Open result files on Desktop"""
        logger.info("\n" + "=" * 80)
        logger.info("RESULTS")
        logger.info("=" * 80)
        
        logger.info("\n📁 Files saved to Desktop:")
        
        if scraper_report and scraper_report.exists():
            logger.info(f"   ✅ {scraper_report.name}")
            # Try to open
            try:
                if sys.platform == 'win32':
                    os.startfile(scraper_report)
                else:
                    subprocess.Popen(['xdg-open', str(scraper_report)])
            except:
                pass
        
        if analysis_report and analysis_report.exists():
            logger.info(f"   ✅ {analysis_report.name}")
            # Try to open
            try:
                if sys.platform == 'win32':
                    os.startfile(analysis_report)
                else:
                    subprocess.Popen(['xdg-open', str(analysis_report)])
            except:
                pass
        
        logger.info("\n🎉 CAMPAIGN COMPLETE!")
    
    async def run(self):
        """Execute complete hunting campaign"""
        try:
            logger.info("\n🎯 STARTING SERVER HUNT CAMPAIGN")
            logger.info("   Target: HP DL380 G8/G9 & Dell R730/R740")
            logger.info("   Specs: 20-28 cores, 64-128GB RAM, <40k UAH")
            logger.info("   Platforms: Ukraine + International")
            
            # Phase 1: Scraping
            scraper_report = await self.run_scraper()
            
            # Phase 2: AI Analysis
            analysis_report = await self.run_analyzer()
            
            # Results
            self._open_results(scraper_report, analysis_report)
            
            logger.info("\n" + "=" * 80)
            logger.info("✅ SERVER HUNT MAESTRO - COMPLETE")
            logger.info("=" * 80)
            
            return {
                'scraper_report': scraper_report,
                'analysis_report': analysis_report,
                'success': scraper_report is not None
            }
        
        except KeyboardInterrupt:
            logger.warning("\n⚠️  Campaign interrupted by user")
            raise
        except Exception as e:
            logger.error(f"\n❌ FATAL ERROR: {e}")
            import traceback
            traceback.print_exc()
            raise


async def main():
    """Main entry point"""
    try:
        maestro = ServerHuntMaestro()
        result = await maestro.run()
        return result
    except KeyboardInterrupt:
        logger.info("\n⏹️  Campaign stopped")
        return None
    except Exception as e:
        logger.error(f"Fatal: {e}")
        return None


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        if result and result.get('success'):
            sys.exit(0)
        else:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️  Stopped")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
