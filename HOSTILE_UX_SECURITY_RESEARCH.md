# HOSTILE UX-SECURITY RESEARCH
## Wallet Control Loss Without Key Compromise

**Role:** UX-security researcher (NOT smart contract auditor)  
**Focus:** "Non-custodial" → irreversible loss of control (no malware/phishing/key theft)  
**Scope:** Account Abstraction, social recovery, guardians, approvals, session keys, upgrades  
**Goal:** Violations of "user-controlled" claim while protocol works as designed

---

## ATTACK 1: THE SESSION KEY EXPIRY TRAP

**System:** Account Abstraction wallet with session keys (e.g., meta-tx style)

**Claim:** "You control your funds via session keys, private signers are just for security"

**Preconditions:**
- User sets up AA wallet on Ethereum
- User creates session key (low-privilege signer) that can spend up to $10k per day
- Session key expires in 30 days
- Private signer is safely stored (hardware wallet, not on device)

**User Intent:**
- Daily spending via session key
- Large transactions use private signer
- Comfortable with 30-day session key rotation

**What Goes Wrong:**

Day 25:
```
User: Still happy with session key setup
Session key: Still active (5 days left)
User behavior: Moves private signer to different device
          (replacing old hardware wallet)
          (backing up, security refresh)
```

Day 27:
```
User: Realizes session key expires in 3 days
      Wants to rotate to new session key before expiry
      Initiates: "Create new session key" transaction
      
Wallet: Needs private signer signature to authorize new session key
        "Please sign with your private signer"
        
User: Goes to hardware wallet (new device)
      Imports private key (recovery process)
      "Signature confirmed"
      
Transaction submitted (needs private signer approval)
Time: Day 27, 2 PM
```

Day 27, 2:05 PM:
```
New session key creation: Mempool (pending)
Status: Waiting for inclusion (gas is normal, no urgency)

User: Continues normal activities with OLD session key
      (still valid for 3 more days)
      Makes purchases, interacts with dapps
      Sessions key is used normally
```

Day 27, 11 PM:
```
New session key creation: STILL pending (8 hours later)
Block space is expensive (network congestion)
Transaction fee: $50 (reasonable)

User: "Why isn't this confirming?"
Wallet: "Transaction is pending, should confirm in next block"
User: Waits
```

Day 28, 6 AM:
```
New session key creation: NOW confirmed
New session key: Is active
Old session key: Revoked (via contract update)

User: Happy, rotated session successfully
```

But wait... let's rewind to Day 27, 2:05 PM:

Day 27, 2:05 PM (Alternative Timeline):
```
New session key creation: Submitted
Status: Mempool pending

At SAME TIME:
User is using old session key to interact with dapp
Dapp: "Approve spending limit increase to $50k"
Session key: Signs the approval (it's still valid)

Transaction: Old session key is signing new approvals
Time: Day 27, 2:15 PM

Now we have:
  Tx 1: New session key creation (pending, not yet confirmed)
  Tx 2: Approval for $50k spending (signed by old session key, pending)
  Tx 3: User unknowingly uses old session key for other things
  
When Tx 1 confirms:
  New session key: Is now the ONLY valid signer
  Old session key: Should be revoked
  But: Approvals signed by old session key are still valid
  
Dapp has: $50k spending approval
Source: Old, revoked session key
Dapp: Can now spend $50k using old session key
(Because approval was signed before revocation happened)
```

Worse version:

Day 27, 2:05 PM:
```
New session key creation: Pending
Old session key: Still valid, used for daily spending

User: Hasn't realized what's happening
      Uses old session key normally

Day 27, 4 PM:
  Attacker: Watches mempool
  Sees: User's "new session key creation" pending
  Attacker: Quickly submits malicious transaction
  Malicious tx: "Approve spending of 100 ETH to attacker"
  Signed: With old session key
  
Both transactions: Pending in mempool
Ordering: Malicious approval could be included BEFORE session key update
  
If malicious approval is included first:
  Old session key signed it
  New session key creation confirms later
  But: Approval is already on-chain, from before revocation

Result: Attacker can use that approval forever
        User's old session key is compromised (but user doesn't realize)
        Attacker drains funds
```

**Why This Is NOT User Error:**

