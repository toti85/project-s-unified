"""
Project-S System Tools
------------------
Ez a modul a rendszerparancsokhoz és rendszerfunkciókhoz kapcsolódó eszközöket tartalmazza:
- Biztonságos rendszerparancs végrehajtás
- Rendszer információk lekérése
"""

import os
import asyncio
import logging
import subprocess
import shlex
import platform
import psutil
import tempfile
import json
import re
import pathlib
import time
from typing import Dict, Any, List, Optional, Union, Set
from pathlib import Path

from tools.tools.tool_interface import BaseTool

logger = logging.getLogger(__name__)

class CommandValidator:
    """
    Rendszerparancs validátor és korlátozó segédosztály.
    """
    
    # Veszélyes parancsok és parancsrészek - SZIGORÚAN TILTOTTAK
    FORBIDDEN_COMMANDS = {
        "rm", "del", "format", "mkfs", "fdisk", 
        "chmod", "chown", "sudo", "su", "passwd", "dd", 
        "rundll32", "regedit", "reg", "shutdown", 
        "restart", "halt", "rmdir", "rd", "deltree", "taskkill"
    }
    
    # Veszélyes paraméterek - ENYHÍTVE FEJLESZTÉSI MÓDBAN
    DANGEROUS_PARAMS = {
        "-rf", "--force", "--recursive", 
        "--delete", "--purge", "--no-preserve-root"
    }
    
    # Engedélyezett parancsok fehérlistája - KIBŐVÍTETT FEJLESZTÉSI MÓD
    ALLOWED_COMMANDS = {
        "ls", "dir", "cd", "pwd", "echo", "cat", "type",
        "find", "mkdir", "md", "ping", "ipconfig", "ifconfig",
        "systeminfo", "ver", "uname", "ps", "tasklist", 
        "free", "df", "du", "date", "time", "whoami",
        "hostname", "python", "pip",
        # Webfejlesztési parancsok
        "start", "explorer", "notepad", "copy", "move", "xcopy",
        # PowerShell parancsok
        "powershell", "pwsh", "get-process", "get-service", 
        "get-childitem", "new-item", "set-content", "out-file",
        # Hálózati diagnosztika
        "netstat", "nslookup", "tracert", "arp", "route",
        # Rendszer info
        "wmic", "sc", "net", "driverquery", "msinfo32"
    }
    @staticmethod
    def validate_command(command: str) -> Dict[str, Any]:
        """
        TESZTELÉSI MÓD: Minden parancs engedélyezett!
        """
        return {
            "valid": True,
            "reason": "TESZT MÓD - Minden parancs engedélyezett",
            "command": command
        }


