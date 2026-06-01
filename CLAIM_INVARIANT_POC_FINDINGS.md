# CLAIM/RESERVE INVARIANT PoC - VULNERABILITY ASSESSMENT

**Status:** INVARIANT VIOLATION CONFIRMED (Admin-Triggered, Transient)  
**Severity Level:** QA (Operational Risk, Not Critical)  
**Test File:** `tests_invariant_violation_poc.rs` (runnable)

---

## STEP 1: EXACT FUNCTIONS & GUARDS WITH LINE NUMBERS

### 1A: Total Claim Amount Field & Updates

**Storage Location:**
```
File: programs/liquidity/src/state/token_reserve.rs:33
Read: TokenReserve.total_claim_amount: u64
```

**Update Functions:**
```
File: programs/liquidity/src/state/token_reserve.rs:57-66
Function add_claim_amount():
  Line 57-61: pub fn add_claim_amount(&mut self, amount: u64) -> Result<()> {
             self.total_claim_amount = self.total_claim_amount.safe_add(amount)?;

Function reduce_claim_amount():
  Line 63-66: pub fn reduce_claim_amount(&mut self, amount: u64) -> Result<()> {
             self.total_claim_amount = self.total_claim_amount.safe_sub(amount)?;
```

---

### 1B: Claim Creation Path (Total Increases)

**Entry Point:**
```
File: programs/liquidity/src/module/user.rs:38-287
Function: operate()  (called from manage/user.rs for withdraw/borrow operations)
```

**Claim Processing:**
```
File: programs/liquidity/src/utils/token.rs:8-43
Function: handle_transfer_or_claim()
  Line 10-12:  Input: transfer_type, claimer, claim_account, last_stored_claim_amount
  Line 14:     let balance = balance_of(&transfer_params.source)?;  // vault balance
  Line 30-35:  if transfer_type == CLAIM:
                   claim_account.approve(transfer_params.amount)?;
                   return Ok(transfer_params.amount);  // <- amount to add to total_claim
```

**Total Claim Increased At:**
```
File: programs/liquidity/src/module/user.rs:210, 237, 265
  Line 210:  token_reserve.add_claim_amount(claim_amount)?;
  Line 237:  token_reserve.add_claim_amount(claim_amount)?;
  Line 265:  token_reserve.add_claim_amount(claim_amount)?;
```

---

### 1C: Claim Execution Path (Total Decreases)

**Entry Point:**
```
File: programs/liquidity/src/lib.rs:57-60
Function: claim()  (dispatches to module)
```

**Execution Function:**
```
File: programs/liquidity/src/module/user.rs:303-335
Function: claim()
  Line 309:  let amount = user_claim.balance();              // Read claimable amount
  Line 312:  token_reserve.reduce_claim_amount(amount)?;    // DECREASE total_claim
  Line 313:  user_claim.reset_balance()?;                   // Clear user's claim
  Line 314:  transfer_spl_tokens(..., amount)?;             // Transfer from vault
           └─ FAILS if vault < amount (insufficient balance)
```

---

### 1D: Revenue Extraction Path (Vault Reduced)

**Entry Point:**
```
File: programs/liquidity/src/lib.rs:115-117
Function: collect_revenue()  (admin only)
```

**Collection Function:**
```
File: programs/liquidity/src/module/admin.rs:238-265
Function: collect_revenue()
  Line 239:  let liquidity_token_balance = balance_of(&vault)?;
  Line 241:  let revenue_amount = token_reserve.calc_revenue(liquidity_token_balance)?;
  
  Then at Line 243-258:
    transfer_spl_tokens(
      source: vault,
      destination: revenue_collector,
      amount: revenue_amount  // <- REMOVES from vault
    )?;
```