1. **User did the right thing:** Rotated session key before expiry
2. **Wallet design issue:** Session key revocation and approval management are not atomic
3. **UX claim violated:** "Non-custodial, you control all your funds"
   - User controls the session key rotation
   - But control is conditional on mempool ordering
   - User can't guarantee atomicity

4. **Normal behavior:** Approvals are issued all the time, this one just happened during rotation

**What Security Claim is Violated:**
> "Your funds are protected by session keys, you can rotate them securely"

→ **VIOLATED:** Session key rotation creates a window where old keys can still sign approvals that survive revocation

**Severity:** HIGH (specific timing required, but plausible)

---

## ATTACK 2: THE SOCIAL RECOVERY RACE CONDITION

**System:** Smart contract wallet with social recovery (Argent, loopring style)

**Claim:** "Lost your signer? Guardians can recover your account in 48 hours"

**Preconditions:**
- User has AA wallet with 3 guardians
- 2-of-3 guardians needed for recovery
- Recovery has 48-hour waiting period for security
- Guardians: Friend A, Friend B, Cold storage (hardware wallet)

**User Intent:**
- Normal usage for 1 year
- Security backup: Guardians are trusted

**What Goes Wrong:**

Year 1, Day 1:
```
User: Sets up wallet
      Designates guardians: Friend A, Friend B, Cold storage
      Sends 100 ETH to wallet
```

Year 1, Day 200:
```
Friend A: Changes phone, loses private keys
          No longer able to be a guardian
          
User: "I should update guardians"
      Initiates: Replace Friend A with new guardian (Friend C)
      
Wallet: "Guardian replacement requires 48-hour timelock"
        (same security as recovery)
        
User: Confirms replacement
      Transaction: Starts 48-hour timelock
      Current guardians: A, B, Cold storage
      Pending: Replace A with C
```

Day 200 + 12 hours:
```
Friend A: Now realizes private key is gone forever
          Panics
          Calls User: "I can't be a guardian anymore"
          
User: "It's ok, I'm replacing you anyway (timelock in progress)"
Friend A: (relieved)
```

Day 200 + 24 hours:
```
Timelock: Expires in 24 hours
Replacement: Friend A → Friend C
Current status: A, B, Cold storage can still do recovery
Pending: Replace A with C
```

Day 200 + 30 hours:
```
Timelock: Expired, replacement is confirmed
New guardians: C, B, Cold storage
Old guardian A: Officially removed

But: HERE'S THE TRAP:
Old guardian A: Lost keys, but still knows the account address
                If A's old key is recovered or leaked elsewhere...
                
Actually, let me re-frame this differently:
```

Day 200 (Alternative Attack):
```
Friend A & Friend B: Conspire (not realistic, but possible)
                     They want to steal the wallet
                     
They initiate: "Account Recovery"
              Claim: "User lost signer"
              
Wallet: "2-of-3 guardians must approve"
        A approves: ✓
        B approves: ✓
        C (cold storage): User should confirm or block
        
User: Gets notification: "Account recovery initiated"
      Realizes: "Wait, I didn't lose my signer!"
      Should block recovery: Calls friend C (cold storage guardian)
      
But here's the issue:
      Recovery has 48-hour waiting period
      During these 48 hours:
        User can initiate counter-recovery
        User can add new guardians
        User can disable recovery
        
So this attack doesn't work IF user is vigilant.
```

**Better version: The Automatic Guardian Revocation Attack**

Day 200:
```
User: Sets up wallet with guardians A, B, C
      Wallet feature: "Auto-remove guardians who haven't signed in 6 months"
      (Feature is enabled by default)
      
User: Takes vacation, forgets about this feature
      6 months pass
      
Month 7:
User: Returns from vacation
      Wallet: Has automatically removed Guardian C
      (No activity in 6 months, removed for security)
      
Current guardians: A, B
      
User: Doesn't realize C is gone
      Doesn't check guardian list
      
Month 8:
Guardian A & B: Conspire (or bribed by attacker)
                Initiate recovery
                
Wallet: "2-of-3 guardians needed"
        But C is already gone
        A & B: Can unilaterally recover
        
User: Gets recovery notification
      Expected to verify with 3 guardians
      But only 2 exist now
      
User might think: "This must be a scam, I haven't lost my signer"
                 "Ignore recovery notification"
                 
But: A & B can complete recovery anyway
     (They are the only guardians left)
     
User: Account is recovered
      New signer: Installed by A & B
      Original signer: Removed
      User is locked out
```

