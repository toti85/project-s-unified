# V4_PHASEC_TEST_PLAN_TOP3.md

**Status**: Phase C executable test design (NO PoC code, no exploit)  
**Date**: 2026-01-25  
**Target**: Mainnet fork testing (Foundry) to validate/falsify H11 variants  
**Baseline**: Project-S H11 PoC already proven; Phase C quantifies extent + confirms scope

---

## Overview: Top 3 Hypotheses

| Rank | Hypothesis | Status | Test Type | Difficulty |
|------|-----------|--------|-----------|------------|
| **#1** | **H11: Donate-Based Fee Inflation** | PROVEN | Quantification + Scale | **EASY** |
| **#2** | **H11.1: LP Claim Divergence** | DERIVABLE | Accounting Mismatch | **MEDIUM** |
| **#3** | **H11.2: Fee Growth ≠ Swap Activity** | PROVABLE | Correlation Test | **EASY** |

---

## Hypothesis #1: Donate-Based Fee Inflation (H11)

### Objective
Measure the extent to which `donate()` can inflate `feeGrowthGlobal` relative to actual swap-driven fee activity, and quantify the LP revenue mismatch.

### Setup

**Pool Configuration**:
- Token0/Token1: arbitrary (USDC/USDT acceptable)
- Fee Tier: 3000 bps (0.3%, standard)
- Hook: None (or minimal hook that doesn't interfere with fee accounting)
- Initial State: Empty (liquidity = 0)

**Actors**:
- **Victim LP**: Provides liquidity at full range
- **Swapper**: Executes legitimate swaps (for comparison)
- **Attacker**: Calls donate() with arbitrary amounts

**Initial Conditions**:
1. Deploy pool (feeGrowthGlobal = 0)
2. LP adds 1000 liquidity (full range, price = 1.0)
3. Record: `feeGrowthGlobal0_initial = 0`, `feeGrowthGlobal1_initial = 0`

---

### Action Sequence

#### Phase 1: Baseline (Legitimate Fee Activity)
1. **Scenario A**: Legitimate swap
   - Swapper executes: `swap(poolKey, zeroForOne=true, amountSpecified=100)`
   - Expected: feeGrowthGlobal0 increases by `(100 * 0.3% * Q128) / 1000`
   - Record: `feeGrowthGlobal0_after_swap`, `feesEarned_A`

#### Phase 2: Attack (Donation Inflation)
2. **Scenario B**: Donation without swap
   - Attacker executes: `donate(poolKey, 500, 0)`
   - Expected: feeGrowthGlobal0 increases by `(500 * Q128) / 1000` (no fee multiplication!)
   - Record: `feeGrowthGlobal0_after_donate`, `feesEarned_B`

#### Phase 3: Comparison
3. **Measurement**:
   - `donationAmount = 500`
   - `swapAmountForEquivalentFees = ?` (solve for swap amount that produces same feeGrowth)
   - Ratio: `swapAmountNeeded / donationAmount` (should be >> 1.0 if donate is cheaper)

---

### Measurements

| Metric | Formula | Type | Expected | Failure Condition |
|--------|---------|------|----------|-------------------|
| **feeGrowthGlobal0 delta (swap)** | `feeGrowthGlobal0_after_swap - feeGrowthGlobal0_initial` | Q128 | > 0 | = 0 (core broken) |
| **feeGrowthGlobal0 delta (donate)** | `feeGrowthGlobal0_after_donate - feeGrowthGlobal0_after_swap` | Q128 | > 0 | = 0 (no inflation) |
| **Fee inflation ratio** | `delta_donate / (delta_swap * proportionalCost)` | decimal | >> 1.0 | ≤ 1.0 (safe) |
| **Unearned fee magnitude (wei)** | `donationAmount` (attacker pays) = LP claims | wei | Attacker pays 500, LP gains 500 | LP gains < Attacker pays |
| **Attack cost efficiency** | `donationAmount / equivalentSwapAmount` | ratio | << 1.0 (donate cheaper) | ≥ 1.0 (safe) |
| **Fee growth inflation factor** | `delta_donate / (donationAmount * Q128 / liquidity)` | ratio | ≈ 1.0 (formula applies) | ≠ 1.0 (formula broken) |

---

### Pass / Fail Conditions

**PASS**: H11 is confirmed vulnerable
- ✓ feeGrowthGlobal increases WITHOUT swap activity
- ✓ Donation amount directly proportional to fee inflation (formula verified)
- ✓ Attacker can inflate LP fees at cost << legitimate swap fees

**FAIL**: H11 is false (core is safe)
- ✗ feeGrowthGlobal does NOT increase after donate() (code broken differently)
- ✗ Donation amounts have NO effect on feeGrowthGlobal (unexpected)
- ✗ Core prevents donate() from being called (access control exists)

---

### Test Implementation Notes (No Code)

**Mainnet Fork Setup**:
```
RPC: https://eth.llamarpc.com (or equivalent)
Block: ~24.27M (or current)
Chain: 1 (mainnet)
V4 PoolManager: 0x000000000004444c5dc75cb358380d2e3de08a90
```

**Test Sequence** (pseudocode, not executable):
```
test_H11_DonatePoisoningScale() {
  // 1. Setup
  pool = createPool(token0, token1, 3000, noHook)
  lp = addLiquidity(pool, 1000, 1000)
  
  // 2. Baseline: legitimate swap
  swapResult = swap(pool, 100, zeroForOne=true)
  feeGrowth_swap = pool.feeGrowthGlobal0X128
  
  // 3. Attack: donation
  donate(pool, 500, 0)
  feeGrowth_donate = pool.feeGrowthGlobal0X128
  
  // 4. Assertions
  assert feeGrowth_donate > feeGrowth_swap
  assert (feeGrowth_donate - feeGrowth_swap) == (500 * Q128 / 1000)
  assert lp.feesOwed >= 500  // unearned income
}
```

**Metrics to Log**:
- feeGrowthGlobal0X128 values (before, after swap, after donate)
- LP fee claim calculations (before, after each action)
- Pool balance deltas
- Gas costs (for efficiency comparison)

---

## Hypothesis #2: LP Claim Divergence (H11.1)

### Objective
Measure the gap between LP's claimed fees (derived from feeGrowthGlobal) and the actual economic value they earned.

### Setup

**Pool & Actors** (same as H11):
- Pool: Token0/Token1, 3000 bps, no hook
- LP: Adds 1000 liquidity full range
- Attacker: Calls donate() multiple times

**Initial Conditions**:
1. Pool initialized, LP adds liquidity
2. Record: `lpFeesOwed_initial = 0`, `poolReserves_initial = 2000` (1000 + 1000)

---

### Action Sequence

#### Phase 1: Build Fee Claim via Donation
1. Attacker donates 1000 wei in 10 tranches: donate(100), donate(100), ..., donate(100)
   - Each donation inflates feeGrowthGlobal0 by `(100 * Q128) / 1000`
   - Cumulative: feeGrowthGlobal0 = `(1000 * Q128) / 1000` = `Q128`

#### Phase 2: Measure Fee Claim
2. LP calculates fees owed:
   - `feesOwed = liquidity * feeGrowthGlobal0X128 / Q128`
   - `feesOwed = 1000 * Q128 / Q128 = 1000 wei`
   - LP believes they earned 1000 wei in fees

#### Phase 3: Compare to Reality
3. Pool state:
   - Actual reserves: `initialReserves + donations = 2000 + 1000 = 3000 wei`
   - LP claim: 1000 wei (from fees)
   - Swapper claims (if any): minimal (no swaps executed)
   - Available for LP: 3000 wei total

#### Phase 4: Withdrawal Test (if applicable)
4. If LP tries to withdraw fees:
   - Request: 1000 wei (fees owed)
   - Available: 3000 wei total, but this includes the donation
   - Question: Can LP withdraw more than legitimately earned?

---

### Measurements

| Metric | Formula | Type | Expected | Failure = Safe |
|--------|---------|------|----------|----------------|
| **LP fees claimed (feeGrowthGlobal)** | `liquidity × feeGrowthGlobal0X128 / Q128` | wei | 1000 | = 0 |
| **Pool total reserves** | `token0.balanceOf(pool) + token1.balanceOf(pool)` | wei | 3000+ | < claimed fees |
| **Swapper fees earned** | `actual swap fee input - donation` | wei | ~0 (no swaps) | > 0 (unexpected) |
| **LP claim excess** | `LP fees claimed - actual swap fees` | wei | 1000 (all from donation) | = 0 (safe) |
| **Shortfall if multiple LPs** | `(LP1 fees + LP2 fees) - actual pool reserves` | wei | > 0 (if H11 true) | = 0 (safe) |

---

### Pass / Fail Conditions

**PASS**: H11.1 is confirmed (fee claims diverge from reality)
- ✓ LP fees owed = donation amount (unearned)
- ✓ Pool reserves = legitimate input + unearned donation
- ✓ If multiple LPs claim fees, total claims exceed available reserves

**FAIL**: H11.1 is false (claims match reality)
- ✗ LP fees owed = 0 or much less than donation (core prevents inflation)
- ✗ Pool reserves can cover all LP claims (no shortfall)
- ✗ Donations do NOT appear in LP fee calculations

---

### Test Implementation Notes

**Mainnet Fork Setup**: (same as H11)

**Test Sequence** (pseudocode):
```
test_H11_1_LPClaimDivergence() {
  // 1. Setup
  pool = createPool(...)
  lp = addLiquidity(pool, 1000, 1000)
  initialReserves = pool.reserves()
  
  // 2. Attacker donates
  for i in 1..10:
    donate(pool, 100, 0)
  
  // 3. Measure LP claim
  feeGrowth = pool.feeGrowthGlobal0X128
  lpFeesClaimed = lp.liquidity * feeGrowth / Q128
  
  // 4. Measure pool state
  currentReserves = pool.reserves()
  totalClaimed = lpFeesClaimed  // assuming single LP
  
  // 5. Assertions
  assert lpFeesClaimed == 1000  // unearned from donations
  assert currentReserves == initialReserves + 1000  // reserves include donation
  assert lpFeesClaimed <= currentReserves  // safe (single LP)
}
```

**Metrics to Log**:
- feeGrowthGlobal0X128 after each donation
- LP fees claimed (calculated)
- Pool reserves (token0 + token1)
- Donation cumulative total
- Claim / reserves ratio

---

## Hypothesis #3: Fee Growth Uncorrelated with Swap Activity (H11.2)

### Objective
Prove that `feeGrowthGlobal` can increase independently of swap count, violating the expected correlation.

### Setup

**Pool & Actors** (minimal):
- Pool: Token0/Token1, 3000 bps, no hook
- LP: Adds 1000 liquidity
- Monitor: Track feeGrowthGlobal vs. swap count

**Initial Conditions**:
1. Pool initialized, LP adds liquidity
2. Record: `swapCount = 0`, `feeGrowthGlobal0 = 0`

---

### Action Sequence

#### Scenario 1: Fee Growth via Swaps (Expected)
1. Execute 10 legitimate swaps, each 100 wei
2. Record: `swapCount = 10`, `feeGrowthGlobal0_after_swaps`
3. Expected: feeGrowthGlobal0 increases by swap fee formula

#### Scenario 2: Fee Growth via Donation (Unexpected)
4. Execute 10 donate() calls, each 100 wei
5. Record: `swapCount = 10` (still), `feeGrowthGlobal0_after_donates`
6. Expected (if H11.2 true): feeGrowthGlobal0 increases MORE than swaps (because donation is unvalidated)

#### Scenario 3: Direct Comparison
7. Compare:
   - `feeGrowth_per_swap = feeGrowthGlobal0_after_swaps / swapCount`
   - `feeGrowth_per_donate = feeGrowthGlobal0_after_donates / 10`
   - Ratio: `feeGrowth_per_donate / feeGrowth_per_swap` (should be >> 1 if donations bypass fee logic)

---

### Measurements

| Metric | Formula | Type | Expected | Failure = Safe |
|--------|---------|------|----------|----------------|
| **Fee growth per swap** | `feeGrowthGlobal0_delta / swapCount` | Q128 | X | |
| **Fee growth per donate** | `feeGrowthGlobal0_delta / donateCount` | Q128 | >> X | = X |
| **Swap cost (in fees)** | `swap amount * feeRate` | wei | 3 wei per 1000 | varies |
| **Donate cost (in fees)** | `donate amount * 0` | wei | 0 (no fee logic) | > 0 (safe) |
| **Fee inflation efficiency** | `feeGrowthGlobal_delta / (cost in wei)` | ratio | >> 1 for donate, ~1 for swap | ≤ 1 |
| **Swap vs Donate correlation** | Measure feeGrowthGlobal after each action, track divergence | chart | Divergence visible | Parallel lines |

---

### Pass / Fail Conditions

**PASS**: H11.2 is confirmed (fee growth ≠ swap activity)
- ✓ feeGrowthGlobal increases after donate() without corresponding swap
- ✓ Donation inflation is not proportional to swap count
- ✓ Attacker can achieve same feeGrowthGlobal delta at much lower cost via donation vs. swap

**FAIL**: H11.2 is false (fee growth tied to swaps)
- ✗ feeGrowthGlobal only increases after swaps, not donations
- ✗ Donations have no effect on feeGrowthGlobal (or minimal)
- ✗ Core prevents unvalidated fee inflation

---

### Test Implementation Notes

**Mainnet Fork Setup**: (same as H11)

**Test Sequence** (pseudocode):
```
test_H11_2_FeeGrowthDecoupling() {
  // 1. Setup
  pool = createPool(...)
  lp = addLiquidity(pool, 1000, 1000)
  feeGrowth_initial = 0
  
  // 2. Scenario: Swaps
  for i in 1..10:
    swap(pool, 100, zeroForOne=true)
  feeGrowth_after_swaps = pool.feeGrowthGlobal0X128
  
  // 3. Scenario: Donations (reset pool state if needed)
  pool2 = createPool(...) // or use same pool if state carries
  lp2 = addLiquidity(pool2, 1000, 1000)
  for i in 1..10:
    donate(pool2, 100, 0)
  feeGrowth_after_donates = pool2.feeGrowthGlobal0X128
  
  // 4. Comparison
  feePerSwap = feeGrowth_after_swaps / 10
  feePerDonate = feeGrowth_after_donates / 10
  ratio = feePerDonate / feePerSwap
  
  // 5. Assertions
  assert feeGrowth_after_donates > 0  // donations DO inflate fees
  assert ratio > 1.0  // donations more efficient than swaps
}
```

**Metrics to Log**:
- feeGrowthGlobal0X128 after each swap
- feeGrowthGlobal0X128 after each donation
- Cumulative: swapCount, donateCount
- Fee growth per unit cost (wei/Q128)
- Efficiency ratio

---

## Testing Checklist (Phase C)

### Before Starting

- [ ] Mainnet fork RPC endpoint confirmed (https://eth.llamarpc.com or equivalent)
- [ ] V4 PoolManager contract address verified: `0x000000000004444c5dc75cb358380d2e3de08a90`
- [ ] Contract bytecode confirmed deployed (24009+ bytes)
- [ ] Test wallet has ETH for gas
- [ ] Fork block height >= 24.27M (or choose stable historical block)

### During Testing

- [ ] Test H11 runs without revert
- [ ] Test H11.1 runs without revert
- [ ] Test H11.2 runs without revert
- [ ] All metrics logged (feeGrowth, fees owed, reserves, donations)
- [ ] No unexpected access control errors
- [ ] No unexpected revert reasons

### After Testing

- [ ] Results compared to expected pass/fail conditions
- [ ] If PASS: H11 is confirmed in-scope, ready for submission
- [ ] If FAIL: Core is safe, H11 is a false positive (investigate root cause)
- [ ] All test output captured for report

---

## Success Criteria

### H11 is Actionable If:
1. Test executes without unexpected errors (core works as designed)
2. donate() increases feeGrowthGlobal proportionally to amount (formula confirmed)
3. feeGrowthGlobal increases WITHOUT corresponding swap activity (invariant broken)
4. LP fee claims can exceed legitimate economic value (accounting diverges)

### H11 is Falsified If:
1. donate() is blocked by access control → OOS
2. donate() fails to inflate feeGrowthGlobal → false positive
3. Core has hidden validation preventing arbitrary donations → core is safe
4. Donations are consumed by protocol fees before reaching LPs → fees are safe

---

## Phase C Output Deliverables

1. **Test Results Log** — Raw metrics for H11, H11.1, H11.2
2. **Pass/Fail Verdict** — Whether each hypothesis is confirmed or falsified
3. **Quantified Impact** — Extent of fee inflation, LP claim divergence, cost efficiency
4. **Scope Confirmation** — Whether H11 variants are in-scope under bounty rules
5. **Submission Readiness** — Go/no-go decision for Cantina

---

**Ready for Phase C execution on mainnet fork.**