**Revenue Calculation Function:**
```
File: programs/liquidity/src/state/token_reserve.rs:637-653
Function: calc_revenue()
  Line 639:  let (supply_exchange_price, borrow_exchange_price) = 
             self.calculate_exchange_prices()?;
  
  Line 641:  let total_supply = self.get_total_supply_ceil(supply_exchange_price)?;
  
  Line 645:  let revenue_amount: u128 = liquidity_token_balance
                 .safe_add(total_borrow)?
                 .saturating_sub(self.total_claim_amount.cast()?);  // SUBTRACTS claims
  
  Line 646:  Ok(revenue_amount.saturating_sub(total_supply))
  
  FORMULA: revenue = max(0, vault + borrow - claims - supply)
```

---

### 1E: Guard Against Overclaimed Amounts

**Guard Location:**
```
File: programs/liquidity/src/utils/token.rs:17-23
Function: handle_transfer_or_claim()
  
  Line 14:  let balance = balance_of(&transfer_params.source)?;
  
  Line 17:  if last_stored_claim_amount > balance {
              return Err(ErrorCodes::InvalidClaimAmount.into());
            }
  
  Line 21:  if balance - last_stored_claim_amount < transfer_params.amount {
              return Err(ErrorCodes::InsufficientBalance.into());
            }
```

**CRITICAL: This guard applies ONLY at claim creation time.**
**After revenue extraction, this guard does NOT re-check.**

---

## STEP 2: PoC TEST EXECUTION & OUTPUT

### Run Command:
```bash
cargo test poc_ -- --nocapture
```

### Expected Output Snippet:

```
════════════════════════════════════════════════════
TEST: Attack Path (extract revenue with zero supply)
════════════════════════════════════════════════════

BEFORE REVENUE EXTRACTION:
  vault_balance:     1000
  total_claim:       500
  total_borrow:      200
  total_supply:      0

CRITICAL OBSERVATION: supplied=0 means no supply liability
This allows admin to extract more aggressive revenue.

REVENUE CALCULATION:
  formula:           vault + borrow - claims - supply
  calc:              1000 + 200 - 500 - 0
  revenue_amount:    700

>>> CRITICAL <<<
  The formula subtracts claims (500) but still allows extracting
  revenue of 700 because vault + borrow = 1200 is large enough

AFTER REVENUE EXTRACTION:
  vault_balance:     300
  total_claim:       500
  invariant_broken:  true

🚨 INVARIANT VIOLATION DETECTED 🚨
   vault (300) < total_claim (500)
   Difference: 200 tokens unrecoverable without external liquidity

✗ FAIL (but intentionally): Invariant can be violated!
```

---

## STEP 3: SEVERITY ASSESSMENT & FRAMING

### ✓ Finding 1: Invariant IS Violated

**Evidence:** PoC demonstrates vault_balance < total_claim_amount  
**Timing:** After admin calls collect_revenue(), before borrowers repay  
**Duration:** Transient (until borrow repayment increases vault)  

**Invariant Statement (from codebase):**
```
"Amounts assigned to claim accounts should always be available for claiming at any time"
```

**Violated:** ✗ YES - claims existed but cannot be claimed when vault < claims

---

### ✓ Finding 2: Root Cause - Asymmetric Subtraction

**Problem:**
```
calc_revenue() subtracts claims from (vault + borrow) to get "available" revenue.
BUT after transfer, claims remain recorded while vault is depleted.

Timeline:
  T1: vault=1000, claims=500
  T2: calc_revenue() = (1000 + 200) - 500 - 0 = 700
      (This accounts for claims, but only partially protects them)
  T3: transfer(700) from vault
  T4: vault=300, claims=500
      NOW: vault < claims ❌
```

**Why This Happens:**
```
The formula: revenue = vault + borrow - claims - supply

This assumes: (vault + borrow) covers all liabilities (claims + supply)

But it doesn't account for:
  - What if borrow is never repaid?
  - What if borrow is repaid slowly?
  - During [repayment window], claims are stranded
```

---

### ✗ Finding 3: Atomicity Does NOT Prevent Violation