**Why This Is NOT User Error:**

1. **User didn't intentionally remove guardian C** - wallet did it automatically
2. **Default behavior was not visible** - auto-removal was enabled by default
3. **No reminder** - wallet never warned that a guardian was missing
4. **User trusted the system** - expected 3-of-3 protection, but only 2 remained

**What Security Claim is Violated:**
> "Guardians provide 48-hour recovery window, you can always block unauthorized recovery"

→ **VIOLATED:** If a guardian is silently removed (auto-revocation), recovery can happen with fewer guardians than expected, and user's block is ineffective

**Severity:** CRITICAL (silent removal of security, undetectable until attack)

---

## ATTACK 3: THE APPROVAL SCOPE CREEP

**System:** Wallet with per-app approval UX (permit-style, token approvals)

**Claim:** "You approve exactly what each app can spend, you're in control"

**Preconditions:**
- User uses DeFi wallet (MetaMask-like)
- User approves Uniswap: "Spend 100 USDC"
- User also approves different app: "Spend 100 USDC"
- Both approvals exist in the wallet

**User Intent:**
- Use Uniswap for one swap
- Use another app for separate transaction
- Control spending limits per app

**What Goes Wrong:**

Day 1:
```
User: Interacts with Uniswap
      Approves: "Uniswap can spend 100 USDC"
      Makes swap: 50 USDC → 100 ETH
      Remaining approval: 50 USDC
      
User: Is happy, leaves Uniswap
```

Day 5:
```
User: Wants to use Curve (different DeFi app)
      Approves: "Curve can spend 100 USDC"
      
Wallet: Shows two separate approvals:
        Uniswap: 50 USDC remaining
        Curve: 100 USDC
        Total: 150 USDC at risk
        
User: "That's fine, I trust both apps"
      Proceeds
```

Day 10:
```
Uniswap: Gets hacked / compromised
         Attacker gains access to Uniswap's smart contract
         
Uniswap: Can now spend the remaining 50 USDC from User
         (Original approval is still valid)
         
Attacker: Drains the 50 USDC
          
User: "Only 50 USDC lost, that's what Uniswap could spend"
```

But here's the hidden failure:

Day 1-5:
```
User: Is NOT told what happens to remaining approvals
      Approves: "100 USDC"
      Uses: 50 USDC
      Thinks: "50 USDC approval remains, but Uniswap won't use it without my transaction"
      
WRONG: Many dapps allow approve + automate later
       Uniswap could have a feature: "Schedule swaps"
       Or: "Automated yield farming"
       Or: "Emergency liquidity provision"
       
Uniswap uses remaining 50 USDC: Without user explicitly approving this transaction
                                 Because original approval allows it
                                 
User: Sees 50 USDC gone from wallet
      Confused: "I only did one swap"
      
What happened: Uniswap + some other service used the approval
               User never intended this
```

**Worse version: Approval Scope Aggregation**

Day 1:
```
User: Wants to provide liquidity on Uniswap
      Approves: "Uniswap can spend 1,000 USDC"
      Provides: 1,000 USDC + 1,000 USDT liquidity
      
User: Gets LP tokens
      Receives: Dividend yield, automatically reinvested
      
After 1 month:
User: Has 1,050 USDC + 1,050 USDT in liquidity
      LP position is still using original 1,000 USDC approval
      
User: Wants to withdraw liquidity
      Tries to remove LP tokens
      
Uniswap: "You've earned 50 USDC in fees"
         "This dividend is being auto-invested"
         "Your approval covers: 1,000 USDC"
         "Current approved but not yet used: 1,000 USDC"
         "Auto-investment is using: 50 USDC"
         
User: Approves withdrawal
      But: Auto-investment is still active
      Auto-investment automatically reinvests all future dividends
      
This continues: Until approval is exhausted or user manually stops
                User might not realize this is happening
```

**Why This Is NOT User Error:**

1. **User approved a spending limit** - expected it to be respected
2. **Approval UX didn't disclose** - what happens to remaining approval
3. **Automation features hidden** - user didn't know about auto-invest
4. **Normal dapp behavior** - reinvesting dividends is standard

**What Security Claim is Violated:**
> "You approve exactly what each app can spend, no more"

