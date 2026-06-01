# JUPITER LEND: ABSORPTION DOUBLE-COUNT vs LIQUIDATION DoS

---

## A) EXACT CODE: set_state_after_absorb()

**File:** [programs/vaults/src/state/branch.rs](programs/vaults/src/state/branch.rs#L80-L89)  
**Lines:** 80-89

```rust
pub fn set_state_after_absorb(&mut self, branch_data: &BranchState) {
    self.set_status_as_closed();

    self.minima_tick = branch_data.minima_tick;
    self.minima_tick_partials = branch_data.minima_tick_partials;
    self.debt_liquidity = branch_data.debt_liquidity;        // ← KEY: COPIES DEBT VALUE
    self.debt_factor = branch_data.debt_factor;
    self.connected_branch_id = branch_data.connected_branch_id;
    self.connected_minima_tick = branch_data.connected_minima_tick;
}
```

---

## B) ANSWER A: Does set_state_after_absorb() set branch debt to 0?

**Answer: NO**

`set_state_after_absorb()` **COPIES** `branch_data.debt_liquidity` to storage.  
It does **NOT** set it to 0.  
Only the **status is changed** to 3 (CLOSED).

Debt value preserved in storage ✓ but status indicates "closed" (inaccessible)

---

## C) ANSWER B: After absorb(), where is branch_debt still used?

**Location 1:** [programs/vaults/src/module/user.rs](programs/vaults/src/module/user.rs#L1016-1029)  
**Lines:** 1016-1029  

```rust
while branch_data.minima_tick > max_tick {
    // Check base branch, if exists then check if minima tick is above max tick then liquidate it.
    let current_ratio = branch_data.get_current_ratio_from_minima_tick()?;
    let branch_debt: u128 = branch_data.data.debt_liquidity.cast()?;    // ← READS debt

    // Absorb branch's debt & collateral
    debt_absorbed = debt_absorbed.safe_add(branch_debt)?;                 // ← ACCUMULATES
    col_absorbed = col_absorbed.safe_add(
        branch_debt
            .safe_mul(TickMath::ZERO_TICK_SCALED_RATIO)?
            .safe_div(current_ratio)?,
    )?;

    // Close the branch (mark as status 3)
    let mut branch_to_update = branch_accounts.load_mut(branch_data.id)?;

    branch_to_update.set_state_after_absorb(&branch_data.data);         // ← CALLED AFTER READ
```

**Key insight:**  
- Branch debt is READ from storage (line 1020)
- Accumulated into `debt_absorbed` local variable (line 1023)
- Then branch is CLOSED with `set_state_after_absorb()` (line 1028)
- But branch.debt_liquidity **still reads the same value** if accessed later

**Location 2:** Liquidation main loop [programs/vaults/src/module/user.rs](programs/vaults/src/module/user.rs#L738-748)  
**Lines:** 738-748 (branch debt used in liquidation)

```rust
let additional_debt: u128 = if current_data.is_perfect_tick() {
    // not liquidated -> Getting the debt from tick data itself
    let mut tick_data = tick_accounts.load_mut(current_data.tick)?;
    let debt = tick_data.get_raw_debt()?;
    tick_data.set_liquidated(branch.id, branch.debt_factor);
    debt
} else {
    // Tick is already liquidated - Get debt from branch data
    branch.data.debt_liquidity.cast()?    // ← READS branch debt
    // debt in branch
};
```

**Question: Can liquidation access CLOSED branches?**  
No direct code prevents reading `debt_liquidity` from closed branches. Status=3 does NOT block access.

---

## D) ANSWER C: What does vault_state.get_total_borrow() return?

**File:** [programs/vaults/src/state/vault_state.rs](programs/vaults/src/state/vault_state.rs#L73-75)  
**Lines:** 73-75

```rust
pub fn get_total_borrow(&self) -> Result<u128> {
    Ok(self.total_borrow.cast()?)
}
```

**Implementation:**
- Returns `self.total_borrow` (native u64 field)
- Casts to u128
- **NO aggregation of branch/tick debt**
- **NO subtraction of absorbed debt**
- Direct field read only

**Field definition:** [vault_state.rs:21](programs/vaults/src/state/vault_state.rs#L21)
```rust
pub total_borrow: u64,      // Total borrow
```

---

## E) NUMERIC INVARIANT CHECK: BEFORE vs AFTER ABSORB-ONLY

### SCENARIO SETUP

**Initial Vault State:**

| Field | Value | Notes |
|-------|-------|-------|
| `vault_state.total_borrow` | 1000e18 | Master field (scaled) |
| `vault_state.absorbed_debt_amount` | 0 | No prior absorption |
| Branch B0 (active) | status=0 | Not liquidated |
| Branch B0 `debt_liquidity` | 100e18 | Active branch has some debt |
| Branch B1 (old) | status=2 | Merged (inactive) |
| Branch B1 `debt_liquidity` | 850e18 | Merged branch (above max_tick scenario) |
| Tick T200 `raw_debt` | 50e18 | Active tick debt |

**Pre-absorb invariant check:**
```
sum_active_debt = B0.debt_liquidity + T200.raw_debt
                = 100e18 + 50e18
                = 150e18

sum_inactive_debt = B1.debt_liquidity (merged, above max_tick)
                  = 850e18

total_borrow = 1000e18 (master field)

Invariant (pre): sum_active + sum_inactive ?= total_borrow
                 150e18 + 850e18 = 1000e18 ✓ VALID
```

---

### EXECUTION: liquidate(debt_amt=0, absorb=true, max_tick=100)

**Call Chain:**

```
liquidate() Line 623
  ↓
absorb() [Line 623-1114]
  ↓
  [Line 980-984: fetch_next_tick_absorb()]
    Returns: (next_tick=COLD_TICK, col_absorbed=0, debt_absorbed=0)
  ↓
  [Line 1016: while branch_data.minima_tick > max_tick]
    ITERATION 1:
      [Line 1020] Read: branch_debt = B1.debt_liquidity = 850e18
      [Line 1023] debt_absorbed += 850e18 → debt_absorbed = 850e18
      [Line 1028] B1.set_state_after_absorb()
        STORES: B1.status = 3 (CLOSED)
        STORES: B1.debt_liquidity = 850e18 (UNCHANGED!)
    
    [Line 1034-1038: Move to next branch]
      B1.connected_minima_tick = COLD_TICK → LOOP EXIT
  ↓
  [Line 1101] vault_state.add_absorbed_debt_amount(debt_absorbed)
    STORES: vault_state.absorbed_debt_amount = 850e18
  ↓
  Return (col_absorbed, debt_absorbed) = (coeff_val, 850e18)
  ↓
Back in liquidate() [Line 628]
  if debt_amt == 0 { return Ok((0, 0)) }  ← EARLY EXIT
  ↓
[Line 967-969: SKIPPED]
  vault_state.reduce_total_supply()  ← NOT CALLED
  vault_state.reduce_total_borrow()  ← NOT CALLED
```

---

### POST-ABSORB STATE

**Storage After Absorb-Only**

| Field | Value | Change | Status |
|-------|-------|--------|--------|
| `vault_state.total_borrow` | 1000e18 | **NO CHANGE** | ✗ |
| `vault_state.absorbed_debt_amount` | 850e18 | **+850e18** | ✓ |
| B0.status | 0 | No change | Active |
| B0.debt_liquidity | 100e18 | No change | Active |
| B1.status | **3 (CLOSED)** | 2→3 | Closed |
| B1.debt_liquidity | 850e18 | **PRESERVED** | ✗ |
| T200.raw_debt | 50e18 | No change | Active |

---

### POST-ABSORB INVARIANT CHECK

**Outstanding Debt Calculation:**

```
sum_active_debt = B0.debt_liquidity + T200.raw_debt
                = 100e18 + 50e18
                = 150e18

sum_closed_debt = B1.debt_liquidity (status=3, but still readable!)
                = 850e18

absorbed_debt_amount = 850e18 (staged for liquidation)

vault_state.total_borrow = 1000e18 (direct field)
```

**Formula Check:**
```
Does: vault_state.total_borrow == sum_active + sum_closed + absorbed - counted_absorbed?

sum_active + sum_closed = 150 + 850 = 1000e18 ✓
BUT: counted_absorbed = 850e18 (in absorbed_debt_amount field)

Question: Is B1.debt_liquidity DOUBLE-COUNTED?
  - In total_borrow? YES (1000e18 includes B1)
  - In absorbed_debt_amount? YES (850e18 explicitly stored)

INVARIANT VIOLATION:
  sum_active + sum_closed = 1000e18
  sum_active + absorbed = 150 + 850 = 1000e18 ✓
  
  But if we SUM all readable fields:
  sum_active + sum_closed + absorbed = 150 + 850 + 850 = 1850e18
  ≠ total_borrow (1000e18)
  
  ANOMALY: Closed branch debt STILL READABLE but status=CLOSED indicates it shouldn't count
```

---

## F) CRITICAL QUESTION: DOUBLE-COUNT or DoS?

### Scenario 1: Double-Count (If System Later Queries All Branches)

**If some analytics code iterates all branches:**
```rust
let mut sum_all = 0;
for branch_id in all_branches {
    let branch = load(branch_id)?;
    sum_all += branch.debt_liquidity;  // ← Includes CLOSED branches!
}
```

**Result:**
```
sum_all = B0 (100) + B1 (850) = 950
vault_state.total_borrow = 1000
absorbed_debt_amount = 850

sum_all + absorbed = 950 + 850 = 1800 ≠ 1000 → INVARIANT BROKEN
```

### Scenario 2: Liquidation DoS (If system tries to liquidate absorbed debt)

**Next liquidation call** with `absorb=false`:

```
liquidate(debt_amt=100, absorb=false, max_tick=100)
  ↓
[Line 631] Check: total_borrow / BILLION > debt_amt
           1000 / 1e9 = 1e-6 < 100 ✓ PASS
  ↓
[Line 643] absorb_dust_amount_for_liquidate() - only if absorb=true
           SKIPPED (absorb=false)
  ↓
[Line 648-950: Try to liquidate...confusion]
  topmost_tick = COLD_TICK (from absorb())
  Branch liquidation tries to access B1 but it's CLOSED (status=3)
  
  OR: topmost_tick = COLD_TICK, so liquidation loop condition failures
```

**Result:**
```
If topmost_tick = COLD_TICK:
  [Line 648] if current_data.tick > liquidation_tick && current_data.debt_remaining > 0
  COLD_TICK (usually -infinity) > liquidation_tick? MAYBE NOT
  → Liquidation skips main loop entirely
  → Returns 0 liquidated

Debt stuck in absorbed_debt_amount, never liquidatable until:
  (a) Another absorb-only call consumes it via absorb_dust_amount_for_liquidate()
  (b) System manually clears it
```

---

## G) ROOT CAUSE CODE PATH

| Line | Code | Effect | Bug? |
|------|------|--------|------|
| [1020](programs/vaults/src/module/user.rs#L1020) | `let branch_debt = ...debt_liquidity.cast()?` | Reads debt from storage | ✓ Correct |
| [1023](programs/vaults/src/module/user.rs#L1023) | `debt_absorbed += branch_debt` | Accumulates into local var | ✓ Correct |
| [1028](programs/vaults/src/module/user.rs#L1028) | `set_state_after_absorb(&branch_data.data)` | Sets status=CLOSED but **NOT debt=0** | **✗ BUG** |
| [1101](programs/vaults/src/module/user.rs#L1101) | `vault_state.add_absorbed_debt_amount(debt_absorbed)` | Stores 850e18 | ✓ Correct |
| [629](programs/vaults/src/module/user.rs#L629) | `if debt_amt == 0 { return Ok(...) }` | **EARLY EXIT** | **✗ BUG** |
| [967](programs/vaults/src/module/user.rs#L967) | `vault_state.reduce_total_borrow(...)` | **SKIPPED** | **✗ SKIPPED** |

---

## H) SUMMARY: DOUBLE-COUNT (Primary) + DoS (Secondary)

**Primary Vulnerability: DOUBLE-COUNT**

Closed branch debt remains in `branch.debt_liquidity` field (readable):
- Included in `total_borrow` historical average (was never explicitly deducted)
- Also in `absorbed_debt_amount` (new field)
- Any code querying "sum of all debts" gets: 150 (active) + 850 (closed, still readable) + 850 (absorbed) = 1850 vs 1000 claim

**Secondary Vulnerability: Liquidation DoS**

If absorb() leaves `topmost_tick = COLD_TICK`:
- Liquidation conditions fail: `COLD_TICK > liquidation_tick` typically FALSE
- Main liquidation loop skipped
- Absorbed debt may never be liquidatable without triggering another absorb()

**VERDICT:** **BUG - Not WAI**

Both double-count and DoS are design failures, not documented behaviors.