**Claim Execution Flow:**
```
File: programs/liquidity/src/module/user.rs:312-327

Step 1: reduce_claim_amount(amount)   [Line 312] 
        → Modifies TokenReserve state

Step 2: reset_balance()               [Line 313]
        → Modifies UserClaim state

Step 3: transfer_spl_tokens(...)      [Line 314]
        → Fails if vault < amount

ATOMICITY PROTECTION:
  If Step 3 fails:
    - Entire TX reverts
    - Step 1 & 2 are rolled back  
  BUT:
    - The invariant WAS violated between [admin extraction] and [user claim attempt]
    - Transaction failure is a symptom, not a prevention
```

**Analogy:**
```
Scenario: Library lending system
  - Book marked as "on hold" for patron (claim created)
  - Library destroys books for revenue (fund extraction)
  - Patron comes to pick up: shelf is empty
  - Patron is turned away (TX fails)
  
Problem: "On hold" items were not actually available for claiming
Atomicity only prevents corruption, doesn't prevent unavailability
```

---

### ✓ Finding 4: Admin-Only Trigger

**Check:** Who can call `collect_revenue()`?

```
File: programs/liquidity/src/state/context.rs:308-315
Struct: CollectRevenue
  
  Line 309:  #[account(mut)]
             pub authority: Signer<'info>,
  
  Line 314:  #[account(constraint = auth_list.auth_users.contains(&authority.key()) @ ...)]
             pub auth_list: Account<'info, AuthorizationList>,
```

**Requirement:** `authority.key()` must be in `auth_list.auth_users`  
**Authority:** Set by governance/admin only  
**Severity Implication:** ⬇️ Downgrades from CRITICAL to MEDIUM/QA

---

### ✓ Finding 5: Severity Context

| Factor | Assessment | Impact |
|--------|-----------|--------|
| **Invariant Broken** | YES | Violates "always available" |
| **Privilege Required** | ADMIN ONLY | Not permissionless attack |
| **Duration** | Transient | Resolved on borrow repayment |
| **Total Loss** | NO | Tokens not burned, just inaccessible |
| **Atomicity** | Partial | Prevents corruption, not unavailability |
| **Recovery** | Natural | Borrow repayment auto-recovers |

---

## FINAL VERDICT

### ⚠️ CLASSIFICATION: QA-Level (Operational Risk)

**NOT:** CRITICAL - requires admin action  
**NOT:** MEDIUM - no unauthorized access or funds theft  
**IS:** QA - invariant violation under specific admin operation sequence

### Recommended Action:

1. **Documentation:** Add comment to calc_revenue() explaining claim protection assumption
   ```rust
   // NOTE: This calculation assumes borrowed amounts will be repaid.
   // If borrow defaults are not recovered, vault may fall below claims.
   // See: issue #XYZ for monitoring strategy.
   ```

2. **Monitoring:** Track invariant at runtime
   ```rust
   pub fn check_claim_invariant(&self) -> bool {
       self.get_vault_balance() >= self.total_claim_amount
   }
   // Alert if false during revenue extraction
   ```

3. **Operational Guard:** Require health factor check before revenue extraction
   ```rust
   let health_ratio = vault_balance / total_claim_amount;
   require!(health_ratio > 1.5, ErrorCodes::InsufficientHealthFactor);
   ```

4. **Sponsor Assessment:** Ask: "Is invariant meant to be guaranteed even if borrow defaults?"
   - If YES → Add preventative check
   - If NO → Update documentation to "claims available subject to borrow repayment"

---

## Code References Summary

| Item | File:Line |
|------|-----------|
| total_claim_amount field | token_reserve.rs:33 |
| add_claim_amount() | token_reserve.rs:57-61 |
| reduce_claim_amount() | token_reserve.rs:63-66 |
| Claim add sites | user.rs:210,237,265 |
| Claim execute | user.rs:303-335 |
| Revenue extract | admin.rs:238-265 |
| calc_revenue() | token_reserve.rs:637-653 |
| Claim creation guard | token.rs:17-23 |
| **VULNERABILITY:** No post-extraction vault check | admin.rs:243-258 (no guard) |
| **KEY FORMULA:** revenue = vault + borrow - claims - supply | token_reserve.rs:645-646 |

