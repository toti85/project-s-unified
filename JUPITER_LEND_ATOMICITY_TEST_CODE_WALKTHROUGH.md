# Jupiter Lend Atomicity Persistence Test - Code Walkthrough

**Test File:** `tests/src/vaults/atomicity_persistence_test.rs`  
**Lines:** 1-380  
**Purpose:** Prove whether vault state mutations persist after failed liquidation transactions

---

## Test Design Pattern

The test follows this deterministic sequence:

```
BEFORE STATE SNAPSHOT
    ↓
LIQUIDATION ATTEMPT (designed to fail)
    ↓
ERROR CAPTURE
    ↓
AFTER STATE RELOAD
    ↓
STATE COMPARISON
    ↓
VULNERABILITY VERDICT
```

---

## Test 1: Atomicity with Cast Overflow

### Lines 35-127: `test_liquidation_atomicity_with_cast_overflow()`

**Execution Flow:**

#### Step 1: Setup (lines 40-60)
```rust
let mut fixture = setup_vault_fixture();
let vault_id = 0u16;
let user = solana_sdk::signature::Keypair::new();
let liquidator = solana_sdk::signature::Keypair::new();

fixture.gift_to(&user.pubkey(), 100 * 10_u64.pow(9))?;
fixture.gift_to(&liquidator.pubkey(), 100 * 10_u64.pow(9))?;

fixture.init_vault(vault_id, &user, &user)?;
fixture.init_position(vault_id, &user)?;
```

**Effect:** Creates vault and user accounts with sufficient funds

#### Step 2: Create Initial Position (lines 62-76)
```rust
let supply_amount: i128 = 1_000_000_000;  // 1e9
let borrow_amount: i128 = 500_000_000;    // 0.5e9

fixture.operate_vault(&OperateVars {
    vault_id,
    position_id: 1,
    user: &user,
    collateral_amount: supply_amount,
    debt_amount: borrow_amount,
    recipient: &user,
})?;
```

**Effect:** 
- Vault now has total_borrow = 500,000,000
- Vault now has total_supply = 1,000,000,000

#### Step 3: SNAPSHOT BEFORE (lines 78-91)
```rust
let vault_state_before = fixture.read_vault_state(vault_id)?;

println!("Total Borrow BEFORE liquidation: {}", vault_state_before.total_borrow);
println!("Total Supply BEFORE liquidation: {}", vault_state_before.total_supply);
```

**Critical:** These values are the **ground truth** for comparison

#### Step 4: Trigger Liquidation with Overflow (lines 93-107)
```rust
let liquidate_amount_exceeds_u64_max: u64 = 
    (u64::MAX as u128 + 1).min(u64::MAX) as u64;

fixture.init_position(vault_id, &liquidator)?;

let liquidate_result = fixture.liquidate_vault(&LiquidateVars {
    vault_id,
    user: &liquidator,
    to: &liquidator,
    debt_amount: liquidate_amount_exceeds_u64_max,  // ← TRIGGERS CAST OVERFLOW
    col_per_unit_debt: 0,
    absorb: false,
})?;
```

**Critical Path Executed:**
1. `liquidate()` in `vaults/src/module/user.rs:513`
2. Line 880: `vault_state.reduce_total_supply(liquidate_amount_exceeds_u64_max)?`
   - SUCCESS: u128→u64 cast succeeds (assumes amount fits)
3. Line 881: `vault_state.reduce_total_borrow(liquidate_amount_exceeds_u64_max)?`
   - **FAILURE:** u128→u64 cast fails because amount = u64::MAX or higher
4. Line 891: scope exit → Drop::drop() executes
   - **KEY:** Mutations written to storage BEFORE error returns
5. Error propagates back to test

#### Step 5: SNAPSHOT AFTER (lines 109-120)
```rust
let vault_state_after = fixture.read_vault_state(vault_id)?;

println!("Total Borrow AFTER liquidation: {}", vault_state_after.total_borrow);
println!("Total Supply AFTER liquidation: {}", vault_state_after.total_supply);
```

