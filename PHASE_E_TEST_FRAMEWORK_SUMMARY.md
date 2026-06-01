## Phase E: Timing/Visibility Invariant Measurement Tests – Progress Report

**Status**: Framework Created (Compilation Requires API Refinement)

**Date Initiated**: Current Session  
**Previous Phases**: A–D all COMPLETE  
**Current Objective**: Create 3 measurement tests for delta accounting timing/visibility behaviors

---

## Summary

Three new Foundry test suites have been created to investigate subtle delta accounting behaviors in Uniswap V4:

1. **T1_IntermediateRealityLeak.t.sol** – Multi-step operation consistency
2. **T2_ReturnDeltaObserverParadox.t.sol** – Swap symmetry and price impact analysis  
3. **T3_LiquidityIdempotenceNetting.t.sol** – Round-trip liquidity netting behavior

### Test Philosophy

These tests follow a **measurement-only** approach:
- ✅ NO exploit attempts
- ✅ NO attacker personas  
- ✅ NO value-from-nothing narratives
- ✅ ONLY metric collection and logging
- ✅ Pure delta accounting investigation

---

## Test Descriptions

### T1: IntermediateRealityLeak

**Purpose**: Measure whether sequential operations (swap → donate → swap) produce idempotent deltas.

**Tests Defined**:
1. **test_T1_1_BaselineSwap()** – Single swap X, measure deltas
2. **test_T1_2_MultiStepOperations()** – Swap X/2 → Donate → Swap X/2, measure intermediate deltas
3. **test_T1_3_DeltaConsistency()** – Compare baseline vs multi-step outputs (bps precision)

**Metrics Collected**:
- delta0, delta1 for each step
- Net deltas (sum across operation sequence)
- Output difference in basis points (bps)
- Fee accrual breakdown

**Expected Outcome**: Multi-step deltas should be approximately equal to baseline (rounding tolerance <1 bps)

---

### T2: ReturnDeltaObserverParadox  

**Purpose**: Measure swap output asymmetry and price impact across different input sizes.

**Tests Defined**:
1. **test_T2_1_ForwardSwap()** – Swap token0→token1, measure output and fee
2. **test_T2_2_ReverseSwap()** – Swap token1→token0 back, measure round-trip loss
3. **test_T2_3_AsymmetryMeasurement()** – Quantify forward/reverse asymmetry (bps)
4. **test_T2_4_PriceImpactComparison()** – Test 3 input sizes: 100e18, 500e18, 1000e18

**Metrics Collected**:
- Forward output (token0→token1)
- Reverse output (token1→token0)  
- Fee charged per swap (wei)
- Effective fee per swap (bps)
- Round-trip loss (wei and bps)

**Expected Outcome**: Round-trip loss ≈ 2x fee (forward + reverse). Larger swaps show steeper price impact.

---

### T3: LiquidityIdempotenceNetting

**Purpose**: Measure whether adding/removing liquidity nette correctly when performed with swaps.

**Tests Defined**:
1. **test_T3_1_BaselineSwap()** – Swap alone, baseline deltas
2. **test_T3_2_AddLiquidityDelta()** – Add liquidity, measure token provision deltas
3. **test_T3_3_RoundTripNetting()** – Add → Swap → Remove (same ticks), measure net deltas
4. **test_T3_4_MultipleRoundTrips()** – Perform 3 add/swap/remove cycles, measure accumulation
5. **test_T3_5_EntitlementsDrift()** – Check if LP breaks even on add/remove (excluding swap fees)

**Metrics Collected**:
- Add/remove delta tokens (wei)
- Swap deltas (wei)
- Net deltas for full round-trip
- Unexplained drift (net - expected swap)
- LP entitlements after round-trip

**Expected Outcome**: 
- Add/remove should net to ~0 wei (idempotent)
- Net delta should equal swap delta (add/remove cancel)
- Cumulative error should not accumulate across multiple rounds (<100 wei/round)

---

## Current Status

### Completed ✅
- [x] Test design and hypothesis documentation
- [x] Test contract skeletal structure (3 files created)
- [x] setUp() infrastructure for each test
- [x] Test functions defined with console2.log metrics
- [x] Pass/fail thresholds documented
- [x] Comments explaining test methodology

### Pending (API Refinement Required) ⏳
- [ ] Fix `swapRouter.swap()` API signature (expects 4 args, not 3)
- [ ] Handle `BalanceDelta` return type casting (`int128` → safe uint256 handling)
- [ ] Resolve `console2.log()` signature compatibility with int256 multiple args
- [ ] Compilation verification
- [ ] Execution and metric collection

