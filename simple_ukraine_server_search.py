#!/usr/bin/env python3
"""
SIMPLE UKRAINE SERVER SEARCH
====================================
Standalone browser scraper using Playwright directly (NO Meta Layer)

Features:
- Direct Playwright browser automation
- No browser-use library complexity
- Simple error handling
- Real webpage content extraction
- Saved output for later analysis

Usage:
    python simple_ukraine_server_search.py
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'scrape_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

class UkraineServerScraper:
    """Direct Playwright-based scraper for Ukrainian server marketplaces"""
    
    def __init__(self):
        self.browser = None
        self.context = None
        self.scraped_data = {}
        self.output_dir = Path.home() / "Desktop"
        
    async def initialize(self):
        """Initialize Playwright browser"""
        logger.info("🚀 Initializing Playwright browser...")
        
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=False,  # Show browser window
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
            ]
        )
        
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        logger.info("✅ Browser initialized successfully")
        
    async def scrape_serverparts(self):
        """Scrape serverparts.com.ua for server offers"""
        logger.info("\n📍 SCRAPING: serverparts.com.ua")
        logger.info("=" * 70)
        
        page = await self.context.new_page()
        
        try:
            # Navigate to website
            logger.info("🌐 Navigating to serverparts.com.ua...")
            await page.goto('https://serverparts.com.ua/', wait_until='networkidle', timeout=30000)
            
            # Wait for dynamic content
            await page.wait_for_timeout(3000)
            
            # Try to find server listings
            logger.info("🔍 Searching for server listings...")
            
            # Look for category or search
            try:
                # Try to find servers category
                await page.click('.category-link:has-text("Серверы")', timeout=5000)
                await page.wait_for_timeout(2000)
            except:
                logger.warning("⚠️ Server category not found, trying search...")
                # Fallback: use search
                search_box = await page.query_selector('input[placeholder*="Search"], input[placeholder*="Поиск"]')
                if search_box:
                    await search_box.fill('HP DL380')
                    await page.press('input', 'Enter')
                    await page.wait_for_timeout(3000)
            
            # Extract page content
            logger.info("📄 Extracting page content...")
            
            # Get page text
            page_text = await page.evaluate('() => document.body.innerText')
            
            # Get structured data if available
            listings = await page.evaluate('''() => {
                const items = [];
                document.querySelectorAll('[data-product], .product-item, .listing-item, article').forEach(el => {
                    items.push({
                        text: el.innerText,
                        html_snippet: el.innerHTML.substring(0, 500)
                    });
                });
                return items;
            }''')
            
            # Process data
            self.scraped_data['serverparts.com.ua'] = {
                'url': 'https://serverparts.com.ua/',
                'timestamp': datetime.now().isoformat(),
                'page_text_length': len(page_text),
                'page_text_preview': page_text[:2000],
                'listings_found': len(listings),
                'listings_preview': listings[:3] if listings else []
            }
            
            logger.info(f"✅ Extracted {len(page_text)} characters from serverparts.com.ua")
            logger.info(f"   Found {len(listings)} potential listings")
            
        except Exception as e:
            logger.error(f"❌ Error scraping serverparts.com.ua: {e}")
            self.scraped_data['serverparts.com.ua'] = {'error': str(e)}
        
        finally:
            await page.close()
    
    async def scrape_server_ua(self):
        """Scrape server.ua for server offers"""
        logger.info("\n📍 SCRAPING: server.ua")
        logger.info("=" * 70)
        
        page = await self.context.new_page()
        
        try:
            logger.info("🌐 Navigating to server.ua...")
            await page.goto('https://server.ua/ua', wait_until='networkidle', timeout=30000)
            
            await page.wait_for_timeout(3000)
            
            logger.info("🔍 Searching for enterprise servers...")
            
            # Try to find servers section
            try:
                await page.click('a:has-text("Сервери"), a:has-text("Server")', timeout=5000)
                await page.wait_for_timeout(2000)
            except:
                logger.warning("⚠️ Server section not found")
            
            # Extract content
            logger.info("📄 Extracting page content...")
            
            page_text = await page.evaluate('() => document.body.innerText')
            
            listings = await page.evaluate('''() => {
                const items = [];
                document.querySelectorAll('[data-offer], .offer-item, .product, .item').forEach(el => {
                    items.push({
                        text: el.innerText,
                        href: el.href || el.querySelector('a')?.href
                    });
                });
                return items;
            }''')
            
            self.scraped_data['server.ua'] = {
                'url': 'https://server.ua/ua',
                'timestamp': datetime.now().isoformat(),
                'page_text_length': len(page_text),
                'page_text_preview': page_text[:2000],
                'listings_found': len(listings),
                'listings_preview': listings[:3] if listings else []
            }
            
            logger.info(f"✅ Extracted {len(page_text)} characters from server.ua")
            logger.info(f"   Found {len(listings)} potential listings")
            
        except Exception as e:
            logger.error(f"❌ Error scraping server.ua: {e}")
            self.scraped_data['server.ua'] = {'error': str(e)}
        
        finally:
            await page.close()
    
    async def scrape_it_komplekt(self):
        """Scrape it-komplekt.com.ua for server offers"""
        logger.info("\n📍 SCRAPING: it-komplekt.com.ua")
        logger.info("=" * 70)
        
        page = await self.context.new_page()
        
        try:
            logger.info("🌐 Navigating to it-komplekt.com.ua...")
            await page.goto('https://it-komplekt.com.ua/', wait_until='networkidle', timeout=30000)
            
            await page.wait_for_timeout(3000)
            
            logger.info("🔍 Searching for servers category...")
            
            try:
                await page.click('a:has-text("Сервери")', timeout=5000)
                await page.wait_for_timeout(2000)
            except:
                logger.warning("⚠️ Server category not found")
            
            # Extract content
            logger.info("📄 Extracting page content...")
            
            page_text = await page.evaluate('() => document.body.innerText')
            
            self.scraped_data['it-komplekt.com.ua'] = {
                'url': 'https://it-komplekt.com.ua/',
                'timestamp': datetime.now().isoformat(),
                'page_text_length': len(page_text),
                'page_text_preview': page_text[:2000]
            }
            
            logger.info(f"✅ Extracted {len(page_text)} characters from it-komplekt.com.ua")
            
        except Exception as e:
            logger.error(f"❌ Error scraping it-komplekt.com.ua: {e}")
            self.scraped_data['it-komplekt.com.ua'] = {'error': str(e)}
        
        finally:
            await page.close()
    
    async def scrape_prom(self):
        """Scrape prom.ua for server offers"""
        logger.info("\n📍 SCRAPING: prom.ua")
        logger.info("=" * 70)
        
        page = await self.context.new_page()
        
        try:
            logger.info("🌐 Navigating to prom.ua and searching for servers...")
            url = 'https://prom.ua/ua/search?q=HP%20DL380'
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            await page.wait_for_timeout(3000)
            
            logger.info("📄 Extracting search results...")
            
            page_text = await page.evaluate('() => document.body.innerText')
            
            self.scraped_data['prom.ua'] = {
                'url': url,
                'timestamp': datetime.now().isoformat(),
                'page_text_length': len(page_text),
                'page_text_preview': page_text[:2000]
            }
            
            logger.info(f"✅ Extracted {len(page_text)} characters from prom.ua")
            
        except Exception as e:
            logger.error(f"❌ Error scraping prom.ua: {e}")
            self.scraped_data['prom.ua'] = {'error': str(e)}
        
        finally:
            await page.close()
    
    async def save_results(self):
        """Save scraped data to files"""
        logger.info("\n💾 SAVING RESULTS")
        logger.info("=" * 70)
        
        # Save as JSON
        json_file = self.output_dir / f'ukraine_servers_scraped_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.scraped_data, f, indent=2, ensure_ascii=False)
        logger.info(f"✅ JSON saved: {json_file}")
        
        # Save as text report
        report_file = self.output_dir / f'ukraine_servers_scraped_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("UKRAINE SERVER MARKETPLACES - SCRAPED DATA\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Scrape Date: {datetime.now()}\n\n")
            
            for site, data in self.scraped_data.items():
                f.write(f"\n{'='*80}\n")
                f.write(f"SITE: {site}\n")
                f.write(f"URL: {data.get('url', 'N/A')}\n")
                f.write(f"Data Length: {data.get('page_text_length', 0)} characters\n")
                f.write(f"{'='*80}\n\n")
                
                if 'error' in data:
                    f.write(f"ERROR: {data['error']}\n")
                else:
                    f.write(f"PREVIEW:\n{data.get('page_text_preview', 'No data')}\n")
                f.write("\n")
        
        logger.info(f"✅ Report saved: {report_file}")
        
        return json_file, report_file
    
    async def cleanup(self):
        """Clean up browser resources"""
        logger.info("\n🧹 CLEANUP")
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        logger.info("✅ Browser closed")
    
    async def run(self):
        """Execute full scraping pipeline"""
        logger.info("\n" + "=" * 80)
        logger.info("🚀 UKRAINE SERVER MARKETPLACE SCRAPER (STANDALONE)")
        logger.info("=" * 80 + "\n")
        
        try:
            await self.initialize()
            
            # Scrape all sites
            await self.scrape_serverparts()
            await self.scrape_server_ua()
            await self.scrape_it_komplekt()
            await self.scrape_prom()
            
            # Save results
            json_file, report_file = await self.save_results()
            
            # Summary
            logger.info("\n" + "=" * 80)
            logger.info("✅ SCRAPING COMPLETE")
            logger.info("=" * 80)
            logger.info(f"\n📊 Scraped {len(self.scraped_data)} websites")
            logger.info(f"📁 Files saved:")
            logger.info(f"   - JSON: {json_file}")
            logger.info(f"   - Report: {report_file}")
            
            # Show total data extracted
            total_chars = sum(
                data.get('page_text_length', 0) 
                for data in self.scraped_data.values() 
                if 'error' not in data
            )
            logger.info(f"\n📈 Total data extracted: {total_chars:,} characters")
            
            return json_file, report_file
            
        except Exception as e:
            logger.error(f"\n❌ FATAL ERROR: {e}")
            raise
        
        finally:
            await self.cleanup()


async def main():
    """Main entry point"""
    scraper = UkraineServerScraper()
    json_file, report_file = await scraper.run()
    return json_file, report_file


if __name__ == "__main__":
    try:
        json_file, report_file = asyncio.run(main())
        print(f"\n✅ Success! Files ready for AI analysis:")
        print(f"  JSON: {json_file}")
        print(f"  Report: {report_file}")
    except KeyboardInterrupt:
        print("\n⚠️ Scraping interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