→ **VIOLATED:** Remaining approval can be used for purposes user didn't explicitly authorize (auto-invest, scheduled swaps, etc.)

**Severity:** MEDIUM (not permanent loss of control, but loss of fund predictability)

---

## ATTACK 4: THE GUARDIAN BRIBERY CASCADES

**System:** AA wallet with guardian-based recovery

**Claim:** "Guardians are trusted friends, they can help recover your account"

**Preconditions:**
- User has 5 guardians: 3 friends, 1 hardware wallet (family vault), 1 angel investor
- 3-of-5 guardians needed to recover
- User trusts all guardians with $50k+ decisions
- Angel investor's key is in a secure setup (not available for casual use)

**User Intent:**
- Guardians are security backup for key loss
- Trust guardians to act in user's interest

**What Goes Wrong:**

Month 1:
```
User: Sets up wallet with 5 guardians
      Large angel investment secured
      Guardians: 3 friends, 1 family, 1 angel investor
```

Month 6:
```
User: Makes a bad investment decision
      Invests $500k in shitcoin on their chain
      Position is now worth $50k (90% loss)
      
User: Panics, realizes mistake
      Can't undo on-chain transaction (it's finalized)
      
User: Calls guardians: "I made a mistake, can you help?"
```

Month 6 + 12 hours:
```
Friends' reaction to $500k loss:
  "We need to protect you from yourself"
  Friend A: "The signer is compromised by bad decisions"
            "We should recover the account"
            
User: "No, that's not necessary, I'll be more careful"
      "Don't recover"
      
Angel investor: Calls User
                "I noticed the shitcoin investment"
                "This is reckless, we're concerned"
                "Can we recover and manage the account?"
                
User: "No, I want to maintain control"
```

Month 6 + 24 hours:
```
User: Realizes a second problem
      Another investment: $200k locked in smart contract
      Contract has a bug, funds are frozen
      Recovery would require admin key
      
User: Panics
      Calls guardians: "Account is locked, I need recovery"
      
Friends: "OK, let's do recovery to fix the frozen funds"
         They initiate recovery
         User approves: "Yes, recover to fix the frozen funds"
         
Angel investor: Can access family vault (cold storage signer)
                Approves recovery with other friends
                
Recovery: Completes
New signer: Installed (controlled by angel investor + friends)
Original signer: Removed
```

Month 6 + 48 hours (After recovery):
```
User: Now has a different signer
      Angel investor's security team is now managing the account
      
User: "Can I have my signer back?"
Angel investor: "Your judgment is compromised, we'll manage it for now"
                "We're preventing further losses"
                
User: Objects, but:
      To get signer back, needs 3-of-5 guardians
      Friends are agreeing with angel investor
      Family vault (conservative) is also agreeing
      
User: Cannot recover their own account
      Guardians won't authorize recovery back to original signer
      (They believe they're protecting user's interests)
      
User: Is now locked out of their own account
      Under "protection" by guardians + angel investor
      
This is NOT malicious, it's "rational paternalism"
```

**Why This Is NOT User Error:**

1. **User did nothing wrong** - asked guardians for legitimate help
2. **Guardians acted rationally** - protecting user from bad decisions
3. **Recovery worked as designed** - completed successfully
4. **User expected to maintain control** - but guardians believed they knew better

**What Security Claim is Violated:**
> "You control your account, guardians are only for recovery from key loss"

→ **VIOLATED:** Once guardians control the account, user can't unilaterally recover it, even if user is not incapacitated

**Severity:** CRITICAL (permanent loss of control, even though user is capable)

---

## ATTACK 5: THE GAS ABSTRACTION HIDDEN COST

**System:** AA wallet with gas abstraction (paymaster)

**Claim:** "We handle gas costs, you just pay in your preferred token"

**Preconditions:**
- User has $5,000 USDC in wallet
- Wallet uses paymaster for gas abstraction
- Paymaster charges: 1% of transaction value
- User doesn't know about the 1% fee

**User Intent:**
- Send $5,000 USDC to friend
- Paymaster handles gas

**What Goes Wrong:**

Day 1:
```
User: Wants to send $5,000 USDC to friend
      Initiates: Send 5,000 USDC
      
Wallet UI: Shows:
           "Recipient: Friend"
           "Amount: 5,000 USDC"
           "Gas: Covered by paymaster"
           Button: "SEND"
           
User: Doesn't see fee disclosure
      Clicks: SEND
```

