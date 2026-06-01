"""
Strategic AI Overlay - Lightweight Integration
--------------------------------------------
This module adds Strategic AI capabilities to the existing working Project-S V2 system
without breaking the core functionality that already works.

Strategy: Minimal intervention, maximum enhancement
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import json

from integrations.ai_models.multi_model_ai_client import AIClient

logger = logging.getLogger(__name__)

class StrategicOverlay:
    """
    Lightweight Strategic AI overlay that enhances existing Project-S V2
    without disrupting working functionality.
    """
    
    def __init__(self):
        self.ai_client = AIClient()
        self.strategic_model = "qwen/qwen-2.5-72b-instruct:free"  # Qwen3 235B
        self.logger = logger
        
        # Keep original system intact, just add strategic layer
        self.original_system_intact = True
        
        logger.info("🧠 Strategic AI Overlay initialized - preserving original functionality")
    
    async def strategic_pre_analysis(self, task: str) -> Dict[str, Any]:
        """
        Strategic analysis BEFORE task execution - lightweight overlay.
        Returns strategic guidance without interfering with core system.
        """
        try:
            strategic_prompt = f"""
            As Strategic AI (Qwen3 235B), analyze this task for optimal execution:
            
            TASK: {task}
            
            Provide strategic guidance in JSON format:
            {{
                "complexity": "simple|medium|complex",
                "confidence": 0.0-1.0,
                "recommended_approach": "direct|multi_step|iterative",
                "optimization_notes": "brief guidance for execution",
                "preserve_original": true
            }}
            
            Focus on enhancing, not replacing, the existing working system.
            """
            
            response = await self.ai_client.generate_response(
                prompt=strategic_prompt,
                model=self.strategic_model
            )
            
            # Parse strategic guidance
            try:
                if "```json" in response:
                    json_start = response.find("```json") + 7
                    json_end = response.find("```", json_start)
                    json_str = response[json_start:json_end].strip()
                elif "{" in response:
                    json_start = response.find("{")
                    json_end = response.rfind("}") + 1
                    json_str = response[json_start:json_end]
                else:
                    json_str = '{"complexity": "medium", "confidence": 0.7, "recommended_approach": "direct"}'
                
                strategic_guidance = json.loads(json_str)
                strategic_guidance["preserve_original"] = True
                
                logger.info(f"🎯 Strategic guidance: {strategic_guidance.get('recommended_approach', 'direct')} approach")
                return strategic_guidance
                
            except Exception as parse_e:
                logger.warning(f"Strategic parsing failed: {parse_e}")
                return {
                    "complexity": "medium",
                    "confidence": 0.7,
                    "recommended_approach": "direct", 
                    "optimization_notes": "Use original system capabilities",
                    "preserve_original": True
                }
                
        except Exception as e:
            logger.error(f"Strategic analysis failed: {e}")
            return {
                "complexity": "medium",
                "confidence": 0.5,
                "recommended_approach": "direct",
                "optimization_notes": "Fallback to original system",
                "preserve_original": True
            }
    
    async def strategic_post_analysis(self, task: str, result: Any) -> Dict[str, Any]:
        """
        Strategic analysis AFTER task execution - learn and optimize.
        """
        try:
            # Simple success detection
            success = result is not None and str(result) != "None"
            
            meta_learning = {
                "task": task,
                "timestamp": datetime.utcnow().isoformat(),
                "success": success,
                "strategic_enhancement": "overlay_applied",
                "original_system_preserved": True
            }
            
            logger.info(f"🎓 Strategic learning: {'success' if success else 'improvement_needed'}")
            return meta_learning
            
        except Exception as e:
            logger.error(f"Strategic post-analysis failed: {e}")
            return {"status": "error", "message": str(e)}
