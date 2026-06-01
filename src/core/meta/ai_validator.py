"""
Individual AI validator for execution result validation.
"""
import logging
import time
from typing import Dict, Any, Optional, List
from .validation_result import ValidationCheck, ValidationIssue


logger = logging.getLogger(__name__)


class AIValidator:
    """
    Single AI model for validation checks.
    
    Check types:
    - correctness: Did execution achieve goal? Accurate results?
    - security: Security vulnerabilities? Data exposure? Auth issues?
    - quality: Code quality? Error handling? Performance?
    """
    
    def __init__(self, model_name: str, check_type: str, api_client=None):
        """
        Initialize validator.
        
        Args:
            model_name: AI model identifier (e.g., "qwen3-235b", "gpt-4o")
            check_type: One of "correctness", "security", "quality"
            api_client: Optional API client for real validation
        """
        self.model_name = model_name
        self.check_type = check_type
        self.api_client = api_client
        self.validation_count = 0
        
        # Check-specific prompts
        self.check_prompts = {
            "correctness": """Verify execution correctness:
1. Did it achieve the intended goal completely?
2. Are results accurate and complete?
3. Any logic errors or failed operations?
4. Data integrity issues?
5. Edge cases handled?

Return: PASS/FAIL with confidence 0-100""",
            
            "security": """Security review of execution:
1. Any security vulnerabilities introduced?
2. Data exposure risks?
3. Authentication/authorization issues?
4. Input validation problems?
5. Injection attacks possible?
6. API key or credential exposure?

Return: PASS/FAIL with confidence 0-100""",
            
            "quality": """Quality assessment:
1. Code quality and practices followed?
2. Error handling adequate?
3. Performance concerns?
4. Best practices followed?
5. Maintainability issues?
6. Documentation adequate?

Return: PASS/FAIL with confidence 0-100"""
        }
        
        logger.info(f"AIValidator initialized: {model_name} ({check_type})")
    
    async def validate(
        self,
        execution_result: Dict[str, Any],
        original_goal: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ValidationCheck:
        """
        Validate execution result.
        
        Args:
            execution_result: Result from execution
            original_goal: Original goal/task
            context: Additional context
            
        Returns:
            ValidationCheck with this validator's assessment
        """
        self.validation_count += 1
        start_time = time.time()
        
        if self.api_client:
            check = await self._validate_with_api(execution_result, original_goal, context)
        else:
            check = self._validate_mock(execution_result, original_goal, context)
        
        # Record timing
        check.check_time_ms = int((time.time() - start_time) * 1000)
        
        logger.debug(f"{self.model_name} ({self.check_type}): "
                    f"{'PASS' if check.passed else 'FAIL'} "
                    f"(confidence: {check.confidence}, issues: {len(check.issues)})")
        
        return check
    
    async def _validate_with_api(
        self,
        execution_result: Dict[str, Any],
        original_goal: str,
        context: Optional[Dict[str, Any]]
    ) -> ValidationCheck:
        """Call real AI API for validation."""
        # Placeholder for real API implementation
        return self._validate_mock(execution_result, original_goal, context)
    
    def _validate_mock(
        self,
        execution_result: Dict[str, Any],
        original_goal: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ValidationCheck:
        """Mock validation for testing."""
        
        context = context or {}
        result_status = execution_result.get("status", "unknown").lower()
        
        if self.check_type == "correctness":
            return self._validate_correctness(execution_result, original_goal, context)
        elif self.check_type == "security":
            return self._validate_security(execution_result, original_goal, context)
        elif self.check_type == "quality":
            return self._validate_quality(execution_result, original_goal, context)
        else:
            return self._validate_generic(execution_result, original_goal, context)
    
    def _validate_correctness(
        self,
        execution_result: Dict[str, Any],
        original_goal: str,
        context: Dict[str, Any]
    ) -> ValidationCheck:
        """Validate correctness of execution."""
        
        status = execution_result.get("status", "unknown").lower()
        
        # Check for actual errors (not just the word "error" in field names)
        error_list = execution_result.get("errors", [])
        error_field = execution_result.get("error", "")
        has_errors = bool(error_list) or bool(error_field)
        
        passed = status == "success" and not has_errors
        confidence = 85 if passed else 65
        
        issues = []
        if has_errors:
            issues.append(ValidationIssue(
                severity="high" if not passed else "medium",
                category="correctness",
                description="Errors detected in execution result",
                found_by=self.model_name,
                location="execution_result.error",
                recommendation="Review error messages and retry with adjusted parameters"
            ))
        
        if not passed:
            issues.append(ValidationIssue(
                severity="high",
                category="correctness",
                description="Execution did not complete successfully",
                found_by=self.model_name,
                location="execution_result.status",
                recommendation=f"Goal '{original_goal}' not achieved. Review execution flow."
            ))
        
        reasoning = (
            f"Goal execution status: {status}. "
            f"Errors present: {has_errors}. "
            f"Result meets correctness criteria: {passed}."
        )
        
        return ValidationCheck(
            validator_name=self.model_name,
            check_type=self.check_type,
            passed=passed,
            confidence=confidence,
            issues=issues,
            reasoning=reasoning
        )
    
    def _validate_security(
        self,
        execution_result: Dict[str, Any],
        original_goal: str,
        context: Dict[str, Any]
    ) -> ValidationCheck:
        """Validate security of execution."""
        
        result_str = str(execution_result).lower()
        
        # Check for security concerns
        has_api_key = "api_key" in result_str or "apikey" in result_str
        has_password = "password" in result_str or "passwd" in result_str
        has_token = "token" in result_str
        
        security_concerns = has_api_key or has_password or has_token
        
        passed = not security_concerns
        confidence = 90 if passed else 75
        
        issues = []
        
        if has_api_key:
            issues.append(ValidationIssue(
                severity="critical",
                category="security",
                description="API key exposed in execution result",
                found_by=self.model_name,
                location="execution_result",
                recommendation="Implement secrets masking and use secure key management"
            ))
        
        if has_password:
            issues.append(ValidationIssue(
                severity="critical",
                category="security",
                description="Password/credential exposed in result",
                found_by=self.model_name,
                location="execution_result",
                recommendation="Never log or return passwords. Use secure credential handling."
            ))
        
        if has_token:
            issues.append(ValidationIssue(
                severity="high",
                category="security",
                description="Token data present in execution result",
                found_by=self.model_name,
                location="execution_result",
                recommendation="Mask tokens in output. Implement token rotation policies."
            ))
        
        reasoning = (
            f"Security check findings: API key exposure={has_api_key}, "
            f"Password exposure={has_password}, Token exposure={has_token}. "
            f"Overall security status: {'SECURE' if passed else 'CONCERNS FOUND'}."
        )
        
        return ValidationCheck(
            validator_name=self.model_name,
            check_type=self.check_type,
            passed=passed,
            confidence=confidence,
            issues=issues,
            reasoning=reasoning
        )
    
    def _validate_quality(
        self,
        execution_result: Dict[str, Any],
        original_goal: str,
        context: Dict[str, Any]
    ) -> ValidationCheck:
        """Validate quality of execution."""
        
        # Check for quality indicators
        has_execution_time = "execution_time" in execution_result or "duration" in execution_result
        has_step_count = "steps" in execution_result or "step_count" in execution_result
        has_metadata = "metadata" in execution_result or "metrics" in execution_result
        
        quality_indicators = sum([has_execution_time, has_step_count, has_metadata])
        
        passed = quality_indicators >= 2
        confidence = 75 if passed else 70
        
        issues = []
        
        if not has_execution_time:
            issues.append(ValidationIssue(
                severity="low",
                category="quality",
                description="Missing execution timing information",
                found_by=self.model_name,
                location="execution_result",
                recommendation="Add timing metrics (execution_time, start_time, end_time)"
            ))
        
        if not has_step_count:
            issues.append(ValidationIssue(
                severity="low",
                category="quality",
                description="Missing step tracking information",
                found_by=self.model_name,
                location="execution_result",
                recommendation="Include step count and individual step metrics"
            ))
        
        if not has_metadata:
            issues.append(ValidationIssue(
                severity="low",
                category="quality",
                description="Missing execution metadata",
                found_by=self.model_name,
                location="execution_result",
                recommendation="Add metadata about execution context and environment"
            ))
        
        reasoning = (
            f"Quality assessment: Execution timing={has_execution_time}, "
            f"Step tracking={has_step_count}, Metadata present={has_metadata}. "
            f"Quality score: {quality_indicators}/3."
        )
        
        return ValidationCheck(
            validator_name=self.model_name,
            check_type=self.check_type,
            passed=passed,
            confidence=confidence,
            issues=issues,
            reasoning=reasoning
        )
    
    def _validate_generic(
        self,
        execution_result: Dict[str, Any],
        original_goal: str,
        context: Dict[str, Any]
    ) -> ValidationCheck:
        """Generic validation."""
        
        return ValidationCheck(
            validator_name=self.model_name,
            check_type=self.check_type,
            passed=True,
            confidence=70,
            issues=[],
            reasoning="Generic validation passed."
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get validator statistics."""
        return {
            "model_name": self.model_name,
            "check_type": self.check_type,
            "validation_count": self.validation_count
        }
