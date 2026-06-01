#!/usr/bin/env python3
"""
Knowledge Manager — Project-S Knowledge Layer v1
Manages system state, generates context documents, provides AI briefings.

Usage:
    from knowledge.knowledge_manager import KnowledgeManager
    
    km = KnowledgeManager()
    state = km.read_state()
    km.update_state("phase.current_task", "pattern_learning_library")
    km.generate_context()  # writes master_context.md
    briefing = km.generate_briefing("coder")  # short context for coding AI
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


class KnowledgeManager:
    """Manages Project-S knowledge layer: state, context, decisions, briefings."""
    
    def __init__(self, knowledge_dir: Optional[str] = None):
        """Initialize with knowledge directory path."""
        if knowledge_dir:
            self.knowledge_dir = Path(knowledge_dir)
        else:
            # Default: knowledge/ directory relative to this file
            self.knowledge_dir = Path(__file__).parent
        
        self.state_file = self.knowledge_dir / "project_state.json"
        self.context_file = self.knowledge_dir / "master_context.md"
        self.decisions_file = self.knowledge_dir / "decisions.jsonl"
        
        # Ensure knowledge directory exists
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
    
    # =========================================================================
    # STATE MANAGEMENT
    # =========================================================================
    
    def read_state(self) -> dict:
        """Load project_state.json and return as dict."""
        if not self.state_file.exists():
            raise FileNotFoundError(f"State file not found: {self.state_file}")
        
        with open(self.state_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def write_state(self, state: dict) -> None:
        """Write full state dict to project_state.json."""
        state["meta"]["last_updated"] = datetime.now(timezone.utc).isoformat()
        state["meta"]["updated_by"] = "knowledge_manager"
        
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    
    def update_state(self, key_path: str, value: Any) -> dict:
        """
        Update a specific field in project_state.json using dot notation.
        
        Examples:
            km.update_state("phase.current_task", "pattern_learning")
            km.update_state("models.available_count", 5)
            km.update_state("system.status", "maintenance")
        """
        state = self.read_state()
        
        keys = key_path.split(".")
        target = state
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        
        target[keys[-1]] = value
        self.write_state(state)
        return state
    
    def get_state(self, key_path: str) -> Any:
        """
        Get a specific value from state using dot notation.
        
        Examples:
            km.get_state("system.status")  # "operational"
            km.get_state("models.available_count")  # 4
        """
        state = self.read_state()
        
        keys = key_path.split(".")
        target = state
        for key in keys:
            if isinstance(target, dict) and key in target:
                target = target[key]
            else:
                return None
        return target
    
    # =========================================================================
    # DECISION LOGGING
    # =========================================================================
    
    def log_decision(self, category: str, decision: str, reasoning: str, 
                     outcome: Optional[str] = None, confidence: float = 0.0) -> None:
        """
        Append a decision to decisions.jsonl.
        
        Args:
            category: model_selection | tool_selection | task_priority | architecture | strategy
            decision: What was decided
            reasoning: Why
            outcome: Result (can be updated later)
            confidence: 0.0-1.0
        """
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "category": category,
            "decision": decision,
            "reasoning": reasoning,
            "outcome": outcome,
            "confidence": confidence
        }
        
        with open(self.decisions_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    def get_recent_decisions(self, count: int = 10, category: Optional[str] = None) -> list:
        """Get the most recent N decisions, optionally filtered by category."""
        if not self.decisions_file.exists():
            return []
        
        decisions = []
        with open(self.decisions_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entry = json.loads(line)
                        if category is None or entry.get("category") == category:
                            decisions.append(entry)
                    except json.JSONDecodeError:
                        continue
        
        return decisions[-count:]
    
    # =========================================================================
    # CONTEXT GENERATION
    # =========================================================================
    
    def generate_context(self) -> str:
        """
        Generate master_context.md from current project_state.json.
        Writes to file AND returns the content.
        """
        state = self.read_state()
        
        # Build context document
        lines = []
        lines.append("# PROJECT-S — MASTER CONTEXT (Auto-Generated)")
        lines.append(f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
        lines.append(f"**Source:** project_state.json v{state['meta']['schema_version']}")
        lines.append(f"**System Status:** {state['system']['status'].upper()}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # System overview
        lines.append("## System Overview")
        sys = state["system"]
        lines.append(f"- **Entry point:** `{sys['entry_point']}`")
        lines.append(f"- **Startup time:** {sys['startup_time_seconds']}s")
        lines.append(f"- **Codebase:** `{sys['codebase']}/`")
        lines.append(f"- **Platform:** {sys['platform']} / Python {sys['python_version']}")
        lines.append("")
        
        # Models
        lines.append("## AI Models")
        models = state["models"]
        lines.append(f"- **Available:** {models['available_count']} / {models['total_configured']} configured")
        lines.append(f"- **Fallback chain:** {' → '.join(models['fallback_chain'])}")
        lines.append("")
        for name, info in models["configured"].items():
            status = "✅" if info.get("available", False) else "❌"
            reason = f" ({info['reason']})" if not info.get("available", False) and "reason" in info else ""
            lines.append(f"  - {status} **{name}** [{info['provider']}] — {info['role']}{reason}")
        lines.append("")
        
        # Components
        lines.append("## Components")
        for group_name, group in state["components"].items():
            lines.append(f"### {group_name.replace('_', ' ').title()}")
            for comp_name, comp in group.items():
                status_icon = "✅" if comp["status"] == "working" else "⚠️"
                loc = f" — `{comp['file']}`" if "file" in comp else ""
                lines.append(f"  - {status_icon} **{comp_name}**: {comp['status']}{loc}")
            lines.append("")
        
        # Memory
        lines.append("## Memory & Evidence")
        mem = state["memory"]
        lines.append(f"- **Total records:** {mem['total_records']:,}")
        lines.append(f"- **Learning:** {mem['learning_records']} records (`{mem['learning_file']}`)")
        lines.append(f"- **Meta-evidence:** {mem['meta_evidence_records']:,} records")
        lines.append(f"- **Telemetry:** {mem['execution_events']} events")
        lines.append("")
        
        # Phase
        lines.append("## Current Phase")
        phase = state["phase"]
        lines.append(f"- **Phase:** {phase['current']}")
        lines.append(f"- **Current task:** {phase['current_task']}")
        lines.append(f"- **Next tasks:** {', '.join(phase['next_tasks'])}")
        lines.append(f"- **Phase 1 completed:** {phase['phase_1_completed']} (score: {phase['phase_1_score']})")
        lines.append("")
        
        # Not implemented
        lines.append("## Not Yet Implemented")
        for item in state["not_implemented"]:
            lines.append(f"- {item}")
        lines.append("")
        
        # Recent decisions
        recent = self.get_recent_decisions(5)
        if recent:
            lines.append("## Recent Decisions (last 5)")
            for d in recent:
                lines.append(f"- [{d['timestamp'][:10]}] **{d['category']}**: {d['decision']}")
            lines.append("")
        
        content = "\n".join(lines)
        
        # Write to file
        with open(self.context_file, "w", encoding="utf-8") as f:
            f.write(content)
        
        return content
    
    # =========================================================================
    # AI BRIEFINGS
    # =========================================================================
    
    def generate_briefing(self, role: str = "general") -> str:
        """
        Generate a SHORT briefing for a specific AI role.
        
        Roles:
            general  — Full overview (default)
            coder    — Focus on code structure, tools, file paths
            reviewer — Focus on architecture, decisions, what's working/broken
            strategist — Focus on phase, priorities, what to build next
        
        Returns a string suitable for pasting into an AI system prompt.
        """
        state = self.read_state()
        
        # Common header
        header = (
            f"Project-S is an autonomous multi-AI agent system. "
            f"Status: {state['system']['status']}. "
            f"Codebase: {state['system']['codebase']}/. "
            f"Models: {state['models']['available_count']}/{state['models']['total_configured']} available. "
            f"Phase: {state['phase']['current']}, task: {state['phase']['current_task']}."
        )
        
        if role == "coder":
            # Coder needs file paths and tool info
            components = []
            for group in state["components"].values():
                for name, info in group.items():
                    if "file" in info:
                        components.append(f"  {name}: {info['file']} ({info['status']})")
            
            return (
                f"{header}\n\n"
                f"Key files:\n"
                f"  Entry: main.py\n"
                f"  AI client: {state['components']['golden_age']['ai_client']['file']}\n"
                f"  Config: {state['config']['model_config']}\n"
                f"  Tools: {state['tools']['registry_file']}\n\n"
                f"Components:\n" + "\n".join(components)
            )
        
        elif role == "reviewer":
            # Reviewer needs architecture state and decisions
            working = []
            partial = []
            for group in state["components"].values():
                for name, info in group.items():
                    if info["status"] == "working":
                        working.append(name)
                    else:
                        partial.append(f"{name} ({info['status']})")
            
            recent = self.get_recent_decisions(3)
            decision_text = "\n".join(
                f"  [{d['category']}] {d['decision']}" for d in recent
            ) if recent else "  No recent decisions logged."
            
            return (
                f"{header}\n\n"
                f"Working: {', '.join(working)}\n"
                f"Partial/Issues: {', '.join(partial) if partial else 'none'}\n"
                f"Not built: {', '.join(state['not_implemented'])}\n\n"
                f"Recent decisions:\n{decision_text}"
            )
        
        elif role == "strategist":
            return (
                f"{header}\n\n"
                f"Phase 1 completed {state['phase']['phase_1_completed']} ({state['phase']['phase_1_score']}).\n"
                f"Current task: {state['phase']['current_task']}\n"
                f"Next: {', '.join(state['phase']['next_tasks'])}\n"
                f"Not built yet: {', '.join(state['not_implemented'])}\n\n"
                f"Infrastructure: DL380 Gen9 {state['infrastructure']['dl380_gen9']['status']} "
                f"({state['infrastructure']['dl380_gen9']['specs']})\n"
                f"Memory: {state['memory']['total_records']:,} total records"
            )
        
        else:  # general
            return self.generate_context()
    
    # =========================================================================
    # UTILITY
    # =========================================================================
    
    def health_check(self) -> dict:
        """Quick health check of knowledge layer files."""
        return {
            "state_file_exists": self.state_file.exists(),
            "context_file_exists": self.context_file.exists(),
            "decisions_file_exists": self.decisions_file.exists(),
            "state_readable": self._can_read_json(self.state_file),
            "knowledge_dir": str(self.knowledge_dir)
        }
    
    def _can_read_json(self, path: Path) -> bool:
        """Check if a JSON file is readable and valid."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                json.load(f)
            return True
        except (FileNotFoundError, json.JSONDecodeError):
            return False


