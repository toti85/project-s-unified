# V4_DONATE_REALITY_CHECK.md

**Date**: 2026-01-26  
**Objective**: Determine if "donate poisoning" is a real v4-core vulnerability or just intended donation semantics  
**Method**: Mainnet fork test with explicit balance deltas (no mocks)  
**Status**: INVESTIGATION IN PROGRESS

---

## Code Analysis: How v4 Settle Works

### Key Discovery: v4 Uses Unlock Callbacks

**Pattern in PoolManager.sol**:
```solidity
// Line 256: donate() is marked onlyWhenUnlocked
function donate(...) external onlyWhenUnlocked noDelegateCall returns (BalanceDelta delta) {
    // ... compute fee inflation ...
    delta = pool.donate(amount0, amount1);  // Returns (int256 amount0, int256 amount1)
    
    // CRITICAL: Account the delta
    _accountPoolBalanceDelta(key, delta, msg.sender);
    
    // emit event
    // call hook
}
```

**What `onlyWhenUnlocked` means**:
- Function can ONLY be called from within an `unlock()` callback
- This is NOT a normal external call
- Caller must have established an active lock via `unlock()`

**Settlement Requirement**:
- When `unlock()` exits, v4 checks that all currency deltas = 0
- If attacker has outstanding delta (owed 500 USDC but didn't settle), unlock fails
- **This means: donate() CANNOT be called without settling**

### Implications for "Donate Poisoning"

If `donate()` requires settlement, then:
- ✅ Attacker MUST provide the tokens
- ✅ Pool gets the tokens
- ✅ LPs receive those tokens as fees (redistributed)
- ❌ This is NOT "value from nothing"
- ❌ This is just "donation with fee redistribution"

### The Real Question Now

**Is there a way to call `donate()` WITHOUT settling the delta?**

If YES → Vulnerability (value from nothing)
If NO → Not a vulnerability (just donation)

**Answer**: The `onlyWhenUnlocked` modifier enforces settlement at unlock exit.

---

## Revised Blockers Assessment

### Blocker A: Is Value Created from Nothing? 
**CODE EVIDENCE**: `onlyWhenUnlocked` + `_accountPoolBalanceDelta()`

**Analysis**:
- `donate()` is guarded by `onlyWhenUnlocked`
- Caller must have active lock (from `unlock()` call)
- At unlock exit, v4 requires net delta ≈ 0
- If caller has +500 USDC delta, they must transfer tokens
- If they don't, `unlock()` exit fails

**Preliminary Verdict**: ✅ Settlement IS enforced

---

### Blocker B: Extract from Other Users?
**Question**: Does `donate()` cause other LPs to lose funds?

**Analysis**:
- `donate()` inflates `feeGrowthGlobal` uniformly
- ALL LPs gain fees proportional to their liquidity
- No LP loses funds directly
- The only way LPs "lose" is if:
  1. They had earned fees before the donation
  2. Donation causes LP's share % to change
  3. But this is just redistribution, not theft

**Preliminary Verdict**: ❌ No extraction (just redistribution)

---

### Blocker C: Grief/DoS Without Hooks?
**Question**: Can repeated `donate()` cause swaps/burns to revert?

**Analysis**:
- `feeGrowthGlobal` is Q128 (huge range)
- Even 1000x donations unlikely to overflow
- Swaps and burns don't directly depend on whether donation happened
- Worst case: feeGrowth gets large, but division still works

**Preliminary Verdict**: ❌ No DoS vector identified

---

### Blocker D: Scope Alignment
**CODE PATHS**:
- PoolManager.sol:256-280 — v4-core/src ✅
- Pool.sol:donate() — v4-core/src ✅
- Both in-scope

**Preliminary Verdict**: ✅ In-scope code

---

## UPDATED HYPOTHESIS

### Before: "Donate Poisoning is a Vulnerability"
**Assumption**: Attacker calls `donate()` without paying, LPs get free fees.

### Reality Check:
**Finding**: `donate()` requires token settlement at `unlock()` exit.

### After: "Donate is Intended Behavior"
**Conclusion**: `donate()` is a feature, not a bug. Anyone can donate to LPs.

This means:
- 🟢 Donation happens as intended
- 🟢 LPs get the donated funds (proportional to liquidity)
- 🟢 No value created from nothing
- 🟢 No extraction from other users
- 🟢 No DoS/grief vector
- 🔴 **NOT A VULNERABILITY** (assuming settlement enforcement is real)

### Next Step: Verify Settlement Enforcement
Need to measure on mainnet fork:
1. Can `donate()` be called without settling?
2. Does `unlock()` actually enforce net-zero settlement?
3. What happens if attacker tries to exit with unpaid delta?



### Blocker A: Is Value Created from Nothing?

**Testable Claim**: `donate(X)` increases LP fees by X without attacker paying X

**How to Verify**:
```
BEFORE:
  attacker.balance[token0] = B_attacker
  pool.reserves[token0] = R_pool
  pool.feeGrowthGlobal0 = F_before

CALL:
  PoolManager.donate(key, 500 ether, 0)
  
AFTER:
  attacker.balance[token0] = B_attacker' 
  pool.reserves[token0] = R_pool'
  pool.feeGrowthGlobal0 = F_after

VERDICT:
  If B_attacker' == B_attacker (no change) AND R_pool' > R_pool:
    → VULNERABILITY (attacker didn't pay, pool got richer, LPs got fees)
  
  If B_attacker' == B_attacker - 500 AND R_pool' == R_pool + 500:
    → NOT A VULNERABILITY (attacker paid, LPs received donation)
```

**Status**: ⏳ PENDING (needs mainnet fork test)

---

### Blocker B: Extract from Other Users?

**Testable Claim**: An attacker can use `donate()` to steal/divert funds from existing LPs

**Scenario**:
```
Setup:
  LP1 owns 1000 liquidity
  Attacker calls donate(500)
  
Question:
  Does LP1's token balance DECREASE due to the donation?
  Or does LP1 only see LP fees increase (their own gain)?
  
If LP1's tokens decrease → VULN (theft from LP1)
If LP1's tokens only increase (LP fees) → NOT A VULN (just redistribution)
```

**Status**: ⏳ PENDING (needs scenario test)

---

### Blocker C: Grief/DoS Without Hooks?

**Testable Claims**:
1. Repeated `donate()` calls cause swaps to revert
2. Repeated `donate()` causes fee collection to underflow/overflow
3. `donate()` creates accounting inconsistency that breaks downstream operations

**How to Verify**:
```
Setup:
  Create pool, add LP, execute swap (baseline)
  
Attack:
  Call donate() 100 times
  
Question:
  Does the next swap revert?
  Does LP fee claim revert?
  Does accounting overflow/underflow?
  
If any reverts → POTENTIAL VULN (DoS)
If none revert but operations work → NOT A VULN (just cosmetic fee inflation)
```

**Status**: ⏳ PENDING (needs stress test)

---

### Blocker D: Scope Alignment

**Files to Check**:
- ✅ `src/PoolManager.sol` (v4-core/src) — IN-SCOPE
- ✅ `src/libraries/Pool.sol` (v4-core/src) — IN-SCOPE
- ❌ `src/test/PoolDonateTest.sol` (test helpers) — OUT-OF-SCOPE
- ❌ Third-party hooks — OUT-OF-SCOPE
- ❌ Periphery contracts — OUT-OF-SCOPE

**Status**: ✅ CONFIRMED (issue is in v4-core/src)

---

## What We Know So Far (From Documentation)

### From HYPOTHESIS_11_PoC_SUMMARY.md:
- Attacker calls `donate(500 ether)`
- `feeGrowthGlobal0` increases by ~172e30 (Q128 value)
- LP sees fee claim increase by ~500 ether
- **Claimed transfer**: "Attacker (paid 500) → LP (gained 500)"

### From SUBMISSION_DRAFT.md:
- "Attacker can call donate() to make LPs claim unearned fees"
- "Attack is 333x cheaper than legitimate swaps"
- Severity rated: CRITICAL

### Key Assumption (UNVERIFIED):
- The phrase "Attacker paid 500" assumes attacker SETTLED the delta
- But we haven't verified: does `donate()` actually require token settlement?

---

## What We Need to Verify on Mainnet Fork

### Test 1: Token Settlement Check

**Code Pattern in v4**:
```solidity
// Most v4 functions follow this pattern:
function doSomething(...) external {
  // 1. Update internal state (accounting)
  // 2. Return delta (change to balances owed)
}

// Caller must then settle the delta by transferring tokens
// This happens in a separate call: manager.settle(...)
```

**Question**: Does `donate()` REQUIRE the attacker to call `settle()`?

**Test**:
```solidity
function test_DonateSettlementRequirement() public {
  // Try to call donate() without settling
  
  uint256 donateAmount = 100 ether;
  
  // Setup: Attacker has tokens but hasn't approved
  token0.mint(attacker, donateAmount);
  
  // Call donate WITHOUT settle
  vm.prank(attacker);
  (int256 delta0, int256 delta1) = PoolManager.donate(key, donateAmount, 0);
  
  // Assertions:
  // Did pool.feeGrowthGlobal increase? (likely YES)
  // Did attacker's token balance decrease? (likely NO)
  // Did pool's token reserve increase? (likely NO)
  
  // If all three conditions: NOT SETTLED → VULNERABILITY
  // If pool's reserve increased: SETTLED → NOT A VULNERABILITY
}
```

### Test 2: Balance Delta Verification

**Setup**:
- Create pool (USDC/USDT, 3000 bps)
- LP adds 1000 liquidity
- Attacker has 500 USDC

**Test**:
```solidity
function test_DonateBalanceDeltas() public {
  uint256 donateAmount = 100 ether;
  
  // BEFORE
  uint256 attacker_balance_before = token0.balanceOf(attacker);
  uint256 pool_balance_before = token0.balanceOf(address(manager));
  (uint256 feeGrowth0Before, , , ) = manager.pools(key);
  
  // EXECUTE
  vm.prank(attacker);
  PoolManager.donate(key, donateAmount, 0);
  
  // AFTER
  uint256 attacker_balance_after = token0.balanceOf(attacker);
  uint256 pool_balance_after = token0.balanceOf(address(manager));
  (uint256 feeGrowth0After, , , ) = manager.pools(key);
  
  // ASSERTIONS
  uint256 attacker_delta = attacker_balance_before - attacker_balance_after;
  uint256 pool_delta = pool_balance_after - pool_balance_before;
  uint256 feeGrowth_delta = feeGrowth0After - feeGrowth0Before;
  
  console2.log("Attacker balance change:", attacker_delta);
  console2.log("Pool balance change:", pool_delta);
  console2.log("feeGrowth delta:", feeGrowth_delta);
  
  // DECISION TREE
  if (attacker_delta == 0 && pool_delta == 0 && feeGrowth_delta > 0) {
    console2.log("VERDICT: Value created from NOTHING (VULNERABILITY)");
  } else if (attacker_delta == donateAmount && pool_delta == donateAmount) {
    console2.log("VERDICT: Attacker paid, pool received (NOT A VULN)");
  } else {
    console2.log("VERDICT: UNCLEAR");
  }
}
```

---

## Current Status: HYPOTHESIS vs REALITY

| Claim | Status | Evidence |
|-------|--------|----------|
| `donate()` inflates `feeGrowthGlobal` | ✅ CONFIRMED (code) | Pool.sol:466-481 |
| LPs see fee claim increase | ✅ CONFIRMED (code) | Position.fees = liquidity × feeGrowth |
| Attacker "pays" tokens | ❓ UNVERIFIED | Assumption only |
| Value created from nothing | ❓ UNVERIFIED | Needs mainnet fork test |
| This is a v4-core vulnerability | ❓ UNVERIFIED | Depends on ↑ |

---

## Expected Outcomes & Verdicts

### Scenario 1: Value Created from Nothing
```
Attacker balance: unchanged
Pool balance: +500 ether
feeGrowth: +huge amount
LPs: +500 ether claimed

VERDICT: IN-SCOPE VULNERABILITY
Reason: Attacker didn't pay, but LPs gained real value (pool got richer without swap activity)
```

### Scenario 2: Attacker Paid (Settled)
```
Attacker balance: -500 ether
Pool balance: +500 ether
feeGrowth: +huge amount
LPs: +500 ether claimed

VERDICT: NOT A VULNERABILITY
Reason: Attacker paid 500, LPs got 500. This is just "donation". v4 intended this.
```

### Scenario 3: Attacker Paid But LPs Lost
```
Attacker balance: -500 ether
Pool balance: +500 ether
LP1 token balance: -X ether (where X > 0)
LPs overall: lose more than donation

VERDICT: IN-SCOPE VULNERABILITY
Reason: Donation causes redistribution that hurts some LPs
```

---

## Next Steps

1. **Create mainnet fork test** with explicit balance assertions
2. **Run test** against deployed PoolManager (0x000000000004444c5dc75cb358380d2e3de08a90)
3. **Measure deltas** for all 4 blockers
4. **Generate verdict** based on measurements
5. **Update SUBMISSION_DRAFT.md** if and only if vulnerability is PROVEN

---

## Files Referenced

- `H11_PHASE_C_EXECUTION_RESULTS.md` — Previous analysis
- `SUBMISSION_DRAFT.md` — Current submission draft (may need update)
- `HYPOTHESIS_11_PoC_SUMMARY.md` — Original PoC summary
- `v4-core/src/PoolManager.sol` — Entry point
- `v4-core/src/libraries/Pool.sol` — Fee inflation logic

---

**Status**: Ready for mainnet fork execution

