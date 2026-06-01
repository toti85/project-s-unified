# META Layer Integration Guide

## Overview

The META layer provides consensus-based decision making through coordinated analysis from multiple specialized AI strategists. This document describes how to integrate the Strategy Council into Project-S super_core.

## Architecture

```
SuperIntelligentAI
    ↓
[Task Analysis]
    ↓
StrategyCouncil (NEW)
    ├── AIStrategist (Strategic Role)
    ├── AIStrategist (Security Role)
    └── AIStrategist (Technical Role)
    ↓
[Consensus Decision]
    ↓
LangGraphEngine / SmartToolOrchestrator
    ↓
[Execution]
```

## Integration Points

### 1. Import in SuperIntelligentAI

**File:** `src/core/super_intelligent_ai.py`

```python
from core.meta import StrategyCouncil, AIStrategist
```

### 2. Initialize Council in SuperIntelligentAI.__init__()

```python
class SuperIntelligentAI:
    def __init__(self):
        # ... existing code ...
        
        # Initialize META layer strategy council
        self.strategy_council = StrategyCouncil()
        self.strategy_council.add_strategist(
            AIStrategist("qwen3-235b", "strategic")
        )
        self.strategy_council.add_strategist(
            AIStrategist("claude-opus", "security")
        )
        self.strategy_council.add_strategist(
            AIStrategist("deepseek-v3", "technical")
        )
        
        logger.info("META layer strategy council initialized")
```

### 3. Call Council in Task Analysis Phase

**File:** `src/core/super_intelligent_ai.py`

**Location:** In the main task processing flow (after initial task understanding, before tool execution)

```python
async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
    """Process a task using multi-AI consensus."""
    
    # Phase 1: Task understanding (existing code)
    logger.info(f"Processing task: {task.get('description', '')}")
    
    # Phase 2: META LAYER - Get strategic consensus (NEW)
    logger.info("🧠 Consulting META layer strategy council...")
    
    decision = await self.strategy_council.decide(
        goal=task.get('description', ''),
        context={
            'task_id': task.get('id'),
            'tools_available': len(self.tool_registry.tools),
            'complexity': self._assess_complexity(task),
            'security_context': task.get('security_level', 'normal')
        }
    )
    
    # Handle decision
    if decision.decision == "rejected":
        logger.warning(f"Council rejected task: {decision.consensus_type} consensus")
        return {
            "status": "rejected",
            "reason": f"Strategy council consensus: {decision.consensus_type}",
            "details": decision.recommended_plan
        }
    
    if decision.decision == "conditional":
        logger.info(f"Council approved conditionally: {decision.consensus_type}")
        logger.info(f"Conditions: {decision.aggregated_risks}")
    
    # Phase 3: Continue with existing orchestration (existing code)
    logger.info("📋 Executing task with council approval...")
    # ... rest of existing code ...
```

### 4. Configuration Thresholds

**File:** `src/core/meta/strategy_council.py`

Adjust in `StrategyCouncil.__init__()`:

```python
# Decision thresholds (current defaults)
self.feasibility_threshold = 70.0      # Min avg feasibility to approve
self.confidence_threshold = 60.0       # Min avg confidence to approve
self.approval_threshold = 0.5          # Min 50% approval ratio
```

**Recommended adjustments:**
- **Conservative:** feasibility=75, confidence=70, approval=0.67 (2/3 majority)
- **Moderate (default):** feasibility=70, confidence=60, approval=0.5
- **Aggressive:** feasibility=65, confidence=50, approval=0.33 (1/3 majority)

## Real AI Model Integration

### Phase 1 (Current): Mock Implementation

Strategists use mock analysis based on role:
- **Strategic:** Assesses long-term implications
- **Security:** Evaluates security risks and API exposure
- **Technical:** Checks implementation feasibility

### Phase 2: Real API Integration

Replace mock implementations in `AIStrategist._analyze_with_api()`:

```python
async def _analyze_with_api(self, goal: str, context: Dict[str, Any]) -> AIOpinion:
    """Call actual AI API for analysis."""
    
    # Build role-specific prompt
    prompt = self._build_prompt(goal, context)
    
    # Call appropriate AI provider
    if self.ai_name.startswith("qwen3"):
        response = await self.qwen3_client.call(prompt)
    elif self.ai_name.startswith("claude"):
        response = await self.claude_client.call(prompt)
    elif self.ai_name.startswith("deepseek"):
        response = await self.deepseek_client.call(prompt)
    
    # Parse response into AIOpinion
    opinion = self._parse_response(response)
    return opinion
```

