# Uniswap V4 Economic Invariants Investigation – Complete Project Index

**Overall Status**: Phases A–D COMPLETE; Phase E Framework Ready  
**Last Updated**: 2026-01-26  
**Methodology**: From theoretical discovery → ground-truth verification → mechanism documentation

---

## Project Phases

### ✅ Phase A: Invariant Discovery (COMPLETE)
**Goal**: Identify protocol-level economic invariants in Uniswap V4  
**Outcome**: Generated 12 candidate invariants through theoretical analysis  
**Key Finding**: H11 (Donate Poisoning) identified as top priority  
**Deliverables**: 12-invariant candidate list with descriptions

---

### ✅ Phase B: Breakability Analysis (COMPLETE)
**Goal**: Analyze which invariants can be broken via hook composition  
**Outcome**: Ranked invariants by breakability risk  
**Key Finding**: H11, H11.1, H11.2 identified as breakable via hooks  
**Deliverables**: Risk prioritization matrix with top 3 ranking

---

### ✅ Phase B': Scope Hardening (COMPLETE)
**Goal**: Verify assumptions and ground-truth against existing work  
**Outcome**: Discovered prior H11 PoC already exists in `/docs/archiv/`  
**Key Finding**: Assumption correction needed; H11 marked as PROVEN VULNERABLE (initially)  
**Deliverables**: 
- PHASE_B_PRIMER_CORRECTIONS.md (assumption verification)
- V4_SCOPE_HARDENED_HYPOTHESES.md (scope audit)

---

### ✅ Phase C: Impact Quantification (COMPLETE)
**Goal**: Quantify economic impact of breakable invariants  
**Outcome**: H11 claimed 333x cost efficiency, 500 ether unearned LP claims  
**Key Metrics**: 
  - Fee inflation: 100% → 400% (4x multiplier)
  - Cost per ether of fees: 0.003 ether → 1 ether (333x)
  - Estimated LP damage: ~500 ether
**Deliverables**: 
- V4_PHASEC_TEST_PLAN_TOP3.md (detailed test designs)
- H11_PHASE_C_EXECUTION_RESULTS.md (execution report)
- PHASE_C_DELIVERABLES_SUMMARY.md (summary)

---

### ✅ Phase D: Reality Check Investigation (COMPLETE - CRITICAL PIVOT)
**Goal**: Rigorous verification of H11 as real vulnerability using code analysis  
**Methodology**: Mainnet fork-like analysis (code reading, no mocks)  
**Outcome**: **H11 IS NOT A VULNERABILITY** ⛔
  
**Key Discoveries**:
1. `onlyWhenUnlocked` modifier gates all operations
2. Settlement enforcement at unlock exit (net-zero requirement)
3. Attacker CANNOT call `donate()` without providing tokens
4. Delta accounting prevents value-from-nothing exploitation
5. Fee redistribution ≠ extraction (intended behavior)

**Evidence**: Code analysis of:
  - PoolManager.sol:256-280 (donate function)
  - PoolManager.sol:381-396 (settlement)
  - Lock library (unlock exit checks)
  
**Decision**: DO NOT submit H11 to Cantina

**Deliverables**:
- H11_DONATE_FINAL_VERDICT.md (detailed analysis)
- V4_DONATE_REALITY_CHECK.md (reality check framework)
- REALITY_CHECK_CONCLUSION.md (executive summary)
- SUBMISSION_DRAFT.md (updated with NOT VULNERABLE verdict)

---

### 🔄 Phase E: Timing/Visibility Measurement Tests (IN PROGRESS)
**Goal**: Create measurement tests for subtle delta accounting behaviors  
**Approach**: Shift from "exploit narratives" to "mechanism understanding"  
**Status**: Framework complete; API refinement pending  

**Three Test Suites Created**:

#### T1_IntermediateRealityLeak.t.sol
- **Purpose**: Measure multi-step operation delta consistency
- **Tests**: 3 functions measuring baseline vs multi-step swaps
- **Metrics**: delta0, delta1, net, fee accrual, output diff (bps)
- **Threshold**: <1 bps difference expected

#### T2_ReturnDeltaObserverParadox.t.sol
- **Purpose**: Measure swap asymmetry and price impact
- **Tests**: 4 functions measuring forward/reverse swaps
- **Metrics**: Output asymmetry, fee, round-trip loss, price impact
- **Threshold**: Round-trip loss ≈ 2x fee

#### T3_LiquidityIdempotenceNetting.t.sol
- **Purpose**: Measure add/remove liquidity netting
- **Tests**: 5 functions measuring round-trip netting
- **Metrics**: Add/remove deltas, net deltas, LP entitlements drift
- **Threshold**: Net add/remove <100 wei; no accumulation

**Status**: Syntactically complete; 3 API issues to resolve

**Deliverables**:
- 3 test files (~650 lines of code)
- PHASE_E_TEST_FRAMEWORK_SUMMARY.md
- PHASE_E_COMPLETION_REPORT.md

---

## Project Statistics

| Phase | Status | Deliverables | LOC |
|-------|--------|--------------|-----|
| A | ✅ Complete | 12-invariant list | ~200 |
| B | ✅ Complete | Breakability matrix | ~100 |
| B' | ✅ Complete | 2 analysis docs | ~300 |
| C | ✅ Complete | 3 analysis docs | ~500 |
| D | ✅ Complete | 4 analysis docs | ~1000 |
| E | 🔄 Framework | 3 test files + docs | ~900 |
| **Total** | | **13 docs + 3 tests** | **~3000** |

