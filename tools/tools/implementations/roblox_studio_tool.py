#!/usr/bin/env python3
"""
Roblox Studio Tool - Integration with Roblox Studio IDE
========================================================

Allows Project-S to interact with Roblox Studio:
- Launch Roblox Studio
- Create new game projects
- Open existing projects
- Execute Roblox Lua scripts
"""

import os
import sys
import json
import logging
import asyncio
import subprocess
import time
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import winreg  # Windows registry access

from tools.tools.tool_interface import BaseTool

logger = logging.getLogger(__name__)


class RobloxStudioTool(BaseTool):
    """
    Roblox Studio Integration Tool
    
    Provides programmatic access to Roblox Studio IDE:
    - Launch Studio instance
    - Create new game projects
    - Open existing projects
    - Read/write place files
    - Execute Lua commands
    """
    
    def __init__(self):
        super().__init__()
        self.name = "roblox_studio"
        self.description = "Launch Roblox Studio, create new games, and manage Roblox projects"
        self.parameters = {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["launch", "create_game", "open_project", "get_info"],
                    "description": "Action to perform: launch (Studio), create_game (new project), open_project (existing), get_info (system info)"
                },
                "game_name": {
                    "type": "string",
                    "description": "Name for new game project (required for create_game)"
                },
                "project_path": {
                    "type": "string",
                    "description": "Path to project file (for open_project)"
                },
                "game_location": {
                    "type": "string",
                    "description": "Directory to create game in (optional, defaults to Documents)"
                }
            },
            "required": ["action"]
        }
        
        self.studio_exe = None
        self.projects_dir = None
        self._discover_roblox_studio()
    
    def _discover_roblox_studio(self):
        """Discover Roblox Studio executable path and projects directory."""
        try:
            # Method 1: Direct file system search in known locations
            versions_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "Roblox", "Versions")
            if os.path.exists(versions_dir):
                # Find latest RobloxStudio exe
                for version_folder in sorted(os.listdir(versions_dir), reverse=True):
                    exe_paths = [
                        os.path.join(versions_dir, version_folder, "RobloxStudio.exe"),
                        os.path.join(versions_dir, version_folder, "RobloxStudioBeta.exe")
                    ]
                    for exe_path in exe_paths:
                        if os.path.exists(exe_path):
                            self.studio_exe = exe_path
                            logger.info(f"✅ Roblox Studio found: {self.studio_exe}")
                            break
                    if self.studio_exe:
                        break
            
            # Method 2: Try Windows registry if Method 1 didn't work
            if not self.studio_exe and sys.platform == "win32":
                try:
                    key = winreg.OpenKey(
                        winreg.HKEY_CURRENT_USER,
                        r"SOFTWARE\Classes\roblox-studio\shell\open\command"
                    )
                    cmd_value, _ = winreg.QueryValueEx(key, "(Default)")
                    exe_path = cmd_value.split('"')[1]
                    if os.path.exists(exe_path):
                        self.studio_exe = exe_path
                        logger.info(f"✅ Roblox Studio found (registry): {self.studio_exe}")
                    winreg.CloseKey(key)
                except Exception as e:
                    logger.debug(f"Registry lookup failed: {e}")
            
            # Setup projects directory (in user Documents)
            docs_path = os.path.join(os.path.expanduser("~"), "Documents", "Roblox Projects")
            os.makedirs(docs_path, exist_ok=True)
            self.projects_dir = docs_path
            logger.info(f"✅ Projects directory: {self.projects_dir}")
            
        except Exception as e:
            logger.error(f"Failed to discover Roblox Studio: {e}")
            self.studio_exe = None
    
    async def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute Roblox Studio action."""
        try:
            if not self.studio_exe or not os.path.exists(self.studio_exe):
                return {
                    "success": False,
                    "error": f"Roblox Studio not found. Looked for: {self.studio_exe}",
                    "action": action
                }
            
            if action == "launch":
                return await self._launch_studio()
            elif action == "create_game":
                game_name = kwargs.get("game_name")
                if not game_name:
                    return {"success": False, "error": "game_name is required for create_game"}
                return await self._create_new_game(game_name, kwargs.get("game_location"))
            elif action == "open_project":
                project_path = kwargs.get("project_path")
                if not project_path:
                    return {"success": False, "error": "project_path is required for open_project"}
                return await self._open_project(project_path)
            elif action == "get_info":
                return await self._get_info()
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        
        except Exception as e:
            logger.error(f"Error in RobloxStudioTool.execute: {e}")
            return {
                "success": False,
                "error": str(e),
                "action": action
            }
    
    async def _launch_studio(self) -> Dict[str, Any]:
        """Launch Roblox Studio."""
        try:
            logger.info("🚀 Launching Roblox Studio...")
            
            # Launch without arguments opens Studio normally
            process = subprocess.Popen(
                [self.studio_exe],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            logger.info(f"✅ Roblox Studio started (PID: {process.pid})")
            
            # Give it time to start
            await asyncio.sleep(3)
            
            return {
                "success": True,
                "action": "launch",
                "status": "Roblox Studio launched",
                "pid": process.pid,
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Failed to launch Roblox Studio: {e}")
            return {
                "success": False,
                "error": str(e),
                "action": "launch"
            }
    
    async def _create_new_game(self, game_name: str, location: Optional[str] = None) -> Dict[str, Any]:
        """Create a new Roblox game project."""
        try:
            logger.info(f"🎮 Creating new Roblox game: {game_name}")
            
            # Use provided location or default
            base_dir = location or self.projects_dir
            project_path = os.path.join(base_dir, game_name)
            
            # Create project directory
            os.makedirs(project_path, exist_ok=True)
            logger.info(f"📁 Project directory created: {project_path}")
            
            # Create a basic place file (RBXL format is binary, so create metadata)
            metadata = {
                "game_name": game_name,
                "created_at": datetime.now().isoformat(),
                "creator": "Project-S",
                "version": 1,
                "description": f"Roblox game created by Project-S AI system",
                "game_id": None,
                "universe_id": None
            }
            
            metadata_file = os.path.join(project_path, "metadata.json")
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"📄 Metadata created: {metadata_file}")
            
            # Create a placeholder main.lua script file
            main_lua = os.path.join(project_path, "main.lua")
            with open(main_lua, "w") as f:
                f.write("""-- Main Game Script for: {}
