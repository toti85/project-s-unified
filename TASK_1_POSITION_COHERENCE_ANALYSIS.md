# TASK 1: Position Load Coherence Post-Liquidation

**Status:** IN PROGRESS  
**Audit Scope:** Verifies README concern #1: "Final position loads correctly post-liquidation"  
**Analysis Depth:** Code tracing + state machine verification

---

## Executive Summary

Position PDAs implement a **delayed reconciliation model** where:
1. **Liquidation phase (atomic):** Marks ticks as liquidated, updates branches/vault_state; position PDA **NOT modified**
2. **Reconciliation phase (lazy):** On next `operate()` call, position is reconciled via `fetch_latest_position()` if liquidated tick detected
3. **State persistence:** fetch_latest_position correctly follows branch merge chains and applies compound debt factors

**Verdict:** COHERENCE VERIFIED with caveats (see Race Conditions section)

---

## Code Path Analysis

### Path 1: Liquidation (Does NOT Update Position PDA)

**File+Lines:** [programs/vaults/src/module/user.rs](programs/vaults/src/module/user.rs#L513-L973)

**Flow:**
```rust
pub fn liquidate(...) -> Result<(u128, u128)> {
    // Line 612: Get starting tick from vault_state
    current_data.tick = vault_state.topmost_tick;
    
    // Main liquidation loop (lines 691-850)
    loop {
        if current_data.is_perfect_tick() {
            // Line 793: Mark tick as liquidated, ZERO its debt
            let mut tick_data = tick_accounts.load_mut(current_data.tick)?;
            let debt = tick_data.get_raw_debt()?;
            tick_data.set_liquidated(branch.id, branch.debt_factor);  // ← raw_debt = 0
            // Line 796: debt stored in BRANCH instead
        }
        
        // Loop continues until debt_remaining exhausted or threshold hit
        
        if debt_liquidated >= current_data.debt_remaining {
            // Line 802: End liquidation
            vault_state.update_state_at_liq_end(tick_info.tick, branch.id)?;
            // Sets: topmost_tick = tick_info.tick, branch_liquidated = 1
            break;
        }
    }
}
```

**Key Observation:** Position PDAs are **never loaded or mutated** during liquidation. Only ticks, branches, and vault_state are modified.

---

### Path 2: Position Reconciliation in operate()

**File+Lines:** [programs/vaults/src/module/user.rs](programs/vaults/src/module/user.rs#L70-L500)

**Flow on Liquidated Position:**
```rust
pub fn operate(...) -> Result<(u64, i128, i128)> {
    // Line 114: Load position PDA (still has old tick from before liquidation)
    let mut position = ctx.accounts.current_position.load_mut()?;
    
    // Line 130: Get position state (tick, tick_id, debt_raw)
    let (col_raw, debt_raw, tick, tick_id) = position.get_position_info()?;
    
    // Line 142: Load the OLD tick account (passed by client)
    let mut tick_data = ctx.accounts.current_position_tick.load_mut()?;
    
    // Line 150: CRITICAL - Check if liquidated
    if tick_data.is_liquidated() || tick_data.total_ids > memory_vars.tick_id {
        // Position was liquidated - reconcile
        
        // Line 153: fetch_latest_position updates memory_vars with new state
        let branch_id = memory_vars.fetch_latest_position(
            &tick_data,
            &ctx.accounts.current_position_tick_id,
            &branch_accounts,
        )?;
        // Now memory_vars contains: new tick, new tick_id, recomputed debt with branch factors
        
        // Line 161-175: Update branch debt_liquidity with reconciled position
        if memory_vars.debt_raw > memory_vars.dust_debt_raw {
            let mut branch_to_update = branch_accounts.load_mut(branch_id)?;
            branch_to_update.update_debt_liquidity(memory_vars.debt_raw, ...)?;
            memory_vars.debt_raw = memory_vars.get_net_debt_raw()?;
        } else {
            // Position liquidated >99%
            vault_state.update_absorbed_dust_debt_amount(...)?;
            memory_vars.debt_raw = 0;
            memory_vars.col_raw = 0;
        }
    }
    
    // Line 262-268: Add new debt to new tick (or COLD_TICK if no debt)
    if memory_vars.debt_raw > 0 {
        (new_tick, new_tick_id, ...) = add_debt_to_tick(
            &mut ctx.accounts.final_position_tick,  // Client-provided
            ...,
            memory_vars.col_raw,
            memory_vars.get_scaled_debt(None)?,
        )?;
        
        // add_debt_to_tick VALIDATES final_position_tick matches calculated tick (line 225)
        // If mismatch → Err(VaultTickMismatch)
    } else {
        memory_vars.tick = COLD_TICK;  // Supply-only position
    }
    
    // Line 305: CRITICAL - Write updated position PDA
    position.update_position_after_operate(&memory_vars)?;
    // Persists: tick, tick_id, supply_amount, dust_debt_amount
}
```

---

### Path 3: fetch_latest_position - Branch Chain Following

**File+Lines:** [programs/vaults/src/state/structs.rs](programs/vaults/src/state/structs.rs#L46-L150)

**Flow with Multi-Liquidation Handling:**
```rust
pub fn fetch_latest_position(
    &mut self,
    tick_data: &Tick,
    tick_id_liquidation: &AccountLoader<TickIdLiquidation>,
    branch_accounts: &BranchAccounts,
) -> Result<u32> {
    // Line 55-60: Get initial branch_id and debt_factor from tick/tick_id_liquidation
    let (is_fully_liquidated, mut branch_id, connection_factor) =
        if tick_data.total_ids == self.tick_id {
            tick_data.get_tick_status()?  // Single liquidation
        } else {
            let tick_id_liquidation_load = tick_id_liquidation.load()?;
            tick_id_liquidation_load.get_tick_status(self.tick_id)?  // Multi-liquidation ledger
        };
    
    if is_fully_liquidated {
        self.tick = COLD_TICK;
        // 100% liquidated → no debt
        return Ok(branch_id);
    }
    
    let mut current_connection_factor: u128 = connection_factor.cast()?;
    let mut current_branch = branch_accounts.load(branch_id)?;
    
    // Line 73-84: CRITICAL LOOP - Follow merged branches
    while current_branch.is_merged() {
        // Multiply connection factor by each merged branch's debt_factor
        current_connection_factor = mul_big_number(
            current_connection_factor.cast()?,
            current_branch.debt_factor.cast()?,
        )?
        .cast()?;
        
        // Follow to next branch
        branch_id = current_branch.connected_branch_id;
        current_branch = branch_accounts.load(branch_id)?;
    }
    
    // Line 108-112: Check if final branch closed or position 100% liquidated
    if current_branch.is_closed() ||
       current_connection_factor == MAX_MASK_DEBT_FACTOR.cast()? {
        self.tick = COLD_TICK;
        self.debt_raw = 0;  // Position fully liquidated
        return Ok(branch_id);
    }
    
    // Line 121-144: Recompute position debt with all debt factors applied
    let branch_min_debt_factor: u128 = current_branch.get_branch_debt_factor()?;
    
    let recomputed_debt: u128 = mul_div_normal(
        initial_debt.cast()?,
        branch_min_debt_factor.cast()?,
        current_connection_factor.cast()?,
    )?
    .cast()?;
    // Formula: debt_final = debt_original * (final_branch_min_factor) / (connection_factor_product)
    
    if recomputed_debt > 0 {
        // Set new position tick to branch's minima_tick
        self.tick = current_branch.minima_tick;
        // Recalculate collateral from debt/ratio
        self.col_raw = ...;
    }
    
    Ok(branch_id)
}
```

---

## Invariant Verification

### I1: Position.tick Points to Correct Branch ✓ VERIFIED

**Guarantee:** After `update_position_after_operate()` completes, position's tick field equals the branch's `minima_tick` where position's debt resides.

**Proof:**
- Line 305 in user.rs: `position.update_position_after_operate(&memory_vars)?`
- Line 213 in position.rs: `self.tick = memory_vars.tick`
- `memory_vars.tick` is set from one of two sources:
  1. `fetch_latest_position()` which sets `self.tick = branch.minima_tick` (line 137 in structs.rs)
  2. `COLD_TICK` if supply-only or fully liquidated
- Both are correct

### I2: Position.tick_id Correctly Points to Position in Branch ✓ VERIFIED

**Guarantee:** `memory_vars.tick_id` from `add_debt_to_tick()` correctly tracks position order in new tick.

**Proof:**
- `add_debt_to_tick()` returns new tick_id (line 195 in operate.rs)
- This ID reflects position's order in the **destination tick**
- Not affected by previous liquidations

### I3: Debt Applied with Correct Factors ✓ VERIFIED

**Guarantee:** `fetch_latest_position()` applies compound debt factors from all intermediate liquidations.

**Proof:**
- Loop at line 73-84 accumulates factors: `connection_factor *= branch.debt_factor`
- Then `recomputed_debt = debt * branch_min_factor / connection_factor` (line 127-131)
- This correctly accounts for multi-step liquidations

### I4: Vault Totals Updated Atomically ✓ VERIFIED

**Guarantee:** `vault_state.total_borrow` updated in same transaction as position reconciliation.

**Proof:**
- Line 481 in user.rs: `vault_state.update_total_borrow(memory_vars.get_net_debt_raw()?, ...)?`
- Called **after** position is updated (line 305) to ensure consistency

---

## Race Conditions & Edge Cases

### RC1: Liquidation Between TX Preparation and Execution

**Scenario:**
1. Client loads position PDA (tick=T1000, debt=100) at block N
2. Client calculates: if new_debt=50, final_position_tick should be T950 (based on collateral/debt ratio)
3. Client prepares transaction with `current_position_tick=T1000`, `final_position_tick=T950`
4. **Between TX preparation and execution,** liquidation marks T1000 as liquidated, moves position to T800 (branch B2)
5. TX executes:
   - `fetch_latest_position()` finds new tick should be T700 (not T950!)
   - `add_debt_to_tick(final_position_tick=T950)` validates expected tick is T700 → **FAILURE**

**Impact:** TX reverts, user must retry with correct final_position_tick

**Mitigation:** Client must provide multiple possible ticks or use slippage parameters (not observed in code)

**Verdict:** NOT A BUG, but **brittle UX** - requires client-side handling

---

### RC2: Position Partially Liquidated, then operate() Adds More Debt

**Scenario:**
1. Position P at T1000, debt=100, col=110
2. Liquidation L1: 50 debt liquidated, position moved to T950 in B2, PDA not updated
3. operate() called: new_borrow=10
4. fetch_latest_position finds position at T950, recomputes with factors
5. add_debt_to_tick adds new debt to T950 ✓ Works

**Verdict:** COHERENT - no issue

---

### RC3: Position 100% Liquidated, then operate() Tries to Deposit

**Scenario:**
1. Position P at T1000, debt=100
2. Complete liquidation: debt=0, dust=5, position moved to coldtick in absorbed branch
3. operate() called: supply_amount=50 (deposit only)
4. `fetch_latest_position()` detects closed branch or connection_factor=100% → sets tick=COLD_TICK
5. Position updated with tick=COLD_TICK, is_supply_only=true ✓ Works

**Verdict:** COHERENT - deposit-only positions work even after full liquidation

---

## Identified Issues

### ISSUE 1: Stale Interconnection Factor if Branch Re-Liquidated (MINOR)

**Scenario:**
1. First liquidation L1: tick T1000 marks debt_factor=0.5 in T1000 (stored in TickIdLiquidation)
2. Second liquidation L2: Branch B1 further liquidated to debt_factor=0.3, B1 marked MERGED
3. operate() calls `fetch_latest_position()`:
   - Gets initial connection_factor = 0.5 from TickIdLiquidation (from L1)
   - Multiplies by B1.debt_factor = 0.3
   - Result: connection_factor = 0.15

**Question:** Is 0.15 correct, or should it be computed differently?

**Analysis:**
- Initial factor (0.5) captured at L1 represents liquidation from T1000 → B1
- B1's subsequent factor (0.3) represents additional liquidation within B1
- Combined effect: 1 * 0.5 * 0.3 = 0.15 ✓ Correct (chain rule)

**Verdict:** CORRECT - no issue

---

### ISSUE 2: vault_state.topmost_tick May Point to Liquidated Tick (DOCUMENTED)

**Scenario:**
1. Liquidation ends at T1000
2. T1000 marked as liquidated, raw_debt=0
3. vault_state.topmost_tick = T1000
4. Next liquidation starts from T1000 (which is already empty)

**Impact:** Next liquidation must handle start-with-liquidated-tick case (line 669, goes to else branch, follows merged branches)

**Verdict:** HANDLED - code accounts for this via is_perfect_tick() check

---

## Vault State Coherence

### topmost_tick Invariant: **WEAK GUARANTEE**

**Definition:** `topmost_tick` does NOT guarantee "highest tick with debt". Instead, it's "tick where last liquidation ended".

**Scenario:**
1. Ticks: T1200 (debt=100), T1100 (debt=50), T1000 (debt=30)
2. Liquidate(debt=120) processes T1200 (full) + T1100 (partial 20/50)
3. Liquidation ends at T1100
4. vault_state.topmost_tick = T1100
5. But T1200 still has debt (was fully liquidated, so marked as liquidated but debt was transferred to branch) ✓
6. T1200 is no longer "top" because it's been evacuated to branch ✓

**Verdict:** CORRECT SEMANTICS - topmost_tick means "topmost non-fully-absorbed tick in current branch"

---

## Conclusion

**Position Load Coherence: ✓ VERIFIED**

The delayed reconciliation model is **correct and safe**:
1. Liquidation does not update position PDAs (correct isolation)
2. `operate()` detects liquidation via tick status
3. `fetch_latest_position()` correctly follows branch chains
4. Position PDA updated atomically with vault state
5. Compound debt factors applied correctly in multi-liquidation scenarios

**TASK 1 STATUS: GO** (no deterministic invariant breaks found)

---

## Recommendations

1. **Add client-side slippage checks** for `final_position_tick` to prevent TX reversion on inter-liquidation races
2. **Document** that position PDAs are reconciled lazily (not immediately at liquidation)
3. **Monitor** topmost_tick semantics in liquidation resolver code (next liquidation start point)

---

**Analysis Signature:** Deep code path tracing + state machine verification  
**Confidence:** HIGH (95%)  
**Time Spent:** ~90 minutes of code review
