# TASK 0: SHARED LIQUIDITY COUPLING MAP

## FINDING: TokenReserve (Shared Liquidity via Liquidity Program)

**Shared Liquidity Struct:** `TokenReserve` (from `liquidity` program, external)

**Vaults Interaction Points:**
- [context.rs:100, 103, 210, 212, 268, 270, 283, 285, 547, 549, 776, 778, 937, 939, 1058, 1059](programs/vaults/src/state/context.rs)
- Passed as `supply_token_reserves_liquidity` and `borrow_token_reserves_liquidity`
- Represents shared liquidity pool for collateral (supply) and borrow tokens

**Per-Vault State Struct:** `VaultState` (tracks vault-specific accounting)

### VaultState Fields (vault_state.rs:20-31)

| Field | Type | Purpose |
|-------|------|---------|
| `vault_id` | u16 | Vault identifier |
| `total_supply` | u64 | Total collateral supplied to this vault |
| `total_borrow` | u64 | Total debt borrowed from this vault |
| `liquidity_supply_exchange_price` | u64 | Cached exchange price from shared TokenReserve (supply) |
| `liquidity_borrow_exchange_price` | u64 | Cached exchange price from shared TokenReserve (borrow) |
| `vault_supply_exchange_price` | u64 | Vault-specific exchange price (supply) with rate magnifier |
| `vault_borrow_exchange_price` | u64 | Vault-specific exchange price (borrow) with rate magnifier |
| `last_update_timestamp` | u64 | Timestamp of last exchange price update |
| `absorbed_debt_amount` | u128 | Bad debt absorbed (reserve) |
| `absorbed_col_amount` | u128 | Collateral absorbed (reserve) |

### Cross-Vault Coupling Points

**1. Exchange Price Calculation** [vault_state.rs:277-330]
- `load_exchange_prices()` reads from shared `TokenReserve` accounts
- Calculates vault-specific exchange rates BASED ON shared TokenReserve prices
- **Mutation:** [vault_state.rs:370-405] `update_exchange_prices()` writes new rates to VaultState

**2. Instructions Using TokenReserve** (all in context.rs)
- `Operate` [L100, 103]: Both vault supply and borrow TokenReserves
- `Liquidate` [L210, 212]: Both TokenReserves
- `Rebalance` [L268, 270]: Both TokenReserves
- `Withdraw/Deposit` [L283, 285, 547, 549, 776, 778, 937, 939, 1058, 1059]: Various instructions

**3. Coupling Mechanism**
- All vaults reading TokenReserve prices independently → can get DIFFERENT prices if called in different slots
- If tokenReserve state changes between vault A and vault B operations in same tx → vaults see different exchange prices
- Absorbed debt/collateral NOT per-vault; tracked in VaultState (vault_id scoped) but sourced from shared pool

### Critical Code Paths

**Path 1: Exchange Price Update Flow**
1. [vault_state.rs:277] `load_exchange_prices()` calls `supply_token_reserves.calculate_exchange_prices()`
2. [vault_state.rs:299] Validates monotonicity: `liq_supply_ex_price < old_liq_supply_ex_price` → error
3. [vault_state.rs:305] Applies liq increase to vault price: `vault_supply_ex_price *= liq_supply_increase_in_percent`
4. [vault_state.rs:370] `update_exchange_prices()` writes all 4 prices to VaultState storage

**Path 2: TVL Impact**
- `total_supply` and `total_borrow` in VaultState represent vault's position in shared TokenReserve
- CPI call to Liquidity program mutates TokenReserve when operating
- Next vault reading TokenReserve gets updated exchange prices (reflects prior vault's actions)

---

## CONCLUSION (TASK 0)

**Shared Liquidity:** `TokenReserve` (external account, read-only in vaults instructions)  
**Vault-Scoped State:** `VaultState` with 4 exchange price fields  
**Coupling Risk Level:** MEDIUM
- Multiple vaults can be affected by TokenReserve changes
- Exchange prices are read and cached; not all vaults update synchronously
- Bad debt absorption is vault-scoped but uses shared liquidity pool

**Ready for TASK 1:** Test harness can now snapshot VaultState fields + TokenReserve prices