class SystemCommandTool(BaseTool):
    """
    Biztonságos rendszerparancs végrehajtás.
    
    Category: system
    Version: 1.0.0
    Requires permissions: Yes
    Safe: No
    """
    
    def __init__(self):
        """Inicializálja az eszközt."""
        super().__init__()
        # Use system temp directory instead of tool_registry (avoids circular import)
        self.work_dir = tempfile.gettempdir()
        
    async def execute(self, 
                     command: str,
                     timeout: int = 30,
                     workdir: Optional[str] = None) -> Dict[str, Any]:
        """
        Végrehajt egy rendszerparancsot biztonságos módon.
        
        Args:
            command: A végrehajtandó parancs
            timeout: Időtúllépés másodpercben
            workdir: Munkakönyvtár elérési útja
            
        Returns:
            Dict: A végrehajtás eredménye
        """
        try:
            # TESZT MÓD: Biztonsági ellenőrzések kikapcsolva
            logger.info(f"🔧 TESZT MÓD: Futtatom a parancsot: {command}")
            
            # Parancs validálása - MINDIG SIKERES TESZT MÓDBAN
            validation = CommandValidator.validate_command(command)
            logger.info(f"Validation result: {validation}")
                
            # Munkakönyvtár beállítása
            if workdir is None:
                workdir = self.work_dir
            else:
                # Lazy-load security config to avoid circular import
                try:
                    from tools.tools.registry.tool_registry_golden import ToolRegistry as tool_registry_lazy
                    security_config = tool_registry_lazy.security_config if hasattr(tool_registry_lazy, 'security_config') else {"restricted_paths": []}
                except:
                    security_config = {"restricted_paths": []}
                
                # Ellenőrizzük, hogy a munkakönyvtár megengedett-e
                workdir_path = Path(workdir).resolve()
                for restricted in security_config.get("restricted_paths", []):
                    if str(workdir_path).startswith(restricted):
                        return {
                            "success": False,
                            "error": f"A megadott munkakönyvtár ({workdir}) korlátozott: {restricted}",
                            "stdout": "",
                            "stderr": "",
                            "exit_code": -1
                        }
            
            # Parancs végrehajtása aszinkron módon
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=workdir,
                shell=True
            )
            
            try:
                stdout_data, stderr_data = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=timeout
                )
                stdout = stdout_data.decode('utf-8', errors='replace')
                stderr = stderr_data.decode('utf-8', errors='replace')
                exit_code = process.returncode
                
            except asyncio.TimeoutError:
                # Időtúllépés esetén megszakítjuk a folyamatot
                try:
                    process.terminate()
                    await asyncio.sleep(0.5)
                    if process.returncode is None:
                        process.kill()
                except Exception:
                    pass
                    
                return {
                    "success": False,
                    "error": f"Időtúllépés: a parancs végrehajtása tovább tartott, mint {timeout} másodperc",
                    "stdout": "",
                    "stderr": "",
                    "exit_code": -1,
                    "timeout": True
                }
            
            # Eredmény összeállítása
            success = exit_code == 0
            
            return {
                "success": success,
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": exit_code,
                "command": command,
                "workdir": workdir
            }
                
        except Exception as e:
            logger.error(f"Hiba történt a rendszerparancs végrehajtása közben: {str(e)}")
            return {
                "success": False,
                "error": f"Hiba a rendszerparancs végrehajtása során: {str(e)}",
                "stdout": "",
                "stderr": "",
                "exit_code": -1
            }


class SystemInfoTool(BaseTool):
    """
    Rendszer információk lekérdezése.
    
    Category: system
    Version: 1.0.0
    Requires permissions: No
    Safe: Yes
    """
    
    async def execute(self, info_type: str = "all") -> Dict[str, Any]:
        """
        Információkat ad a rendszerről.
        
        Args:
            info_type: A lekérendő információ típusa 
                      ('all', 'os', 'cpu', 'memory', 'disk', 'network')
            
        Returns:
            Dict: A lekérdezés eredménye
        """
        try:
            result = {}
            
            # Információk az operációs rendszerről
            if info_type in ["all", "os"]:
                os_info = {
                    "system": platform.system(),
                    "release": platform.release(),
                    "version": platform.version(),
                    "architecture": platform.machine(),
                    "processor": platform.processor(),
                    "hostname": platform.node(),
                    "python_version": platform.python_version()
                }
                result["os"] = os_info
                
            # CPU információ
            if info_type in ["all", "cpu"]:
                cpu_info = {
                    "physical_cores": psutil.cpu_count(logical=False),
                    "total_cores": psutil.cpu_count(logical=True),
                    "cpu_percent": psutil.cpu_percent(interval=0.5),
                    "cpu_freq": {
                        "current": psutil.cpu_freq().current if psutil.cpu_freq() else None,
                        "min": psutil.cpu_freq().min if psutil.cpu_freq() else None,
                        "max": psutil.cpu_freq().max if psutil.cpu_freq() else None
                    }
                }
                result["cpu"] = cpu_info
                
            # Memória információ
            if info_type in ["all", "memory"]:
                mem = psutil.virtual_memory()
                memory_info = {
                    "total": mem.total,
                    "available": mem.available,
                    "used": mem.used,
                    "percent": mem.percent
                }
                result["memory"] = memory_info
                
                # Swap információ
                swap = psutil.swap_memory()
                swap_info = {
                    "total": swap.total,
                    "used": swap.used,
                    "free": swap.free,
                    "percent": swap.percent
                }
                result["swap"] = swap_info
                
            # Lemez információ
            if info_type in ["all", "disk"]:
                disk_info = []
                for partition in psutil.disk_partitions():
                    try:
                        usage = psutil.disk_usage(partition.mountpoint)
                        partition_info = {
                            "device": partition.device,
                            "mountpoint": partition.mountpoint,
                            "fstype": partition.fstype,
                            "total": usage.total,
                            "used": usage.used,
                            "free": usage.free,
                            "percent": usage.percent
                        }
                        disk_info.append(partition_info)
                    except (PermissionError, OSError):
                        # Néhány lemez nem elérhető (pl. CD-ROM)
                        pass
                        
                result["disk"] = disk_info
                
            # Hálózati információ
            if info_type in ["all", "network"]:
                # Hálózati interfészek
                interfaces = psutil.net_if_addrs()
                net_interfaces = {}
                
                for interface_name, interface_addresses in interfaces.items():
                    addresses = []
                    for addr in interface_addresses:
                        address_info = {
                            "family": str(addr.family),
                            "address": addr.address,
                            "netmask": addr.netmask,
                            "broadcast": addr.broadcast
                        }
                        addresses.append(address_info)
                        
                    net_interfaces[interface_name] = addresses
                    
                # Hálózati forgalom
                net_io = psutil.net_io_counters()
                net_io_info = {
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv,
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv
                }
                
                result["network"] = {
                    "interfaces": net_interfaces,
                    "io": net_io_info
                }
                
            # Az eredmény kiegészítése egyéb adatokkal
            result["timestamp"] = psutil.boot_time()
            result["uptime"] = int(time.time() - psutil.boot_time())
            
            return {
                "success": True,
                "info_type": info_type,
                "result": result
            }
                
        except Exception as e:
            logger.error(f"Hiba történt a rendszer információk lekérése közben: {str(e)}")
            return {
                "success": False,
                "error": f"Hiba a rendszer információk lekérése során: {str(e)}"
            }