### Known API Issues to Resolve
1. **swapRouter.swap() signature**: Current calls pass 3 args (key, params, bytes), expects 4
   - Need to check PoolSwapTest interface for 4th parameter (likely `address` for recipient or similar)
   
2. **BalanceDelta type system**: amount0/amount1 return `int128`, not int256
   - Unsafe to cast directly to uint256; need careful sign handling
   
3. **console2.log() signature**: Calling with mixed int256 and string args may fail
   - May need to convert int256 to string or use separate log calls

---

## Test Execution Plan (Next Steps)

1. **Fix PoolSwapTest API**
   - Review src/test/PoolSwapTest.sol interface
   - Identify 4th parameter requirement
   - Update all swap() calls to include 4th arg

2. **Handle BalanceDelta Conversion Safely**
   - Check BalanceDelta struct definition (int128 fields)
   - Implement safe casting or access raw amounts directly

3. **Refactor console2 Logging**
   - Split complex log statements
   - Or cast int types to string explicitly

4. **Compile and Execute**
   - `forge build` - verify compilation
   - `forge test --match-contract "T[123]_" -vv` - run all 3 tests with verbose output
   - Capture metrics from console output

5. **Analyze Results**
   - Collect metric spreadsheet from test output
   - Document findings for each test
   - Compare against hypothesized thresholds

---

## Code Artifacts

**Files Created**:
- `test/T1_IntermediateRealityLeak.t.sol` (130 lines)
  - 3 test functions
  - Measures multi-step operation consistency
  - Metrics: delta0, delta1, net, output diff (bps)

- `test/T2_ReturnDeltaObserverParadox.t.sol` (202 lines)
  - 4 test functions
  - Measures swap symmetry and price impact
  - Metrics: forward output, reverse output, fees, round-trip loss

- `test/T3_LiquidityIdempotenceNetting.t.sol` (320 lines)
  - 5 test functions
  - Measures liquidity netting across operations
  - Metrics: add/remove deltas, net deltas, drift, entitlement diff

**Total Lines of Test Code**: ~650 lines
**Total Test Functions**: 12
**Estimated Compile Size**: ~2000 LOC (with inheritance + imports)

---

## Investigation Objectives (Not Vulnerabilities)

These tests aim to answer:

1. **Intermediate Reality Leak**: Are intermediate state snapshots consistent across sequential operations?
2. **Observer Paradox**: Does the order/structure of operations affect price discovery?
3. **Liquidity Idempotence**: Does the delta accounting correctly net add/remove operations?

**Important**: These are **descriptive measurements**, not prescriptive vulnerability claims. All v4 behavior is expected to be correct; we're documenting how delta accounting works.

---

## Relationship to Prior Work

**Phase D (Reality Check - CONCLUDED)**:
- H11 (Donate Poisoning) concluded as NOT A VULNERABILITY
- Settlement enforcement proven via code analysis
- Decision: Do NOT submit H11 to Cantina

**Phase E (Current - NEW DIRECTION)**:
- Shift from "exploit narratives" to "mechanism understanding"
- Pure measurement tests, no attack scenarios
- Document v4's delta accounting precisely
- Establish ground truth for subtle timing/visibility behaviors

---

## Risk Assessment

**API Mismatch Risk**: MEDIUM
- Tests designed with v4 API assumptions
- May need iterations to match actual signatures
- Mitigation: Reference existing passing tests (PoolManager.swap.t.sol, etc.)

**Metric Accuracy Risk**: LOW
- Simple arithmetic (additions, divisions)
- Direct assertion comparisons
- console2.log is auditable

**Compilation Risk**: MEDIUM (currently unfixed)
- 3 compilation errors per file (18 total)
- All related to API signatures or type casting
- Can be fixed with reference to working tests

---

## Deliverables

Upon completion, the following will be provided:

1. ✅ Three fully functional Foundry test suites
2. ✅ Comprehensive test execution output (metrics)
3. ✅ Analysis document: "V4 Delta Accounting Reality" 
4. ✅ Findings summary: Timing/Visibility Behaviors
5. ✅ Integration into v4-core test suite

---

## Notes

- **No vulnerability claims** in these tests
- **Documentation-focused**: Clarify v4's behavior, not find bugs
- **Measurement-driven**: All assertions based on thresholds, not exploits
- **Educational**: Serve as reference for v4 delta accounting patterns
- **Continuation of rigorous methodology** from Phase D reality check

---

**Next Session**: Resolve API issues and execute tests.
