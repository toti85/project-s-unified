"""
Evaluator Agent - Assesses tool execution results and triggers replanning
This component evaluates whether tool execution achieved the intended goal
and can trigger replanning or self-improvement actions when needed.
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import statistics

# Add parent directory to path for imports
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

# Import components
from core.infrastructure.event_bus import event_bus
from core.infrastructure.error_handler import error_handler
from core.infrastructure.execution_events import get_event_logger, ExecutionEvent
from utils.performance_monitor import monitor_performance, EnhancedLogger

# AI client might not be available during infrastructure tests
try:
    from integrations.ai_models.multi_model_ai_client import AIClient
except ImportError:
    # Mock AI client for testing
    class AIClient:
        async def generate_response(self, prompt, model="gpt-3.5-turbo"):
            return '{"success": true, "confidence": 0.8, "goal_achieved": true, "assessment": "Mock evaluation", "recommendations": {"action": "continue", "reason": "Mock response"}}'

@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    timestamp: str
    metric_name: str
    value: float
    context: Dict[str, Any]
    domain: str = "general"

@dataclass 
class StrategicInsight:
    """Strategic insight from system analysis"""
    timestamp: str
    insight_type: str  # performance, pattern, optimization, risk
    description: str
    confidence: float
    evidence: Dict[str, Any]
    recommendations: List[str]
    impact_level: str  # low, medium, high, critical

@dataclass
class LearningPattern:
    """Learning pattern discovered by the system"""
    pattern_id: str
    pattern_type: str  # workflow, execution, error, success
    frequency: int
    success_rate: float
    context_conditions: Dict[str, Any]
    optimization_potential: float

class PerformanceTracker:
    """Tracks system performance metrics and trends"""
    
    def __init__(self):
        self.metrics_history: List[PerformanceMetric] = []
        self.performance_trends: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.domain_performance: Dict[str, List[float]] = defaultdict(list)
        
    def record_metric(self, name: str, value: float, context: Dict[str, Any] = None, domain: str = "general"):
        """Record a performance metric"""
        metric = PerformanceMetric(
            timestamp=datetime.utcnow().isoformat(),
            metric_name=name,
            value=value,
            context=context or {},
            domain=domain
        )
        
        self.metrics_history.append(metric)
        self.performance_trends[name].append((datetime.utcnow(), value))
        self.domain_performance[domain].append(value)
        
    def get_performance_trend(self, metric_name: str, hours: int = 24) -> List[Tuple[datetime, float]]:
        """Get performance trend for specific metric"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return [(ts, val) for ts, val in self.performance_trends[metric_name] 
                if ts >= cutoff_time]
                
    def get_domain_performance(self, domain: str) -> Dict[str, float]:
        """Get performance statistics for a domain"""
        values = self.domain_performance[domain]
        if not values:
            return {"average": 0.0, "trend": 0.0, "variance": 0.0}
            
        return {
            "average": statistics.mean(values),
            "trend": (values[-1] - values[0]) / len(values) if len(values) > 1 else 0.0,
            "variance": statistics.variance(values) if len(values) > 1 else 0.0
        }

class StrategicAnalyzer:
    """Analyzes system behavior for strategic insights"""
    
    def __init__(self):
        self.insights_history: List[StrategicInsight] = []
        self.pattern_detector = PatternDetector()
        
    async def analyze_system_performance(self, performance_data: List[PerformanceMetric]) -> List[StrategicInsight]:
        """Analyze system performance and generate strategic insights"""
        insights = []
        
        # Performance trend analysis
        if len(performance_data) > 10:
            recent_performance = [m.value for m in performance_data[-10:]]
            older_performance = [m.value for m in performance_data[-20:-10]] if len(performance_data) > 20 else []
            
            if older_performance:
                recent_avg = statistics.mean(recent_performance)
                older_avg = statistics.mean(older_performance)
                trend = (recent_avg - older_avg) / older_avg * 100
                
                if abs(trend) > 10:  # Significant trend
                    insights.append(StrategicInsight(
                        timestamp=datetime.utcnow().isoformat(),
                        insight_type="performance",
                        description=f"Performance trend: {trend:.1f}% {'improvement' if trend > 0 else 'decline'}",
                        confidence=0.8,
                        evidence={"recent_avg": recent_avg, "older_avg": older_avg, "trend_percent": trend},
                        recommendations=self._generate_performance_recommendations(trend),
                        impact_level="medium" if abs(trend) < 25 else "high"
                    ))
        
        # Error pattern analysis
        error_metrics = [m for m in performance_data if "error" in m.metric_name.lower()]
        if error_metrics:
            error_rate = len(error_metrics) / len(performance_data) * 100
            if error_rate > 15:  # High error rate
                insights.append(StrategicInsight(
                    timestamp=datetime.utcnow().isoformat(),
                    insight_type="risk",
                    description=f"High error rate detected: {error_rate:.1f}%",
                    confidence=0.9,
                    evidence={"error_rate": error_rate, "error_count": len(error_metrics)},
                    recommendations=["investigate_error_patterns", "implement_error_prevention", "improve_robustness"],
                    impact_level="high" if error_rate > 25 else "medium"
                ))
        
        self.insights_history.extend(insights)
        return insights
        
    def _generate_performance_recommendations(self, trend: float) -> List[str]:
        """Generate recommendations based on performance trend"""
        if trend > 0:
            return ["maintain_current_strategy", "identify_success_factors", "scale_successful_patterns"]
        else:
            return ["analyze_performance_decline", "optimize_workflows", "investigate_bottlenecks", "consider_strategy_change"]

class PatternDetector:
    """Detects patterns in system execution and learning"""
    
    def __init__(self):
        self.detected_patterns: Dict[str, LearningPattern] = {}
        self.execution_history: deque = deque(maxlen=1000)
        
    def record_execution(self, execution_data: Dict[str, Any]):
        """Record an execution for pattern analysis"""
        self.execution_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "success": execution_data.get("success", False),
            "tool_used": execution_data.get("tool_used", "unknown"),
            "context": execution_data.get("context", {}),
            "duration": execution_data.get("duration", 0),
            "outcome": execution_data.get("outcome", {})
        })
        
    def detect_workflow_patterns(self) -> List[LearningPattern]:
        """Detect patterns in workflow execution"""
        patterns = []
        
        # Tool usage patterns
        tool_usage = defaultdict(lambda: {"count": 0, "success": 0})
        for execution in self.execution_history:
            tool = execution["tool_used"]
            tool_usage[tool]["count"] += 1
            if execution["success"]:
                tool_usage[tool]["success"] += 1
                
        for tool, stats in tool_usage.items():
            if stats["count"] > 5:  # Minimum threshold
                success_rate = stats["success"] / stats["count"]
                pattern = LearningPattern(
                    pattern_id=f"tool_usage_{tool}",
                    pattern_type="workflow",
                    frequency=stats["count"],
                    success_rate=success_rate,
                    context_conditions={"tool": tool},
                    optimization_potential=1.0 - success_rate if success_rate < 0.8 else 0.1
                )
                patterns.append(pattern)
                self.detected_patterns[pattern.pattern_id] = pattern
                
        return patterns
        
    def get_optimization_opportunities(self) -> List[Dict[str, Any]]:
        """Identify optimization opportunities based on patterns"""
        opportunities = []
        
        for pattern in self.detected_patterns.values():
            if pattern.optimization_potential > 0.3:
                opportunities.append({
                    "pattern_id": pattern.pattern_id,
                    "type": pattern.pattern_type,
                    "optimization_potential": pattern.optimization_potential,
                    "current_success_rate": pattern.success_rate,
                    "frequency": pattern.frequency,
                    "recommendations": self._generate_optimization_recommendations(pattern)
                })
                
        return sorted(opportunities, key=lambda x: x["optimization_potential"], reverse=True)
        
    def _generate_optimization_recommendations(self, pattern: LearningPattern) -> List[str]:
        """Generate optimization recommendations for a pattern"""
        recommendations = []
        
        if pattern.success_rate < 0.5:
            recommendations.extend(["critical_review_needed", "consider_alternative_approach", "investigate_failure_causes"])
        elif pattern.success_rate < 0.8:
            recommendations.extend(["improve_tool_parameters", "add_error_handling", "optimize_context_conditions"])
        else:
            recommendations.extend(["monitor_for_degradation", "document_best_practices", "consider_automation"])
            
        return recommendations

