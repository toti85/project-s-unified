"""
Project-S Tool Registry
---------------------
Ez a modul felelős az eszközök (tool-ok) kezeléséért és regisztrálásáért.
A rendszer központi pontjaként szolgál az elérhető eszközök számára.
"""

import os
import importlib
import inspect
import logging
import asyncio
from typing import Dict, Any, List, Optional, Set, Type, Union
import json
from pathlib import Path
import sys

_tools_dir = str(Path(__file__).parent.parent)
_repo_root = str(Path(__file__).parent.parent.parent.parent)
sys.path.insert(0, _repo_root)

from tools.tools.tool_interface import BaseTool

# Import with fallback for infrastructure components
try:
    from core.infrastructure.event_bus import event_bus
    from core.infrastructure.error_handler import error_handler
    from core.infrastructure.execution_events import get_event_logger, ExecutionEvent
except ImportError:
    # Mock for testing
    class MockEventBus:
        async def publish(self, event_type, data): pass
        def subscribe(self, event_type, handler): pass
    class MockErrorHandler:
        async def handle_error(self, error, context): return {"status": "error", "message": str(error)}
    class MockEventLogger:
        def emit(self, event): pass
    class MockExecutionEvent:
        def __init__(self, **kwargs): self.data = kwargs
    event_bus = MockEventBus()
    error_handler = MockErrorHandler()
    def get_event_logger(): return MockEventLogger()
    ExecutionEvent = MockExecutionEvent

logger = logging.getLogger(__name__)

