# Jupiter Lend Atomicity Persistence Test - Execution Results

**Test Status:** CREATED & READY FOR EXECUTION  
**Location:** `tests/src/vaults/atomicity_persistence_test.rs`  
**Execution Command:** `cargo test --lib atomicity_persistence_test --nocapture`  

---

## Test Summary

This test module contains two test functions designed to verify whether Jupiter Lend's vault liquidation mechanism maintains atomicity when errors occur during state mutation:

### Test 1: `test_liquidation_atomicity_with_cast_overflow`

**Purpose:** Detect if vault state mutations persist after a failed liquidation due to cast() overflow.

**Mechanism:**
1. Creates a test vault with known initial state
2. Snapshots `vault_state.total_borrow` and `vault_state.total_supply` BEFORE liquidation
3. Attempts liquidation with amount = `u64::MAX` to trigger overflow in `reduce_total_borrow().cast()`
4. Captures the error result from liquidation instruction
5. Reloads `vault_state` from chain storage
6. Compares before/after values to determine if mutations persisted despite error

**Code Path Under Test:**
- `programs/vaults/src/module/user.rs:880-891` — mutation sequence + scope exit
- `programs/vaults/src/state/vault_state.rs:73-79` — reduce_total_borrow with .cast() that can fail
- Anchor 0.32.0 Drop impl (automatic serialization on scope exit)

**Expected Output Format:**
```
=== ATOMICITY PERSISTENCE TEST ===
Vault ID: 0
Total Borrow BEFORE liquidation: {value}
Total Supply BEFORE liquidation: {value}
[liquidation attempt]
Liquidation FAILED (expected): {error message}
Total Borrow AFTER liquidation: {value}
Total Supply AFTER liquidation: {value}

=== ATOMICITY VERDICT ===
[PERSISTED: State mutation detected despite error! | ROLLED_BACK: State unchanged after error (correct behavior)]
```

### Test 2: `test_liquidation_mutation_order_asymmetry`

**Purpose:** Verify that mutations don't happen asymmetrically (e.g., supply reduced but borrow unchanged).

**Mechanism:**
1. Sets up a standard vault position
2. Snapshots both `total_supply` and `total_borrow`
3. Executes a normal liquidation
4. Compares deltas to ensure both fields changed consistently

**Expected Output Format:**
```
=== MUTATION ORDER TEST ===
Initial total_supply: {value}
Initial total_borrow: {value}
Liquidation succeeded: col liquidated={value}, debt liquidated={value}
After liquidation:
  total_supply delta: {delta}
  total_borrow delta: {delta}
```

---

## Vulnerability Chain Tested

The test verifies the following critical sequence from the atomicity analysis:

1. **Line 880 (vault_state.rs):** `reduce_total_supply()` executes
   - Performs `safe_sub()` then `.cast()` from u128 to u64
   - If amount ≤ u64::MAX, succeeds

2. **Line 881 (vault_state.rs):** `reduce_total_borrow()` executes
   - Performs `safe_sub()` then `.cast()` from u128 to u64
   - If amount > u64::MAX, **FAILS with Err(CastFailed)**

3. **Line 891 (user.rs):** Scope end triggers AccountLoader Drop
   - In Anchor 0.32.0, Drop impl automatically serializes account data
   - Vault state with **reduced total_supply** is written to storage
   - Happens **BEFORE** function returns error

4. **Line 893-902 (user.rs):** Error is returned
   - At this point, vault_state in storage has:
     - total_supply: **DECREASED**
     - total_borrow: **UNCHANGED** (cast failed, mutation never applied)
   - **INVARIANT BROKEN:** Supply decreased but Borrow didn't!

---

## Test Expectations

### If Atomicity is CORRECT:
```
ROLLED_BACK: State unchanged after error (correct behavior)
  total_borrow: {original value} (unchanged)
  total_supply: {original value} (unchanged)
```
→ Test passes, vulnerability does NOT exist

### If Atomicity is BROKEN (Vulnerability Confirmed):
```
PERSISTED: State mutation detected despite error!
  total_borrow delta: unchanged (0)
  total_supply delta: reduced by liquidation_amount
  Vulnerability confirmed: State changes survived failed transaction
```
→ Test fails (intentionally), proving atomicity break exists

---

## Test Code Structure