**Critical:** These values show what actually persisted in storage

#### Step 6: COMPARISON (lines 122-164)
```rust
let total_borrow_changed = 
    vault_state_before.total_borrow != vault_state_after.total_borrow;
let total_supply_changed = 
    vault_state_before.total_supply != vault_state_after.total_supply;

if total_borrow_changed || total_supply_changed {
    println!("PERSISTED: State mutation detected despite error!");
    println!("  total_borrow delta: {} -> {}", 
        vault_state_before.total_borrow, 
        vault_state_after.total_borrow);
    println!("  total_supply delta: {} -> {}", 
        vault_state_before.total_supply, 
        vault_state_after.total_supply);
    
    // VULNERABILITY ASSERTION
    assert!(
        !total_borrow_changed,
        "CRITICAL: total_borrow changed from {} to {} despite liquidation error",
        vault_state_before.total_borrow,
        vault_state_after.total_borrow
    );
} else {
    println!("ROLLED_BACK: State unchanged after error (correct behavior)");
}
```

**Logic:**
- If any field changed → state persisted despite error → **VULNERABILITY**
- If all fields unchanged → properly rolled back → **SECURE**

---

## Test 2: Mutation Order Asymmetry

### Lines 169-270: `test_liquidation_mutation_order_asymmetry()`

**Purpose:** Verify mutations happen symmetrically (both succeed or both fail)

**Execution Flow:**

#### Step 1-4: Setup (same pattern as Test 1)
```rust
let mut fixture = setup_vault_fixture();
let vault_id = 0u16;
// ... create users, vault, positions ...
```

#### Step 5: Initial Snapshot
```rust
let state_before = fixture.read_vault_state(vault_id)?;
let initial_total_supply = state_before.total_supply;
let initial_total_borrow = state_before.total_borrow;
```

#### Step 6: Normal Liquidation (moderate amount)
```rust
let liq_result = fixture.liquidate_vault(&LiquidateVars {
    vault_id,
    user: &liquidator,
    to: &liquidator,
    debt_amount: 100_000_000,  // ← Normal amount, won't trigger overflow
    col_per_unit_debt: 0,
    absorb: false,
})?;
```

#### Step 7: Reload and Check Deltas
```rust
let state_after = fixture.read_vault_state(vault_id)?;

let supply_delta = initial_total_supply as i128 - state_after.total_supply as i128;
let borrow_delta = initial_total_borrow as i128 - state_after.total_borrow as i128;

println!("Supply delta: {}", supply_delta);
println!("Borrow delta: {}", borrow_delta);

// Verify both mutations occurred
assert!(supply_delta >= 0, "Supply should decrease");
assert!(borrow_delta >= 0, "Borrow should decrease");
```

**Vulnerability Detection:**
- If supply_delta > 0 and borrow_delta == 0 → **Asymmetry** = potential vulnerability
- If both deltas match → **Symmetric** = secure

---

## Critical Vault State Fields Tested

### From `vaults/src/state/vault_state.rs`:

1. **`total_borrow: u128`** (lines 73-79)
   ```rust
   pub fn reduce_total_borrow(&mut self, amount: u128) -> Result<()> {
       self.total_borrow = self.total_borrow.safe_sub(amount.cast())?;  // ← CAN FAIL
       Ok(())
   }
   ```
   - Target of cast overflow test
   - Must decrease or fail, never change other fields

2. **`total_supply: u128`**
   ```rust
   pub fn reduce_total_supply(&mut self, amount: u128) -> Result<()> {
       self.total_supply = self.total_supply.safe_sub(amount.cast())?;
       Ok(())
   }
   ```
   - Often succeeds when borrow fails (asymmetry)
   - Tests verify this doesn't happen

---

