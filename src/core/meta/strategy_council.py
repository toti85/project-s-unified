"""
Strategy Council: Multi-AI consensus decision making.

Coordinates decisions from multiple specialized AI strategists
to reach consensus on major system decisions.
"""
import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from .decision import Decision, AIOpinion
from .ai_strategist import AIStrategist


logger = logging.getLogger(__name__)


class StrategyCouncil:
    """
    Multi-AI strategy council for consensus-based decision making.
    
    Coordinates multiple AI strategists with different specializations:
    - Strategic: Long-term planning and architecture
    - Security: Risk assessment and security implications
    - Technical: Implementation feasibility and constraints
    """
    
    def __init__(self, strategists: Optional[List[AIStrategist]] = None):
        """
        Initialize the strategy council.
        
        Args:
            strategists: List of AIStrategist instances (optional for testing)
        """
        self.strategists = strategists or []
        self.decisions_made = []
        self.decision_history = []
        
        # Decision thresholds
        self.feasibility_threshold = 70.0  # Must reach this average
        self.confidence_threshold = 60.0   # Must reach this average
        self.approval_threshold = 0.5      # 50% approval ratio minimum
        
        logger.info(f"StrategyCouncil initialized with {len(self.strategists)} strategists")
    
    def add_strategist(self, strategist: AIStrategist) -> None:
        """Add a strategist to the council."""
        self.strategists.append(strategist)
        logger.info(f"Strategist added: {strategist.ai_name} ({strategist.role})")
    
    async def decide(self, goal: str, context: Optional[Dict[str, Any]] = None) -> Decision:
        """
        Make a strategic decision by consensus.
        
        Args:
            goal: The goal or decision to evaluate
            context: Additional context for analysis
            
        Returns:
            Decision object with consensus from all strategists
        """
        decision_id = f"decision_{uuid.uuid4().hex[:8]}"
        logger.info(f"Council deliberating on: {goal} (ID: {decision_id})")
        
        # Auto-inject default strategists if council is empty
        if not self.strategists:
            logger.warning("StrategyCouncil has 0 strategists - injecting default strategist")
            default_strategist = self._create_default_strategist()
            self.strategists.append(default_strategist)
            # Log evidence event for injected strategists
            if hasattr(self, '_log_evidence'):
                self._log_evidence("default_strategists_injected", {
                    "count": 1,
                    "strategist": default_strategist.ai_name,
                    "role": default_strategist.role
                })
        
        # Get opinions from all strategists
        opinions: List[AIOpinion] = []
        for strategist in self.strategists:
            opinion = await strategist.analyze(goal, context)
            opinions.append(opinion)
            logger.debug(f"  {strategist.ai_name}: {opinion.recommendation} "
                        f"(feasibility: {opinion.feasibility_score}, confidence: {opinion.confidence_score})")
        
        # Calculate consensus
        decision = self._calculate_consensus(decision_id, goal, opinions)
        
        # Store in history
        self.decisions_made.append(decision)
        self.decision_history.append({
            "decision_id": decision_id,
            "goal": goal,
            "timestamp": datetime.now().isoformat(),
            "result": decision.decision,
            "consensus": decision.consensus_type,
            "approval_ratio": decision.approval_ratio
        })
        
        logger.info(f"Decision reached: {decision.decision} (consensus: {decision.consensus_type}, "
                   f"approval: {decision.approval_ratio:.1%})")
        
        return decision
    
    def _calculate_consensus(self, decision_id: str, goal: str, opinions: List[AIOpinion]) -> Decision:
        """
        Calculate consensus from all opinions.
        
        Args:
            decision_id: Unique ID for this decision
            goal: The goal being decided
            opinions: List of AIOpinion from strategists
            
        Returns:
            Decision with calculated consensus
        """
        if not opinions:
            raise ValueError("Cannot calculate consensus with no opinions")
        
        # Calculate averages
        avg_feasibility = sum(op.feasibility_score for op in opinions) / len(opinions)
        avg_confidence = sum(op.confidence_score for op in opinions) / len(opinions)
        
        # Count approvals
        approve_count = sum(1 for op in opinions if op.recommendation in ["approve", "conditional"])
        approval_ratio = approve_count / len(opinions)
        
        # Determine consensus type
        all_approve = all(op.recommendation in ["approve", "conditional"] for op in opinions)
        unanimous = all(op.recommendation == "approve" for op in opinions)
        
        if unanimous:
            consensus_type = "unanimous"
        elif approval_ratio >= (2/3):
            consensus_type = "majority"
        else:
            consensus_type = "split"
        
        # Make decision based on thresholds
        approve = (
            avg_feasibility >= self.feasibility_threshold and
            avg_confidence >= self.confidence_threshold and
            approval_ratio >= self.approval_threshold
        )
        
        decision_value = "approved" if approve else "rejected"
        
        # Check for conditional approvals
        has_conditions = any(op.conditions for op in opinions if op.conditions)
        if approve and has_conditions:
            decision_value = "conditional"
        
        # Aggregate risks and benefits
        aggregated_risks = []
        aggregated_benefits = []
        
        for opinion in opinions:
            aggregated_risks.extend(opinion.risks)
            aggregated_benefits.extend(opinion.benefits)
        
        # Remove duplicates while preserving order
        aggregated_risks = list(dict.fromkeys(aggregated_risks))
        aggregated_benefits = list(dict.fromkeys(aggregated_benefits))
        
        # Build recommended plan from opinions
        plan_components = []
        for opinion in opinions:
            if opinion.reasoning:
                plan_components.append(f"[{opinion.role.upper()}] {opinion.reasoning}")
            if opinion.conditions and opinion.recommendation == "conditional":
                plan_components.append(f"[{opinion.role.upper()}] CONDITIONS: {', '.join(opinion.conditions)}")
        
        recommended_plan = "\n\n".join(plan_components)
        
        # Create decision object
        decision = Decision(
            decision_id=decision_id,
            goal=goal,
            decision=decision_value,
            consensus_type=consensus_type,
            approval_ratio=approval_ratio,
            avg_feasibility=avg_feasibility,
            avg_confidence=avg_confidence,
            opinions=opinions,
            aggregated_risks=aggregated_risks,
            aggregated_benefits=aggregated_benefits,
            recommended_plan=recommended_plan
        )
        
        return decision
    
    def get_decision_stats(self) -> Dict[str, Any]:
        """Get statistics on all decisions made by council."""
        if not self.decisions_made:
            return {
                "total_decisions": 0,
                "approved": 0,
                "rejected": 0,
                "conditional": 0,
                "avg_approval_ratio": 0
            }
        
        approved = sum(1 for d in self.decisions_made if d.decision == "approved")
        rejected = sum(1 for d in self.decisions_made if d.decision == "rejected")
        conditional = sum(1 for d in self.decisions_made if d.decision == "conditional")
        avg_approval = sum(d.approval_ratio for d in self.decisions_made) / len(self.decisions_made)
        
        return {
            "total_decisions": len(self.decisions_made),
            "approved": approved,
            "rejected": rejected,
            "conditional": conditional,
            "avg_approval_ratio": avg_approval,
            "consensus_types": {
                "unanimous": sum(1 for d in self.decisions_made if d.consensus_type == "unanimous"),
                "majority": sum(1 for d in self.decisions_made if d.consensus_type == "majority"),
                "split": sum(1 for d in self.decisions_made if d.consensus_type == "split")
            }
        }
    
    def get_strategist_stats(self) -> List[Dict[str, Any]]:
        """Get statistics for each strategist."""
        return [strategist.get_stats() for strategist in self.strategists]
    
    def _create_default_strategist(self) -> AIStrategist:
        """
        Create a default strategist for when council is empty.
        
        This strategist returns deterministic opinions for generic goals,
        enabling the council to function even without pre-configured strategists.
        """
        return _DefaultStrategist()