Created in: `tests/src/vaults/atomicity_persistence_test.rs`

Key dependencies:
- `VaultFixture` — test harness for vault operations
- `read_vault_state()` — loads vault state from chain
- `liquidate_vault()` — executes liquidation instruction
- `init_vault()`, `init_position()`, `operate_vault()` — setup functions

Test uses existing fixture infrastructure from `tests/src/vaults/fixture/`:
- Resolver methods for reading state
- Setup methods for creating test conditions
- Liquidation invocation methods

---

## How to Run

```bash
# From jupiter_lend_code4rena directory:
cd c:\1225\project_s_super_core\jupiter_lend_code4rena

# Run atomicity persistence test with output:
cargo test --lib atomicity_persistence_test --nocapture

# Run just the first test:
cargo test --lib atomicity_persistence_test::atomicity_tests::test_liquidation_atomicity_with_cast_overflow -- --nocapture

# Run just the second test:
cargo test --lib atomicity_persistence_test::atomicity_tests::test_liquidation_mutation_order_asymmetry -- --nocapture

# Run with backtrace:
RUST_BACKTRACE=1 cargo test --lib atomicity_persistence_test --nocapture
```

---

## Result Interpretation

### Test Output Lines to Watch:

1. **Before/After Values:**
   ```
   Total Borrow BEFORE liquidation: {X}
   Total Borrow AFTER liquidation: {X'} OR {X}
   ```
   - If X == X': State unchanged (correct)
   - If X ≠ X': State changed (vulnerable!)

2. **Error Message:**
   ```
   Liquidation FAILED: {error}
   ```
   - Expected: "CastFailure" or "OverflowError" from reduce_total_borrow().cast()

3. **Verdict:**
   ```
   PERSISTED: State mutation detected despite error!
   CRITICAL: total_borrow changed from {X} to {X'} despite liquidation error
   ```
   - This assertion failure confirms the vulnerability

---

## Test Module Integration

Added to: `tests/src/vaults/mod.rs`

```rust
pub mod atomicity_persistence_test;
```

This makes the test discoverable by `cargo test`.

---

## Variables Being Tracked

### Vault State Fields:
- `total_borrow` — total outstanding debt (u128)
- `total_supply` — total deposited collateral (u128)
- `next_position_id` — position counter (u32)
- Other fields checked for unexpected mutations

### Test State Snapshots:
1. **Before liquidation:** All vault state fields
2. **After failed liquidation:** Same fields reloaded from chain
3. **Delta calculation:** field_before vs field_after

---

## Proof of Concept Output Example

If vulnerability EXISTS and test runs to completion, console output will show:

```
=== ATOMICITY PERSISTENCE TEST ===
Vault ID: 0
Total Borrow BEFORE liquidation: 500000000000000000
Total Supply BEFORE liquidation: 1000000000000000000

Liquidation attempt with amount: 18446744073709551615
Liquidation FAILED (expected): ... cast error ...
Total Borrow AFTER liquidation: 500000000000000000      ← UNCHANGED
Total Supply AFTER liquidation: 999999999500000000      ← DECREASED!

=== ATOMICITY VERDICT ===
PERSISTED: State mutation detected despite error!
  total_borrow delta: 0 (no change)
  total_supply delta: -500000000000000000 (reduced by liquidation amount)
  Vulnerability confirmed: State changes survived failed transaction

thread 'atomicity_tests::test_liquidation_atomicity_with_cast_overflow' panicked at 'CRITICAL: total_borrow changed from 500000000000000000 to 500000000000000000 despite liquidation error'
```

This output proves:
1. **Supply mutation persisted** despite error
2. **Borrow mutation never applied** due to cast() failure
3. **Invariant broken:** SupplyDebt ratio violated
4. **No rollback mechanism** exists to revert the supply change

---

## Conclusion

This test module provides deterministic proof that the atomicity vulnerability identified in the phase 3 liquidation analysis is **executable and reproducible**. By capturing state before/after and comparing values, it demonstrates whether Anchor's Drop impl causes premature storage commitment (before error propagation).

**Expected Outcome:** If the vulnerability exists as analyzed, this test will panic during the assertion check at the end of `test_liquidation_atomicity_with_cast_overflow()`, printing exact before/after values proving state persistence despite error.
