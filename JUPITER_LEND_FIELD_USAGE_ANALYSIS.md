# JUPITER LEND: FIELD USAGE & INTEREST ACCRUAL ANALYSIS

---

## A) `total_borrow` USAGE SITES

### READ/USE Site 1: Liquidation Eligibility Check
**File:** [programs/vaults/src/module/user.rs](programs/vaults/src/module/user.rs#L631-L639)  
**Lines:** 631-639  
**Context:** `liquidate()` function, early validation

```rust
// Line 631
let total_debt: u128 = vault_state.get_total_borrow()?;

if total_debt.safe_div(BILLION)? > current_data.debt_remaining {
    // if liquidation amount is less than 1e9 of total debt then revert
    // so if total debt is $1B then minimum liquidation limit = $1
    // so if total debt is $1T then minimum liquidation limit = $1000
    // partials precision is slightly above 1e9 so this will make sure that on every liquidation at least 1 partial gets liquidated
    // not sure if it can result in any issue but restricting amount further more to remove very low amount scenarios totally
    return Err(error!(ErrorCodes::VaultInvalidLiquidationAmt));
}
```

**Purpose:** Enforce minimum liquidation threshold  
**Formula:** `if liquidation_amount < total_borrow / 1e9: REJECT`  
**Fields Used:** `vault_state.total_borrow` only  
**Does NOT use:** `absorbed_debt_amount`, `absorbed_col_amount`, individual branch/tick debt

---

### WRITE Site 1: Reduce After Liquidation
**File:** [programs/vaults/src/module/user.rs](programs/vaults/src/module/user.rs#L967-L969)  
**Lines:** 967-969  

```rust
vault_state.reduce_total_supply(current_data.total_col_liq)?;
vault_state.reduce_total_borrow(current_data.total_debt_liq)?;
```

**Condition:** Only executed if `debt_amt > 0` (NOT called in absorb-only path)

---

### WRITE Site 2: Update After Operate
**File:** [programs/vaults/src/module/user.rs](programs/vaults/src/module/user.rs#L591-L595)  
**Lines:** 591-595  

```rust
let mut vault_state = ctx.accounts.vault_state.load_mut()?;

// Update final vault variables on storage
vault_state.update_total_supply(memory_vars.col_raw, old_state.old_col_raw)?;
vault_state
    .update_total_borrow(memory_vars.get_net_debt_raw()?, old_state.old_net_debt_raw)?;
```

---

## B) `absorbed_*` USAGE SITES

### READ/WRITE Site 1: Store Absorbed Branch Debt
**File:** [programs/vaults/src/module/user.rs](programs/vaults/src/module/user.rs#L1100-L1105)  
**Lines:** 1100-1105  
**Context:** Inside `absorb()` function, processing branches above max_tick

```rust
// Absorb branch's debt & collateral
debt_absorbed = debt_absorbed.safe_add(branch_debt)?;
col_absorbed = col_absorbed.safe_add(...)?;

// (...later...)
vault_state.add_absorbed_debt_amount(debt_absorbed)?;
vault_state.add_absorbed_col_amount(col_absorbed)?;
```

**Purpose:** Persist absorbed (bad debt) to vault state  
**Note:** Called BEFORE early return in absorb-only case

---

### READ/WRITE Site 2: Consume Absorbed During Liquidation
**File:** [programs/vaults/src/state/vault_state.rs](programs/vaults/src/state/vault_state.rs#L406-L424)  
**Lines:** 406-424  
**Function:** `absorb_dust_amount_for_liquidate()`

```rust
pub fn absorb_dust_amount_for_liquidate(
    &mut self,
    current_data: &mut CurrentLiquidity,
) -> Result<()> {
    let absorbed_debt: u128 = self.absorbed_debt_amount;          // ← READ
    let absorbed_col: u128 = self.absorbed_col_amount;            // ← READ

    if absorbed_debt > current_data.debt_remaining {
        // Removing collateral in equal proportion as debt
        current_data.total_col_liq = absorbed_col
            .safe_mul(current_data.debt_remaining)?
            .safe_div(absorbed_debt)?;

        // Update absorbed amounts
        self.absorbed_col_amount = absorbed_col.safe_sub(current_data.total_col_liq)?;  // ← WRITE

        // Update debt
        current_data.total_debt_liq = current_data.debt_remaining;
        self.absorbed_debt_amount = absorbed_debt.safe_sub(current_data.debt_remaining)?;  // ← WRITE

        current_data.debt_remaining = 0;
    } else {
        // Clean out all absorbed debt and collateral
        self.reset_absorbed_amounts();  // ← RESET (sets both to 0)

        current_data.debt_remaining = current_data.debt_remaining.safe_sub(absorbed_debt)?;
        current_data.total_debt_liq = absorbed_debt;
        current_data.total_col_liq = absorbed_col;
    }

    Ok(())
}
```

**Caller:** [user.rs:643](programs/vaults/src/module/user.rs#L643)  
**Condition:** Only called if `absorb == true` AND `current_data.tick > liquidation_tick`

---

### RESET Site: No Data Persistence
**File:** [programs/vaults/src/state/vault_state.rs](programs/vaults/src/state/vault_state.rs#L85-L90)  
**Lines:** 85-90  

```rust
pub fn reset_absorbed_amounts(&mut self) {
    self.absorbed_debt_amount = 0;
    self.absorbed_col_amount = 0;
}
```

---

## C) HEALTH FACTOR & LIQUIDATION ELIGIBILITY

### Health Factor Function
**File:** [programs/vaults/src/utils/operate.rs](programs/vaults/src/utils/operate.rs#L48-L128)  
**Lines:** 48-128  
**Function Name:** `check_if_position_safe()`

#### Inputs:
- `memory_vars.tick` — position's current risk tier
- `collateral_factor` or `liquidation_threshold` — from vault_config
- `supply_ex_price`, `borrow_ex_price` — exchange rates
- `new_col`, `new_debt` — proposed changes

#### Formula:
```
exchange_rate = (debt price / col price) from oracle
threshold = collateral_factor OR liquidation_threshold

check_ratio = exchange_rate * threshold / 1000
check_tick = TickMath::get_tick_at_ratio(check_ratio)?

if position.tick > check_tick:
    REJECT "Position above safety threshold"
else:
    ALLOW
```

#### Code:
```rust
// Line 95-103
let (exchange_rate, threshold, error_code) = if new_col < 0 || new_debt > 0 {
    // withdraw or borrow, check collateral factor
    (&mut exchange_rate_operate, collateral_factor, ErrorCodes::VaultPositionAboveCF)
} else {
    // deposit or payback, check liquidation threshold
    (&mut exchange_rate_liquidate, liquidation_threshold, ErrorCodes::VaultPositionAboveLiquidationThreshold)
};

*exchange_rate = get_sanitized_exchange_rate(exchange_rate, supply_ex_price, borrow_ex_price)?;

let mut check_ratio: u128 = (*exchange_rate)
    .safe_mul(threshold)?
    .safe_div(THREE_DECIMALS)?;

check_ratio = safe_multiply_divide(check_ratio, TickMath::ZERO_TICK_SCALED_RATIO, 10u128.pow(RATE_OUTPUT_DECIMALS))?;

if memory_vars.tick > TickMath::get_tick_at_ratio(check_ratio)?.0 {
    return Err(error!(error_code));
}
```

#### **CRITICAL FINDING:**
- Uses **position-level tick only**
- Does **NOT** aggregate across vault positions
- Does **NOT** use `total_borrow`, `total_supply`
- Does **NOT** use `absorbed_debt_amount`
- **Per-position formula**, not vault-level health factor

---

### Liquidation Eligibility Function
**File:** [programs/vaults/src/module/user.rs#L631-L639](programs/vaults/src/module/user.rs#L631-L639)  
**Lines:** 631-639  

#### Inputs:
- `vault_state.total_borrow` (from `get_total_borrow()`)
- User's requested `debt_amt`

#### Formula:
```
if total_borrow / 1e9 > debt_amt:
    REJECT "Liquidation amount too small"
else:
    PROCESS liquidation
```

#### Code:
```rust
let total_debt: u128 = vault_state.get_total_borrow()?;

if total_debt.safe_div(BILLION)? > current_data.debt_remaining {
    return Err(error!(ErrorCodes::VaultInvalidLiquidationAmt));
}
```

#### **CRITICAL FINDING:**
- Uses **`vault_state.total_borrow` only**
- Does **NOT** check `absorbed_debt_amount`
- Does **NOT** adjust for absorbed bad debt
- Treats absorbed & active debt identically in threshold calculation
- **Absorbed debt counted in total but not in collateral?** → Orphaned in I4 invariant

---

## D) INTEREST ACCRUAL BUCKET MAPPING

### Location: Liquidity Reserve (NOT Vaults)
**File:** [programs/liquidity/src/state/token_reserve.rs](programs/liquidity/src/state/token_reserve.rs#L270-L360)  
**Lines:** 270-360  
**Function:** `update_exchange_prices_and_rates()`

#### Interest Rate Calculation:
```rust
// Line 340-347
let mut utilization: u16 = 0;
if total_supply > 0 {
    let total_borrow = self.get_total_borrow(borrow_exchange_price)?;
    utilization = total_borrow
        .safe_mul(FOUR_DECIMALS)?
        .safe_div(total_supply)?
        .cast()?;
}

// Calculate updated borrow rate from utilization
let borrow_rate: u16 = rate_model.calc_borrow_rate_from_utilization(utilization.cast()?)?;
```

#### **Formula:**
```
utilization = total_borrow_with_interest / total_supply
borrow_rate = rate_model(utilization)
supply_rate = (borrow_rate - revenue_fee%) * utilization_yield_ratio
```

#### Buckets Affected:
```rust
total_borrow_with_interest      ← Accrues per borrow_rate
total_borrow_interest_free      ← NO accrual (stays flat)
total_supply_with_interest      ← Accrues per supply_rate
total_supply_interest_free      ← NO accrual
```

#### Code:
```rust
// Line 351-366 (borrow rate accrual)
borrow_exchange_price = borrow_exchange_price.safe_add(
    borrow_exchange_price
        .safe_mul(borrow_rate)?
        .safe_mul(seconds_since_last_update)?
        .safe_div(SECONDS_PER_YEAR.safe_mul(FOUR_DECIMALS)?)?,
)?;

// (...supply rate calculation follows with supplyRatio, borrowRatio, ratioSupplyYield...)
```

---

### Vaults ↔ Liquidity Connection
**File:** [programs/vaults/src/state/vault_state.rs#L360-375](programs/vaults/src/state/vault_state.rs#L360-375)

```rust
let (liq_supply_ex_price, _) = supply_token_reserves.calculate_exchange_prices()?;
let (_, liq_borrow_ex_price) = borrow_token_reserves.calculate_exchange_prices()?;

// Vault downloads pre-accrued rates from liquidity
vault_supply_exchange_price = vault_supply_exchange_price
    .safe_mul(liq_supply_increase_in_percent)?
    .safe_div(EXCHANGE_PRICE_SCALE_FACTOR)?;

vault_borrow_exchange_price = vault_borrow_exchange_price
    .safe_mul(liq_borrow_increase_in_percent)?
    .safe_div(EXCHANGE_PRICE_SCALE_FACTOR)?;
```

#### **CRITICAL FINDING:**
- Interest accrues **exclusively in Liquidity reserve buckets** (`total_borrow_with_interest`)
- Vaults **mirrors the accrued rates** but does NOT track interest per-position
- `vault_state.total_borrow` is **SCALED and STATIC** (never auto-incremented)
- Accrued interest is embedded in **exchange prices**, not account balances

---

## E) ABSORBED DEBT ACCOUNTING: COHERENCE ANALYSIS

| Aspect | Field | Behavior | Issue |
|--------|-------|----------|-------|
| **Aggregation** | `total_borrow` | Reduced by liquidated amounts | ✓ Updated |
| **Aggregation** | `absorbed_debt_amount` | NOT deducted from `total_borrow` | ✗ **ORPHANED** |
| **Health Factor** | `check_if_position_safe()` | Per-position, tick-based | ✓ Independent |
| **Liquidation Min** | Threshold formula | Uses `total_borrow / 1e9` | ✗ **Counts absorbed as active** |
| **Interest Accrual** | Liquidity reserve | Applied to active borrow amount | ✓ No phantom accrual |
| **Absorbed Persistence** | `absorb()` early return | Stores debt but does NOT reduce `total_borrow` | ✗ **CRITICAL BUG** |

---

## F) WAI vs BUG DETERMINATION

### **Absorb-Only Early Return Path** (debt_amt = 0)

**Call Sequence:**
```
liquidate(debt_amt=0, absorb=true, max_tick=X)
  ↓
vault_state.absorb()  [Line 623]
  ↓
vault_state.add_absorbed_debt_amount(debt_absorbed)  [Line 1104]  ← WRITES
  ↓
return Ok((0, 0))  [Line 629]  ← EARLY EXIT
  ↓
[Lines 967-969 SKIPPED: reduce_total_supply() + reduce_total_borrow() NOT called]
```

**Result:**
- `absorbed_debt_amount` += debt_from_absorbed_branches ✓ (PERSISTED)
- `total_borrow` -= 0 ✗ (UNCHANGED)
- **Invariant I4 BROKEN:** `sum(branch_debt) + sum(tick_debt) + absorbed_debt_amount ≠ total_borrow`

### **Verdict: BUG (Not WAI)**

**Evidence:**
1. Branch debt removed from circulation (`set_state_after_absorb()` marks as CLOSED)
2. Debt stored in `absorbed_debt_amount` field
3. Liquidation eligibility uses `total_borrow` (untouched)
4. Next liquidation triggers `absorb_dust_amount_for_liquidate()` which consumes from `absorbed_debt_amount`
5. But if NO liquidation happens, absorbed debt is **phantom** in total_borrow calculation

---

## SUMMARY TABLE

| Field | Location | Read By | Write By | Interest Applied? | Absorbed Included? |
|-------|----------|---------|----------|-------------------|--------------------|
| `total_borrow` | VaultState | Liq eligibility check | operate(), liquidate() | **NO** (vault static) | **YES** (undeducted) |
| `absorbed_debt_amount` | VaultState | absorb_dust_for_liquidate() | absorb() | **NO** | **N/A** (reserve bucket) |
| `total_borrow_with_interest` | TokenReserve | Utilization calc | Interest accrual | **YES** | **NO** (liquidity-only) |
| `memory_vars.tick` | Operate context | Position health check | operate() | **NO** (per-position) | **NO** (position-specific) |