class MetaLearningEngine:
    """Meta-learning engine for system-wide learning and optimization"""
    
    def __init__(self):
        self.learning_history: List[Dict[str, Any]] = []
        self.optimization_strategies: Dict[str, Any] = {}
        self.adaptation_rules: List[Dict[str, Any]] = []
        
    async def analyze_execution_patterns(self, execution_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze execution patterns for meta-learning insights"""
        if len(execution_history) < 10:
            return {"status": "insufficient_data", "recommendations": []}
            
        # Success pattern analysis
        successful_executions = [e for e in execution_history if e.get("success", False)]
        failed_executions = [e for e in execution_history if not e.get("success", False)]
        
        success_rate = len(successful_executions) / len(execution_history)
        
        # Tool effectiveness analysis
        tool_effectiveness = defaultdict(lambda: {"total": 0, "success": 0})
        for execution in execution_history:
            tool = execution.get("tool_used", "unknown")
            tool_effectiveness[tool]["total"] += 1
            if execution.get("success", False):
                tool_effectiveness[tool]["success"] += 1
                
        # Context pattern analysis
        context_patterns = self._analyze_context_patterns(successful_executions, failed_executions)
        
        return {
            "status": "complete",
            "overall_success_rate": success_rate,
            "tool_effectiveness": dict(tool_effectiveness),
            "context_patterns": context_patterns,
            "recommendations": self._generate_meta_learning_recommendations(success_rate, tool_effectiveness, context_patterns)
        }
        
    def _analyze_context_patterns(self, successful: List[Dict], failed: List[Dict]) -> Dict[str, Any]:
        """Analyze context patterns between successful and failed executions"""
        # Simple pattern analysis - can be enhanced with ML algorithms
        success_contexts = [e.get("context", {}) for e in successful]
        failure_contexts = [e.get("context", {}) for e in failed]
        
        return {
            "success_patterns": self._extract_common_patterns(success_contexts),
            "failure_patterns": self._extract_common_patterns(failure_contexts),
            "discriminative_features": self._find_discriminative_features(success_contexts, failure_contexts)
        }
        
    def _extract_common_patterns(self, contexts: List[Dict]) -> Dict[str, Any]:
        """Extract common patterns from context data"""
        if not contexts:
            return {}
            
        # Simple frequency-based pattern extraction
        pattern_counts = defaultdict(int)
        for context in contexts:
            for key, value in context.items():
                pattern_counts[f"{key}={value}"] += 1
                
        total_contexts = len(contexts)
        common_patterns = {pattern: count/total_contexts 
                          for pattern, count in pattern_counts.items() 
                          if count/total_contexts > 0.5}
                          
        return common_patterns
        
    def _find_discriminative_features(self, success_contexts: List[Dict], failure_contexts: List[Dict]) -> List[str]:
        """Find features that discriminate between success and failure"""
        # Simple discriminative feature detection
        success_patterns = self._extract_common_patterns(success_contexts)
        failure_patterns = self._extract_common_patterns(failure_contexts)
        
        discriminative = []
        for pattern in success_patterns:
            if pattern not in failure_patterns or success_patterns[pattern] > failure_patterns[pattern] + 0.3:
                discriminative.append(f"success_indicator: {pattern}")
                
        for pattern in failure_patterns:
            if pattern not in success_patterns or failure_patterns[pattern] > success_patterns[pattern] + 0.3:
                discriminative.append(f"failure_indicator: {pattern}")
                
        return discriminative
        
    def _generate_meta_learning_recommendations(self, success_rate: float, tool_effectiveness: Dict, context_patterns: Dict) -> List[str]:
        """Generate meta-learning based recommendations"""
        recommendations = []
        
        if success_rate < 0.7:
            recommendations.append("overall_strategy_review_needed")
            
        # Tool-specific recommendations
        for tool, stats in tool_effectiveness.items():
            if stats["total"] > 5:
                tool_success_rate = stats["success"] / stats["total"]
                if tool_success_rate < 0.5:
                    recommendations.append(f"review_tool_usage: {tool}")
                elif tool_success_rate > 0.9:
                    recommendations.append(f"expand_usage: {tool}")
                    
        # Context-based recommendations
        if context_patterns.get("discriminative_features"):
            recommendations.append("optimize_context_conditions")
            
        return recommendations
        
    async def optimize_workflow_strategies(self, current_strategies: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize workflow strategies based on learning"""
        optimized_strategies = current_strategies.copy()
        
        # Apply learned optimizations
        for strategy_name, strategy_config in current_strategies.items():
            # Simple optimization based on historical performance
            if strategy_name in self.optimization_strategies:
                optimization = self.optimization_strategies[strategy_name]
                if optimization.get("success_rate", 0) > 0.8:
                    # Apply successful optimization
                    optimized_strategies[strategy_name].update(optimization.get("config_changes", {}))
                    
        return optimized_strategies

class Evaluator:
    """
    Strategic evaluation agent that assesses execution results and determines
    if goals were achieved or if replanning/self-improvement is needed.
    Enhanced with strategic monitoring and meta-learning capabilities.
    """
    
    def __init__(self, ai_client: Optional[AIClient] = None):
        """Initialize the evaluator with AI client, logger, and strategic components."""
        self.ai_client = ai_client or AIClient()
        self.logger = EnhancedLogger("evaluator")
        self.evaluation_history: List[Dict[str, Any]] = []
        
        # Strategic AI model preference - Use GPT-4o Mini for strategic decision making
        self.strategic_model = "openai/gpt-4o-mini"  # Fast and reliable model
        
        # Disable GitHub Copilot integration for now - use GPT-4o Mini instead
        self.use_copilot_strategic = False
        self.copilot_client = None
        self.logger.info("Strategic AI configured to use GPT-4o Mini (reliable and fast)")
        
        # Strategic components
        self.performance_tracker = PerformanceTracker()
        self.strategic_analyzer = StrategicAnalyzer()
        self.meta_learning_engine = MetaLearningEngine()
        
        # Strategic monitoring
        self.strategic_insights: List[StrategicInsight] = []
        self.system_health_score: float = 0.8
        self.learning_velocity: float = 0.1
        self.autonomy_level: float = 0.7
        
        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)
        
        # Subscribe to execution events
        event_bus.subscribe("tool.execution.completed", self._on_execution_completed)
        event_bus.subscribe("execution.failed", self._on_execution_failed)
        
        # Subscribe to strategic events
        event_bus.subscribe("strategic.analysis.request", self._on_strategic_analysis_request)
        event_bus.subscribe("system.optimization.trigger", self._on_optimization_trigger)
        
        self.logger.info("Strategic Evaluator initialized with meta-learning capabilities")
    
    async def detect_and_record_tool_mistakes(self, task_context: str = "") -> Optional[Dict[str, Any]]:
        """
        Automatically detect tool mistakes from execution events and create regression learning records.
        
        Checks execution_events.jsonl for tool failures and categorizes them:
        - Category mismatch: tool used on incompatible input type (e.g., file_reader on URL)
        - Parameter mismatch: tool failed due to invalid parameters
        - Unsupported operation: tool cannot perform requested action
        
        If mistake detected, creates a regression learning record automatically.
        
        Returns:
            {
                "mistake_detected": bool,
                "tool_name": str,
                "error_type": str,
                "suggested_tool": str,
                "record_id": str
            }
            or None if no mistakes detected
        """
        try:
            event_logger = get_event_logger()
            recent_failures = event_logger.read_recent(limit=100)
            
            # Filter tool_failure events
            tool_failures = [e for e in recent_failures if e.get("event_type") == "tool_failure"]
            
            if not tool_failures:
                return None
            
            # Analyze the most recent failure
            last_failure = tool_failures[-1]
            tool_name = last_failure.get("tool_name")
            error = last_failure.get("error", "")
            error_type = last_failure.get("error_type", "Unknown")
            params = last_failure.get("params", {})
            
            # Detect category mismatches
            category_mismatch_patterns = {
                "file_reader": [
                    "http", "https", "url", "urllib", "fetch", "request"  # URL-related operations
                ],
                "directory_reader": [
                    "single file", "binary", "image", "pdf"  # Single file operations
                ],
            }
            
            mistake_detected = False
            suggested_tool = None
            mistake_type = None
            
            # Check for category mismatches in task context or error message
            task_lower = (task_context + " " + error).lower()
            
            if tool_name in category_mismatch_patterns:
                for pattern in category_mismatch_patterns[tool_name]:
                    if pattern in task_lower:
                        mistake_detected = True
                        mistake_type = "category_mismatch"
                        
                        # Suggest alternative tool
                        if tool_name == "file_reader" and "http" in task_lower:
                            suggested_tool = "web_api_call"
                        elif tool_name == "file_reader" and "url" in task_lower:
                            suggested_tool = "web_api_call"
                        break
            
            # Check for explicit unsupported errors
            if not mistake_detected and ("unsupported" in error.lower() or "cannot" in error.lower()):
                mistake_detected = True
                mistake_type = "unsupported_operation"
                
                # Try to find a better tool
                suggested_tool = self._find_best_alternative_tool(tool_name, task_context)
            
            if mistake_detected and suggested_tool:
                # Create regression learning record automatically
                learning_record = {
                    "type": "learning_record",
                    "timestamp": datetime.utcnow().isoformat(),
                    "domain": "tool_selection",
                    "error_type": "suboptimal_tool_selection",
                    "wrong_tool": tool_name,
                    "suggested_tool": suggested_tool,
                    "lesson": f"Tool '{tool_name}' failed on task requiring '{suggested_tool}'. Context: {task_context[:100]}",
                    "evidence": {
                        "error": error[:200],
                        "error_type": mistake_type,
                        "failure_event": last_failure,
                        "task_context": task_context[:200]
                    },
                    "severity": "medium",
                    "auto_detected": True
                }
                
                # Write to learning.jsonl
                learning_file = Path("memory/intelligence/learning.jsonl")
                learning_file.parent.mkdir(parents=True, exist_ok=True)
                
                with open(learning_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(learning_record) + "\n")
                
                self.logger.info(
                    f"AUTO-DETECTED MISTAKE: {tool_name} failed on {task_context[:50]}. "
                    f"Recorded lesson: use {suggested_tool} instead."
                )
                
                return {
                    "mistake_detected": True,
                    "tool_name": tool_name,
                    "error_type": mistake_type,
                    "suggested_tool": suggested_tool,
                    "record_id": learning_record["timestamp"],
                    "evidence": last_failure
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in auto-detect mistakes: {e}")
            return None
    
    def _find_best_alternative_tool(self, failed_tool: str, task_context: str) -> Optional[str]:
        """Find best alternative tool based on task context."""
        alternatives = {
            "file_reader": ["web_api_call", "web_scraper", "browser_automation"],
            "directory_reader": ["file_reader", "web_api_call"],
            "terminal": ["file_reader", "web_api_call"],
        }
        
        task_lower = task_context.lower()
        
        # Check for URL-related keywords
        if any(kw in task_lower for kw in ["http", "https", "url", "fetch", "web", "api", "scrape"]):
            return "web_api_call"
        
        # Check for file-related keywords
        if any(kw in task_lower for kw in ["file", "read", "content", "data"]):
            return "file_reader"
        
        # Return first alternative
        if failed_tool in alternatives and alternatives[failed_tool]:
            return alternatives[failed_tool][0]
        
        return None
    
    def get_regression_learning_avoidances(self, task_context: str = "") -> Dict[str, Any]:
        """
        Load regression learning records and extract tool/strategy avoidances.
        Used to prevent previously discovered mistakes.
        
        Returns:
            {
                "avoid_tools": [...],
                "avoid_strategies": [...],
                "suggested_tools": [...],
                "records_found": int
            }
        """
        avoidances = {
            "avoid_tools": [],
            "avoid_strategies": [],
            "suggested_tools": [],
            "records_found": 0,
            "lessons": []
        }
        
        try:
            learning_file = Path("memory/intelligence/learning.jsonl")
            if not learning_file.exists():
                return avoidances
            
            # Read recent learning records
            with open(learning_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Look for regression error records (last 50 records)
            for line in lines[-50:]:
                try:
                    record = json.loads(line.strip())
                    
                    # Check if this is a regression learning record
                    if "suboptimal" in record.get("insight", "").lower() or \
                       record.get("evidence", {}).get("error_type") == "suboptimal_tool_selection":
                        
                        evidence = record.get("evidence", {})
                        
                        # Extract what to avoid
                        wrong_tool = evidence.get("wrong_tool_used")
                        if wrong_tool and wrong_tool not in avoidances["avoid_tools"]:
                            avoidances["avoid_tools"].append(wrong_tool)
                        
                        # Extract what to use instead
                        suggested_tool = evidence.get("suggested_tool")
                        if suggested_tool and suggested_tool not in avoidances["suggested_tools"]:
                            avoidances["suggested_tools"].append(suggested_tool)
                        
                        # Extract lesson
                        lesson = evidence.get("lesson")
                        if lesson and lesson not in avoidances["lessons"]:
                            avoidances["lessons"].append(lesson)
                        
                        avoidances["records_found"] += 1
                
                except json.JSONDecodeError:
                    pass
            
            if avoidances["records_found"] > 0:
                self.logger.info(f"Regression learning: {avoidances['records_found']} error records found. "
                               f"Avoid: {avoidances['avoid_tools']}, Suggest: {avoidances['suggested_tools']}")
        
        except Exception as e:
            self.logger.warning(f"Failed to load regression learning records: {e}")
        
        return avoidances
    
    async def strategic_task_planning(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Strategic AI plans and coordinates the entire task execution process using DeepSeek V3"""
        try:
            self.logger.info(f"Strategic AI (Qwen3 235B) analyzing task: {task}")
            
            # ── Self-referential routing guidance (GAP_026 fix) ──
            # Detect prompts that reference Project-S itself and inject
            # internal-state-preference guidance so the planner does not
            # incorrectly route to web_search.
            self_ref_patterns = [
                "project-s", "projects", "project s",
                "mi a project", "project jelenlegi", "project állapota",
                "current state of project", "project status",
                "what is project", "project about",
                "system status", "current system",
                "our project", "this project",
            ]
            task_lower = task.lower()
            self_ref = any(p in task_lower for p in self_ref_patterns)
            
            # Load regression learning avoidances (if any)
            avoidances = self.get_regression_learning_avoidances(task)
            
            # Build prompt with regression learning constraints + self-ref guidance
            avoidance_note = ""
            if avoidances["avoid_tools"]:
                avoidance_note = f"\n\nIMPORTANT - LESSONS FROM PREVIOUS ERRORS:\n" \
                               f"- Avoid tools: {', '.join(avoidances['avoid_tools'])}\n" \
                               f"- Suggested instead: {', '.join(avoidances['suggested_tools'])}\n" \
                               f"- Lessons: {chr(10).join(f'  * {l}' for l in avoidances['lessons'])}"

            # Self-referential routing note (GAP_026)
            self_ref_note = ""
            if self_ref:
                self_ref_note = (
                    "\n\n*** IMPORTANT SELF-REFERENTIAL ROUTING RULE ***\n"
                    "This question is about Project-S itself (our own system).\n"
                    "DO NOT use web_search, web_scraper, or web_analyzer.\n"
                    "Use ONLY internal tools: file_reader, file_search, file_content_search,\n"
                    "system_info, or your direct knowledge.\n"
                    "The answer must come from internal state, docs, or runtime context.\n"
                    "*** END SELF-REFERENTIAL ROUTING RULE ***\n"
                )

            # Use DeepSeek V3 for strategic planning
            strategic_prompt = f"""
You are the Strategic AI coordinator using DeepSeek V3 for an advanced AI system.
Your role is to analyze tasks and create optimal execution strategies.

TASK TO ANALYZE: {task}
CONTEXT: {context or {}}{self_ref_note}{avoidance_note}

 AVAILABLE TOOLS (only choose from this list!):
- file_reader: read the contents of a file
- file_writer: create or write to a file
- file_search: search for files by name/pattern
- file_content_search: search inside files for text patterns
- system_command: execute shell commands
- system_info: get system information
- pdf_generator: generate PDF files
- web_scraper: scrape web pages
- web_analyzer: analyze web page content
- web_page_fetch: fetch a web page
- web_api_call: call a REST API
- web_search: search the web
- browser_automation: automate browser actions (Playwright)
- tech_news_aggregator: aggregate tech news
- roblox_studio: interact with Roblox Studio

--- TOOL MANIFEST (use these rules to select tools) ---
1. web_search
   Use for: search-engine style discovery of candidate URLs and broad web information.
   Prefer when the task requires finding information but does not yet have a specific URL.

2. web_page_fetch
   Use for: direct fetching of simple/static page content when rendered browser behavior is NOT required.
   Prefer over browser_automation when the target is known to be a static or server-rendered page.

3. web_scraper
   Use for: extracting structured content from known web pages or URLs.
   Prefer when you already have a URL and need to extract structured data from it.

4. browser_automation  ⚠ CRITICAL — prefer this when dynamic rendering is expected
   Use when ANY of the following apply:
     * The task explicitly says to use browser automation,
     * The page may be dynamic / JavaScript-rendered (SPAs, single-page apps, client-side rendering),
     * Real rendered browser inspection is required (e.g. inspecting the final DOM after JS execution),
     * Clicking, navigation, or interactive page handling may be needed,
     * The task involves "external" web content that may require a real browser to access.
   Prefer this over static fetch/scrape tools (web_page_fetch, web_scraper) when those conditions apply.
   This is the ONLY tool that drives a real headless browser (Playwright).

5. file_writer
   Use to write the final report/output artifact.

--- END TOOL MANIFEST ---

Please provide a strategic analysis and execution plan:

1. TASK COMPLEXITY ASSESSMENT:
   - Complexity level (simple/medium/complex/expert)
   - Required capabilities
   - Potential challenges
   
2. STRATEGIC APPROACH:
   - Best execution strategy
   - Resource requirements
   - Success indicators
   
3. EXECUTION PLAN:
   - Should I use Cognitive Core for decomposition? (yes/no + reason)
   - Should I use Tool Orchestration? (yes/no + reason)
   - What tools would be most effective? (MUST be from the AVAILABLE TOOLS list above)
   - Any special considerations?
   
4. OPTIMIZATION OPPORTUNITIES:
   - How can this be done more efficiently?
   - Learning opportunities
   - Risk mitigation
   
5. SUCCESS PREDICTION:
   - Estimated success probability
   - Key success factors
   - Fallback strategies

Respond ONLY with valid JSON using this exact schema (no extra text):
{{
  "complexity": "simple|medium|complex|expert",
  "use_cognitive_core": true/false,
  "use_orchestration": true/false,
  "recommended_tools": ["tool_name_1", "tool_name_2"],
  "confidence": 0.0-1.0,
  "strategy": "brief strategy description",
  "optimizations": ["optimization 1"],
  "success_prediction": 0.0-1.0,
  "recommendations": ["recommendation 1"]
}}

IMPORTANT: "recommended_tools" MUST be a JSON array of tool names chosen ONLY from the AVAILABLE TOOLS list above.
For multi-step tasks (e.g. "search...then write"), include ALL needed tools in order.
"""
            
            strategic_response = await self.ai_client.generate_response(
                strategic_prompt, 
                model=self.strategic_model,
                temperature=0.3  # Lower temperature for strategic decisions
            )
            
            # Parse strategic response
            strategic_plan = self._parse_strategic_response(strategic_response)
            
            # Apply regression learning adjustments
            if avoidances["avoid_tools"]:
                strategic_plan["avoided_previous_mistakes"] = True
                strategic_plan["regression_learning_applied"] = True
                strategic_plan["tools_to_avoid"] = avoidances["avoid_tools"]
                strategic_plan["suggested_tools"] = avoidances["suggested_tools"]
                self.logger.info(f"Regression learning applied: avoiding {avoidances['avoid_tools']}")
            
            # Record strategic decision
            self.strategic_insights.append(StrategicInsight(
                timestamp=datetime.utcnow().isoformat(),
                insight_type="planning",
                description=f"Strategic plan created for: {task}",
                confidence=strategic_plan.get("confidence", 0.8),
                evidence={"task": task, "plan": strategic_plan},
                recommendations=strategic_plan.get("recommendations", []),
                impact_level="high"
            ))
            
            self.logger.info(f"Strategic plan created using Qwen3 235B with {strategic_plan.get('confidence', 0.8)} confidence")
            
            # Add metadata about which AI was used
            strategic_plan["strategic_ai_used"] = "DeepSeek V3"
            strategic_plan["model"] = self.strategic_model
            
            return strategic_plan
            
        except Exception as e:
            self.logger.error(f"Strategic planning failed: {e}")
            return {
                "status": "fallback",
                "use_cognitive_core": True,
                "use_orchestration": True,
                "confidence": 0.5,
                "reason": f"Strategic planning failed: {e}"
            }
    
    def _parse_strategic_response(self, response: str) -> Dict[str, Any]:
        """Parse the strategic AI response into actionable plan"""
        try:
            # Try to extract JSON from response
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            elif "{" in response:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                json_str = response[json_start:json_end]
            else:
                raise ValueError("No JSON found in strategic response")
            
            parsed = json.loads(json_str)
            
            # Ensure required fields with defaults
            result = {
                "status": "success",
                "complexity": parsed.get("complexity", "medium"),
                "use_cognitive_core": parsed.get("use_cognitive_core", True),
                "use_orchestration": parsed.get("use_orchestration", True),
                "recommended_tools": parsed.get("recommended_tools", []),
                "confidence": parsed.get("confidence", 0.7),
                "strategy": parsed.get("strategy", "standard_execution"),
                "optimizations": parsed.get("optimizations", []),
                "success_prediction": parsed.get("success_prediction", 0.7),
                "recommendations": parsed.get("recommendations", [])
            }
            return result
            
        except Exception as e:
            self.logger.warning(f"Failed to parse strategic response: {e}")
            return {
                "status": "parsing_failed",
                "use_cognitive_core": True,
                "use_orchestration": True,
                "confidence": 0.5
            }
    
    async def evaluate_strategic_performance(self, timeframe_hours: int = 24) -> Dict[str, Any]:
        """Evaluate strategic performance over specified timeframe"""
        try:
            # Get recent evaluations within timeframe
            cutoff_time = datetime.utcnow() - timedelta(hours=timeframe_hours)
            recent_evaluations = [
                eval_result for eval_result in self.evaluation_history
                if datetime.fromisoformat(eval_result.get("timestamp", "1970-01-01")) >= cutoff_time
            ]
            
            if not recent_evaluations:
                return {
                    "status": "insufficient_data",
                    "timeframe_hours": timeframe_hours,
                    "message": "No evaluations in specified timeframe"
                }
            
            # Calculate strategic metrics
            total_evaluations = len(recent_evaluations)
            successful_evaluations = sum(1 for e in recent_evaluations if e.get("goal_achieved", False))
            success_rate = successful_evaluations / total_evaluations
            
            # Calculate confidence trend
            confidences = [e.get("confidence", 0.0) for e in recent_evaluations]
            avg_confidence = statistics.mean(confidences) if confidences else 0.0
            
            # Analyze tool effectiveness
            tool_performance = defaultdict(lambda: {"total": 0, "success": 0})
            for eval_result in recent_evaluations:
                tool = eval_result.get("tool_used", "unknown")
                tool_performance[tool]["total"] += 1
                if eval_result.get("goal_achieved", False):
                    tool_performance[tool]["success"] += 1
            
            # Generate strategic insights
            insights = await self.strategic_analyzer.analyze_system_performance(
                [PerformanceMetric(
                    timestamp=e.get("timestamp", ""),
                    metric_name="evaluation_success",
                    value=1.0 if e.get("goal_achieved", False) else 0.0,
                    context=e.get("context", {}),
                    domain=e.get("domain", "general")
                ) for e in recent_evaluations]
            )
            
            # Update system health score
            self.system_health_score = self._calculate_system_health(success_rate, avg_confidence, tool_performance)
            
            # Record performance metrics
            self.performance_tracker.record_metric("success_rate", success_rate)
            self.performance_tracker.record_metric("avg_confidence", avg_confidence)
            self.performance_tracker.record_metric("system_health", self.system_health_score)
            
            return {
                "status": "complete",
                "timeframe_hours": timeframe_hours,
                "total_evaluations": total_evaluations,
                "success_rate": success_rate,
                "avg_confidence": avg_confidence,
                "system_health_score": self.system_health_score,
                "tool_performance": dict(tool_performance),
                "strategic_insights": [asdict(insight) for insight in insights],
                "recommendations": self._generate_strategic_recommendations(success_rate, avg_confidence, insights)
            }
            
        except Exception as e:
            self.logger.error(f"Strategic performance evaluation failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def identify_improvement_opportunities(self) -> Dict[str, Any]:
        """Identify system improvement opportunities using meta-learning"""
        try:
            # Analyze execution patterns
            execution_data = [
                {
                    "success": e.get("goal_achieved", False),
                    "tool_used": e.get("tool_used", "unknown"),
                    "context": e.get("context", {}),
                    "timestamp": e.get("timestamp", ""),
                    "confidence": e.get("confidence", 0.0)
                }
                for e in self.evaluation_history[-100:]  # Last 100 evaluations
            ]
            
            # Run meta-learning analysis
            meta_analysis = await self.meta_learning_engine.analyze_execution_patterns(execution_data)
            
            # Detect workflow patterns
            pattern_analysis = self.strategic_analyzer.pattern_detector.detect_workflow_patterns()
            
            # Get optimization opportunities
            optimization_opportunities = self.strategic_analyzer.pattern_detector.get_optimization_opportunities()
            
            # Calculate learning velocity
            self._update_learning_velocity()
            
            return {
                "status": "complete",
                "meta_analysis": meta_analysis,
                "workflow_patterns": [asdict(pattern) for pattern in pattern_analysis],
                "optimization_opportunities": optimization_opportunities,
                "learning_velocity": self.learning_velocity,
                "autonomy_level": self.autonomy_level,
                "strategic_recommendations": self._generate_improvement_recommendations(
                    meta_analysis, optimization_opportunities
                )
            }
            
        except Exception as e:
            self.logger.error(f"Improvement opportunity analysis failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def optimize_system_learning(self) -> Dict[str, Any]:
        """Optimize system learning based on accumulated insights"""
        try:
            # Get current performance data
            performance_data = self.performance_tracker.metrics_history[-50:]  # Last 50 metrics
            
            # Analyze trends and generate optimizations
            optimization_results = []
            
            # Performance trend optimization
            for domain in self.performance_tracker.domain_performance.keys():
                domain_stats = self.performance_tracker.get_domain_performance(domain)
                if domain_stats["average"] < 0.7:  # Below threshold
                    optimization_results.append({
                        "type": "performance_optimization",
                        "domain": domain,
                        "current_performance": domain_stats["average"],
                        "trend": domain_stats["trend"],
                        "recommendations": self._generate_domain_optimizations(domain, domain_stats)
                    })
            
            # Learning strategy optimization
            current_strategies = {
                "evaluation_frequency": "per_execution",
                "confidence_threshold": 0.7,
                "learning_rate": self.learning_velocity
            }
            
            optimized_strategies = await self.meta_learning_engine.optimize_workflow_strategies(current_strategies)
            
            # Update learning parameters if optimization shows improvement
            if optimized_strategies != current_strategies:
                self.learning_velocity = optimized_strategies.get("learning_rate", self.learning_velocity)
                optimization_results.append({
                    "type": "strategy_optimization",
                    "changes_applied": optimized_strategies,
                    "expected_improvement": 0.1  # Estimated improvement
                })
            
            # Publish optimization event
            await event_bus.publish("evaluator.optimization.completed", {
                "optimizations": optimization_results,
                "system_health": self.system_health_score,
                "learning_velocity": self.learning_velocity
            })
            
            return {
                "status": "complete",
                "optimizations_applied": len(optimization_results),
                "optimization_results": optimization_results,
                "new_learning_velocity": self.learning_velocity,
                "expected_performance_gain": sum(o.get("expected_improvement", 0) for o in optimization_results)
            }
            
        except Exception as e:
            self.logger.error(f"System learning optimization failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def _calculate_system_health(self, success_rate: float, avg_confidence: float, tool_performance: Dict) -> float:
        """Calculate overall system health score"""
        # Weighted health calculation
        success_weight = 0.4
        confidence_weight = 0.3
        tool_health_weight = 0.3
        
        # Tool health calculation
        tool_health = 0.0
        if tool_performance:
            tool_scores = []
            for tool_data in tool_performance.values():
                if tool_data["total"] > 0:
                    tool_scores.append(tool_data["success"] / tool_data["total"])
            tool_health = statistics.mean(tool_scores) if tool_scores else 0.0
        
        health_score = (
            success_rate * success_weight +
            avg_confidence * confidence_weight +
            tool_health * tool_health_weight
        )
        
        return min(1.0, max(0.0, health_score))
    
    def _update_learning_velocity(self):
        """Update learning velocity based on recent performance"""
        if len(self.evaluation_history) < 10:
            return
            
        # Calculate improvement rate over last 20 evaluations
        recent_20 = self.evaluation_history[-20:]
        first_half = recent_20[:10]
        second_half = recent_20[10:]
        
        first_half_success = sum(1 for e in first_half if e.get("goal_achieved", False)) / len(first_half)
        second_half_success = sum(1 for e in second_half if e.get("goal_achieved", False)) / len(second_half)
        
        improvement = second_half_success - first_half_success
        
        # Adjust learning velocity based on improvement
        if improvement > 0.1:
            self.learning_velocity = min(1.0, self.learning_velocity * 1.1)  # Increase by 10%
        elif improvement < -0.1:
            self.learning_velocity = max(0.01, self.learning_velocity * 0.9)  # Decrease by 10%
    
    def _generate_strategic_recommendations(self, success_rate: float, avg_confidence: float, insights: List[StrategicInsight]) -> List[str]:
        """Generate strategic recommendations based on performance analysis"""
        recommendations = []
        
        if success_rate < 0.7:
            recommendations.append("improve_success_rate_critical")
        elif success_rate < 0.85:
            recommendations.append("optimize_success_rate")
            
        if avg_confidence < 0.6:
            recommendations.append("improve_confidence_mechanisms")
        elif avg_confidence < 0.8:
            recommendations.append("enhance_confidence_calibration")
            
        # Add insight-based recommendations
        for insight in insights:
            if insight.impact_level in ["high", "critical"]:
                recommendations.extend(insight.recommendations)
                
        return recommendations
    
    def _generate_improvement_recommendations(self, meta_analysis: Dict, optimization_opportunities: List[Dict]) -> List[str]:
        """Generate improvement recommendations based on meta-learning analysis"""
        recommendations = []
        
        if meta_analysis.get("overall_success_rate", 0) < 0.8:
            recommendations.append("systematic_improvement_needed")
            
        # Tool-specific recommendations
        tool_effectiveness = meta_analysis.get("tool_effectiveness", {})
        for tool, stats in tool_effectiveness.items():
            if stats["total"] > 5:
                success_rate = stats["success"] / stats["total"]
                if success_rate < 0.6:
                    recommendations.append(f"investigate_tool_performance: {tool}")
                    
        # High-impact optimizations
        high_impact_optimizations = [
            opp for opp in optimization_opportunities 
            if opp.get("optimization_potential", 0) > 0.3
        ]
        
        if high_impact_optimizations:
            recommendations.append("high_impact_optimizations_available")
            
        return recommendations
    
    def _generate_domain_optimizations(self, domain: str, stats: Dict[str, float]) -> List[str]:
        """Generate domain-specific optimization recommendations"""
        recommendations = []
        
        if stats["average"] < 0.5:
            recommendations.extend([
                f"critical_review_domain: {domain}",
                f"redesign_approach: {domain}",
                f"expert_intervention_needed: {domain}"
            ])
        elif stats["average"] < 0.7:
            recommendations.extend([
                f"optimize_domain_performance: {domain}",
                f"improve_domain_tools: {domain}",
                f"enhance_domain_strategies: {domain}"
            ])
            
        if stats["trend"] < -0.1:
            recommendations.append(f"address_declining_trend: {domain}")
            
        return recommendations
    
    async def _on_strategic_analysis_request(self, event_data: Dict[str, Any]):
        """Handle strategic analysis requests"""
        try:
            analysis_type = event_data.get("analysis_type", "performance")
            timeframe = event_data.get("timeframe_hours", 24)
            
            if analysis_type == "performance":
                result = await self.evaluate_strategic_performance(timeframe)
            elif analysis_type == "improvement":
                result = await self.identify_improvement_opportunities()
            elif analysis_type == "optimization":
                result = await self.optimize_system_learning()
            else:
                result = {"status": "error", "message": f"Unknown analysis type: {analysis_type}"}
                
            await event_bus.publish("strategic.analysis.completed", {
                "request": event_data,
                "result": result
            })
            
        except Exception as e:
            self.logger.error(f"Strategic analysis request failed: {e}")
            
    async def _on_optimization_trigger(self, event_data: Dict[str, Any]):
        """Handle system optimization triggers"""
        try:
            # Run comprehensive optimization
            optimization_result = await self.optimize_system_learning()
            
            # If optimization was successful, update autonomy level
            if optimization_result.get("status") == "complete":
                performance_gain = optimization_result.get("expected_performance_gain", 0)
                if performance_gain > 0.05:  # Significant improvement
                    self.autonomy_level = min(1.0, self.autonomy_level + performance_gain * 0.1)
                    
            await event_bus.publish("system.optimization.completed", {
                "optimization_result": optimization_result,
                "new_autonomy_level": self.autonomy_level
            })
            
        except Exception as e:
            self.logger.error(f"System optimization trigger failed: {e}")
    
    def get_strategic_status(self) -> Dict[str, Any]:
        """Get comprehensive strategic status"""
        return {
            "system_health_score": self.system_health_score,
            "autonomy_level": self.autonomy_level,
            "learning_velocity": self.learning_velocity,
            "total_evaluations": len(self.evaluation_history),
            "recent_insights": len([i for i in self.strategic_insights if 
                                  datetime.fromisoformat(i.timestamp) > datetime.utcnow() - timedelta(hours=24)]),
            "performance_trends": {
                name: len(trend) for name, trend in self.performance_tracker.performance_trends.items()
            },
            "meta_learning_status": "active" if self.learning_velocity > 0.05 else "passive"
        }
    @monitor_performance
    async def evaluate_execution_result(
        self, 
        original_goal: str,
        tool_used: str,
        tool_params: Dict[str, Any],
        execution_result: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate if the execution result achieved the original goal.
        Enhanced with strategic learning and pattern detection.
        
        Args:
            original_goal: The original user intent/goal
            tool_used: Name of the tool that was executed
            tool_params: Parameters passed to the tool
            execution_result: Result from tool execution
            context: Additional context information
            
        Returns:
            Dict containing evaluation results and strategic insights
        """
        evaluation_id = f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        try:
            # Prepare evaluation prompt (truncate large results to avoid token overflow, GAP_016)
            safe_execution_result = self._truncate_for_prompt(execution_result)
            evaluation_prompt = self._build_evaluation_prompt(
                original_goal, tool_used, tool_params, safe_execution_result, context
            )
            
            # Get AI evaluation - using OpenRouter with qwen3-235b fizetős verzió
            ai_evaluation = await self.ai_client.generate_response(
                prompt=evaluation_prompt,
                model="deepseek/deepseek-chat",
                task_type="general",
                temperature=0.3,
                max_tokens=1000
            )
            
            # Parse AI evaluation
            evaluation_result = self._parse_evaluation_response(ai_evaluation)
            
            # Add metadata
            evaluation_result.update({
                "evaluation_id": evaluation_id,
                "timestamp": datetime.now().isoformat(),
                "original_goal": original_goal,
                "tool_used": tool_used,
                "tool_params": tool_params,
                "execution_result": execution_result,
                "context": context or {}
            })
            
            # Strategic enhancements
            # Record execution for pattern detection
            self.strategic_analyzer.pattern_detector.record_execution({
                "success": evaluation_result.get("goal_achieved", False),
                "tool_used": tool_used,
                "context": context or {},
                "duration": execution_result.get("duration", 0),
                "outcome": evaluation_result
            })
            
            # Record performance metrics
            self.performance_tracker.record_metric(
                name="execution_success",
                value=1.0 if evaluation_result.get("goal_achieved", False) else 0.0,
                context={"tool": tool_used, "goal": original_goal},
                domain=context.get("domain", "general") if context else "general"
            )
            
            self.performance_tracker.record_metric(
                name="evaluation_confidence",
                value=evaluation_result.get("confidence", 0.0),
                context={"tool": tool_used},
                domain=context.get("domain", "general") if context else "general"
            )
            
            # Store evaluation in history
            self.evaluation_history.append(evaluation_result)
            
            # Log evaluation
            await self._log_evaluation(evaluation_result)
            
            # Trigger actions based on evaluation
            await self._handle_evaluation_result(evaluation_result)
            
            # Strategic analysis if enough data accumulated
            if len(self.evaluation_history) % 10 == 0:  # Every 10 evaluations
                await self._trigger_strategic_analysis()
            
            return evaluation_result
            
        except Exception as e:
            error_context = {
                "component": "evaluator",
                "operation": "evaluate_execution_result",
                "evaluation_id": evaluation_id,
                "original_goal": original_goal,
                "tool_used": tool_used
            }
            return await error_handler.handle_error(e, error_context)
    
    async def _trigger_strategic_analysis(self):
        """Trigger strategic analysis based on accumulated evaluations"""
        try:
            # Publish strategic analysis request
            await event_bus.publish("strategic.analysis.request", {
                "analysis_type": "performance",
                "timeframe_hours": 24,
                "trigger": "evaluation_threshold"
            })
            
            # Check if optimization is needed
            recent_success_rate = self.get_success_rate()
            if recent_success_rate < 0.7:  # Below acceptable threshold
                await event_bus.publish("system.optimization.trigger", {
                    "reason": "low_success_rate",
                    "current_rate": recent_success_rate
                })
                
        except Exception as e:
            self.logger.error(f"Strategic analysis trigger failed: {e}")
    
    def _truncate_for_prompt(self, value, max_chars=50000):
        """Truncate large strings/dicts to prevent context-size overflow (GAP_016)."""
        if isinstance(value, str) and len(value) > max_chars:
            return value[:max_chars] + f'\n\n[... TRUNCATED, original was {len(value)} chars]'
        elif isinstance(value, dict):
            return {k: self._truncate_for_prompt(v, max_chars) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._truncate_for_prompt(v, max_chars) for v in value[:100]]
        return value

    def _safe_json_serialize(self, obj, default=str):
        """Safe JSON serialization that handles non-serializable objects (GAP_022).

        Converts any non-JSON-serializable object (e.g. browser_use.AgentHistoryList)
        into a string representation via str() or the provided default converter.
        Preserves all serializable data; only falls back to repr for unserializable values.
        """
        try:
            return json.dumps(obj, default=default)
        except (TypeError, ValueError):
            return str(obj)

    def _sanitize_for_json(self, obj):
        """Recursively sanitize an object so it is fully JSON-serializable (GAP_022).

        Walks dicts and lists, converting any non-serializable leaf values to str.
        Returns a new fully-serializable structure.
        """
        if isinstance(obj, dict):
            return {k: self._sanitize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._sanitize_for_json(v) for v in obj]
        else:
            try:
                json.dumps(obj)
                return obj
            except (TypeError, ValueError):
                return f"[non-serializable: {type(obj).__name__}] {str(obj)[:500]}"

    def _build_evaluation_prompt(
        self,
        original_goal: str,
        tool_used: str,
        tool_params: Dict[str, Any],
        execution_result: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Build the evaluation prompt for AI assessment."""
        
        # Sanitize execution_result and context for JSON serialization (GAP_022)
        safe_execution_result = self._sanitize_for_json(execution_result)
        safe_context = self._sanitize_for_json(context or {})
        
        # ── GAP_027 FIX: Answer adequacy check for direct-answer tasks ──
        # Detect if the user asked for concrete content (bullet points, analysis, list, etc.)
        # and add explicit instruction that the output must contain the actual requested
        # content, not just an execution wrapper or strategic summary.
        _direct_answer_keywords = [
            "bullet point", "bullet list", "short point", "5", "3", "4", "10",
            "list", "analysis", "summary", "report", "answer",
            "mi a", "project jelenlegi", "project állapota",
            "current state", "project status", "what is",
        ]
        _is_direct_answer = any(kw in original_goal.lower() for kw in _direct_answer_keywords)
        
        _adequacy_note = ""
        if _is_direct_answer:
            _adequacy_note = (
                "\n\n*** CRITICAL ANSWER ADEQUACY CHECK (GAP_027) ***\n"
                "The user asked for CONCRETE CONTENT (bullet points, analysis, list, report, etc.).\n"
                "The execution result MUST contain the actual requested content, NOT just:\n"
                "- An execution wrapper like 'STRATEGIC AI EXECUTION COMPLETE'\n"
                "- A strategic plan summary without the actual answer\n"
                "- A tool execution log without the extracted content\n"
                "- Meta-status about what happened without the payload itself\n\n"
                "If the result is ONLY a wrapper/summary/log WITHOUT the actual requested content,\n"
                "mark goal_achieved=false and action=replan.\n\n"
                "Example: If user asks for '5 bullet points', the output must contain\n"
                "5 actual bullet points with substantive information, not just a statement\n"
                "that the system 'executed a task to find information'.\n"
                "*** END ANSWER ADEQUACY CHECK ***\n"
            )

        return f"""
EVALUATION REQUEST:
Please evaluate whether the tool execution successfully achieved the original goal.

ORIGINAL GOAL: {original_goal}

TOOL EXECUTED: {tool_used}
TOOL PARAMETERS: {json.dumps(tool_params, indent=2)}

EXECUTION RESULT:
{json.dumps(safe_execution_result, indent=2)}

ADDITIONAL CONTEXT: {json.dumps(safe_context, indent=2)}{_adequacy_note}

Please provide your evaluation in the following JSON format:
{{
    "success": true/false,
    "confidence": 0.0-1.0,
    "goal_achieved": true/false,
    "assessment": "detailed explanation of why the goal was/wasn't achieved",
    "issues_found": ["list", "of", "any", "issues"],
    "recommendations": {{
        "action": "continue|replan|improve_tool|create_new_tool",
        "reason": "explanation of recommended action",
        "details": "specific details about what should be done"
    }},
    "suggested_improvements": ["list", "of", "suggested", "improvements"]
}}

Focus on:
1. Did the execution produce the expected outcome?
2. Are there any errors or unexpected results?
3. Could the tool or process be improved?
4. Is additional action needed to fully achieve the goal?
"""
    
    def _parse_evaluation_response(self, ai_response: str) -> Dict[str, Any]:
        """Parse the AI evaluation response into structured data."""
        try:
            # Try to extract JSON from the response
            if "```json" in ai_response:
                json_start = ai_response.find("```json") + 7
                json_end = ai_response.find("```", json_start)
                json_str = ai_response[json_start:json_end].strip()
            elif "{" in ai_response:
                json_start = ai_response.find("{")
                json_end = ai_response.rfind("}") + 1
                json_str = ai_response[json_start:json_end]
            else:
                raise ValueError("No JSON found in AI response")
            
            parsed_result = json.loads(json_str)
            
            # Validate required fields
            required_fields = ["success", "confidence", "goal_achieved", "assessment"]
            for field in required_fields:
                if field not in parsed_result:
                    parsed_result[field] = None
            
            # Ensure recommendations structure
            if "recommendations" not in parsed_result:
                parsed_result["recommendations"] = {
                    "action": "continue",
                    "reason": "No specific recommendation provided",
                    "details": ""
                }
            
            return parsed_result
            
        except Exception as e:
            self.logger.error(f"Failed to parse AI evaluation response: {e}")
            # Return default evaluation
            return {
                "success": False,
                "confidence": 0.0,
                "goal_achieved": False,
                "assessment": f"Failed to parse evaluation response: {ai_response}",
                "issues_found": ["evaluation_parsing_failed"],
                "recommendations": {
                    "action": "replan",
                    "reason": "Could not properly evaluate the result",
                    "details": "Manual review needed"
                },
                "suggested_improvements": ["improve_evaluation_parsing"]
            }
    
    async def _log_evaluation(self, evaluation_result: Dict[str, Any]):
        """Log the evaluation result to strategic decisions log."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "evaluation",
            "evaluation_id": evaluation_result.get("evaluation_id"),
            "goal_achieved": evaluation_result.get("goal_achieved"),
            "success": evaluation_result.get("success"),
            "confidence": evaluation_result.get("confidence"),
            "assessment": evaluation_result.get("assessment"),
            "recommendations": evaluation_result.get("recommendations"),
            "original_goal": evaluation_result.get("original_goal"),
            "tool_used": evaluation_result.get("tool_used")
        }
        
        # Append to strategic decisions log
        strategic_log_path = Path("logs/strategic_decisions.md")
        with open(strategic_log_path, "a", encoding="utf-8") as f:
            f.write(f"\n## Evaluation Result - {evaluation_result.get('evaluation_id')}\n")
            f.write(f"**Timestamp:** {log_entry['timestamp']}\n")
            f.write(f"**Original Goal:** {log_entry['original_goal']}\n")
            f.write(f"**Tool Used:** {log_entry['tool_used']}\n")
            f.write(f"**Goal Achieved:** {log_entry['goal_achieved']}\n")
            f.write(f"**Success:** {log_entry['success']}\n")
            f.write(f"**Confidence:** {log_entry['confidence']}\n")
            f.write(f"**Assessment:** {log_entry['assessment']}\n")
            f.write(f"**Recommended Action:** {log_entry['recommendations'].get('action', 'none')}\n")
            f.write(f"**Reason:** {log_entry['recommendations'].get('reason', 'none')}\n\n")
        
        self.logger.info(f"Logged evaluation result: {evaluation_result.get('evaluation_id')}")
    
    async def _handle_evaluation_result(self, evaluation_result: Dict[str, Any]):
        """Handle the evaluation result by triggering appropriate actions.
        
        GAP_029 FIX: Before handling, normalize the evaluator action to validate
        replan requests. A replan is only valid if it includes concrete corrective
        delta (specific_issues, proposed_change, or details).
        """
        # GAP_029: Normalize the evaluator action
        from .evaluator_gap029 import normalize_evaluator_action
        
        normalized = normalize_evaluator_action(evaluation_result)
        action = normalized.get("normalized_action", "continue")
        
        # Log the normalization decision
        gap029_status = normalized.get("gap029_status", "not_replan")
        gap029_reason = normalized.get("gap029_reason", "")
        if gap029_status != "not_replan":
            self.logger.info(f"GAP_029: {gap029_status} - {gap029_reason}")
        
        if action == "continue":
            # Goal achieved, no further action needed
            await event_bus.publish("evaluation.success", normalized)
            
        elif action == "replan":
            # Goal not achieved, trigger replanning (with concrete corrective delta)
            await event_bus.publish("evaluation.replan_needed", normalized)
            
        elif action == "fail":
            # GAP_029: Vague replan downgraded to fail
            await event_bus.publish("evaluation.failed", normalized)
            
        elif action == "improve_tool":
            # Tool worked but could be improved
            await event_bus.publish("evaluation.tool_improvement_needed", normalized)
            
        elif action == "create_new_tool":
            # Current tool insufficient, need new tool
            await event_bus.publish("evaluation.new_tool_needed", normalized)
        
        self.logger.info(f"Handled evaluation result with action: {action} (original: {evaluation_result.get('recommendations', {}).get('action', 'continue')})")
    
    async def _on_execution_completed(self, event_data: Dict[str, Any]):
        """Handle tool execution completion events."""
        if event_data and "auto_evaluate" in event_data and event_data["auto_evaluate"]:
            # Auto-evaluate the result
            await self.evaluate_execution_result(
                original_goal=event_data.get("original_goal", "Unknown"),
                tool_used=event_data.get("tool_name", "Unknown"),
                tool_params=event_data.get("tool_params", {}),
                execution_result=event_data.get("result", {}),
                context=event_data.get("context", {})
            )
    
    async def _on_execution_failed(self, event_data: Dict[str, Any]):
        """Handle execution failure events."""
        # Create failure evaluation
        failure_evaluation = {
            "success": False,
            "confidence": 1.0,
            "goal_achieved": False,
            "assessment": f"Execution failed: {event_data.get('error', 'Unknown error')}",
            "issues_found": ["execution_failure"],
            "recommendations": {
                "action": "replan",
                "reason": "Execution failed, need to retry with different approach",
                "details": event_data.get("error_details", "")
            }
        }
        
        await self._handle_evaluation_result(failure_evaluation)
    
    def get_evaluation_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get recent evaluation history."""
        if limit:
            return self.evaluation_history[-limit:]
        return self.evaluation_history.copy()
    
    def get_success_rate(self) -> float:
        """Calculate success rate of recent evaluations."""
        if not self.evaluation_history:
            return 0.0
        
        successful = sum(1 for eval_result in self.evaluation_history 
                        if eval_result.get("goal_achieved", False))
        return successful / len(self.evaluation_history)

    # Legacy method for backward compatibility
    async def evaluate_result(self, result, expected_outcome):
        """Legacy method - use evaluate_execution_result instead."""
        return await self.evaluate_execution_result(
            original_goal=str(expected_outcome),
            tool_used="unknown",
            tool_params={},
            execution_result=result
        )

# Create singleton instance
evaluator = Evaluator()

# Backward compatibility
ExecutionEvaluator = Evaluator