Day 1:
```
Transaction executes:
  User's wallet: -5,000 USDC
  Paymaster cost: -$50 (1% of 5,000)
  Total deducted: -$5,050 USDC
  
But user only had: $5,000 USDC
Transaction: FAILS (insufficient balance)
             
User: Confused
      "I have $5,000, why can't I send $5,000?"
      
Wallet UI: Shows error: "Insufficient balance"
           Doesn't explain: 1% fee
           
User: Tries again with $4,900
      Paymaster cost: $49
      Total: $4,949
      Still insufficient
      
User: Tries $4,500
      Paymaster cost: $45
      Total: $4,545
      Insufficient (only has $5,000)
      
User: Gets frustrated, tries $4,000
      Paymaster cost: $40
      Total: $4,040
      Finally sufficient!
```

Wait, that should work. Let me re-frame:

Day 1 (Better version):
```
User: Sends 5,000 USDC
      Paymaster adds 1% fee
      Total needed: 5,050 USDC
      User's balance: 5,000 USDC
      
Transaction: REVERTS
              Insufficient balance
              
User: Doesn't understand why
      Thinks: "I have 5,000, and I'm sending 5,000, why is there a fee?"
      
Alternative: Wallet abstracts the fee
              Silently deducts from recipient amount
              
User: Sends 5,000 USDC
      Wallet: Actually sends 4,900 USDC to friend
              1% paymaster fee is deducted
              
Friend: Receives 4,900 USDC
        User never knew the fee existed
        
User to friend: "I sent 5,000"
Friend: "I only received 4,900"
User: "That's not possible"
```

**More insidious version:**

Day 1:
```
User: Uses account abstraction wallet
      Paymaster fee: 1% of transaction value
      
User: Makes 10 transactions in a week
      Each transaction: Incurs 1% fee
      Total transactions: $50,000
      Total fees: $500
      
User: Doesn't realize cumulative impact
      Notices: "My balance is lower than expected"
      
User: Checks transaction history
      Sees: 10 transactions
      Doesn't see: 10 × 1% fees (totaling $500)
      
User: Blames: "I miscalculated my balance"
      Doesn't realize: Paymaster is taking $500/week
```

**Even worse: Fee structure changes mid-use**

Day 1-30:
```
User: Uses paymaster
      Fee: 1% of transaction value
      Paid: $50/week (approx)
```

Day 31:
```
Paymaster: Changes fee structure
           New fee: 2% + $10 flat
           
User: Has no notification about fee change
      Uses wallet as normal
      
Day 31, transaction 1:
  Transaction value: $1,000
  Fee: 2% + $10 = $30
  Total: $1,030
  
User: Doesn't notice the fee increased
      Transaction succeeds
      
Over next week:
User makes 5 transactions
Old expected cost: $50
New actual cost: ~$100
User's balance: Lower than expected
```

**Why This Is NOT User Error:**

1. **User approved wallet with paymaster** - expected transparent gas handling
2. **Fee was not visible** - UX didn't disclose 1% paymaster fee
3. **No notification of fee change** - user had no way to know
4. **Normal usage pattern** - user just sent money as expected

**What Security Claim is Violated:**
> "Wallet handles all gas costs, you control all your funds"

→ **VIOLATED:** Paymaster fees are hidden from user, reducing actual spending power without disclosure

**Severity:** MEDIUM (not permanent loss of control, but loss of transparency)

---

## ATTACK 6: THE WALLET UPGRADE SECURITY DOWNGRADE

**System:** Upgradeable AA wallet (proxy pattern)

**Claim:** "We improve your wallet with updates, your security never decreases"

**Preconditions:**
- User has AA wallet deployed 1 year ago
- Original implementation: Multisig (3-of-5) + social recovery (2-of-5 guardians)
- User has $500k in the wallet
- Wallet is upgraded 3 times over the year

**User Intent:**
- Wallet improves with updates
- Security stays the same or increases

**What Goes Wrong:**

Year 0:
```
User: Deploys AA wallet
      Security: 3-of-5 multisig + 2-of-5 guardian recovery
      
Implementation: v1.0
Version: Stored in wallet config
```

