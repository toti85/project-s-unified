"""
Research Loop - Executes bug bounty research using MetaController.
Coordinates hypothesis testing and validator feedback into research constraints.
"""

import asyncio
import logging
from typing import Optional
from dataclasses import dataclass

from .research_goal import ResearchGoal
from .research_state import ResearchState

logger = logging.getLogger(__name__)


@dataclass
class ResearchResult:
    """Result of research execution."""
    goal: ResearchGoal
    state: ResearchState
    success: bool
    completion_reason: str  # "submission_ready", "no_more_leads", "max_iterations", "error"
    promising_findings: list[dict]
    iteration_count: int


class ResearchLoop:
    """
    Executes bug bounty research using the Meta Layer.
    
    Uses MetaController.run_goal() internally to coordinate research iterations.
    Does not call real hacking tools or create new executors.
    """
    
    def __init__(self, meta_controller):
        """
        Initialize research loop with MetaController.
        
        Args:
            meta_controller: Instance of MetaController for orchestration
        """
        self.meta_controller = meta_controller
        self.logger = logging.getLogger(__name__)
    
    async def run(self, goal: ResearchGoal) -> ResearchResult:
        """
        Execute research goal using MetaController orchestration.
        
        Args:
            goal: ResearchGoal defining the research objective
            
        Returns:
            ResearchResult with findings and completion status
        """
        self.logger.info(f"Starting research: {goal.target_name}")
        
        # Initialize research state
        research_state = ResearchState()
        research_state.iteration = 0
        
        # Log research started
        self._log_evidence("research_started", {
            "target_name": goal.target_name,
            "scope": goal.scope,
            "focus_vectors": goal.focus_vectors,
            "stop_condition": goal.stop_condition,
        })
        
        # Constraints start empty, updated by validator feedback
        constraints = {}
        
        try:
            # Run research using MetaController orchestration
            # MetaController.run_goal() takes only a goal string (not state/constraints in current impl)
            goal_string = f"Research {goal.target_name}: {goal.description or goal.scope}"
            
            meta_result = await self.meta_controller.run_goal(goal_string)
            
            # Extract final state from meta_result
            if isinstance(meta_result, dict) and "status" in meta_result:
                final_status = meta_result["status"]
                # Update state iteration count if provided by MetaController
                if "iterations" in meta_result:
                    research_state.iteration = meta_result["iterations"]
            else:
                final_status = "unknown"
            
            # Extract final findings
            final_findings = research_state.findings if research_state.findings else []
            
            # If no iteration count set yet, default to 1 for successful runs
            if research_state.iteration == 0 and final_status == "success":
                research_state.iteration = 1
            final_findings = research_state.findings if research_state.findings else []
            
            # If no iteration count set yet, default to 1 for successful runs
            if research_state.iteration == 0 and final_status == "success":
                research_state.iteration = 1
            
            # Determine completion reason
            if final_status == "success":
                completion_reason = goal.stop_condition
            else:
                completion_reason = "error"
            
            # Log research completed
            self._log_evidence("research_completed", {
                "target_name": goal.target_name,
                "status": final_status,
                "iterations": research_state.iteration,
                "findings_count": len(final_findings),
                "completion_reason": completion_reason,
            })
            
            return ResearchResult(
                goal=goal,
                state=research_state,
                success=(final_status == "success"),
                completion_reason=completion_reason,
                promising_findings=final_findings,
                iteration_count=research_state.iteration,
            )
            
        except Exception as e:
            self.logger.error(f"Research failed: {e}")
            self._log_evidence("research_error", {
                "target_name": goal.target_name,
                "error": str(e),
                "iteration": research_state.iteration,
            })
            
            return ResearchResult(
                goal=goal,
                state=research_state,
                success=False,
                completion_reason="error",
                promising_findings=[],
                iteration_count=research_state.iteration,
            )
    
    def _log_evidence(self, event_type: str, data: dict):
        """
        Log research evidence event.
        Integrates with MetaController's evidence logging if available.
        
        Args:
            event_type: Type of event (e.g., "research_started", "hypothesis_tested")
            data: Event data dictionary
        """
        event = {
            "event": event_type,
            "timestamp": asyncio.get_event_loop().time(),
            **data,
        }
        
        # Log to MetaController's evidence logger if available
        if hasattr(self.meta_controller, "_log_evidence"):
            self.meta_controller._log_evidence(event_type, data)
        else:
            self.logger.debug(f"Research event: {event_type} - {data}")
    
    def handle_validator_feedback(self, feedback_type: str, data: dict) -> dict:
        """
        Convert validator feedback into research constraints for next iteration.
        
        Args:
            feedback_type: Type of feedback ("false_positive", "low_impact", "duplicate")
            data: Feedback data including which vector/hypothesis was problematic
            
        Returns:
            Updated constraints dictionary
        """
        constraints = {}
        
        if feedback_type == "false_positive":
            # Mark this vector as producing false positives
            constraints["exclude_vectors"] = [data.get("vector")]
            self._log_evidence("hypothesis_rejected", {
                "reason": "false_positive",
                "vector": data.get("vector"),
                "hypothesis": data.get("hypothesis"),
            })
        
        elif feedback_type == "low_impact":
            # Mark as low impact, deprioritize but don't exclude
            constraints["low_impact_vectors"] = [data.get("vector")]
            self._log_evidence("hypothesis_rejected", {
                "reason": "low_impact",
                "vector": data.get("vector"),
                "hypothesis": data.get("hypothesis"),
            })
        
        elif feedback_type == "duplicate":
            # This finding is duplicate, move to next vector
            constraints["exclude_vectors"] = [data.get("vector")]
            self._log_evidence("hypothesis_rejected", {
                "reason": "duplicate",
                "vector": data.get("vector"),
                "hypothesis": data.get("hypothesis"),
            })
        
        elif feedback_type == "promising":
            # This hypothesis is promising, promote it
            self._log_evidence("hypothesis_promoted", {
                "vector": data.get("vector"),
                "hypothesis": data.get("hypothesis"),
                "confidence": data.get("confidence", 0.0),
            })
        
        return constraints