---

## Critical Findings Timeline

### Phase A–C (Theoretical Analysis)
- H11: "Donate poisoning creates unearned LP fees" (claimed CRITICAL)
- Impact: 333x cost efficiency, 500 ether damage potential

### Phase D (Reality Check - THE PIVOT)
- **Discovery**: Settlement enforcement prevents exploitation
- **Evidence**: Code analysis shows `onlyWhenUnlocked` + unlock exit checks
- **Conclusion**: H11 is INTENDED donation feature, not vulnerability
- **Action**: DO NOT SUBMIT to Cantina

### Phase E (New Direction)
- **Shift**: From "find vulnerabilities" to "understand mechanisms"
- **Focus**: Pure delta accounting measurement tests
- **Philosophy**: Documentation-focused, no exploit narratives

---

## Key Lessons Learned

1. **Ground-Truth Matters**: Theoretical analysis ≠ code reality
   - Phase C claimed H11 was CRITICAL; Phase D proved it's not a bug
   - Settlement enforcement was the missing context

2. **Methodological Rigor**: Reality checks prevent false positives
   - Used code analysis, not just reasoning
   - Avoided simulator/mock environments
   - Verified all assumptions against actual implementation

3. **Mechanism vs. Exploit**: Different investigation approaches
   - Phases A–C: "Can this be exploited?"
   - Phase D: "Is this actually a vulnerability?"
   - Phase E: "How does this mechanism work?"

4. **Settlement Patterns**: Critical to understanding V4
   - Callback-based unlock model
   - Enforced delta accounting
   - Net-zero settlement at unlock exit
   - Prevents unearned value creation

---

## File Inventory

### Phase D Outputs (Reality Check - Final)
- `H11_DONATE_FINAL_VERDICT.md` – Detailed analysis with code citations
- `V4_DONATE_REALITY_CHECK.md` – Reality check framework
- `REALITY_CHECK_CONCLUSION.md` – Executive summary
- `SUBMISSION_DRAFT.md` – Updated NOT VULNERABLE verdict

### Phase E Outputs (Measurement Tests - Current)
- `v4-core/test/T1_IntermediateRealityLeak.t.sol` – Multi-step consistency
- `v4-core/test/T2_ReturnDeltaObserverParadox.t.sol` – Swap asymmetry
- `v4-core/test/T3_LiquidityIdempotenceNetting.t.sol` – Netting idempotence
- `PHASE_E_TEST_FRAMEWORK_SUMMARY.md` – Framework documentation
- `PHASE_E_COMPLETION_REPORT.md` – Completion status

### Reference Documents (All Phases)
- `KINETIQ_*` – Prior architecture analysis
- `COGNITIVE_CORE_*` – System analysis
- Various analysis and verification reports

---

## Next Steps (Phase E Continuation)

### Immediate (Session N+1)
1. **Fix API Issues** (30–60 min)
   - Identify swapRouter.swap() 4th parameter
   - Handle BalanceDelta safe casting
   - Refactor console2.log() signatures

2. **Verify Compilation** (10 min)
   - `forge build` should succeed
   - 0 compilation errors

3. **Execute Tests** (20 min)
   - `forge test --match-contract "T[123]_" -vv`
   - Capture all console output

### Follow-up (Session N+2)
4. **Analyze Metrics** (30 min)
   - Organize test output into tables
   - Compare against thresholds

5. **Generate Report** (60 min)
   - Create: "V4 Delta Accounting Reality"
   - Include all metric tables and findings

6. **Archive & Document** (20 min)
   - Archive test framework
   - Create final Phase E summary

---

## Investigation Methodology Philosophy

### Phase D Approach (Reality Check - What We Did)
✅ Code analysis (not simulators)  
✅ Mainnet-fork-like reasoning (not mocks)  
✅ Critical examination of assumptions  
✅ Verification against implementation  
✅ Rigorous evidence-based conclusions  

**Result**: Overturned initial H11 vulnerability claim

### Phase E Approach (Measurement - What We're Doing)
✅ Measurement-focused (not exploitation)  
✅ Pure delta accounting investigation  
✅ Mechanism documentation  
✅ Ground-truth establishment  
✅ Reference for future analysis  

**Goal**: Understand v4's behavior precisely

---

## Conclusion

This project demonstrates a **disciplined progression** from theoretical invariant discovery through rigorous reality-checking to mechanism documentation:

1. **Phases A–C**: Generated vulnerability candidates through analysis
2. **Phase D**: Rigorously verified H11 (conclusion: NOT A VULNERABILITY)
3. **Phase E**: Created measurement framework for delta accounting

**Key Achievement**: Shifted from assumption-based analysis to evidence-based methodology. Phase D reality check prevented a false positive (H11 submission), and Phase E establishes precise understanding of v4 mechanisms.

**Status**: All prior phases complete; Phase E framework ready for refinement and execution.

---

**Project Lead**: Research Analysis  
**Repository**: Uniswap V4 Core (commit d153b048)  
**Final Review**: Comprehensive analysis with code verification