class ToolRegistry:
    """
    Eszköz regisztráció és kezelő rendszer.
    Minden elérhető eszköz itt kerül regisztrálásra és innen érhető el.
    """
    
    def __init__(self):
        """Inicializálja a tool registry-t."""
        self.tools: Dict[str, BaseTool] = {}
        self.tool_classes: Dict[str, Type[BaseTool]] = {}
        self.categories: Dict[str, Set[str]] = {}
          # Biztonsági beállítások - FEJLESZTÉSI MÓD: minden engedélyezve
        self.security_config = {
            "allow_system_commands": True,  # Engedélyezzük a rendszerparancsokat
            "allow_file_write": True,
            "allow_network_access": True,
            "restricted_paths": [],  # Üres lista - nincs korlátozás
            "allowed_domains": ["*"],  # Engedélyezzük az összes domaint
            "max_file_size": 100 * 1024 * 1024  # 100 MB - nagyobb limit
        }
        
        # Alapértelmezett fájl elérési útvonalak
        self.default_paths = {
            "downloads": Path(__file__).parent.parent / "downloads",
            "outputs": Path(__file__).parent.parent / "outputs",
            "temp": Path(__file__).parent.parent / "temp"
        }
        
        # Létrehozzuk a szükséges mappákat
        for path in self.default_paths.values():
            os.makedirs(path, exist_ok=True)
          # Esemény feliratkozások
        event_bus.subscribe("tool.executed", self._on_tool_executed)
        event_bus.subscribe("security.violation", self._on_security_violation)
        
        # Biztonsági konfiguráció betöltése
        self.load_security_config()
        
        # Auto-register essential tools
        self._register_essential_tools()
        
        logger.info("Tool Registry inicializálva")
        
    def _register_essential_tools(self):
        """Register essential tools directly."""
        try:
            # Import and register file tools
            from tools.tools.implementations.file_tools import FileReadTool, FileWriteTool, FileSearchTool, FileContentSearchTool
            self.tools["file_reader"] = FileReadTool()
            self.tools["file_writer"] = FileWriteTool()
            self.tools["file_search"] = FileSearchTool()
            self.tools["file_content_search"] = FileContentSearchTool()
            logger.info("File tools registered successfully")
            
            # Import and register system tools
            from tools.tools.implementations.system_tools import SystemCommandTool, SystemInfoTool
            self.tools["system_command"] = SystemCommandTool()
            self.tools["system_info"] = SystemInfoTool()
            logger.info("System tools registered successfully")
            
            # Import and register PDF generator
            try:
                from tools.tools.pdf_generator import PDFGeneratorTool
                pdf_generator = PDFGeneratorTool()
                self.tools["pdf_generator"] = pdf_generator
                logger.info("PDF generator registered successfully")
            except Exception as e:
                logger.warning(f"PDF generator not available: {e}")
            
            # Import and register Web Tools
            try:
                from tools.tools.implementations.web_tools import WebScraperTool, WebAnalyzerTool, WebPageFetchTool, WebApiCallTool, WebSearchTool
                
                self.tools["web_scraper"] = WebScraperTool()
                self.tools["web_analyzer"] = WebAnalyzerTool()
                self.tools["web_page_fetch"] = WebPageFetchTool()
                self.tools["web_api_call"] = WebApiCallTool()
                self.tools["web_search"] = WebSearchTool()
                logger.info("Web tools registered successfully")
            except ImportError as e:
                logger.warning(f"Web Tools not available: {e}")
                
            # PRIMARY: Browser Automation Tool (Real Playwright - the ONLY browser automation tool)
            try:
                from tools.tools.implementations.browser_automation_tool import BrowserAutomationTool
                self.tools["browser_automation"] = BrowserAutomationTool()
                logger.info("✅ PRIMARY Browser Automation Tool (Playwright) registered - REAL browser with JS support")
            except ImportError as e:
                logger.warning(f"Browser Automation Tool not available: {e}")
            
            # NOTE: Deprecated variants (optimized_browser_automation, ultra_optimized_browser_automation)
            # are kept in codebase for reference but NOT registered. Use 'browser_automation' exclusively.
            
            
            # Import and register Tech News Aggregator Tool
            try:
                from tools.tools.implementations.tech_news_aggregator_tool import TechNewsAggregatorTool
                self.tools["tech_news_aggregator"] = TechNewsAggregatorTool()
                logger.info("Tech News Aggregator Tool registered successfully")
            except ImportError as e:
                logger.warning(f"Tech News Aggregator Tool not available: {e}")
            
            # Import and register Roblox Studio Tool
            try:
                from tools.tools.implementations.roblox_studio_tool import RobloxStudioTool
                self.tools["roblox_studio"] = RobloxStudioTool()
                logger.info("✅ Roblox Studio Tool registered successfully")
            except ImportError as e:
                logger.warning(f"Roblox Studio Tool not available: {e}")
            
            # Update categories - browser_automation is the PRIMARY browser tool only
            self.categories.setdefault("file", set()).update(["file_reader", "file_writer", "file_search", "pdf_generator"])
            self.categories.setdefault("system", set()).update(["system_command", "system_info"])
            self.categories.setdefault("web", set()).update(["web_scraper", "web_analyzer", "web_page_fetch", "web_api_call", "web_search"])
            self.categories.setdefault("browser", set()).update(["browser_automation"])  # PRIMARY ONLY
            self.categories.setdefault("complex", set()).update(["tech_news_aggregator"])
            self.categories.setdefault("game_dev", set()).update(["roblox_studio"])
            
            logger.info(f"Essential tools registered: {len(self.tools)} tools available")
            
        except ImportError as e:
            logger.warning(f"Could not import essential tools: {e}")
        except Exception as e:
            logger.error(f"Error registering essential tools: {e}")
        
    async def load_tools(self, tools_dir: Optional[str] = None) -> int:
        """
        Betölti az összes elérhető eszközt a megadott könyvtárból.
        
        Args:
            tools_dir: Opcionális könyvtár útvonal, alapértelmezetten 'tools' mappa
            
        Returns:
            int: A betöltött eszközök száma
        """
        if tools_dir is None:
            tools_dir = Path(__file__).parent
            
        tools_path = Path(tools_dir)
        loaded_count = 0
        
        # Csak a python fájlokat vesszük figyelembe, kivéve az __init__.py és interfész fájlokat
        for file_path in tools_path.glob("**/*.py"):
            if file_path.name.startswith("__") or file_path.name == "tool_interface.py" or file_path.name == "tool_registry.py":
                continue
                
            relative_path = file_path.relative_to(Path(__file__).parent.parent)
            module_path = str(relative_path).replace("/", ".").replace("\\", ".").replace(".py", "")
            
            try:
                module = importlib.import_module(module_path)
                
                # Keressük a BaseTool leszármazottjait a modulban
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, BaseTool) and 
                        obj != BaseTool):
                        
                        # Csak akkor regisztráljuk, ha még nincs ilyen nevű
                        if name not in self.tool_classes:
                            self.tool_classes[name] = obj
                            loaded_count += 1
                            logger.debug(f"Tool osztály betöltve: {name} from {module_path}")
            
            except Exception as e:
                logger.error(f"Hiba történt a tool betöltése közben ({module_path}): {str(e)}")
        
        logger.info(f"Összesen {loaded_count} tool osztály betöltve")
        return loaded_count
        
    def register_tool(self, tool_instance: BaseTool) -> bool:
        """
        Regisztrál egy eszköz példányt.
        
        Args:
            tool_instance: A regisztrálandó eszköz példány
            
        Returns:
            bool: True, ha sikeres volt a regisztráció
        """
        name = tool_instance.name
        
        if name in self.tools:
            logger.warning(f"Már létezik '{name}' nevű eszköz, frissítés...")
            
        self.tools[name] = tool_instance
        
        # Kategória kezelése
        category = tool_instance.category
        if category not in self.categories:
            self.categories[category] = set()
            
        self.categories[category].add(name)
        
        logger.debug(f"Tool regisztrálva: {name} (kategória: {category})")
        return True
        
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        Lekér egy eszközt név alapján.
        
        Args:
            name: Az eszköz neve
            
        Returns:
            Optional[BaseTool]: Az eszköz, ha létezik, egyébként None
        """
        # Ha már létezik példány, visszaadja
        if name in self.tools:
            return self.tools[name]
        
        # Ha nem létezik példány, de ismerjük az osztályt, létrehozzuk
        if name in self.tool_classes:
            try:
                tool_instance = self.tool_classes[name]()
                self.register_tool(tool_instance)
                return tool_instance
            except Exception as e:
                logger.error(f"Hiba történt a tool példányosítása közben ({name}): {str(e)}")
                
        return None
        
    def list_tools(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Listázza az elérhető eszközöket, opcionálisan kategória szerint szűrve.
        
        Args:
            category: Opcionális kategória szűrés
            
        Returns:
            List[Dict[str, Any]]: Az elérhető eszközök listája
        """
        result = []
        
        # Ha van kategória szűrés
        if category:
            if category not in self.categories:
                return []
                
            tool_names = self.categories[category]
        else:
            # Az összes tool név a regisztrált és ismert osztályokból
            tool_names = set(self.tools.keys()) | set(self.tool_classes.keys())
        
        # Információk összegyűjtése
        for name in tool_names:
            tool = self.get_tool(name)
            if tool:
                result.append(tool.get_info())
                
        return result
        
    async def execute_tool(self, name: str, **kwargs) -> Dict[str, Any]:
        """
        Végrehajt egy eszközt a megadott paraméterekkel.
        Emits structured execution events for telemetry.
        
        Args:
            name: Az eszköz neve
            **kwargs: Az eszközhöz tartozó paraméterek
            
        Returns:
            Dict[str, Any]: Az eredmény szótár formában
        """
        import uuid
        task_id = kwargs.pop("_task_id", str(uuid.uuid4())[:8])
        
        start_time = asyncio.get_event_loop().time()
        event_logger = get_event_logger()
        
        tool = self.get_tool(name)
        if not tool:
            error_msg = f"Az eszköz nem található: {name}"
            logger.error(error_msg)
            
            # Emit failure event
            event = ExecutionEvent(
                event_type="tool_failure",
                tool_name=name,
                task_id=task_id,
                error=error_msg,
                error_type="tool_not_found",
                params=kwargs
            )
            event_logger.emit(event)
            
            return {"error": error_msg, "success": False}
        
        try:
            # Emit invocation event
            invocation_event = ExecutionEvent(
                event_type="tool_invocation",
                tool_name=name,
                task_id=task_id,
                params=kwargs
            )
            event_logger.emit(invocation_event)
            
            # Végrehajtás
            result = await tool.execute(**kwargs)
            
            # Teljesítmény mérése
            execution_time = asyncio.get_event_loop().time() - start_time
            
            # Determine success
            success = result.get("success", True) if isinstance(result, dict) else True
            
            # Emit success event
            success_event = ExecutionEvent(
                event_type="tool_success",
                tool_name=name,
                task_id=task_id,
                execution_time=execution_time,
                params=kwargs,
                result_keys=list(result.keys()) if isinstance(result, dict) else None
            )
            event_logger.emit(success_event)
            
            # Esemény közzététele (legacy event bus)
            await event_bus.publish("tool.executed", {
                "tool": name,
                "execution_time": execution_time,
                "success": success,
                "parameters": kwargs
            })
            
            # Alapértelmezetten adjunk hozzá success kulcsot, ha nincs
            if isinstance(result, dict) and "success" not in result:
                result["success"] = True
            
            # Adjuk hozzá az execution_time-t
            if isinstance(result, dict):
                result["execution_time"] = execution_time
            
            return result
            
        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            error_msg = str(e)
            
            # Emit failure event with error details
            failure_event = ExecutionEvent(
                event_type="tool_failure",
                tool_name=name,
                task_id=task_id,
                error=error_msg,
                error_type=type(e).__name__,
                execution_time=execution_time,
                params=kwargs
            )
            event_logger.emit(failure_event)
            
            logger.error(f"Tool {name} execution failed: {e}")
            
            await event_bus.publish("execution.failed", {
                "tool": name,
                "error": error_msg,
                "execution_time": execution_time
            })
            
            return {
                "error": error_msg,
                "success": False,
                "execution_time": execution_time,
                "error_type": type(e).__name__
            }
            
        except Exception as e:
            logger.error(f"Hiba történt a tool ({name}) végrehajtása közben: {str(e)}")
            
            # Hibajelentés
            error_msg = str(e)
            error_context = {"component": "tool_registry", "tool": name, "parameters": kwargs}
            await error_handler.handle_error(e, error_context)
            
            # Esemény közzététele
            execution_time = asyncio.get_event_loop().time() - start_time
            await event_bus.publish("tool.executed", {
                "tool": name,
                "execution_time": execution_time,
                "success": False,
                "error": error_msg,
                "parameters": kwargs
            })
            
            return {
                "error": error_msg,
                "success": False,
                "execution_time": execution_time
            }
            
    async def _on_tool_executed(self, data: Dict[str, Any]) -> None:
        """Eszköz végrehajtás esemény kezelése."""
        tool_name = data.get("tool", "unknown")
        success = data.get("success", False)
        execution_time = data.get("execution_time", 0)
        
        # Itt további elemzéseket vagy naplózást lehetne végezni
        
    async def _on_security_violation(self, data: Dict[str, Any]) -> None:
        """Biztonsági esemény kezelése."""
        logger.warning(f"Biztonsági esemény észlelve: {data.get('violation_type')} - {data.get('details')}")
        
        # További biztonsági lépések itt
        
    def load_security_config(self, config_path: Optional[str] = None) -> bool:
        """
        Betölti a biztonsági beállításokat egy konfigurációs fájlból.
        
        Args:
            config_path: A konfigurációs fájl elérési útja
            
        Returns:
            bool: True, ha sikeres volt a betöltés
        """
        if not config_path:
            config_path = Path(__file__).parent.parent / "config" / "tool_security.json"
            
        try:
            if Path(config_path).exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.security_config.update(config)
                    logger.info(f"Biztonsági konfiguráció betöltve: {config_path}")
                    return True
            else:
                logger.info(f"Biztonsági konfiguráció nem található, alapértelmezett beállítások használata")
                return False
                
        except Exception as e:
            logger.error(f"Hiba történt a biztonsági konfiguráció betöltése közben: {str(e)}")
            return False

    def check_security(self, 
                    operation_type: str, 
                    details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ellenőrzi, hogy egy művelet megfelel-e a biztonsági előírásoknak.
        
        Args:
            operation_type: A művelet típusa (pl. "file_write", "network_access")
            details: A művelet részletei
            
        Returns:
            Dict[str, Any]: Az ellenőrzés eredménye
        """
        if operation_type == "file_write" and not self.security_config["allow_file_write"]:
            return {
                "allowed": False,
                "reason": "Fájl írási műveletek nem engedélyezettek a biztonsági beállítások alapján"
            }
            
        if operation_type == "system_command" and not self.security_config["allow_system_commands"]:
            return {
                "allowed": False,
                "reason": "Rendszerparancsok végrehajtása nem engedélyezett a biztonsági beállítások alapján"
            }
            
        if operation_type == "network_access" and not self.security_config["allow_network_access"]:
            return {
                "allowed": False,
                "reason": "Hálózati hozzáférés nem engedélyezett a biztonsági beállítások alapján"
            }
            
        # Fájl műveletekre specifikus ellenőrzések
        if operation_type in ["file_write", "file_read"]:
            file_path = details.get("path", "")
            
            # Korlátozott útvonalak ellenőrzése
            for restricted in self.security_config["restricted_paths"]:
                if str(file_path).startswith(restricted):
                    return {
                        "allowed": False,
                        "reason": f"A megadott útvonal ({file_path}) korlátozott: {restricted}"
                    }
                    
            # Fájlméret ellenőrzése írásnál
            if operation_type == "file_write" and details.get("size", 0) > self.security_config["max_file_size"]:
                return {
                    "allowed": False,
                    "reason": f"A fájl mérete ({details.get('size', 0)} bájt) meghaladja a megengedett méretet ({self.security_config['max_file_size']} bájt)"
                }
                
        # Hálózati hozzáférések ellenőrzése
        if operation_type == "network_access":
            domain = details.get("domain", "")
            allowed_domains = self.security_config["allowed_domains"]
            
            if "*" not in allowed_domains and domain not in allowed_domains:
                return {
                    "allowed": False,
                    "reason": f"A megadott domain ({domain}) nem engedélyezett"
                }
                
        # Minden ellenőrzés sikerült
        return {
            "allowed": True,
            "reason": "A művelet megfelel a biztonsági előírásoknak"
        }

# Singleton példány létrehozása
tool_registry = ToolRegistry()
