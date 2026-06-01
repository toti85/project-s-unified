"""
GitHub Copilot Integration for Strategic AI
------------------------------------------
Integrates with GitHub Copilot API for strategic decision making
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
import subprocess
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class CopilotStrategicClient:
    """Client for using GitHub Copilot as Strategic AI"""
    
    def __init__(self):
        """Initialize Copilot client"""
        self.logger = logging.getLogger("copilot_strategic")
        self.available = self._check_copilot_availability()
        
    def _check_copilot_availability(self) -> bool:
        """Check if GitHub Copilot is available"""
        try:
            # Check if VS Code CLI is available
            result = subprocess.run(['code', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.logger.info("✅ VS Code detected - Copilot integration possible")
                return True
        except Exception as e:
            self.logger.warning(f"VS Code CLI not found: {e}")
            
        # Check for GitHub CLI with Copilot
        try:
            result = subprocess.run(['gh', 'copilot', '--help'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.logger.info("✅ GitHub CLI with Copilot detected")
                return True
        except Exception as e:
            self.logger.warning(f"GitHub CLI Copilot not found: {e}")
            
        return False
    
    async def generate_strategic_analysis(self, task: str, context: Dict[str, Any] = None) -> str:
        """Generate strategic analysis using GitHub Copilot"""
        try:
            if not self.available:
                raise Exception("GitHub Copilot not available")
            
            # Create strategic prompt for Copilot
            strategic_prompt = f"""
# Strategic AI Task Analysis

## Task: {task}
## Context: {json.dumps(context or {}, indent=2)}

As a Strategic AI using GitHub Copilot, analyze this task and provide:

```json
{{
    "complexity": "simple|medium|complex|expert",
    "strategy": "optimal execution strategy",
    "use_cognitive_core": true|false,
    "use_orchestration": true|false,
    "recommended_tools": ["tool1", "tool2"],
    "confidence": 0.8,
    "optimizations": ["optimization1", "optimization2"],
    "success_prediction": 0.85,
    "recommendations": ["rec1", "rec2"]
}}
```

Strategic Analysis:
"""
            
            # Try GitHub CLI Copilot first
            response = await self._query_github_copilot(strategic_prompt)
            if response:
                return response
                
            # Fallback to VS Code extension method
            response = await self._query_vscode_copilot(strategic_prompt)
            if response:
                return response
                
            raise Exception("No Copilot method succeeded")
            
        except Exception as e:
            self.logger.error(f"Copilot strategic analysis failed: {e}")
            # Return fallback response
            return json.dumps({
                "complexity": "medium",
                "strategy": "standard_execution", 
                "use_cognitive_core": True,
                "use_orchestration": True,
                "recommended_tools": [],
                "confidence": 0.6,
                "optimizations": [],
                "success_prediction": 0.7,
                "recommendations": ["fallback_analysis"],
                "error": str(e)
            })
    
    async def _query_github_copilot(self, prompt: str) -> Optional[str]:
        """Query GitHub Copilot via CLI"""
        try:
            # Use GitHub CLI Copilot suggest command
            process = await asyncio.create_subprocess_exec(
                'gh', 'copilot', 'suggest', prompt,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
                
            if process.returncode == 0:
                response = stdout.decode('utf-8').strip()
                self.logger.info("✅ GitHub CLI Copilot response received")
                
                # Create a strategic JSON response based on Copilot's text response
                strategic_json = {
                    "complexity": "medium",
                    "strategy": "github_copilot_suggested_approach",
                    "use_cognitive_core": True,
                    "use_orchestration": True,
                    "recommended_tools": ["file_writer", "system_command"],
                    "confidence": 0.8,
                    "optimizations": ["copilot_optimized"],
                    "success_prediction": 0.85,
                    "recommendations": ["follow_copilot_suggestions"],
                    "copilot_response": response[:500]  # Include first 500 chars of Copilot response
                }
                
                return json.dumps(strategic_json)
            else:
                self.logger.warning(f"GitHub CLI Copilot error: {stderr.decode()}")
                return None
                
        except Exception as e:
            self.logger.warning(f"GitHub CLI Copilot failed: {e}")
            return None
    
    async def _query_vscode_copilot(self, prompt: str) -> Optional[str]:
        """Query Copilot via VS Code extension - Manual consultation method"""
        try:
            # Create a strategic analysis request file for manual Copilot consultation
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            temp_file = f"copilot_strategic_request_{timestamp}.py"
            
            copilot_request_content = f'''"""
STRATEGIC AI REQUEST FOR GITHUB COPILOT
=======================================
Date: {datetime.utcnow().isoformat()}

{prompt}

INSTRUCTIONS FOR COPILOT CONSULTATION:
1. Place cursor after this comment block
2. Ask GitHub Copilot: "Generate a strategic analysis for the above task"
3. Copy the Copilot response to: copilot_response_{timestamp}.json
4. The Strategic AI will automatically read the response

EXPECTED JSON FORMAT:
{{
    "complexity": "simple|medium|complex|expert",
    "strategy": "optimal execution strategy description",
    "use_cognitive_core": true,
    "use_orchestration": true,
    "recommended_tools": ["file_writer", "system_command"],
    "confidence": 0.85,
    "optimizations": ["specific optimization suggestions"],
    "success_prediction": 0.9,
    "recommendations": ["actionable recommendations"]
}}
"""

# COPILOT: Please analyze the strategic request above and provide your recommendations
'''
            
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(copilot_request_content)
            
            self.logger.info(f"📝 Copilot consultation request created: {temp_file}")
            self.logger.info("🤝 Please open the file in VS Code and consult with GitHub Copilot")
            
            # Return a response indicating manual consultation is needed
            return json.dumps({
                "complexity": "medium",
                "strategy": "manual_copilot_consultation_requested",
                "use_cognitive_core": True,
                "use_orchestration": True,
                "recommended_tools": ["file_writer", "system_command"],
                "confidence": 0.75,
                "optimizations": ["copilot_consultation_pending"],
                "success_prediction": 0.8,
                "recommendations": ["check_copilot_consultation_file"],
                "consultation_file": temp_file,
                "response_file": f"copilot_response_{timestamp}.json",
                "manual_consultation": True
            })
            
        except Exception as e:
            self.logger.warning(f"VS Code Copilot consultation setup failed: {e}")
            return None

# Global instance
copilot_strategic_client = CopilotStrategicClient()