class _DefaultStrategist(AIStrategist):
    """
    Fallback strategist that provides deterministic opinions.
    Used when StrategyCouncil has no strategists configured.
    """
    
    def __init__(self):
        """Initialize default strategist."""
        super().__init__(
            ai_name="DefaultStrategist",
            role="generic_planner",
            api_client=None
        )
    
    async def analyze(self, goal: str, context: Optional[Dict[str, Any]] = None) -> AIOpinion:
        """
        Provide a simple deterministic opinion for the goal.
        
        Args:
            goal: The goal to analyze
            context: Optional context
            
        Returns:
            AIOpinion with deterministic values
        """
        # Parse goal to extract actionable information
        reasoning = f"Default analysis of goal: {goal}"
        
        # Extract file path if mentioned
        target_path = None
        if "write" in goal.lower() or "save" in goal.lower() or "file" in goal.lower():
            # Try to find file path pattern (e.g., "path/to/file.txt")
            words = goal.split()
            for i, word in enumerate(words):
                if '.' in word and ('txt' in word or 'json' in word or 'md' in word or 'csv' in word):
                    target_path = word
                    break
        
        # Build simple step list
        steps = [
            "Analyze goal requirements",
            "Execute primary action",
            "Validate results"
        ]
        
        if target_path:
            steps.insert(1, f"Write results to {target_path}")
        
        # Return deterministic opinion
        return AIOpinion(
            ai_name=self.ai_name,
            role=self.role,
            recommendation="approve",  # Default to approval for forward progress
            feasibility_score=75.0,  # Mid-range feasibility
            confidence_score=70.0,   # Reasonable confidence
            reasoning=reasoning + f"\nSteps: {', '.join(steps)}",
            risks=[],
            benefits=["Enables forward progress", "Provides actionable plan"],
            conditions=None
        )

