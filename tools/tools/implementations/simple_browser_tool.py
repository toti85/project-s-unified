"""
SimpleBrowserTool - Adapter for browser.open_url

ADAPTER PATTERN:
- Primary: UltraOptimizedBrowserAutomationTool (Playwright + browser-use + LLM)
- Fallback: WebPageFetchTool (HTTP fetch with HTML parsing)

Unified JSON contract:
  {
    "ok": bool,
    "url": str,
    "title": str,
    "extracted": str,
    "status_code": int,
    "error": str (if any)
  }
"""

import asyncio
import logging
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class SimpleBrowserTool:
    """
    DEPRECATED: This tool is deprecated. DO NOT USE for browser automation.
    ============================================================
    
    **PURPOSE:** HTTP-fetch only for web page content retrieval (NON-INTERACTIVE, NO JAVASCRIPT)
    
    **IMPORTANT:** For browser tasks requiring:
      - JavaScript execution
      - Interactive navigation
      - Clicking elements
      - Session management
      - Visual rendering
    
    USE 'browser_automation' (Playwright-based) DIRECTLY.
    
    **THIS TOOL:** HTTP-only fetch via WebPageFetchTool
      - Simple HTTP GET + HTML parsing (BeautifulSoup)
      - No API key required
      - STATIC CONTENT ONLY (no JavaScript execution)
    """
    
    def __init__(self):
        self.name = "browser.open_url"
        self.description = "Open a URL and extract page title and content (primary: Playwright, fallback: HTTP)"
        self.parameters = {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL to open"
                },
                "extract_text": {
                    "type": "boolean",
                    "description": "Extract page text content (default: True)",
                    "default": True
                },
                "max_length": {
                    "type": "integer",
                    "description": "Maximum characters to extract (default: 1000)",
                    "default": 1000
                },
                "use_browser": {
                    "type": "boolean",
                    "description": "Prefer Playwright browser automation if available (default: True)",
                    "default": True
                }
            },
            "required": ["url"]
        }
        self.last_result = None
        self._primary_tool = None
        self._fallback_tool = None
        self._init_primary_and_fallback()
    
    def _init_primary_and_fallback(self):
        """Initialize primary and fallback tools."""
        # Try to load primary: UltraOptimizedBrowserAutomationTool
        try:
            from tools.tools.implementations.ultra_optimized_browser_automation_tool import UltraOptimizedBrowserAutomationTool
            api_key = os.getenv('OPENROUTER_API_KEY') or os.getenv('OPENAI_API_KEY')
            if api_key:
                self._primary_tool = UltraOptimizedBrowserAutomationTool()
                logger.info("[PRIMARY] UltraOptimizedBrowserAutomationTool loaded")
            else:
                logger.debug("[PRIMARY] No API key - fallback will be used")
        except Exception as e:
            logger.debug(f"[PRIMARY] Not available ({e})")
        
        # Load fallback: WebPageFetchTool
        try:
            from tools.tools.implementations.web_tools import WebPageFetchTool
            self._fallback_tool = WebPageFetchTool()
            logger.info("[FALLBACK] WebPageFetchTool loaded")
        except Exception as e:
            logger.warning(f"[FALLBACK] Not available ({e})")
    
    async def execute(self, url: str, extract_text: bool = True, max_length: int = 1000, 
                      use_browser: bool = True, **kwargs) -> Dict[str, Any]:
        """
        Execute browser.open_url adapter.
        
        Strategy:
        1. If use_browser=True and primary tool available: try primary
        2. If primary fails or not available: try fallback
        3. If fallback fails: return error
        """
        
        # Validate URL
        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"
        
        logger.info(f"🔗 browser.open_url: {url} (extract_text={extract_text}, use_browser={use_browser})")
        
        # Try PRIMARY: Playwright browser automation
        if use_browser and self._primary_tool:
            try:
                logger.debug(f"  → Attempting PRIMARY path (UltraOptimizedBrowserAutomationTool)...")
                result = await self._execute_primary(url, extract_text, max_length)
                if result and result.get("ok"):
                    logger.info(f"✅ PRIMARY succeeded: {result.get('status_code')}")
                    self.last_result = result
                    return result
                else:
                    logger.debug(f"  → PRIMARY returned error, trying FALLBACK...")
            except Exception as e:
                logger.debug(f"  → PRIMARY failed ({e}), trying FALLBACK...")
        
        # Try FALLBACK: HTTP fetch
        if self._fallback_tool:
            try:
                logger.debug(f"  → Attempting FALLBACK path (WebPageFetchTool)...")
                result = await self._execute_fallback(url, extract_text, max_length)
                if result and result.get("ok"):
                    logger.info(f"✅ FALLBACK succeeded: {result.get('status_code')}")
                    self.last_result = result
                    return result
            except Exception as e:
                logger.debug(f"  → FALLBACK also failed ({e})")
        
        # Both paths failed
        error_msg = "Both PRIMARY and FALLBACK paths failed"
        logger.error(f"❌ {error_msg}")
        result = {
            "ok": False,
            "url": url,
            "error": error_msg,
            "title": None,
            "extracted": None,
            "status_code": None
        }
        self.last_result = result
        return result
    
    async def _execute_primary(self, url: str, extract_text: bool, max_length: int) -> Dict[str, Any]:
        """
        Execute primary path: UltraOptimizedBrowserAutomationTool.
        
        Converts from browser-use format to unified JSON contract.
        """
        try:
            # Create task: "Navigate to URL and extract title and main text content"
            task = f"Navigate to {url}, wait for page load, then return the page title and first 1000 characters of main text content"
            
            # Execute via primary tool
            result = await self._primary_tool.execute(
                task=task,
                max_steps=2,
                headless=True,
                timeout=30
            )
            
            if not result or not result.get("success", False):
                return {"ok": False, "error": str(result.get("error", "Unknown error"))}
            
            # Extract from browser-use result
            output = result.get("result") or result.get("output") or ""
            
            # Parse title and content from output
            title = None
            extracted = output[:max_length] if output else None
            
            return {
                "ok": True,
                "url": url,
                "title": title,
                "extracted": extracted,
                "status_code": 200,
                "error": None
            }
        except Exception as e:
            logger.debug(f"Primary execution failed: {e}")
            return None
    
    async def _execute_fallback(self, url: str, extract_text: bool, max_length: int) -> Dict[str, Any]:
        """
        Execute fallback path: WebPageFetchTool.
        
        Returns unified JSON contract.
        WebPageFetchTool returns: {success, status_code, title, text, html, ...}
        """
        try:
            # Call WebPageFetchTool
            result = await self._fallback_tool.execute(
                url=url,
                extract_text=extract_text,
                timeout=10
            )
            
            if not result or not result.get("success", False):
                return {
                    "ok": False,
                    "url": url,
                    "error": result.get("error", "HTTP fetch failed") if result else "No response",
                    "title": None,
                    "extracted": None,
                    "status_code": result.get("status_code") if result else None
                }
            
            # Extract from WebPageFetchTool result
            # It already extracts title and text, just pass them through
            title = result.get("title")
            extracted = result.get("text", "")
            
            # Truncate if needed
            if extracted:
                extracted = extracted[:max_length]
            
            return {
                "ok": result.get("success", False),
                "url": url,
                "title": title,
                "extracted": extracted if extracted else None,
                "status_code": result.get("status_code", 200),
                "error": None
            }
        except Exception as e:
            logger.debug(f"Fallback execution failed: {e}")
            return None
    
    def __call__(self, *args, **kwargs):
        """Allow tool to be called directly."""
        return asyncio.run(self.execute(*args, **kwargs))
