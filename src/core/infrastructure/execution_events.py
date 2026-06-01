"""
Structured execution telemetry framework.
Every tool invocation emits a structured event to execution_events.jsonl.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ExecutionEvent:
    """Structured execution event."""
    
    def __init__(
        self,
        event_type: str,  # "tool_invocation", "tool_success", "tool_failure", etc.
        tool_name: str,
        task_id: str,
        timestamp: Optional[str] = None,
        **kwargs
    ):
        self.event_type = event_type
        self.tool_name = tool_name
        self.task_id = task_id
        self.timestamp = timestamp or datetime.utcnow().isoformat()
        self.data = kwargs
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "tool_name": self.tool_name,
            "task_id": self.task_id,
            "timestamp": self.timestamp,
            **self.data
        }


class ExecutionEventLogger:
    """
    Append-only structured event logger for execution telemetry.
    Writes to execution_events.jsonl.
    """
    
    def __init__(self, events_file: str = "memory/intelligence/execution_events.jsonl"):
        self.events_file = events_file
        os.makedirs(os.path.dirname(events_file), exist_ok=True)
    
    def emit(self, event: ExecutionEvent) -> None:
        """Append event to execution_events.jsonl."""
        try:
            with open(self.events_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event.to_dict()) + "\n")
            logger.debug(f"Event logged: {event.event_type} {event.tool_name}")
        except Exception as e:
            logger.error(f"Failed to log execution event: {e}")
    
    def read_recent(self, limit: int = 100) -> list:
        """Read last N events from execution_events.jsonl."""
        try:
            if not os.path.exists(self.events_file):
                return []
            
            events = []
            with open(self.events_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                # Read last `limit` lines
                for line in lines[-limit:]:
                    if line.strip():
                        events.append(json.loads(line))
            return events
        except Exception as e:
            logger.error(f"Failed to read execution events: {e}")
            return []
    
    def filter_by_tool(self, tool_name: str, event_type: Optional[str] = None) -> list:
        """Filter events by tool name and optionally event type."""
        events = self.read_recent(limit=200)
        filtered = [
            e for e in events 
            if e.get("tool_name") == tool_name
            and (event_type is None or e.get("event_type") == event_type)
        ]
        return filtered
    
    def get_failures_for_tool(self, tool_name: str) -> list:
        """Get all failure events for a specific tool."""
        return self.filter_by_tool(tool_name, event_type="tool_failure")


# Global singleton
_event_logger = None


def get_event_logger() -> ExecutionEventLogger:
    """Get or create the global event logger."""
    global _event_logger
    if _event_logger is None:
        _event_logger = ExecutionEventLogger()
    return _event_logger
