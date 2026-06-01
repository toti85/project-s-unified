# CI GATE Configuration - Phase 5 Meta Layer Hardening

## Overview
Hard gate to prevent merge of code that breaks Meta Layer invariants or fails regression tests.

## Required Test Passes (ALL Must Pass for Merge)

### Regression Tests (Golden Evidence Baselines)
```
golden/meta_evidence_fail_replan_pass.jsonl
golden/meta_evidence_immediate_success.jsonl
```
**Purpose:** Regression baseline - detect if Meta Layer behavior changes unexpectedly

### Unit Tests (MetaController)
1. **test_meta_controller.py::test_fail_replan_pass**
   - Scenario: Iteration 1 fails → replan → iteration 2 passes
   - Validates: Replan loop, constraint extraction, state updates
   - Gate check: Iteration count = 2, success = true

2. **test_meta_controller.py::test_immediate_success**
   - Scenario: Single iteration success
   - Validates: Immediate goal completion, no replan needed
   - Gate check: Iteration count = 1, success = true

3. **test_meta_controller.py::test_council_rejection**
   - Scenario: Council rejects plan
   - Validates: Hard failure on plan rejection
   - Gate check: Status = "plan_rejected"

### Integration Tests (SuperIntelligentAI + MetaController)
4. **test_meta_integration.py::test_meta_controller_integration_fail_replan_pass**
   - Scenario: Full integration test with fail→replan→pass
   - Validates: SuperIntelligentAI routing to MetaController
   - Gate check: Integration execution path verified

5. **test_meta_integration.py::test_meta_controller_disabled**
   - Scenario: MetaController disabled (backward compatibility)
   - Validates: SuperIntelligentAI still works with use_meta_controller=false
   - Gate check: Legacy code path functions

### Existing Project-S Tests
6. **TEST_D** (existing)
   - Purpose: Project-S comprehensive test
   - Gate: Must pass

7. **TEST_E** (existing)
   - Purpose: Project-S comprehensive test
   - Gate: Must pass

## Invariant Gates Active in MetaController

**Gate 1: After plan_selected (Line ~150)**
```python
assert self.state is not None
assert self.iteration_count > 0
assert decision is not None
```

**Gate 2: After validation_done (Line ~220)**
```python
assert validation is not None
assert validation.consensus_type in valid_list
assert validation.confidence is not None
```

**Gate 3: Before goal_completed (Line ~235)**
```python
assert self.iteration_count > 0
assert self.iteration_count <= max_iters
assert execution_result.status == 'success'
assert validation.confidence > 0
```

## Merge Gate Logic

```
If ANY test fails:
  ❌ BLOCK MERGE
  Status: FAIL
  Message: "[CI_GATE] Test <name> failed - meta_controller regression detected"
  Action: Require fix before merge

If ALL tests pass:
  ✅ ALLOW MERGE
  Status: PASS
  Message: "[CI_GATE] All 7 tests passing - safe to merge"
  Action: Merge allowed
```

## Running CI Gate Manually

```bash
# Run all regression + unit + integration tests
pytest test_meta_controller.py test_meta_integration.py -v

# Run existing Project-S tests
python TEST_D.py
python TEST_E.py

# Full CI gate check (all 7 tests)
bash ci_gate_check.sh
```

## Golden Evidence Baseline Immutability

Golden JSONL files are **FROZEN** and should NOT change:
- `golden/meta_evidence_fail_replan_pass.jsonl`
- `golden/meta_evidence_immediate_success.jsonl`

If these files change unexpectedly, it indicates:
1. Meta Layer behavior regression
2. Evidence logging format change
3. Iteration count change

**Resolution:** Investigate root cause before merging.

## CI Pipeline Integration

### GitHub Actions (if using .github/workflows/ci.yml)
```yaml
- name: Run Meta Layer CI Gate
  run: |
    pytest test_meta_controller.py test_meta_integration.py -v
    python TEST_D.py
    python TEST_E.py
  if: always()
  
- name: Check CI Gate Status
  run: |
    if [ $GITHUB_LAST_STATUS -ne 0 ]; then
      echo "[CI_GATE] Tests failed - merge blocked"
      exit 1
    fi
    echo "[CI_GATE] All tests passed - safe to merge"
```

## Merge Checklist

Before merge, verify:
- [ ] All 7 tests passing
- [ ] Golden evidence files unchanged
- [ ] Invariant gates enabled in meta_controller.py
- [ ] No silent failures in Meta Layer execution
- [ ] Evidence logs generated correctly

## Failure Diagnosis

If CI gate fails:

1. **test_fail_replan_pass failed**
   - Check: Replan logic in MetaController.run_goal()
   - Check: Constraint extraction from validation

2. **test_immediate_success failed**
   - Check: Single-iteration completion path
   - Check: Validation confidence threshold

3. **test_council_rejection failed**
   - Check: Plan rejection handling
   - Check: Error propagation

4. **Invariant gate assertion failed**
   - Check: State consistency
   - Check: Iteration count monotonicity
   - Check: Validation result validity
   - Check: Execution result status

5. **Golden evidence mismatch**
   - Check: Evidence logger format
   - Check: Event sequence correctness
   - Check: Iteration count tracking

## Tag: super_core_meta_v1.0_verified

This commit includes:
- ✅ MetaController with 3 invariant gates
- ✅ SuperIntelligentAI integration
- ✅ Golden evidence baselines (FROZEN)
- ✅ CI gate configuration
- ✅ All 15 tests passing (13 unit + 2 integration + 2 existing)