### API Key Configuration

**File:** `.env` (create if needed)

```
QWEN3_API_KEY=your_qwen3_key
CLAUDE_API_KEY=your_claude_key
DEEPSEEK_API_KEY=your_deepseek_key
```

**Load in SuperIntelligentAI:**

```python
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize with real API clients
from integrations.ai_models import QwenClient, ClaudeClient, DeepSeekClient

strategist_strategic = AIStrategist(
    "qwen3-235b",
    "strategic",
    api_client=QwenClient(api_key=os.getenv("QWEN3_API_KEY"))
)
```

## Testing Integration

### Run Council Tests

```bash
cd c:\1225\project_s_super_core
python -m src.core.meta.test_council
```

**Expected output:**
```
TEST 1: UNANIMOUS CONSENSUS
  ✅ PASS

TEST 2: MAJORITY CONSENSUS
  ✅ PASS

TEST 3: SPLIT CONSENSUS
  ✅ PASS

TEST 4: CONDITIONAL APPROVAL
  ✅ PASS

🎉 ALL TESTS PASSED
```

### Integration Test with SuperIntelligentAI

```python
# tests/test_meta_integration.py
import asyncio
from src.core.super_intelligent_ai import SuperIntelligentAI

async def test_council_integration():
    ai = SuperIntelligentAI()
    
    task = {
        "description": "Analyze security of a web application",
        "complexity": "high"
    }
    
    result = await ai.process_task(task)
    
    assert result["status"] in ["approved", "conditional", "rejected"]
    print(f"✅ Council decision: {result['status']}")

asyncio.run(test_council_integration())
```

## Monitoring & Logging

### Council Decisions in Logs

META layer logs all decisions to:
- **Log file:** `logs/meta_decisions.log`
- **Structured data:** `memory/meta_decisions.jsonl`

```python
# Get council statistics
stats = council.get_decision_stats()
# {
#   "total_decisions": 42,
#   "approved": 28,
#   "rejected": 8,
#   "conditional": 6,
#   "consensus_types": {"unanimous": 15, "majority": 20, "split": 7}
# }
```

### Strategist Performance

```python
# Track individual strategist performance
strategist_stats = council.get_strategist_stats()
# [
#   {"ai_name": "qwen3-235b", "role": "strategic", "analysis_count": 42},
#   {"ai_name": "claude-opus", "role": "security", "analysis_count": 42},
#   {"ai_name": "deepseek-v3", "role": "technical", "analysis_count": 42}
# ]
```

## Performance Impact

### Overhead per Decision

- **3 strategists:** ~100-200ms (mock) / ~2-5s (real API)
- **Decision storage:** ~2KB per decision in memory/meta_decisions.jsonl

### Scaling Considerations

- Add more strategists as needed (recommended max: 7)
- Cache common analysis patterns
- Batch decisions for similar goals

## Troubleshooting

### Council Returns "Split" Consensus

**Issue:** Low approval ratio (less than 50%)

**Solutions:**
1. Adjust `approval_threshold` to lower value
2. Review strategist configurations
3. Improve task context provided to council
4. Add more strategists to reduce individual impact

### High Confidence but Low Feasibility

**Issue:** All strategists confident but few think it's feasible

**Solutions:**
1. Break down complex tasks into smaller ones
2. Provide more context about available resources
3. Lower `feasibility_threshold` if tasks are ambitious

### Strategist Disagreement

**Issue:** Strategists have conflicting opinions

**This is expected!** Use `decision.recommended_plan` to understand different perspectives.

## Phase 2 Planning

After META layer is stable in production:

1. **Execution Validator:** Verify council decisions against actual execution results
2. **Learning Integration:** Feed execution results back to strategists
3. **Prompt Optimization:** Improve role-specific prompts based on results
4. **Ensemble Methods:** Weight strategist opinions by historical accuracy

## References

- [Decision data structure](./decision.py)
- [AIStrategist implementation](./ai_strategist.py)
- [StrategyCouncil implementation](./strategy_council.py)
- [Test suite](./test_council.py)
