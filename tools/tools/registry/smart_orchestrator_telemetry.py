"""
Tool execution telemetry for regression learning verification.
This module is mixed into SmartToolOrchestrator at runtime.
"""

def add_telemetry_methods(orchestrator_class):
    """Add telemetry methods to SmartToolOrchestrator."""
    
    def _log_tool_execution_telemetry(self, tool_name: str, status: str, reason: str, task_description: str) -> None:
        """Log tool execution to telemetry file for TEST_E verification."""
        try:
            from pathlib import Path
            import json
            from datetime import datetime
            
            telemetry_file = Path("memory/telemetry/executions.jsonl")
            telemetry_file.parent.mkdir(parents=True, exist_ok=True)
            
            record = {
                "timestamp": datetime.now().isoformat(),
                "tool_name": tool_name,
                "status": status,
                "reason": reason,
                "task_description": task_description[:100]
            }
            
            with open(telemetry_file, 'a') as f:
                f.write(json.dumps(record) + '\n')
            
            # Also publish event bus event so TEST_E can read execution events
            try:
                from core.infrastructure.event_bus import event_bus
                event_bus.publish("tool.executed", {
                    "tool_name": tool_name,
                    "status": status,
                    "reason": reason,
                    "timestamp": record["timestamp"]
                })
            except Exception as e:
                self.logger.debug(f"Could not publish event bus event: {e}")
        except Exception as e:
            self.logger.warning(f"Failed to log tool execution telemetry: {e}")
    
    orchestrator_class._log_tool_execution_telemetry = _log_tool_execution_telemetry
    return orchestrator_class