Month 3:
```
Wallet team: Releases v1.1
             New feature: Session keys
             Improvement: Lower transaction costs
             
User: Sees "Update available"
      Automatically upgrades
      
Implementation: v1.1
New capability: Session keys available
```

Month 6:
```
Wallet team: Releases v1.2
             New feature: Paymaster support
             Improvement: Pay gas in any token
             
User: Automatically upgrades
      
Implementation: v1.2
New capability: Paymaster support
```

Month 12:
```
Wallet team: Releases v2.0
             Major update: New architecture
             
Implementation changes:
  OLD: 3-of-5 multisig
  NEW: 2-of-3 multisig (simplified)
  
Reason: "Simpler is better, most users only have 2 hardware wallets anyway"
        "Reduces complexity, fewer bugs"
        
User: Auto-upgrades (default setting)
```

Month 12 + 1 day:
```
User: Still has 5 signers configured
      Wallet settings show: "5-of-5 multisig"
      
But: Implementation is now 2-of-3
     Only 3 of the 5 signers are active
     Other 2 signers are ignored by contract
     
User: Doesn't realize this happened
      Thinks: Still protected by 3-of-5
      Actually: Protected by 2-of-3 (one of 3 randomly selected)
      
Or worse: Only 2 signers are now active
          Any compromise of 2 signers = wallet is compromised
```

**Worse: Removing guardian recovery entirely**

Month 12:
```
Wallet v2.0: Removes social recovery feature
             Reason: "We're focusing on hardware signer only"
             "Guardian recovery is legacy"
             
User: Upgrades automatically
      Doesn't realize: Guardian recovery is gone
      
User: Still has 5 configured guardians
      Settings: "Guardian recovery enabled"
      
But: v2.0 contract has no guardian recovery code
     Guardians can't actually do anything
     If user loses hardware signers: Account is permanently lost
```

**Why This Is NOT User Error:**

1. **User expected security to stay the same** - upgrade shouldn't reduce security
2. **Auto-upgrade didn't require confirmation** - user didn't explicitly accept downgrade
3. **UI still showed old security model** - wallet config still showed 5 signers + recovery
4. **Wallet team decided unilaterally** - user had no choice in trade-off

**What Security Claim is Violated:**
> "Your security increases or stays the same with upgrades"

→ **VIOLATED:** v2.0 reduced effective security (3-of-5 → 2-of-3 or removed recovery entirely) without explicit user consent