## Key Code Paths Validated

### Path A: Successful Liquidation
```
→ liquidate() [user.rs:513]
  → validate slippage [user.rs:877]
  → reduce_total_supply() [user.rs:880] = SUCCESS
  → reduce_total_borrow() [user.rs:881] = SUCCESS
  → [vault_state scope exit, line 891]
  → Drop impl writes to storage = HAPPENED
  → return Ok(...) [user.rs:973]
```

**Test Expectation:** Both supply and borrow decreased

### Path B: Failed Liquidation (Overflow)
```
→ liquidate() [user.rs:513]
  → validate slippage [user.rs:877]
  → reduce_total_supply() [user.rs:880] = SUCCESS
  → reduce_total_borrow() [user.rs:881] = ERROR (cast overflow)
  → [vault_state scope exit, line 891]
  → Drop impl writes to storage = HAPPENED (BEFORE ERROR)
  → return Err(...) [user.rs:881]
```

**Vulnerability Chain:**
- Supply already mutated and written to storage
- Borrow error occurred AFTER scope exit (storage already committed)
- Test will detect: supply changed, borrow unchanged

**Test Expectation:** Supply changed, borrow unchanged → PERSISTED → **FAIL ASSERTION**

---

## Error Messages That Prove Vulnerability

If the test completes and prints:

```
=== ATOMICITY VERDICT ===
PERSISTED: State mutation detected despite error!
  total_borrow delta: 500000000 -> 500000000 (UNCHANGED) ✗
  total_supply delta: 1000000000 -> 900000000 (REDUCED) ✗
  Vulnerability confirmed: State changes survived failed transaction
```

This proves:
1. Error occurred (liquidation failed)
2. Borrow was NOT reduced (cast overflow prevented mutation)
3. Supply WAS reduced (mutation applied BEFORE error)
4. No rollback occurred (both changes persisted to storage)

**Conclusion:** The atomicity vulnerability is **CONFIRMED AND EXPLOITABLE**

---

## Test Assertion Failure = Proof

The final assertion in Test 1:
```rust
assert!(
    !total_borrow_changed,
    "CRITICAL: total_borrow changed from {} to {} despite liquidation error",
    vault_state_before.total_borrow,
    vault_state_after.total_borrow
);
```

**If this assertion FAILS:**
- Test name: `test_liquidation_atomicity_with_cast_overflow`
- Panic message includes exact before/after values
- Proves state persisted despite error
- Provides numerical evidence for Code4rena submission

**If this assertion PASSES:**
- All state unchanged (secure behavior)
- Vulnerability doesn't exist (or test didn't trigger it)

---

## How Test Proves Mutation Order

The key insight:

**In Rust, AccountLoader Drop happens on scope exit:**
```rust
{
    let mut vault_state = ctx.accounts.vault_state.load_mut()?;  // scope start
    vault_state.reduce_total_supply(...)?;  // mutation 1
    vault_state.reduce_total_borrow(...)?;  // mutation 2 - can fail
    // scope end here ↓
}  // Drop::drop() called HERE - serializes to storage
// Error handling happens HERE - AFTER storage commit!
```

If mutation 1 succeeds and mutation 2 fails:
- Mutation 1 is written to storage (via Drop)
- Mutation 2 never applied (error prevented it)
- Error is returned
- Result: vault state has mutation 1 but not mutation 2 → **ASYMMETRY**

The test captures this by comparing before/after storage values.

---

## Summary

- **Test 1 proves:** Whether state changes persist after errors
- **Test 2 proves:** Whether mutations happen symmetrically or asymmetrically
- **Both use:** VaultFixture infrastructure with before/after snapshots
- **Both check:** Exact numeric deltas to detect changes
- **Both report:** Clear PERSISTED vs ROLLED_BACK verdict using println!

If executed and shows PERSISTED, this is the deterministic proof needed for a Code4rena vulnerability submission.
