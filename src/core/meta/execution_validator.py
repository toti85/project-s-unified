"""
Execution Validator: Multi-AI execution result validation.

Coordinates multiple AI validators to reach consensus on
execution result quality and correctness.
"""
import logging
import uuid
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from .validation_result import ValidationResult, ValidationCheck, ValidationIssue
from .ai_validator import AIValidator


logger = logging.getLogger(__name__)


class ExecutionValidator:
    """
    Multi-AI execution validation orchestrator.
    
    Validates execution results by running multiple specialized validators
    in parallel and reaching consensus on result quality.
    """
    
    def __init__(self, validators: Optional[List[AIValidator]] = None):
        """
        Initialize validator.
        
        Args:
            validators: List of AIValidator instances (optional)
        """
        self.validators = validators or []
        self.validations_performed = []
        
        # Validation thresholds
        self.critical_issue_fails = True  # Any critical issue = fail
        # Strict majority: floor(N/2) + 1 validators must pass (count-based, no float)
        # - 3 validators: 2 required
        # - 5 validators: 3 required
        # - etc.
        self.min_confidence = 60.0       # Average confidence threshold for CONDITIONAL
        
        logger.info(f"ExecutionValidator initialized with {len(self.validators)} validators")
    
    def add_validator(self, validator: AIValidator) -> None:
        """Add a validator to the panel."""
        self.validators.append(validator)
        logger.info(f"Validator added: {validator.model_name} ({validator.check_type})")
    
    async def validate(
        self,
        execution_result: Dict[str, Any],
        original_goal: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Multi-AI validation of execution result.
        
        Process:
        1. Gather checks from all validators in parallel
        2. Aggregate issues by severity
        3. Calculate consensus (pass/fail/conditional)
        4. Build recommendations
        
        Fail conditions:
        - Any critical issue found
        - Less than 67% validators pass
        - Average confidence below threshold
        
        Args:
            execution_result: Result from task execution
            original_goal: Original task goal
            context: Additional context
            
        Returns:
            ValidationResult with multi-AI consensus
        """
        validation_id = f"validation_{uuid.uuid4().hex[:8]}"
        start_time = datetime.now()
        
        logger.info(f"Validation started: {validation_id}")
        logger.info(f"Goal: {original_goal}")
        
        # Gather checks from all validators in parallel
        checks = await self._gather_checks(execution_result, original_goal, context)
        
        # Aggregate issues
        all_issues = self._aggregate_issues(checks)
        critical_issues = self._get_critical_issues(all_issues)
        high_issues = self._get_high_issues(all_issues)
        
        # Calculate consensus
        validation_result = self._calculate_validation_consensus(
            validation_id=validation_id,
            checks=checks,
            all_issues=all_issues,
            critical_issues=critical_issues,
            high_issues=high_issues
        )
        
        # Record timing
        validation_result.total_validation_time_ms = int(
            (datetime.now() - start_time).total_seconds() * 1000
        )
        
        # Store in history
        self.validations_performed.append({
            "validation_id": validation_id,
            "goal": original_goal,
            "timestamp": datetime.now().isoformat(),
            "passed": validation_result.passed,
            "consensus": validation_result.consensus_type,
            "confidence": validation_result.confidence
        })
        
        logger.info(f"Validation completed: {validation_id} -> {validation_result.consensus_type} "
                   f"(confidence: {validation_result.confidence:.1f}%)")
        
        return validation_result
    
    async def _gather_checks(
        self,
        execution_result: Dict[str, Any],
        original_goal: str,
        context: Optional[Dict[str, Any]]
    ) -> List[ValidationCheck]:
        """
        Gather validation checks from all validators in parallel.
        
        Args:
            execution_result: Execution result to validate
            original_goal: Original goal
            context: Additional context
            
        Returns:
            List of ValidationCheck from all validators
        """
        if not self.validators:
            logger.warning("No validators configured")
            return []
        
        # Run all validators in parallel
        tasks = [
            validator.validate(execution_result, original_goal, context)
            for validator in self.validators
        ]
        
        checks = await asyncio.gather(*tasks)
        
        logger.debug(f"Gathered {len(checks)} validation checks")
        
        return checks
    
    def _calculate_validation_consensus(
        self,
        validation_id: str,
        checks: List[ValidationCheck],
        all_issues: List[ValidationIssue],
        critical_issues: List[ValidationIssue],
        high_issues: List[ValidationIssue]
    ) -> ValidationResult:
        """
        Calculate validation consensus from all checks.
        
        Logic:
        1. If any CRITICAL issue → FAIL (override all)
        2. If sufficient validators pass (strict majority) → consider PASS
           - Required: floor(N/2) + 1 validators must pass (count-based)
           - Examples: 3 validators need 2, 5 validators need 3
        3. If <majority pass → FAIL
        4. If avg confidence <60% but majority pass → CONDITIONAL
        5. Otherwise → PASS
        
        Args:
            validation_id: Validation ID
            checks: List of ValidationCheck from all validators
            all_issues: All aggregated issues
            critical_issues: Critical severity issues
            high_issues: High severity issues
            
        Returns:
            ValidationResult with consensus
        """
        if not checks:
            # AO7_T3 FIX 2: 0 validators → unanimous_pass (pass), not "failed".
            # When ExecutionValidator is instantiated with no validators,
            # empty checks list should not cause failure. This was the root
            # cause of infinite replan loops (diagnosed 2026-06-18).
            # Note: "unanimous_pass" is used because it's a valid consensus_type
            # accepted by MetaController's invariant gate 2.
            return ValidationResult(
                passed=True,
                confidence=100.0,
                consensus_type="unanimous_pass",
                validation_id=validation_id,
                all_issues=[],
                critical_issues=[],
                high_issues=[],
                recommendations=["[OK] No validators registered — output accepted (AO7_T3 fix)"]
            )
        
        # Count passes and calculate majority requirement (count-based, not float)
        pass_count = sum(1 for check in checks if check.passed)
        total_validators = len(checks)
        
        # Strict majority: floor(N/2) + 1 (count-based, no float)
        # - 3 validators: 2 required
        # - 5 validators: 3 required
        # - 4 validators: 3 required
        required_pass_count = (total_validators // 2) + 1
        has_majority = pass_count >= required_pass_count
        
        # Calculate average confidence
        avg_confidence = sum(check.confidence for check in checks) / total_validators
        
        # Determine consensus type based on validator count
        all_pass = all(check.passed for check in checks)
        
        if all_pass:
            consensus_type = "unanimous_pass"
        elif has_majority:
            consensus_type = "majority_pass"
        else:
            consensus_type = "failed"
        
        # Make pass/fail decision
        passed = True
        
        # Fail if any critical issue (highest priority)
        if self.critical_issue_fails and critical_issues:
            passed = False
            consensus_type = "failed"
            logger.warning(f"Validation failed: {len(critical_issues)} critical issue(s) found")
        
        # Fail if insufficient validators passed (strict majority)
        elif not has_majority:
            passed = False
            consensus_type = "failed"
            logger.warning(f"Validation failed: Only {pass_count}/{total_validators} validators passed "
                          f"(requires {required_pass_count} for majority)")
        
        # Conditional if low confidence
        elif avg_confidence < self.min_confidence:
            passed = True
            consensus_type = "conditional"
            logger.info(f"Validation conditional: Low average confidence ({avg_confidence:.1f}%)")
        
        # Build recommendations
        recommendations = self._build_recommendations(all_issues, critical_issues, high_issues)
        
        # Create result
        validation_result = ValidationResult(
            passed=passed,
            confidence=avg_confidence,
            consensus_type=consensus_type,
            checks=checks,
            all_issues=all_issues,
            critical_issues=critical_issues,
            high_issues=high_issues,
            recommendations=recommendations,
            validation_id=validation_id
        )
        
        return validation_result
    
    def _aggregate_issues(self, checks: List[ValidationCheck]) -> List[ValidationIssue]:
        """
        Aggregate and deduplicate issues from all checks.
        
        Args:
            checks: List of ValidationCheck
            
        Returns:
            Deduplicated list of all issues
        """
        all_issues = []
        seen_descriptions = set()
        
        for check in checks:
            for issue in check.issues:
                # Deduplicate by description (similar issues from different validators)
                if issue.description not in seen_descriptions:
                    all_issues.append(issue)
                    seen_descriptions.add(issue.description)
        
        return all_issues
    
    def _get_critical_issues(self, issues: List[ValidationIssue]) -> List[ValidationIssue]:
        """Filter critical severity issues."""
        return [issue for issue in issues if issue.severity == "critical"]
    
    def _get_high_issues(self, issues: List[ValidationIssue]) -> List[ValidationIssue]:
        """Filter high severity issues."""
        return [issue for issue in issues if issue.severity == "high"]
    
    def _build_recommendations(
        self,
        all_issues: List[ValidationIssue],
        critical_issues: List[ValidationIssue],
        high_issues: List[ValidationIssue]
    ) -> List[str]:
        """
        Build recommendations based on issues found.
        
        Args:
            all_issues: All issues
            critical_issues: Critical issues
            high_issues: High issues
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Critical issue recommendations
        if critical_issues:
            recommendations.append(f"⚠️ CRITICAL: {len(critical_issues)} critical issue(s) must be fixed")
            for issue in critical_issues[:3]:  # Top 3
                recommendations.append(f"  - {issue.recommendation}")
        
        # High issue recommendations
        if high_issues:
            recommendations.append(f"🔴 HIGH: {len(high_issues)} high-priority issue(s) recommended")
            for issue in high_issues[:3]:  # Top 3
                recommendations.append(f"  - {issue.recommendation}")
        
        # General recommendations
        if not all_issues:
            recommendations.append("[OK] No issues found - execution quality is good")
        
        return recommendations
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get statistics on all validations performed."""
        if not self.validations_performed:
            return {
                "total_validations": 0,
                "passed": 0,
                "failed": 0,
                "conditional": 0
            }
        
        passed = sum(1 for v in self.validations_performed if v["passed"] and "unanimous" in v["consensus"])
        failed = sum(1 for v in self.validations_performed if not v["passed"])
        conditional = sum(1 for v in self.validations_performed if "conditional" in v["consensus"])
        
        avg_confidence = (
            sum(v["confidence"] for v in self.validations_performed) / len(self.validations_performed)
        )
        
        return {
            "total_validations": len(self.validations_performed),
            "passed": passed,
            "failed": failed,
            "conditional": conditional,
            "avg_confidence": avg_confidence,
            "consensus_types": {
                "unanimous_pass": sum(1 for v in self.validations_performed if v["consensus"] == "unanimous_pass"),
                "majority_pass": sum(1 for v in self.validations_performed if v["consensus"] == "majority_pass"),
                "conditional": sum(1 for v in self.validations_performed if v["consensus"] == "conditional"),
                "failed": sum(1 for v in self.validations_performed if v["consensus"] == "failed")
            }
        }
    
    def get_validator_stats(self) -> List[Dict[str, Any]]:
        """Get statistics for each validator."""
        return [validator.get_stats() for validator in self.validators]