**Severity:** CRITICAL (permanent loss of security guarantee, user can't undo)

---

## ATTACK 7: THE CROSS-CHAIN CONTROL DESYNC

**System:** AA wallet deployed on multiple chains

**Claim:** "Your account is the same across all chains, all funds are under your control"

**Preconditions:**
- User deploys AA wallet on Ethereum, Polygon, Arbitrum
- Wallet address is the same on all chains (via deterministic deployment)
- User has: $200k on Ethereum, $100k on Polygon, $50k on Arbitrum
- Signer setup is identical on all chains

**User Intent:**
- Control funds across all chains with same signer
- Upgrade wallet on all chains at once

**What Goes Wrong:**

Day 1:
```
User: Deploys AA wallet on all 3 chains
      Signer: Same on all chains
      Funds: Distributed across chains
```

Day 100:
```
User: Wants to upgrade wallet to new version
      Initiates: Upgrade on Ethereum
      
Ethereum upgrade: Successful
New implementation: v2.0
```

Day 100 + 1 hour:
```
User: Initiates upgrade on Polygon
      
Polygon upgrade: Successful
New implementation: v2.0
```

Day 100 + 2 hours:
```
User: Initiates upgrade on Arbitrum
      
Arbitrum upgrade: FAILS (technical issue)
                  (Different Arbitrum chain version, incompatible)
                  
User: Gets error message
      Tries to upgrade again
      Fails again
      
User: Decides: "I'll upgrade Arbitrum later"
               "Just using Ethereum and Polygon for now"
```

Day 110:
```
User: Receives alert: "Ethereum upgrade has vulnerability"
      Wallet team: "Please downgrade to v1.5"
      
User: Downgrades Ethereum wallet to v1.5
      
Now wallet versions are:
      Ethereum: v1.5
      Polygon: v2.0
      Arbitrum: v1.0 (original)
      
Signer setup: Same on all chains (in theory)
```

Day 115:
```
Problem discovered: 
  Ethereum v1.5 uses different signer encoding than Polygon v2.0
  When Ethereum signer tries to sign transaction on Polygon: FAILS
  
User: Tries to send funds on Polygon
      Signs with Ethereum hardware wallet
      Signature verification: FAILS (signature format mismatch)
      
User: Can't send funds on Polygon
      Stuck funds: $100k
      
User: Doesn't understand why
      Wallet shows: "Invalid signature"
      Wallet doesn't explain: Version mismatch between chains
```

**Even worse: Cross-chain guardian sync failure**

Day 1:
```
User: Sets up guardian recovery on all 3 chains
      Guardians: Same 5 people on all chains
```

Day 100:
```
User: On Ethereum, initiates: Replace Guardian A with Guardian C
      Timelock: 48 hours
      Current guardians on Ethereum: A, B, D, E (pending change to C)
```

Day 100 + 24 hours:
```
Guardian A (on Polygon): Gets hacked
                         Attacker gains access to A's signing key
                         
User: Panics, initiates on Polygon: Remove Guardian A
      Timelock: 48 hours
```

Day 100 + 48 hours:
```
Ethereum: Guardian A replacement finalizes
          New guardians: C, B, D, E
          Guardian A: Removed
          
Polygon: Guardian A removal finalizes
         New guardians: B, D, E (only 3 now)
         Guardian A: Removed
         
Arbitrum: Guardian A is still there
          (User hasn't initiated change yet)
          New guardians: A, B, D, E
```

Day 101:
```
Attacker (with compromised Guardian A key):
  Initiates recovery on Arbitrum
  2-of-4 guardians needed: Can get A + B (bribed or compromised)
  
Recovery: Starts on Arbitrum
User: Gets notification: "Recovery initiated on Arbitrum"
      Tries to block it
      
But: To block recovery on Arbitrum:
     Need to access and act on Arbitrum chain
     User's Arbitrum signing key: Still safe
     User can still block recovery
     
Actually works fine if user is monitoring...
     
Worse scenario: User doesn't monitor Arbitrum
                Recovery completes on Arbitrum
                New signer: Attacker's signer
                
User: Now has different signers on different chains
      Ethereum: Original signer (Guardian C backup)
      Polygon: Original signer
      Arbitrum: Attacker's signer
      
User: Doesn't realize Arbitrum is compromised
      Moves funds from Ethereum to Arbitrum
      Attacker: Steals funds on Arbitrum
      
User: Loses $200k (Ethereum transfer to Arbitrum)
```

**Why This Is NOT User Error:**

1. **User expected same wallet across chains** - claim was "same account, same control"
2. **Version mismatch wasn't user's problem** - wallet team should manage versions
3. **Cross-chain sync wasn't user's responsibility** - wallet should sync automatically
4. **Arbitrum failure wasn't intentional** - user didn't choose to skip Arbitrum upgrade

**What Security Claim is Violated:**
> "Your account is the same across all chain, unified control"

→ **VIOLATED:** Wallet versions diverge across chains, causing signature mismatches, guardian sync failures, and split-brain security model

**Severity:** CRITICAL (funds can be stolen through cross-chain desync)

---

## ATTACK 8: THE EMERGENCY DISABLE PERMANENCE

**System:** AA wallet with emergency disable feature

**Claim:** "If your wallet is compromised, disable it immediately and recover safely"

**Preconditions:**
- User has AA wallet with emergency disable button
- Disable: Freezes the wallet, prevents all transactions
- Recovery: Takes 48 hours, requires guardians
- User has 2 hardware signers, 3 guardians

**User Intent:**
- Security feature for emergencies
- Can undo if it was a mistake

**What Goes Wrong:**

Day 1:
```
User: Notices suspicious transaction in mempool
      "Someone is trying to drain my wallet"
      Panics: "I need to disable immediately"
      
Clicks: Emergency Disable button
Status: "Wallet disabled, recovery takes 48 hours"
```

Day 1 + 10 minutes:
```
User: Realizes: "Wait, that might not have been a real attack"
                "That was just gas estimation, not a real drain"
                
User: Wants to undo: Clicks "Recover from disabled state"
      
Wallet: "Recovery takes 48 hours, requires 2-of-3 guardians"
        "You can't cancel recovery once initiated"
        
User: Thinks: "That's fine, I'll just approve it with guardians"
              "Takes 48 hours to recover anyway"
```

Day 1 + 48 hours:
```
Recovery: Completes
Wallet: Is now in "recovered" state
        New signer: User's backup signer
        
User: Is now using backup signer
      Original signer: Still there, but in "disabled" state
      
User: Wants to switch back to original signer
      Realizes: Recovery can't be undone quickly
      
Takes: Another 48 hours + more guardians
```

**Worse: Emergency disable during time-sensitive transaction**

Day 1, 2 PM:
```
User: Has a time-sensitive opportunity
      DeFi yield: Available for 24 hours only
      Needs to approve and execute transaction
      
User: Clicks approve button on MetaMask
```

Day 1, 2:05 PM:
```
Transaction: Pending in mempool
            User is waiting for confirmation

User: Notices wallet showing suspicious activity
      Panics: Thinks account is compromised
      Emergency disables wallet
      
Wallet: Disabled immediately
Status: All pending transactions are cancelled
```

Day 1, 2:10 PM:
```
DeFi opportunity: LOST (transaction was cancelled)
Yield opportunity: Window has closed
User: Lost potential $10k gain

User: Realizes: Panic disable was a mistake
                No actual compromise happened
                Just paranoia from suspicious activity
                
User: Initiates recovery
Time: 48 hours to recover
```

Day 3:
```
Recovery: Completes
Wallet: Is now active again
DeFi opportunity: Long gone (expired 24 hours ago)
```

**Why This Is NOT User Error:**

1. **User acted on legitimate security concern** - suspicious activity in mempool
2. **Emergency disable is irreversible for 48 hours** - UX doesn't make this clear
3. **False positive caused real damage** - user's fear was reasonable
4. **Recovery doesn't address the problem** - original signer is still valid, just disabled

**What Security Claim is Violated:**
> "Emergency disable is reversible, you can recover your account anytime"

→ **VIOLATED:** Recovery takes 48 hours, during which user is locked out and can't undo the panic action

**Severity:** MEDIUM (doesn't cause permanent loss, but time-critical value loss)

---

## SUMMARY: UX-SECURITY ATTACK PATTERNS

| Attack | Mechanism | Impact | Severity |
|--------|-----------|--------|----------|
| **Session expiry trap** | Old approval survives key rotation | Funds stolen by old dapp | HIGH |
| **Social recovery race** | Guardian auto-removal enables cartel | Permanent loss of control | CRITICAL |
| **Approval scope creep** | Remaining approval used for auto-invest | Unexpected fund usage | MEDIUM |
| **Guardian bribery cascade** | Guardians act paternalistically | User locked out by guardians | CRITICAL |
| **Gas abstraction hidden cost** | Paymaster fee not disclosed | Fund balance mismatch | MEDIUM |
| **Wallet upgrade downgrade** | v2.0 reduces effective security | Reduced security guarantee | CRITICAL |
| **Cross-chain desync** | Different versions on different chains | Funds locked, signature mismatch | CRITICAL |
| **Emergency disable permanence** | 48-hour recovery for panic disable | Time-critical opportunities lost | MEDIUM |

---

## UNCOMFORTABLE TRUTHS

**Statement 1:**
> "Non-custodial means 'you hold the keys', not 'you understand the consequences'"

**Statement 2:**
> "Guardian recovery is elegant in theory, but creates a new custodian: the social network"

**Statement 3:**
> "Session keys solve timeliness, but create approval windows that aren't atomic"

**Statement 4:**
> "Gas abstraction is great UX, but hidden fees are a security boundary that's never tested"

**Statement 5:**
> "Wallet upgrades always come with assumptions: 'user will notice if security changes' ← false"

**Statement 6:**
> "The only wallet security that works across chains is: don't use multiple chains, or assume they'll desync"

---

## WHAT MAKES THESE DIFFERENT FROM PHISHING

- **No social engineering:** User isn't tricked into revealing keys
- **No malware:** No malicious code on user's device
- **No private key compromise:** User's signing keys are still secure
- **Protocol is working correctly:** All features function as designed
- **User behaves reasonably:** Normal usage patterns trigger the failures

Yet user loses control or funds.

**This is why it's a UX-security problem, not a code problem.**

