#!/usr/bin/env python3
"""
🎯 SERVER HUNT SCRAPER
=====================
Specialized server hunting tool - Find HP DL380 / Dell R730/R740 deals across Ukrainian platforms

Features:
- Multi-platform scraping (OLX, Prom, serverparts, etc.)
- Smart spec extraction & parsing
- Price normalization to UAH
- Deal scoring based on value
- Real-time tracking
- Caching for efficiency

Usage:
    python server_hunt_scraper.py
"""

import asyncio
import json
import logging
import re
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from playwright.async_api import async_playwright

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] 📍 %(message)s'
)
logger = logging.getLogger(__name__)

class ServerHuntScraper:
    """Specialized scraper for server hunting across Ukrainian platforms"""
    
    def __init__(self, config_file: str = "server_hunt_config.yaml"):
        self.config = self._load_config(config_file)
        self.results = []
        self.platform_stats = {}
        self.output_dir = Path.home() / "Desktop"
        self.browser = None
        self.context = None
        
    def _load_config(self, config_file: str) -> dict:
        """Load configuration from YAML file"""
        config_path = Path(config_file)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_file}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        logger.info(f"✅ Configuration loaded: {config_file}")
        return config
    
    async def initialize_browser(self):
        """Initialize Playwright browser"""
        logger.info("🚀 Initializing Playwright browser...")
        
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=self.config['EXECUTION']['headless'],
            args=['--disable-blink-features=AutomationControlled']
        )
        
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        logger.info("✅ Browser ready")
    
    def _extract_cpu_cores(self, text: str) -> Optional[int]:
        """Extract CPU core count from text"""
        patterns = [
            r'(\d+)\s*(?:ядер|core|cores|ц)',
            r'E5-[0-9]+\s*v?\d*',  # Xeon E5 series
            r'EPYC\s+(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except (IndexError, ValueError):
                    pass
        
        return None
    
    def _extract_ram_gb(self, text: str) -> Optional[int]:
        """Extract RAM amount from text"""
        patterns = [
            r'(\d+)\s*(?:GB|ГБ|G)\s*(?:DDR|RAM|пам)',
            r'(\d+)\s*(?:GB|ГБ)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except (IndexError, ValueError):
                    pass
        
        return None
    
    def _extract_price_uah(self, text: str, currency: str = "UAH") -> Optional[float]:
        """Extract price and normalize to UAH"""
        patterns = [
            r'(\d{3,6})\s*(?:₴|UAH|грн)',
            r'(\d{1,5})\s*(?:€|EUR)',  # EUR to UAH: 1 EUR ≈ 40 UAH
            r'(\d{3,5})\s*(?:USD|\$)',  # USD to UAH: 1 USD ≈ 40 UAH
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    price = float(match.group(1))
                    
                    # Normalize to UAH
                    if 'EUR' in pattern.upper():
                        price = price * 40  # Approximate EUR to UAH
                    elif 'USD' in pattern.upper() or '$' in pattern:
                        price = price * 40  # Approximate USD to UAH
                    
                    return price
                except (IndexError, ValueError):
                    pass
        
        return None
    
    def _extract_server_model(self, text: str) -> Optional[str]:
        """Extract server model name"""
        models = ['DL380', 'DL380e', 'DL380 G8', 'DL380 G9', 'DL 380',
                  'R730', 'R740', 'R750', 'PowerEdge R730']
        
        for model in models:
            if model.lower() in text.lower():
                return model
        
        return None
    
    def _score_deal(self, offer: dict) -> float:
        """Score deal based on specs and price"""
        score = 0.0
        
        # CPU cores scoring
        cores = offer.get('cpu_cores', 0)
        if cores >= self.config['SEARCH_SPECS']['cpu_cores_min']:
            score += (cores - 20) * self.config['SCORING_RULES']['cpu_cores_multiplier']
        else:
            return -999  # Invalid if below minimum
        
        # RAM scoring
        ram = offer.get('ram_gb', 0)
        if ram >= self.config['SEARCH_SPECS']['ram_gb_min']:
            score += (ram - 64) * self.config['SCORING_RULES']['ram_gb_multiplier']
        else:
            return -999  # Invalid if below minimum
        
        # Price scoring (negative = lower price is better)
        price = offer.get('price_uah_estimated', float('inf'))
        if price < float('inf'):
            score -= (price / 1000)  # Subtract price in thousands
        
        # Condition bonus
        condition = offer.get('condition', 'unknown')
        condition_factor = self.config['SCORING_RULES']['condition_factor'].get(condition.lower(), 100)
        score += condition_factor
        
        # Warranty bonus
        if offer.get('warranty_info') and 'no warranty' not in offer.get('warranty_info', '').lower():
            score += self.config['SCORING_RULES']['warranty_bonus']
        
        return score
    
    async def scrape_olx_ua(self):
        """Scrape OLX.ua for servers"""
        logger.info("\n📱 Scraping OLX.ua...")
        platform_name = "OLX.ua"
        
        page = await self.context.new_page()
        count = 0
        
        try:
            # Search for servers
            search_url = "https://olx.ua/d/uk/search/?query=сервер+HP+Dell&category_id=2000"
            
            logger.info(f"🌐 Navigating: {search_url}")
            await page.goto(search_url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(2000)
            
            # Extract listings
            listings = await page.query_selector_all('[data-testid="listing-link"]')
            logger.info(f"   Found {len(listings)} listings")
            
            for listing in listings[:15]:  # Get first 15
                try:
                    # Get listing info
                    title = await listing.get_attribute('aria-label')
                    href = await listing.get_attribute('href')
                    
                    # Get price info
                    price_elem = await listing.query_selector('[data-testid="ad-price"]')
                    price_text = await price_elem.inner_text() if price_elem else "N/A"
                    
                    # Parse data
                    cpu_cores = self._extract_cpu_cores(f"{title or ''}")
                    ram_gb = self._extract_ram_gb(f"{title or ''}")
                    price_uah = self._extract_price_uah(price_text)
                    model = self._extract_server_model(f"{title or ''}")
                    
                    # Only add if it matches criteria
                    if model and cpu_cores and cpu_cores >= self.config['SEARCH_SPECS']['cpu_cores_min']:
                        offer = {
                            'platform': platform_name,
                            'server_model': model,
                            'title': title or 'N/A',
                            'cpu_cores': cpu_cores,
                            'ram_gb': ram_gb or 0,
                            'price_text': price_text,
                            'price_uah_estimated': price_uah or 0,
                            'url': href or 'N/A',
                            'scraped_at': datetime.now().isoformat(),
                            'condition': 'unknown'
                        }
                        
                        # Calculate score
                        offer['score'] = self._score_deal(offer)
                        
                        if offer['score'] > 0:
                            self.results.append(offer)
                            count += 1
                            logger.info(f"   ✅ Added: {model} - {cpu_cores}c/{ram_gb}G - {price_text} (score: {offer['score']:.0f})")
                
                except Exception as e:
                    logger.warning(f"   ⚠️  Error parsing listing: {e}")
            
            self.platform_stats[platform_name] = {'listings_found': len(listings), 'matches': count}
            logger.info(f"✅ OLX.ua: {count} relevant offers found")
            
        except Exception as e:
            logger.error(f"❌ OLX.ua scraping failed: {e}")
            self.platform_stats[platform_name] = {'error': str(e)}
        
        finally:
            await page.close()
    
    async def scrape_prom_ua(self):
        """Scrape Prom.ua for servers"""
        logger.info("\n🏪 Scraping Prom.ua...")
        platform_name = "Prom.ua"
        
        page = await self.context.new_page()
        count = 0
        
        try:
            search_url = "https://prom.ua/uk/search?q=сервер"
            
            logger.info(f"🌐 Navigating: {search_url}")
            await page.goto(search_url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(2000)
            
            # Extract product items
            items = await page.query_selector_all('[data-offer-type="shop"]')
            logger.info(f"   Found {len(items)} items")
            
            for item in items[:20]:
                try:
                    # Get name
                    name_elem = await item.query_selector('h2, [class*="name"]')
                    name = await name_elem.inner_text() if name_elem else "N/A"
                    
                    # Get price
                    price_elem = await item.query_selector('[class*="price"]')
                    price_text = await price_elem.inner_text() if price_elem else "N/A"
                    
                    # Parse data
                    model = self._extract_server_model(name)
                    cpu_cores = self._extract_cpu_cores(name)
                    ram_gb = self._extract_ram_gb(name)
                    price_uah = self._extract_price_uah(price_text)
                    
                    # Get URL
                    link = await item.query_selector('a[href]')
                    url = await link.get_attribute('href') if link else 'N/A'
                    
                    # Only add relevant
                    if model and cpu_cores and cpu_cores >= self.config['SEARCH_SPECS']['cpu_cores_min']:
                        offer = {
                            'platform': platform_name,
                            'server_model': model,
                            'title': name,
                            'cpu_cores': cpu_cores,
                            'ram_gb': ram_gb or 0,
                            'price_text': price_text,
                            'price_uah_estimated': price_uah or 0,
                            'url': url,
                            'scraped_at': datetime.now().isoformat(),
                            'condition': 'unknown'
                        }
                        
                        offer['score'] = self._score_deal(offer)
                        
                        if offer['score'] > 0:
                            self.results.append(offer)
                            count += 1
                            logger.info(f"   ✅ Added: {model} - {cpu_cores}c/{ram_gb}G - {price_text}")
                
                except Exception as e:
                    logger.warning(f"   ⚠️  Error: {e}")
            
            self.platform_stats[platform_name] = {'items_found': len(items), 'matches': count}
            logger.info(f"✅ Prom.ua: {count} relevant offers found")
            
        except Exception as e:
            logger.error(f"❌ Prom.ua failed: {e}")
            self.platform_stats[platform_name] = {'error': str(e)}
        
        finally:
            await page.close()
    
    async def scrape_serverparts(self):
        """Scrape serverparts.com.ua"""
        logger.info("\n🖥️  Scraping serverparts.com.ua...")
        platform_name = "serverparts.com.ua"
        
        page = await self.context.new_page()
        count = 0
        
        try:
            url = "https://serverparts.com.ua/server2u/"
            
            logger.info(f"🌐 Navigating: {url}")
            await page.goto(url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(2000)
            
            # Search for server items
            items = await page.query_selector_all('[data-product-id]')
            logger.info(f"   Found {len(items)} products")
            
            for item in items[:25]:
                try:
                    # Extract text content
                    text_content = await item.inner_text()
                    
                    if not text_content:
                        continue
                    
                    # Parse specs
                    model = self._extract_server_model(text_content)
                    cpu_cores = self._extract_cpu_cores(text_content)
                    ram_gb = self._extract_ram_gb(text_content)
                    price_uah = self._extract_price_uah(text_content)
                    
                    # Get URL
                    link = await item.query_selector('a[href*="product"]')
                    url = await link.get_attribute('href') if link else 'N/A'
                    
                    if model and cpu_cores and cpu_cores >= self.config['SEARCH_SPECS']['cpu_cores_min']:
                        offer = {
                            'platform': platform_name,
                            'server_model': model,
                            'title': f"{model} - {cpu_cores}c {ram_gb}G",
                            'cpu_cores': cpu_cores,
                            'ram_gb': ram_gb or 0,
                            'price_text': f"{price_uah} UAH" if price_uah else "N/A",
                            'price_uah_estimated': price_uah or 0,
                            'url': url,
                            'scraped_at': datetime.now().isoformat(),
                            'condition': 'Used'
                        }
                        
                        offer['score'] = self._score_deal(offer)
                        
                        if offer['score'] > 0:
                            self.results.append(offer)
                            count += 1
                            logger.info(f"   ✅ {model}: {cpu_cores}c/{ram_gb}G - {price_uah} UAH")
                
                except Exception as e:
                    logger.warning(f"   ⚠️  Error: {e}")
            
            self.platform_stats[platform_name] = {'products_found': len(items), 'matches': count}
            logger.info(f"✅ serverparts: {count} offers found")
            
        except Exception as e:
            logger.error(f"❌ serverparts failed: {e}")
            self.platform_stats[platform_name] = {'error': str(e)}
        
        finally:
            await page.close()
    
    def _generate_report(self) -> str:
        """Generate comprehensive hunting report"""
        
        # Sort results by score
        sorted_results = sorted(self.results, key=lambda x: x.get('score', 0), reverse=True)
        
        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                    🎯 SERVER HUNT CAMPAIGN REPORT                          ║
║                                                                            ║
║          Find the Best HP DL380 / Dell R730/R740 Deals Online              ║
║                                                                            ║
║                    Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                     ║
╚════════════════════════════════════════════════════════════════════════════╝

🔍 SEARCH TARGETS:
==================
Models: HP DL380 G8/G9, Dell R730/R740
CPU: {self.config['SEARCH_SPECS']['cpu_cores_min']}+ cores minimum
RAM: {self.config['SEARCH_SPECS']['ram_gb_min']}+ GB
Price: ≤ {self.config['SEARCH_SPECS']['price_uah_max']:,} UAH ideal
Form: 2U (GPU-ready)

📊 SEARCH RESULTS:
=================
"""
        
        # Summary
        report += f"\nTotal Offers Found: {len(self.results)}\n"
        report += f"Valid Deals (Score > 0): {len([r for r in self.results if r.get('score', 0) > 0])}\n\n"
        
        # Platform stats
        report += "Platform Statistics:\n"
        for platform, stats in self.platform_stats.items():
            report += f"  {platform}: {stats}\n"
        
        # Top 5 deals
        report += f"\n🏆 TOP 5 BEST DEALS (by value score):\n"
        report += "=" * 80 + "\n"
        
        for i, offer in enumerate(sorted_results[:5], 1):
            report += f"""
{i}. {offer['server_model']} - {offer['cpu_cores']} cores / {offer['ram_gb']} GB RAM
   Platform: {offer['platform']}
   Price: {offer['price_text']}
   Estimated UAH: {offer['price_uah_estimated']:,.0f}
   Score: {offer['score']:.1f}
   URL: {offer['url']}
   Scraped: {offer['scraped_at']}
"""
        
        # All offers table
        report += f"\n📋 ALL VALID OFFERS (sorted by score):\n"
        report += "=" * 80 + "\n"
        report += f"{'Server':<20} {'Platform':<20} {'Cores/RAM':<15} {'Price UAH':<15} {'Score':<10}\n"
        report += "-" * 80 + "\n"
        
        for offer in sorted_results:
            if offer.get('score', 0) > 0:
                server = offer['server_model'][:18]
                platform = offer['platform'][:18]
                cores_ram = f"{offer['cpu_cores']}c/{offer['ram_gb']}G"
                price = f"{offer['price_uah_estimated']:,.0f}" if offer['price_uah_estimated'] > 0 else "N/A"
                score = f"{offer['score']:.0f}"
                
                report += f"{server:<20} {platform:<20} {cores_ram:<15} {price:<15} {score:<10}\n"
        
        # Price analysis
        valid_prices = [r['price_uah_estimated'] for r in sorted_results if r['price_uah_estimated'] > 0]
        if valid_prices:
            report += f"""

💰 PRICE ANALYSIS:
==================
Average Price: {sum(valid_prices) / len(valid_prices):,.0f} UAH
Lowest Price: {min(valid_prices):,.0f} UAH
Highest Price: {max(valid_prices):,.0f} UAH
Target Price: {self.config['SEARCH_SPECS']['price_uah_target']:,} UAH
"""
        
        # Negotiation recommendations
        report += """

💬 NEGOTIATION STRATEGY:
========================
1. Bundle Discount: Multiple units (2+) → 10-15% negotiable
2. Cash Payment: Immediate payment → 5-10% discount possible
3. Pickup: Self-pickup vs shipping → 5-8% savings
4. Volume Buyer: Claim bulk purchasing → 15-20% potential
5. Payment Method: Wire transfer → 3-5% discount
6. Refurbishment Date: Ask for recent refurb units → better warranty claims

⚠️  RISK ASSESSMENT:
====================
Used/Refurbished Servers:
- Check PSU health (common failure point)
- Verify all cooling fans present
- Test both CPUs (if dual-socket)
- Ask for smart data from HDDs/SSDs
- Look for physical damage markers

Warranty Considerations:
- Manufacturer warranty: 3-12 months typical
- Refurbished warranty: Usually 6-12 months
- No warranty: Only buy if price is exceptional (30%+ discount)

🎯 NEXT STEPS:
==============
1. Contact top 3 sellers immediately
2. Request detailed photos (especially cooling/PSU)
3. Ask for CPU specification confirmation
4. Negotiate bundle deals if multiple units available
5. Request shipping quotes to your location
6. Arrange technical inspection if possible

📞 CONTACT RECOMMENDATIONS:
===========================
For sellers that have multiple good units:
- "Hi! I'm interested in bulk server purchases."
- "Can you offer a discount for 2+ units?"
- "What's the best price for immediate delivery?"
- "Are you open to payment terms for bulk orders?"
"""
        
        return report
    
    async def run(self):
        """Execute complete hunting campaign"""
        logger.info("\n" + "=" * 80)
        logger.info("🎯 SERVER HUNTING CAMPAIGN - STARTING")
        logger.info("=" * 80)
        
        try:
            await self.initialize_browser()
            
            # Scrape platforms
            await self.scrape_olx_ua()
            await self.scrape_prom_ua()
            await self.scrape_serverparts()
            
            # Generate report
            logger.info("\n📝 Generating comprehensive report...")
            report = self._generate_report()
            
            # Save report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = self.output_dir / f"server_hunt_campaign_{timestamp}.txt"
            
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            
            # Save JSON data
            json_file = self.output_dir / f"server_hunt_data_{timestamp}.json"
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'offers': self.results,
                    'platform_stats': self.platform_stats,
                    'timestamp': datetime.now().isoformat(),
                    'config': self.config
                }, f, indent=2, ensure_ascii=False)
            
            # Summary
            logger.info("\n" + "=" * 80)
            logger.info("✅ SERVER HUNT CAMPAIGN COMPLETE")
            logger.info("=" * 80)
            logger.info(f"\n📊 Results:")
            logger.info(f"   Total offers found: {len(self.results)}")
            logger.info(f"   Valid deals (score > 0): {len([r for r in self.results if r.get('score', 0) > 0])}\n")
            logger.info(f"📁 Files saved to Desktop:")
            logger.info(f"   Report: {report_file.name}")
            logger.info(f"   Data JSON: {json_file.name}")
            
            return report_file, json_file
            
        except Exception as e:
            logger.error(f"\n❌ FATAL ERROR: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        finally:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            logger.info("🧹 Browser closed")


async def main():
    """Main entry point"""
    try:
        scraper = ServerHuntScraper()
        report_file, json_file = await scraper.run()
        return report_file, json_file
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    try:
        report_file, json_file = asyncio.run(main())
        print(f"\n✅ Success! Campaign complete!")
        print(f"   Report: {report_file}")
        print(f"   Data: {json_file}")
    except KeyboardInterrupt:
        print("\n⚠️  Campaign interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import sys
        sys.exit(1)