# =============================================================================
# CLI INTERFACE — run directly for quick operations
# =============================================================================

if __name__ == "__main__":
    import sys
    
    km = KnowledgeManager()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python knowledge_manager.py status        — Show system status")
        print("  python knowledge_manager.py context       — Generate master_context.md")
        print("  python knowledge_manager.py briefing [role] — Generate AI briefing")
        print("  python knowledge_manager.py health        — Knowledge layer health check")
        print("  python knowledge_manager.py get <key>     — Get state value (dot notation)")
        print("  python knowledge_manager.py set <key> <value> — Set state value")
        print("")
        print("Roles: general, coder, reviewer, strategist")
        sys.exit(0)
    
    command = sys.argv[1]
    
    if command == "status":
        state = km.read_state()
        print(f"System: {state['system']['status']}")
        print(f"Phase: {state['phase']['current']}")
        print(f"Task: {state['phase']['current_task']}")
        print(f"Models: {state['models']['available_count']}/{state['models']['total_configured']}")
        print(f"Memory: {state['memory']['total_records']:,} records")
    
    elif command == "context":
        content = km.generate_context()
        print(f"Generated master_context.md ({len(content)} chars)")
        print(f"Location: {km.context_file}")
    
    elif command == "briefing":
        role = sys.argv[2] if len(sys.argv) > 2 else "general"
        print(km.generate_briefing(role))
    
    elif command == "health":
        health = km.health_check()
        for key, value in health.items():
            status = "✅" if value else "❌"
            print(f"  {status} {key}: {value}")
    
    elif command == "get":
        if len(sys.argv) < 3:
            print("Usage: python knowledge_manager.py get <key_path>")
            sys.exit(1)
        value = km.get_state(sys.argv[2])
        print(json.dumps(value, indent=2) if isinstance(value, (dict, list)) else value)
    
    elif command == "set":
        if len(sys.argv) < 4:
            print("Usage: python knowledge_manager.py set <key_path> <value>")
            sys.exit(1)
        key_path = sys.argv[2]
        value = sys.argv[3]
        # Try to parse as JSON (for numbers, bools, etc.)
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            pass  # keep as string
        km.update_state(key_path, value)
        print(f"Updated: {key_path} = {value}")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