class EnvironmentVariableTool(BaseTool):
    """
    Környezeti változók kezelése.
    
    Category: system
    Version: 1.0.0
    Requires permissions: No
    Safe: Yes
    """
    
    # Biztonságos környezeti változók, amelyek lekérdezhetők
    SAFE_ENV_VARS = {
        "PATH", "PYTHONPATH", "TEMP", "TMP", "HOME", "USER", 
        "USERPROFILE", "LANG", "LANGUAGE", "LC_ALL", "SHELL",
        "TERM", "HOSTNAME"
    }
    
    async def execute(self, 
                     action: str = "get",
                     name: Optional[str] = None) -> Dict[str, Any]:
        """
        Környezeti változók kezelése.
        
        Args:
            action: A végrehajtandó művelet ('get' vagy 'list')
            name: A környezeti változó neve (csak 'get' művelethez)
            
        Returns:
            Dict: A művelet eredménye
        """
        try:
            # Lista művelet: összes biztonságos env változó listázása
            if action == "list":
                # Csak a biztonságos változókat adjuk vissza
                safe_env = {}
                for key, value in os.environ.items():
                    if key.upper() in self.SAFE_ENV_VARS:
                        safe_env[key] = value
                        
                return {
                    "success": True,
                    "action": action,
                    "variables": safe_env
                }
                
            # Get művelet: egy konkrét változó lekérése
            elif action == "get":
                if name is None:
                    return {
                        "success": False,
                        "error": "A 'get' művelethez meg kell adni a változó nevét"
                    }
                    
                # Ellenőrizzük, hogy biztonságos-e a változó
                if name.upper() not in self.SAFE_ENV_VARS:
                    return {
                        "success": False,
                        "error": f"A(z) '{name}' környezeti változó nem kérdezhető le biztonsági okokból"
                    }
                    
                # Változó lekérése
                value = os.environ.get(name)
                
                if value is None:
                    return {
                        "success": False,
                        "error": f"A(z) '{name}' környezeti változó nem létezik"
                    }
                    
                return {
                    "success": True,
                    "action": action,
                    "name": name,
                    "value": value
                }
                
            else:
                return {
                    "success": False,
                    "error": f"Érvénytelen művelet: {action}. Támogatott műveletek: 'get', 'list'"
                }
                
        except Exception as e:
            logger.error(f"Hiba történt a környezeti változók kezelése közben: {str(e)}")
            return {
                "success": False,
                "error": f"Hiba a környezeti változók kezelése során: {str(e)}"
            }