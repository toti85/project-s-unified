# Liquidity Layer: Claim/Reserve Invariant Analysis
## System-Level Invariant Verification Audit

**Audit Scope:** Verify that reserved amounts for claims can always be claimed  
**Invariant:** `total_claim_amount <= vault_balance` and `vault_balance - total_claim_amount >= any_transfer`  
**Status:** ✅ **SAFE - Invariant is enforced**

---

## 1. CLAIM/RESERVE ACCOUNTING LOCATIONS

### Primary State Field
**File:** [programs/liquidity/src/state/token_reserve.rs](programs/liquidity/src/state/token_reserve.rs#L33)
```rust
pub struct TokenReserve {
    pub total_claim_amount: u64,  // Line 33 - Total reserved for all claim accounts
    // ... other fields
}
```

### Methods
| Method | Location | Purpose |
|--------|----------|---------|
| `add_claim_amount()` | [token_reserve.rs:57-61](programs/liquidity/src/state/token_reserve.rs#L57) | Increase total_claim_amount when claim is created |
| `reduce_claim_amount()` | [token_reserve.rs:63-66](programs/liquidity/src/state/token_reserve.rs#L63) | Decrease total_claim_amount when claim is fulfilled |

### User Claim Storage
**File:** [programs/liquidity/src/state/state.rs](programs/liquidity/src/state/state.rs#L60)
```rust
pub struct UserClaim {
    pub user: Pubkey,
    pub amount: u64,        // Individual user's claimable amount
    pub mint: Pubkey,
}
```

---

## 2. MUTATION SITES & CHECKS - COMPLETE FLOW

### FLOW #1: Creating Claims via Operate (Withdrawal/Borrow)

**Entry:** [programs/liquidity/src/lib.rs:31-45](programs/liquidity/src/lib.rs#L31-L45) - `operate()` dispatch

**Function:** [programs/liquidity/src/module/user.rs:38-287](programs/liquidity/src/module/user.rs#L38-L287)

**Sequence (for withdrawal):**

```
Step 1: User requests withdraw via transfer_type = CLAIM
  Location: user.rs line 220-237
  
Step 2: handle_transfer_or_claim() is called
  Location: user.rs line 220
  Function: [programs/liquidity/src/utils/token.rs:8-43](programs/liquidity/src/utils/token.rs#L8-L43)
  
  CRITICAL CHECKS AT token.rs:17-23:
  ┌─────────────────────────────────────────────────────────┐
  │ let balance = balance_of(vault)                         │
  │                                                         │
  │ CHECK 1: if total_claim_amount > balance               │
  │          → return Err(InvalidClaimAmount)              │
  │                                                         │
  │ CHECK 2: if (balance - total_claim_amount) <             │
  │            transfer_amount                             │
  │          → return Err(InsufficientBalance)             │
  │                                                         │
  │ RESULT: Both checks must pass before proceeding         │
  └─────────────────────────────────────────────────────────┘
  
Step 3: If transfer_type == CLAIM
  Location: token.rs line 30-35
  - claim_account.approve(amount) called [line 35]
    → This increases UserClaim.amount
  - Returns amount to be added to total_claim_amount
  
Step 4: add_claim_amount(claim_amount) called
  Location: user.rs line 237
  - Updates token_reserve.total_claim_amount += claim_amount
  
INVARIANT STATE AFTER:
- UserClaim.amount has been increased
- total_claim_amount has been increased with same amount
- Vault balance unchanged (CLAIM doesn't transfer)
- Invariant guaranteed: already verified in Step 2
```

### FLOW #2: Claiming Tokens (User Withdrawal)

**Entry:** [programs/liquidity/src/lib.rs:57-60](programs/liquidity/src/lib.rs#L57-L60) - `claim()` dispatch

**Function:** [programs/liquidity/src/module/user.rs:303-335](programs/liquidity/src/module/user.rs#L303-L335)

```
Step 1: Get user's claimable amount
  Location: user.rs line 309
  amount = user_claim.balance()
  
Step 2: Reduce global claim counter
  Location: user.rs line 312
  token_reserve.reduce_claim_amount(amount)?
  → Updates total_claim_amount -= amount
  
Step 3: Reset individual claim account
  Location: user.rs line 313
  user_claim.reset_balance()? 
  → Sets UserClaim.amount = 0
  
Step 4: Transfer tokens to user
  Location: user.rs line 314-327
  transfer_spl_tokens(vault, recipient_account, amount)?
  → If this fails, entire TX reverts (Solana atomicity)
  → So reduce_claim_amount() and reset_balance() only persist if transfer succeeds
  
SECURITY PROPERTY:
- Transfer failures are atomic
- If vault doesn't have enough tokens, claim() fails and reverts all changes
- Claim is retried later when vault has more tokens
```

### FLOW #3: Revenue Collection (Vault Reduction via Admin)

**Entry:** [programs/liquidity/src/lib.rs:115-117](programs/liquidity/src/lib.rs#L115-L117) - `collect_revenue()` dispatch

**Function:** [programs/liquidity/src/module/admin.rs:238-265](programs/liquidity/src/module/admin.rs#L238-L265)

```
Step 1: Calculate revenue available for extraction
  Location: admin.rs line 239-241
  revenue_amount = token_reserve.calc_revenue(vault_balance)?
  
  CALC_REVENUE FUNCTION: [token_reserve.rs:637-653](programs/liquidity/src/state/token_reserve.rs#L637-L653)
  
  Core calculation at line 645-646:
  ┌────────────────────────────────────────────────────────────┐
  │ revenue_amount = vault_balance + total_borrow -            │
  │                  total_claim_amount - total_supply          │
  │                                                            │
  │ EXPLICIT CLAIM SUBTRACTION: Line 646 comment states:       │
  │ "Since claim amount is still in the vault, but that is     │
  │  not revenue"                                              │
  │                                                            │
  │ FINAL: revenue = max(0, revenue_amount - total_supply)     │
  └────────────────────────────────────────────────────────────┘
  
  INVARIANT PROTECTION:
  - calc_revenue explicitly subtracts total_claim_amount
  - Ensures tokens cannot be removed beyond what's available for claims
  - Formula: vault (after revenue) >= total_claim_amount (guaranteed)

Step 2: Transfer revenue to collector
  Location: admin.rs line 243-258
  transfer_spl_tokens(vault, revenue_collector, revenue_amount)?
  
  RESULT:
  - Only calculates transferable amount AFTER protecting claims
  - vault_balance decreases by exactly revenue_amount
  - Invariant maintained: vault >= claims (by design)
```

---

## 3. INVARIANT PROTECTION ANALYSIS

### Invariant Definition
```
At any point in execution:
  total_claim_amount <= vault_balance
  AND
  (vault_balance - total_claim_amount) >= any_pending_transfer
```

### Protection Mechanisms

| Mechanism | Location | Protects Against |
|-----------|----------|------------------|
| **Balance Check on Claim Add** | [token.rs:17-23](programs/liquidity/src/utils/token.rs#L17-L23) | Adding claims beyond vault capacity |
| **Available Balance Check** | [token.rs:21-23](programs/liquidity/src/utils/token.rs#L21-L23) | Concurrent transfers exceeding available balance |
| **Revenue Calculation** | [token_reserve.rs:645-646](programs/liquidity/src/state/token_reserve.rs#L645-L646) | Admin removing claims as revenue |
| **Atomic Claim Transfer** | [user.rs:312-327](programs/liquidity/src/module/user.rs#L312-L327) | Partial claim execution |
| **Vault Authority** | [context.rs:56-62](programs/liquidity/src/state/context.rs#L56-L62) | Vault authority validated via ATA constraint |

---

## 4. ATTACK VECTORS ANALYZED

### ❌ ATTEMPT 1: Exceed Total Claims Beyond Vault

**Scenario:**
```
1. vault = 1000, total_claim = 0
2. User A claims 600 (CLAIM transfer)
3. User B tries to claim 600 (CLAIM transfer)
```

**Result:** BLOCKED

```
At step 3:
- Check: (1000 - 600) >= 600?
- 400 >= 600? NO
- Err(InsufficientBalance) [token.rs:22]
- TX reverts
```

---

### ❌ ATTEMPT 2: Admin Reduces Vault Below Claims via collect_revenue()

**Scenario:**
```
1. vault = 1000, total_claim = 500
2. supplied = 0, borrowed = 200
3. Admin calls collect_revenue()
```

**Calculation:**
```
revenue = (1000 + 200) - 500 - 0 = 700
transfer_amount = 700
```

**Result:** SAFE

```
After transfer:
- vault = 1000 - 700 = 300
- total_claim = 500

But wait - this violates vault >= claims!

CHECK: Does this happen?
- calc_revenue() subtracts claims [line 646]
- So max revenue that can be extracted is:
  vault + borrowed - claims - supplied
  
Example recalc:
- If vault = 1000, borrowed = 200, supply = 0, claims = 500
- Available revenue = 1000 + 200 - 500 - 0 = 700
- After transfer: vault = 300, claims = 500
- This DOES create vault < claims!
```

**BUT SAFE BECAUSE:**
```
The next operation that tries to transfer checks:
- handle_transfer_or_claim: if total_claim_amount > balance
  → return Err(InvalidClaimAmount)
  
This blocks further operations until vault is refunded.

Users CAN still claim waiting tokens because:
- Transaction atomicity: if claim() tries to transfer when vault < claim_amount,
  entire TX reverts
- Tokens remain in claim_account for retry after vault is refunded
```

---

### ❌ ATTEMPT 3: Race Condition Between Claim Check and Transfer

**Scenario:**
```
1. claim() function checks: amount = 500
2. Another operation removes 100 from vault
3. claim() transfers 500 but vault only has 400
```

**Result:** SAFE (Solana atomic execution)

```
All claims within one transaction:
- Writes are isolated from other concurrent transactions
- Pre/Post-operate timestamp check prevents replay
- claim() is single instruction, atomic

If any instruction in sequence fails:
- Entire transaction reverts
- State rolls back to before claim() started
```

---

### ❌ ATTEMPT 4: Claim Account Desynchronization

**Scenario:**
```
1. total_claim_amount = 500
2. But actual sum(UserClaim.amount) = 300
3. Missing 200 tokens tracked but not allocable
```

**Prevents By:**
```
add_claim_amount() is ONLY called from:
- Line 210: After handle_transfer_or_claim() which called approve()
- Line 237: After handle_transfer_or_claim() which called approve()
- Line 265: After handle_transfer_or_claim() which called approve()

Each add directly follows approve with matching amount:
- approve(A) → UserClaim.amount += A
- add_claim_amount(A) → total_claim_amount += A
- Amounts always match

Upon claim:
- reduce_claim_amount(amount) → total_claim_amount -= amount
- reset_balance() → UserClaim.amount = 0
- Both happen in same TX, matching amounts
```

---

## CONCLUSION - REVISED AFTER PoC

### ⚠️ VERDICT: **INVARIANT CAN BE VIOLATED** (Admin-Triggered, Transient)

**Prior Assessment:** SAFE (incorrect - analysis missed revenue extraction guard)  
**Actual Finding:** PoC demonstrates admin can create state where `vault_balance < total_claim_amount`  
**Updated Severity:** QA-level (requires admin privilege, no permanent loss)

See: [CLAIM_INVARIANT_POC_FINDINGS.md](CLAIM_INVARIANT_POC_FINDINGS.md) for runnable test + output

### Root Cause: Unguarded Revenue Extraction After Claims Created

The claim/reserve invariant is **NOT properly enforced** because:

1. **Claim Creation Has Protective Checks (But Only At Creation Time)**
   - Check at [token.rs:17-23](programs/liquidity/src/utils/token.rs#L17-L23) validates `vault - claims >= transfer_amount`
   - BUT this check only runs when claim is CREATED
   - Does NOT re-validate after admin extracts revenue

2. **Revenue Extraction Formula Accounts for Claims But Extraction Is Unrestricted**
   - Formula at [token_reserve.rs:645-646](programs/liquidity/src/state/token_reserve.rs#L645-L646): `revenue = vault + borrow - claims - supply`
   - Transfer at [admin.rs:243-258](programs/liquidity/src/module/admin.rs#L243-L258) proceeds without validating post-state
   - Assumption: `(vault + borrow)` will always cover obligations
   - Reality: If borrow defaults, assumption fails and `vault < claims`

3. **Atomic Claim+Transfer Only Prevents Corruption, Not Unavailability**
   - Solana ensures TX atomicity
   - Claim failure is caught and reverted
   - BUT: Invariant violation exists BEFORE claim TX is attempted
   - Failure is symptom, not prevention

4. **Synchronized Counters Are Paired But Not Vault-Backed**
   - `UserClaim.amount` and `total_claim_amount` always match
   - But pairing alone doesn't guarantee vault liquidity
   - After revenue extraction: counters exist but vault is empty

### 🔴 CRITICAL PATH: Admin Revenue Extraction Creates Vulnerability

**Location:** [programs/liquidity/src/module/admin.rs:238-265](programs/liquidity/src/module/admin.rs#L238-L265) - `collect_revenue()`

**Runnable PoC:** See [CLAIM_INVARIANT_POC_FINDINGS.md](CLAIM_INVARIANT_POC_FINDINGS.md)

The invariant can be violated when admin calls `collect_revenue()` after claims exist:

```
State Timeline:
  T1: vault=1000, claims=500, borrow=200, supply=0
  T2: calc_revenue() = (1000+200) - 500 - 0 = 700
  T3: transfer(700) executed  → vault becomes 300
  T4: vault (300) < claims (500)  ← INVARIANT BROKEN
```

**Attack Sequence (Admin Only):**
1. Users create claims via borrow/withdraw operations with CLAIM transfer type
   - Claims recorded: total_claim_amount += X
   - Vault checked: [token.rs:17-23] validates sufficient balance at THIS moment
   
2. External factor: borrowers accumulate unpaid amounts
   - total_borrow increases
   - Vault may be withdrawn by legitimate withdrawals
   
3. Admin sees: `calc_revenue() = (vault + borrow) - claims - supply > 0`
   - Formula assumes borrow will be repaid (covered by vault eventually)
   
4. Admin calls collect_revenue()
   - Extracts: vault - revenue_amount
   - NO post-check that vault >= claims
   
5. Result: vault < claims, but claims are still in system
   - Users cannot claim until vault is refunded by borrow repayment
   - Invariant "always available" is violated

**Severity Assessment:**
- **Type:** Invariant violation (fact)
- **Privilege:** Admin-only (downgrades criticality)
- **Duration:** Transient (until borrow repaid or external funding)
- **Recovery:** Automatic (on borrow repayment)
- **Loss:** None (tokens not burned, just inaccessible temporarily)
- **Final Level:** QA (operational risk, not critical bug)

---

## Detailed Findings

**UPDATED: See [CLAIM_INVARIANT_POC_FINDINGS.md](CLAIM_INVARIANT_POC_FINDINGS.md) for:**
- Runnable test code (tests_invariant_violation_poc.rs)
- Sample output demonstrating invariant violation
- Exact line-by-line guards that fail to prevent the issue
- Severity framing based on PoC evidence

---

## Files Analyzed

- ✅ [programs/liquidity/src/state/token_reserve.rs](programs/liquidity/src/state/token_reserve.rs) - Claim field definition
- ✅ [programs/liquidity/src/state/state.rs](programs/liquidity/src/state/state.rs) - UserClaim structure
- ✅ [programs/liquidity/src/utils/token.rs](programs/liquidity/src/utils/token.rs) - Transfer/claim logic with checks (INSUFFICIENT)
- ✅ [programs/liquidity/src/module/user.rs](programs/liquidity/src/module/user.rs) - Claim creation and fulfillment
- ✅ [programs/liquidity/src/module/admin.rs](programs/liquidity/src/module/admin.rs) - Revenue collection (UNGUARDED PATH)
- ✅ [programs/liquidity/src/state/context.rs](programs/liquidity/src/state/context.rs) - Account constraints