-- Created by Project-S AI System
-- Created at: {}

-- Initialize game
local game = game
local workspace = workspace

-- Function to setup the game
local function setupGame()
    print("Game initialized")
end

-- Setup and run
setupGame()

-- Game loop would go here
while true do
    wait(0.1)
end
""".format(game_name, datetime.now().isoformat()))
            logger.info(f"🔧 Main script created: {main_lua}")
            
            # Launch Roblox Studio with this new game using protocol
            try:
                logger.info(f"🚀 Opening in Roblox Studio...")
                # Use roblox-studio protocol to create new place
                studio_url = f"roblox-studio://new"
                subprocess.Popen([self.studio_exe, studio_url])
                await asyncio.sleep(2)
            except Exception as e:
                logger.warning(f"Could not auto-open in Studio: {e}")
            
            return {
                "success": True,
                "action": "create_game",
                "game_name": game_name,
                "project_path": project_path,
                "metadata_file": metadata_file,
                "main_script": main_lua,
                "status": "Game project created successfully",
                "timestamp": datetime.now().isoformat(),
                "next_steps": [
                    "1. Open project directory to view files",
                    "2. Launch Roblox Studio manually if not auto-opened",
                    "3. Load the game metadata and scripts",
                    "4. Begin game development"
                ]
            }
        
        except Exception as e:
            logger.error(f"Failed to create game: {e}")
            return {
                "success": False,
                "error": str(e),
                "action": "create_game",
                "game_name": game_name
            }
    
    async def _open_project(self, project_path: str) -> Dict[str, Any]:
        """Open an existing project in Roblox Studio."""
        try:
            if not os.path.exists(project_path):
                return {
                    "success": False,
                    "error": f"Project path not found: {project_path}",
                    "action": "open_project"
                }
            
            logger.info(f"📂 Opening project: {project_path}")
            
            # Try to open with Roblox Studio
            subprocess.Popen([self.studio_exe, project_path])
            await asyncio.sleep(2)
            
            return {
                "success": True,
                "action": "open_project",
                "project_path": project_path,
                "status": "Project opened in Roblox Studio",
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Failed to open project: {e}")
            return {
                "success": False,
                "error": str(e),
                "action": "open_project",
                "project_path": project_path
            }
    
    async def _get_info(self) -> Dict[str, Any]:
        """Get information about Roblox Studio installation."""
        try:
            info = {
                "studio_installed": self.studio_exe is not None and os.path.exists(self.studio_exe),
                "studio_path": self.studio_exe,
                "projects_directory": self.projects_dir,
                "platform": sys.platform,
                "timestamp": datetime.now().isoformat()
            }
            
            if info["studio_installed"]:
                # Get Studio file info
                stat = os.stat(self.studio_exe)
                info["studio_size_mb"] = stat.st_size / (1024 * 1024)
                info["studio_modified"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
                
                # List existing projects
                if os.path.exists(self.projects_dir):
                    projects = [d for d in os.listdir(self.projects_dir) 
                               if os.path.isdir(os.path.join(self.projects_dir, d))]
                    info["existing_projects"] = projects
                    info["project_count"] = len(projects)
                
                logger.info("✅ Roblox Studio info retrieved")
                return {
                    "success": True,
                    "action": "get_info",
                    "data": info
                }
            else:
                return {
                    "success": False,
                    "error": "Roblox Studio not installed",
                    "data": info
                }
        
        except Exception as e:
            logger.error(f"Failed to get info: {e}")
            return {
                "success": False,
                "error": str(e),
                "action": "get_info"
            }
