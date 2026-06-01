"""
Meta Layer Phase 3: MetaController

Orchestrates the complete feedback loop:
1. StrategyCouncil decides on plan
2. Executor runs the plan
3. ExecutionValidator validates results
4. Replan if validation fails or no progress
5. Log evidence of entire decision→execution→validation cycle
"""
import logging
import asyncio
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class MetaControllerConfig:
    """Configuration for MetaController."""
    max_iters: int = 5              # Maximum planning iterations
    step_timeout_sec: int = 120     # Timeout per execution step
    risk_budget_failures: int = 2   # Max failures before abort
    progress_required: bool = True  # Require measurable progress


class MetaController:
    """
    Meta-cognitive controller orchestrating the full decision→execute→validate loop.
    
    Coordinates StrategyCouncil (planning) + Executor (execution) + 
    ExecutionValidator (verification) with evidence logging and state tracking.
    """
    
    def __init__(
        self,
        council: Any,
        executor: Any,
        validator: Any,
        evidence_logger: Any,
        config: Optional[MetaControllerConfig] = None,
        evidence_path: Optional[str] = None
    ):
        """
        Initialize MetaController.
        
        Args:
            council: StrategyCouncil instance for decision making
            executor: Executor instance for task execution
            validator: ExecutionValidator instance for result validation
            evidence_logger: Logger for JSONL evidence events
            config: MetaControllerConfig (optional, uses defaults)
            evidence_path: Path to meta_evidence.jsonl for observe() writes
        """
        self.council = council
        self.executor = executor
        self.validator = validator
        self.evidence_logger = evidence_logger
        self.config = config or MetaControllerConfig()
        
        # Resolve evidence path for observe() — default: memory/intelligence/meta_evidence.jsonl
        if evidence_path:
            self.evidence_path = evidence_path
        else:
            import os
            self.evidence_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..", "..", "..", "memory", "intelligence", "meta_evidence.jsonl"
            )
        
        # State tracking
        self.iteration_count = 0
        self.failure_count = 0
        self.state = {}
        self.constraints = {}
        
        logger.info(f"MetaController initialized: max_iters={self.config.max_iters}, "
                   f"timeout={self.config.step_timeout_sec}s, "
                   f"risk_budget={self.config.risk_budget_failures}")
    
    async def run_goal(self, goal: str) -> Dict[str, Any]:
        """
        Execute a goal through the full decision→execute→validate loop.
        
        Loop logic:
        1. StrategyCouncil.decide() → plan + decision
        2. Executor.execute() → execution result
        3. ExecutionValidator.validate() → validation result
        4. If FAIL/CONDITIONAL → replan (update constraints)
        5. If success → stop
        6. If max_iters or risk_budget exceeded → abort
        
        Args:
            goal: Goal description
            
        Returns:
            Dictionary with:
            - goal: original goal
            - status: "success" | "failed" | "max_iters"
            - iterations: number of planning iterations
            - final_result: execution result if success
            - final_validation: validation result if success
            - evidence_log: path to JSONL evidence file
        """
        goal_id = self._generate_id()
        self.iteration_count = 0
        self.failure_count = 0
        self.state = {"goal": goal, "history": []}
        self.constraints = {}
        
        # Log goal start
        self._log_evidence("goal_started", {
            "goal_id": goal_id,
            "goal": goal,
            "config": asdict(self.config)
        })
        
        try:
            while self.iteration_count < self.config.max_iters:
                self.iteration_count += 1
                logger.info(f"[MetaController] Iteration {self.iteration_count}/{self.config.max_iters}")
                
                # Phase 1: PLAN
                logger.debug(f"Phase 1: Planning with constraints={self.constraints}")
                try:
                    # Prepare context for council
                    context = {
                        "state": self.state,
                        "constraints": self.constraints,
                        "iteration": self.iteration_count,
                    }
                    decision = await asyncio.wait_for(
                        self.council.decide(goal, context),
                        timeout=self.config.step_timeout_sec
                    )
                except asyncio.TimeoutError:
                    logger.error("Planning timeout exceeded")
                    self.failure_count += 1
                    if self.failure_count >= self.config.risk_budget_failures:
                        return self._build_failure_result(goal_id, goal, "planning_timeout")
                    continue
                except Exception as e:
                    logger.error(f"Planning failed: {e}")
                    self.failure_count += 1
                    if self.failure_count >= self.config.risk_budget_failures:
                        return self._build_failure_result(goal_id, goal, f"planning_error: {e}")
                    continue
                
                # Log plan selected
                self._log_evidence("plan_selected", {
                    "goal_id": goal_id,
                    "iteration": self.iteration_count,
                    "decision": {
                        "decision": decision.decision,
                        "consensus": decision.consensus_type,
                        "approval_ratio": decision.approval_ratio,
                        "avg_confidence": decision.avg_confidence
                    },
                    "constraints": self.constraints
                })
                
                # [INVARIANT GATE 1] After plan_selected
                # Hard assertion: state must not be None, iteration must be monotonic
                assert self.state is not None, "[INVARIANT] state is None after plan_selected"
                assert self.iteration_count > 0, "[INVARIANT] iteration_count not monotonic after plan_selected"
                assert decision is not None, "[INVARIANT] decision is None after plan_selected"
                logger.debug(f"[INVARIANT] Gate 1 PASSED: state OK, iteration={self.iteration_count}, decision valid")
                
                # Check if council rejected
                if decision.decision == "rejected":
                    logger.warning(f"Council rejected plan: {decision.recommended_plan}")
                    return self._build_failure_result(goal_id, goal, "plan_rejected")
                
                # Phase 2: EXECUTE
                logger.debug(f"Phase 2: Executing plan")
                # RISK_001 TRAP: executor must not be None (observe-only instances have no executor)
                if self.executor is None:
                    self._log_evidence("risk_001_trap_triggered", {
                        "message": "executor is None — run_goal() blocked in observe-only mode",
                        "iteration": self.iteration_count,
                        "goal_id": goal_id,
                    })
                    raise RuntimeError(
                        "[RISK_001 TRAP] MetaController.executor is None. "
                        "This instance was constructed in observe-only mode. "
                        "run_goal() requires a real executor."
                    )
                try:
                    execution_result = await asyncio.wait_for(
                        self.executor.execute(goal, decision),
                        timeout=self.config.step_timeout_sec
                    )
                except asyncio.TimeoutError:
                    logger.error("Execution timeout exceeded")
                    self.failure_count += 1
                    if self.failure_count >= self.config.risk_budget_failures:
                        return self._build_failure_result(goal_id, goal, "execution_timeout")
                    continue
                except Exception as e:
                    logger.error(f"Execution failed: {e}")
                    self.failure_count += 1
                    if self.failure_count >= self.config.risk_budget_failures:
                        return self._build_failure_result(goal_id, goal, f"execution_error: {e}")
                    continue
                
                # Log execution done
                self._log_evidence("execution_done", {
                    "goal_id": goal_id,
                    "iteration": self.iteration_count,
                    "execution_status": execution_result.get("status"),
                    "execution_time_ms": execution_result.get("execution_time_ms")
                })
                
                # Phase 3: VALIDATE
                logger.debug(f"Phase 3: Validating result")
                try:
                    validation = await asyncio.wait_for(
                        self.validator.validate(execution_result, goal),
                        timeout=self.config.step_timeout_sec
                    )
                except asyncio.TimeoutError:
                    logger.error("Validation timeout exceeded")
                    self.failure_count += 1
                    if self.failure_count >= self.config.risk_budget_failures:
                        return self._build_failure_result(goal_id, goal, "validation_timeout")
                    continue
                except Exception as e:
                    logger.error(f"Validation failed: {e}")
                    self.failure_count += 1
                    if self.failure_count >= self.config.risk_budget_failures:
                        return self._build_failure_result(goal_id, goal, f"validation_error: {e}")
                    continue
                
                # Log validation done
                self._log_evidence("validation_done", {
                    "goal_id": goal_id,
                    "iteration": self.iteration_count,
                    "validation_passed": validation.passed,
                    "consensus_type": validation.consensus_type,
                    "confidence": validation.confidence,
                    "critical_issues": len(validation.critical_issues) if hasattr(validation, 'critical_issues') else 0,
                    "total_issues": len(validation.all_issues) if hasattr(validation, 'all_issues') else 0
                })
                
                # [INVARIANT GATE 2] After validation_done
                # Hard assertion: validation result must be valid and non-empty
                assert validation is not None, "[INVARIANT] validation result is None"
                assert hasattr(validation, 'passed'), "[INVARIANT] validation missing 'passed' field"
                assert hasattr(validation, 'consensus_type'), "[INVARIANT] validation missing 'consensus_type' field"
                assert validation.consensus_type in ['unanimous_pass', 'majority_pass', 'conditional', 'failed'], \
                    f"[INVARIANT] invalid consensus_type: {validation.consensus_type}"
                assert hasattr(validation, 'confidence') and validation.confidence is not None, \
                    "[INVARIANT] validation missing or invalid 'confidence'"
                logger.debug(f"[INVARIANT] Gate 2 PASSED: validation={validation.consensus_type}, confidence={validation.confidence}")
                
                # Phase 4: DECIDE (replan or succeed)
                # Check for deterministic success: output produced + no critical issues
                # FIX-4: require meaningful output (>100 chars), reject known stub/wrapper strings
                _raw_output = execution_result.get("output") or execution_result.get("result") or ""
                _STUB_PREFIXES = (
                    "[OK] MetaController completed goal",
                    "[FAIL]",
                    "mock result",
                    "no results returned",
                    "Task processed with backup systems",
                )
                has_output = (
                    isinstance(_raw_output, str)
                    and len(_raw_output) > 100
                    and not any(_raw_output.startswith(p) for p in _STUB_PREFIXES)
                ) or (isinstance(_raw_output, dict) and bool(_raw_output))
                has_critical = bool(hasattr(validation, 'critical_issues') and validation.critical_issues)

                # GAP_018: Do not override evaluator's explicit replan signal with
                # deterministic success — an empty/stub output from a failed tool chain
                # must not be counted as a completed goal.
                # FIX-1: evaluator returns action nested under recommendations.action, not top-level.
                _eval_data = execution_result.get("evaluation_result") or {}
                _eval_recs = (_eval_data.get("recommendations") or {})
                _eval_action_val = _eval_recs.get("action", _eval_data.get("action", ""))
                _eval_needs_replan = (
                    _eval_action_val in ("replan", "create_new_tool")
                    or _eval_data.get("goal_achieved") is False
                )
                deterministic_pass = has_output and not has_critical and not _eval_needs_replan
                
                if validation.passed or deterministic_pass:
                    # Success! (either validator approved OR output produced with no critical issues)
                    logger.info(f"[OK] Goal achieved in {self.iteration_count} iterations (validator={validation.passed}, deterministic={deterministic_pass})")
                    
                    # [INVARIANT GATE 3] Before goal_completed
                    # Hard assertion: success state must be valid
                    assert self.iteration_count > 0, "[INVARIANT] iteration_count is 0 before goal_completed"
                    assert self.iteration_count <= self.config.max_iters, \
                        f"[INVARIANT] iteration_count {self.iteration_count} exceeds max_iters {self.config.max_iters}"
                    assert execution_result is not None, "[INVARIANT] execution_result is None before goal_completed"
                    assert isinstance(execution_result, dict) and execution_result.get('status') == 'success', \
                        f"[INVARIANT] execution_result status not 'success': {execution_result.get('status')}"
                    # For deterministic pass: confidence can be 0 (no validator), for validator pass: confidence must be > 0
                    if validation.passed:
                        assert validation.confidence > 0, \
                            f"[INVARIANT] validation confidence must be positive, got {validation.confidence}"
                    logger.debug(f"[INVARIANT] Gate 3 PASSED: iterations={self.iteration_count}, status=success, confidence={validation.confidence}")
                    
                    status_reason = "validator_approved" if validation.passed else "deterministic_output_no_critical_issues"
                    self._log_evidence("goal_completed", {
                        "goal_id": goal_id,
                        "status": "passed",
                        "status_reason": status_reason,
                        "iterations": self.iteration_count,
                        "final_validation_confidence": validation.confidence,
                        "last_validation_summary": {
                            "consensus": validation.consensus_type,
                            "passed": validation.passed,
                            "critical_count": len(validation.critical_issues) if hasattr(validation, 'critical_issues') else 0,
                            "issues_count": len(validation.all_issues) if hasattr(validation, 'all_issues') else 0
                        }
                    })
                    
                    return {
                        "goal": goal,
                        "status": "passed",
                        "iterations": self.iteration_count,
                        "status_reason": status_reason,
                        "output": execution_result.get("output") or execution_result.get("result") or "",
                        "execution_result": execution_result,
                        "final_result": execution_result,
                        "final_validation": {
                            "passed": validation.passed,
                            "consensus_type": validation.consensus_type,
                            "confidence": validation.confidence
                        },
                        "evidence_log": self.evidence_logger.get_log_path() if hasattr(self.evidence_logger, 'get_log_path') else None
                    }
                
                else:
                    # Need to replan
                    logger.info(f"Validation failed ({validation.consensus_type}), replanning...")
                    
                    # Update constraints based on validation issues
                    new_constraints = self._extract_constraints_from_validation(validation)
                    self.constraints.update(new_constraints)
                    
                    # Log replan trigger
                    self._log_evidence("replan_triggered", {
                        "goal_id": goal_id,
                        "iteration": self.iteration_count,
                        "reason": validation.consensus_type,
                        "new_constraints": new_constraints,
                        "cumulative_constraints": self.constraints
                    })
                    
                    # Update state for next iteration
                    self.state["last_execution"] = execution_result
                    self.state["last_validation"] = {
                        "passed": validation.passed,
                        "consensus": validation.consensus_type,
                        "issues": len(validation.all_issues) if hasattr(validation, 'all_issues') else 0
                    }
                    
                    # Continue loop for replan
                    continue
            
            # Max iterations reached
            logger.warning(f"Max iterations ({self.config.max_iters}) reached without success")
            self._log_evidence("goal_completed", {
                "goal_id": goal_id,
                "status": "max_iters",
                "iterations": self.iteration_count
            })
            
            return {
                "goal": goal,
                "status": "max_iters",
                "iterations": self.iteration_count,
                "evidence_log": self.evidence_logger.get_log_path() if hasattr(self.evidence_logger, 'get_log_path') else None
            }
        
        except Exception as e:
            logger.error(f"Unhandled error in MetaController.run_goal(): {e}", exc_info=True)
            self._log_evidence("goal_failed", {
                "goal_id": goal_id,
                "error": str(e),
                "iterations": self.iteration_count
            })
            
            return {
                "goal": goal,
                "status": "failed",
                "error": str(e),
                "iterations": self.iteration_count,
                "evidence_log": self.evidence_logger.get_log_path() if hasattr(self.evidence_logger, 'get_log_path') else None
            }
    
    def _extract_constraints_from_validation(self, validation: Any) -> Dict[str, Any]:
        """Extract constraints from validation issues for next planning iteration."""
        constraints = {}
        
        if hasattr(validation, 'critical_issues') and validation.critical_issues:
            constraints['avoid_critical_issue_categories'] = [
                issue.category for issue in validation.critical_issues
            ]
        
        if hasattr(validation, 'all_issues') and validation.all_issues:
            constraints['fix_issues'] = [
                {
                    "category": issue.category,
                    "description": issue.description,
                    "recommendation": getattr(issue, 'recommendation', '')
                }
                for issue in validation.all_issues
            ]
        
        if hasattr(validation, 'recommendations') and validation.recommendations:
            constraints['recommendations'] = validation.recommendations
        
        return constraints
    
    def _build_failure_result(self, goal_id: str, goal: str, reason: str) -> Dict[str, Any]:
        """Build failure result when goal cannot be achieved."""
        self._log_evidence("goal_failed", {
            "goal_id": goal_id,
            "reason": reason,
            "iterations": self.iteration_count
        })
        
        return {
            "goal": goal,
            "status": "failed",
            "reason": reason,
            "iterations": self.iteration_count,
            "evidence_log": self.evidence_logger.get_log_path() if hasattr(self.evidence_logger, 'get_log_path') else None
        }
    
    def _log_evidence(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Log an evidence event to JSONL logger."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": event_data
        }
        
        try:
            if hasattr(self.evidence_logger, 'log_event'):
                self.evidence_logger.log_event(event_type, event_data)
            elif hasattr(self.evidence_logger, 'append'):
                self.evidence_logger.append(json.dumps(event) + "\n")
            else:
                logger.debug(f"Evidence: {event_type} - {event_data}")
        except Exception as e:
            logger.warning(f"Failed to log evidence: {e}")
    
    async def observe(self, goal: str, result: dict) -> None:
        """Read-only megfigyelés — ír meta_evidence.jsonl-be, NEM hívja
        a dispatcher-t (RISK_001 elkerülés). Az AgentLoop observe-only
        integrációjához."""
        import os
        record = {
            "event_type": "external_observation",
            "timestamp": datetime.now().isoformat(),
            "source": "agent_loop",
            "goal": goal,
            "result": result,
        }
        try:
            path = os.path.normpath(self.evidence_path)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
            logger.debug(f"[observe] Written external_observation to meta_evidence.jsonl")
        except Exception as e:
            logger.warning(f"observe write failed (non-fatal): {e}")

    def _generate_id(self) -> str:
        """Generate unique ID for goal execution."""
        from datetime import datetime
        import random
        import string
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        return f"{timestamp}_{random_suffix}"
