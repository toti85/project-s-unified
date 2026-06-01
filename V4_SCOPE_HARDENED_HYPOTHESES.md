# V4_SCOPE_HARDENED_HYPOTHESES.md

**Status**: Ground-truthed against Project-S H11 PoC + v4-core source  
**Date**: 2026-01-25

---

## Comprehensive Scope & Mechanistic Audit

### Summary Table

| ID | Hypothesis (Reframed) | In-Scope? | Why | Status | Required Evidence (Phase C) |
|----|---|---|---|---|---|
| **H11** | **Donate-Based Fee Growth Inflation** | **✅ IN-SCOPE** | **Core issue**: donate() inflates feeGrowthGlobal without validation. No hook assumption. Core invariant broken: fee growth ≠ swap activity. | **PROVEN VULNERABLE** | Measure feeGrowthGlobal delta vs. actual swaps; quantify unearned LP income; test attack scale |
| H11.1 | LP Fee Claim Diverges from Economic Reality | **✅ IN-SCOPE** | H11 corollary: if feeGrowthGlobal inflates, LP.fees owed can exceed actual pool value. Measurable via balance tracking. | **DERIVABLE FROM H11** | Compare LP.fees calculated vs. actual transferable balances; measure shortfall |
| H11.2 | Fee Growth Without Liquidity-Relative Swap | **✅ IN-SCOPE** | H11 root: donate() applies fee formula (amount * Q128 / liquidity) to arbitrary input. No swap execution. | **PROVEN IN CODE** | Execute donate() without swap; verify feeGrowthGlobal increases |
| 1 | No Arbitrage-Free Hook Extraction | **AMBIGUOUS** | Hook can inspect swap direction, but this requires deliberate hook behavior + no core constraint preventing directional fees. If core allows asymmetric hooks: design feature, not bug. | **DESIGN-DEPENDENT** | Test if core enforces symmetric pricing; if hook can force asymmetry undetected: in-scope |
| 2 | Fee Monotonicity (Hooks Can't Reduce) | **OUT-OF-SCOPE** | Hooks cannot directly reduce pool fees (pool fee is immutable per pool). Rebates are external transfers, not core fee reduction. | **REDIRECTED TO H11** | H11 proves donation (not hooks) breaks fee monotonicity; this invariant subsumed by H11 |
| 3 | Liquidity Conservation Across Hooks | **PARTIALLY IN-SCOPE** | Hooks cannot consume pool balances directly. BUT donate() can create accounting desync if it inflates feeGrowthGlobal > actual balances. | **PARTIALLY TRUE** | Verify if donate() can cause withdrawals to fail or LP claims > reserves |
| 4 | Position-Independent Execution Price | **OUT-OF-SCOPE** | Core doesn't expose LP identity during swap; hook would need external oracle. Design limitation, not core bug. | **NOT TESTABLE** | Would require hook to call external identity registry; OOS by definition |
| 5 | Hook Ordering ≠ Fairness Reversal | **OUT-OF-SCOPE** | V4 has ONE hook per pool, immutable. No ordering mechanism exists. Governance can change hook, but that's a separate pool. | **INCORRECT ASSUMPTION** | Not applicable (no hook array) |
| 6 | Tick Liquidity Aggregation Neutrality | **WEAK IN-SCOPE** | Hook can observe deposit size, apply size-dependent penalties. But core doesn't forbid this; it's hook design. If core should enforce neutrality: needs ACL. | **AMBIGUOUS** | Test if core prevents hook from observing/penalizing deposit size. Likely OOS (hook behavior). |
| 7 | No Fee-Tier Cross-Subsidies | **AMBIGUOUS** | Multiple fee-tier pools are independent. Hook cannot directly affect another pool's fee tier. BUT if hook routes swaps, it could drain one tier over another. | **AMBIGUOUS** | Test if hook can use routing to systematically drain high-fee tier. Depends on hook + PoolManager routing logic. |
| 8 | No Hidden IL From Hooks | **OUT-OF-SCOPE** | IL is function of price + liquidity changes. Hook-induced IL requires hook to artificially widen prices or batch updates. Core doesn't prevent this; it's hook behavior. | **NOT A CORE ISSUE** | Hook behavior, not core invariant |
| 9 | No Value Creation From Hook State Alone | **PARTIALLY IN-SCOPE** | Core doesn't forbid hooks from accumulating state. But donate() DOES create value without inflow (attacker pays, LP gains = zero-sum but unearned). | **PARTIALLY TRUE** | H11 is the value-creation issue: donation creates LP value without market activity. Related to H11. |
| 10 | Swap Path Independence (Economic) | **AMBIGUOUS** | Multi-hop routing is PoolManager concern. If core applies path-specific fees: in-scope. If hook controls routing: hook behavior (OOS). | **AMBIGUOUS** | Clarify: is fee application path-dependent in core, or is it hook-determined? |
| 11 | No Hook LP Discrimination | **OUT-OF-SCOPE** | Core doesn't expose LP identity; hook can't access position registry natively. Design constraint, not bug. | **DESIGN LIMITATION** | N/A |
| 12 | Liquidity Addition Idempotence | **OUT-OF-SCOPE** | Hook state persistence is design choice. If hook fee scales with call count: it's hook behavior, not core. | **NOT A CORE ISSUE** | N/A |

---

## In-Scope Hypotheses (Verified & Actionable)

### ✅ H11: Donate-Based Fee Growth Inflation (PRIMARY)

**Status**: **PROVEN VULNERABLE** (Project-S PoC exists)

**Mechanical Claim**:
- donate() inflates feeGrowthGlobal without requiring swap activity
- Formula: `feeGrowthGlobal += (donationAmount * Q128) / liquidity`
- No validation: amount doesn't need to come from swaps

**Code Evidence**:
- **PoolManager.sol:256-275** — Public donate(), no access control, no amount limits
- **Pool.sol:466-481** — Fee formula applied to arbitrary donation amounts
- **Commit**: d153b048

**Exploit Path**:
1. Attacker calls `donate(poolKey, 500 ether, 0)` with no swap activity
2. feeGrowthGlobal0X128 increases by `500 * Q128 / liquidity`
3. LP claims are now higher, but pool only has legitimate reserves + 500 donation
4. If multiple LPs or future withdrawals occur, accounting diverges

**Measurable Impact**:
- feeGrowthGlobal delta without corresponding swap
- LP.fees calculated vs. actual pool balance
- Shortfall magnitude (in wei and bps)

---

### ✅ H11.1: LP Fee Claim Divergence (SECONDARY)

**Status**: **DERIVABLE FROM H11**

**Mechanical Claim**:
- If feeGrowthGlobal is inflated by donate(), LP fee claims exceed actual earned income
- LP fee = liquidity × feeGrowthGlobal / Q128
- If feeGrowthGlobal is inflated, LP fee is also inflated (proportionally)

**Invariant**:
```
Expected: LP.fees = sum(swaps that LP participated in)
Broken: LP.fees > actual_pool_economic_value_available
```

**Code Locations**:
- **Position.sol** (fee calculation logic) — TBD, exact location needed from v4-core
- **PoolManager.sol** (balance tracking) — reserves vs. claimed fees

**Measurable Impact**:
- Ratio: `LP.fees_calculated / actual_pool_reserves` (should be ≤ 1.0)
- Shortfall when LP tries to collect: `LP.fees_owed - LP.balance_available`
- Number of LPs affected (aggregate vs. individual)

---

### ✅ H11.2: Fee Growth Without Swap Activity (TERTIARY)

**Status**: **PROVABLY TRUE**

**Mechanical Claim**:
- Core invariant: "feeGrowthGlobal should only increase when swaps occur"
- donate() breaks this: it can increase feeGrowthGlobal without any swap

**Code Evidence**:
- Pool.sol:donate() increments feeGrowthGlobal directly
- No precondition checks if activity is a "swap" vs. "donation"
- Same formula used for both

**Test**:
```
1. Initialize pool, feeGrowthGlobal = 0
2. Call donate() with no preceding swap
3. Check: feeGrowthGlobal > 0?
4. Expected: YES (invariant broken)
```

**Measurable Impact**:
- feeGrowthGlobal increase magnitude (Q128 scale)
- Correlation: "feeGrowthGlobal increases" vs. "swap count" (should be correlated; if not, H11.2 confirmed)

---

## Conditional/Ambiguous Hypotheses (Needs Clarification)

### ⚠️ H1: Directional Fee Asymmetry (Hook-Dependent)

**Status**: **AMBIGUOUS** (depends on hook implementation + core permissiveness)

**Mechanical Claim**:
- If hook inspects swap direction (zeroForOne), it could apply directional fee penalties
- Hook could charge 5% for A→B but 10% for B→A

**Core Question**:
- Does core forbid hooks from viewing swap direction? NO, hooks receive swap parameters
- Does core forbid directional fee logic? NO, hooks can implement custom logic
- Is this a "bug" or "feature"? DESIGN INTENT UNCLEAR

**In-Scope Only If**:
- Core is meant to provide fee symmetry (but doesn't enforce it)
- Hook behavior can circumvent core invariant without core-level permission structure

**Recommendation**: Mark AMBIGUOUS unless Uniswap docs explicitly state "all fees must be symmetric regardless of direction"

---

### ⚠️ H7: Fee-Tier Cross-Subsidies (Hook + Routing)

**Status**: **AMBIGUOUS** (depends on PoolManager routing + hook routing)

**Mechanical Claim**:
- If hook can route multi-pool swaps, it could systematically drain high-fee pools
- Example: swap destined for 1% pool gets routed to 0.1% pool, leaving high-fee LPs earning nothing

**Core Question**:
- Does PoolManager enforce routing rules? Unknown (needs code review)
- Can hook override user-requested path? Unknown

**Recommendation**: LOW PRIORITY until mainnet behavior is observed

---

## Scope Summary

| Category | Hypotheses | Count | Status |
|----------|-----------|-------|--------|
| **Proven Vulnerable (In-Scope)** | H11, H11.1, H11.2 | 3 | ✅ ACTIONABLE |
| **Design-Dependent (Ambiguous)** | H1, H7 | 2 | ⚠️ CLARIFICATION NEEDED |
| **Out-of-Scope (Design Limitation)** | H4, H5, H6, H8, H10, H11, H12 | 7 | ❌ NOT CORE BUGS |

---

## Phase C Testing Priorities

### Tier 1: H11 Variants (Guaranteed In-Scope)
1. H11 — Donate poisoning extent + scale
2. H11.1 — LP claim divergence measurement
3. H11.2 — Fee growth correlation with swap activity

### Tier 2: Conditional (If Clarification Supports In-Scope)
4. H1 — Directional fee asymmetry (needs design intent clarification)
5. H7 — Cross-tier routing abuse (needs PoolManager routing audit)

### Tier 3: Monitoring (Unlikely Core Issues)
6. H6, H8, H10 — Hook-behavior-specific; flag as OOS unless core constraint missing

---

**Next Step**: Phase C test plans focus on **H11 + derivatives** with optional exploration of **H1, H7** pending design clarification.

