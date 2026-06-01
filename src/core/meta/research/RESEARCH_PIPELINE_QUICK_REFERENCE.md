# Bug Bounty Research Pipeline - Quick Reference

**Status:** ✅ COMPLETE (10/10 tests passing)

---

## Quick Start

```python
from src.core.meta.research import ResearchGoal, ResearchLoop

# 1. Define research goal
goal = ResearchGoal(
    target_name="TestAPI",
    scope="Public endpoints",
    focus_vectors=["broken_auth", "idor"],
    stop_condition="submission_ready"
)

# 2. Create loop with MetaController
loop = ResearchLoop(meta_controller)

# 3. Run research
result = await loop.run(goal)

# 4. Get findings
print(f"Success: {result.success}")
print(f"Findings: {result.promising_findings}")
```

---

## Components

| Component | File | Purpose |
|-----------|------|---------|
| ResearchGoal | research_goal.py | Define research objective |
| ResearchState | research_state.py | Track research progress |
| ResearchLoop | research_loop.py | Orchestrate via MetaController |
| ResearchResult | research_loop.py | Result dataclass |
| Tests | test_research_loop.py | 10 comprehensive tests |

---

## Key Methods

### ResearchGoal
- `__post_init__()` - Validation
- `to_dict()` - Convert to MetaController format

### ResearchState
- `mark_vector_explored(vector)` - Record tested
- `discard_vector(vector, reason)` - Record failed
- `add_finding(...)` - Record finding
- `get_remaining_vectors(all_vectors)` - Get untested
- `to_dict() / from_dict()` - Serialization

### ResearchLoop
- `async run(goal) -> ResearchResult` - Execute research
- `handle_validator_feedback(type, data)` - Convert feedback
- `_log_evidence(type, data)` - Log events

---

## Evidence Events

ResearchLoop logs these events to MetaController evidence log:

```
research_started       - Begin research
hypothesis_tested      - Test hypothesis
hypothesis_rejected    - Reject hypothesis (false_positive/low_impact/duplicate)
hypothesis_promoted    - Promote finding (promising)
research_completed     - Complete research (success)
research_error         - Error occurred
```

---

## Validator Feedback Types

| Feedback | Constraint | Action |
|----------|-----------|--------|
| false_positive | exclude_vectors | Skip in next iteration |
| low_impact | low_impact_vectors | Deprioritize |
| duplicate | exclude_vectors | Skip in next iteration |
| promising | (none) | Promote finding |

---

## Test Suite

**10/10 Tests Passing** ✅

```bash
# Run tests
cd src/core/meta/research
python -m pytest test_research_loop.py -v

# Run specific test
python -m pytest test_research_loop.py::test_research_loop_failure_replan_success -v
```

---

## Architecture

```
ResearchGoal
    ↓
ResearchLoop.run()
    ↓
MetaController.run_goal()  ← Orchestration!
    ↓
Council / Executor / Validator
    ↓
ResearchResult
    └─ promising_findings
    └─ completion_reason
    └─ evidence_logged
```

---

## Key Design Decisions

✅ **Additive Only** - No changes to existing Meta Layer  
✅ **Reuse Infrastructure** - Uses existing Council/Executor/Validator  
✅ **No Real Tools** - Pure research workflow framework  
✅ **Evidence Integration** - Logs to same JSONL as Meta Layer  
✅ **Clean Separation** - Orthogonal to core Meta Layer  

---

## Files

- `research_goal.py` - Research objective definition
- `research_state.py` - State tracking (60-99 lines)
- `research_loop.py` - MetaController orchestration (170 lines)
- `test_research_loop.py` - 10 comprehensive tests (450+ lines)
- `__init__.py` - Package initialization
- `RESEARCH_PIPELINE_COMPLETE.md` - Full documentation
- `RESEARCH_PIPELINE_QUICK_REFERENCE.md` - This file

---

## Example Workflow

### Iteration 1: Initial hypothesis
```
Goal: Research "Company-X API"
Vector: "broken_auth"
Hypothesis: "Missing password validation"
Result: FAIL
Feedback: "false_positive"
→ Mark vector as discarded
```

### Iteration 2: Second hypothesis
```
Vector: "idor"
Hypothesis: "Predictable user IDs"
Result: PASS
Confidence: 0.85
→ Add to findings
```

### Final Result
```
success: True
findings: [{hypothesis: "Predictable user IDs", confidence: 0.85, ...}]
completion_reason: "submission_ready"
```

---

## Status: READY FOR PRODUCTION 🚀

- ✅ All tests passing
- ✅ Full Meta Layer integration
- ✅ Evidence logging enabled
- ✅ Clean code, no refactoring
- ✅ Comprehensive documentation
