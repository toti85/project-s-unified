# RED TEAM: CELESTIA DA SYSTEMIC FAILURES
## Non-Obvious, High-Impact Failure Modes

**Mode:** Hostile protocol research (NOT code bugs, NOT bounty submissions)  
**Focus:** Systemic collapse scenarios triggered by Celestia architecture  
**Time Budget:** 2-4 hours  
**Goal:** Make protocol teams uncomfortable

---

## HYPOTHESIS 1: ARCHIVAL PROVIDER AS A WEAPON (Cartel/Monopoly)

**The Setup:**
- Celestia has ~3-5 major archival providers (QuickNode, Ankr, Lava, etc.)
- Rollups MUST use them (running full Celestia nodes is expensive)
- Providers notice: rollups have ZERO alternatives after 7 days
- Providers realize: they have absolute pricing power

**Attack Narrative: "The Archival Squeeze"**

```
Timeline:
  Week 1:   Rollup A launches on Celestia, syncs historical data via QuickNode
  Week 2:   Rollup A grows, archival traffic increases
  Week 2.5: QuickNode begins raising fees: $0.01/GB → $0.05/GB (5x)
  Week 3:   Rollup A's validator nodes need to reconstruct state
            Cost for 7 days of data: $10k/week → $50k/week
            Rollup margin: ~$100k/week
            Profit margin collapses from 30% → 5%
  Week 4:   QuickNode notices: Rollup A is now dependent, can't leave
            Sends ultimatum: "Upgrade to premium tier ($100k/month) or we deprioritize your requests"
            Rollup A pays. No choice.
  Week 8:   QuickNode repeats with Rollup B, C, D...
            All paying premium pricing
  Month 3:  New rollup E launches, refuses to pay premium
            QuickNode "degrades service" (adds latency to E's requests)
            When rollup E's fraud challenge arrives, recovery takes 15 hours instead of 3
            Challenge window: 12 hours. Rollup E misses deadline.
            Fraudster's claim is accepted as canonical.
            Rollup E is bankrupt.
```

**Numeric Example:**
```
Rollup A monthly archival cost: 
  - Normal market: 7 days of history × 30 GB/day × $0.01/GB = $210/month
  - Squeezed market: Same data × $0.10/GB × 2-3x "priority premium" = $2,100-$6,300/month
  
Rollup A's revenue:
  - 1000 TPS × $0.10 fee = $100/sec = $8.6M/month
  - Gross margin: 30% = $2.6M/month
  - Archival cost creep: $210 → $6,300 (30x spike)
  - Net margin impact: 0.2% of revenue
  
For rollups with lower volume (100 TPS): archival cost > profit margin entirely
```

**Why this is NOT a bug but breaks the system:**
- Providers are rational profit-maximizers
- No protocol rule prevents selective pricing
- Rollups signed up knowing archival is market-dependent
- But: system-wide rollup economics collapse
- Viable rollups get squeezed out or centralize (only wealthy projects survive)
- Celestia becomes "accessible to the rich only"

**Escalation: Coordinated Cartel**
```
What if the 3 major providers coordinate?
  - They collectively decide: "All new rollups pay $50k/month minimum"
  - Existing rollups: subject to 3x pricing increases
  - Rollups have no escape: can't use Ethereum (too expensive), can't use Polygon (not decentralized enough)
  - Celestia's value proposition collapses: "free DA for rollups" becomes "pay our cartel or die"
```

---

## HYPOTHESIS 2: LIQUIDATION DOS VIA ARCHIVAL PRICING SPIKE

**The Setup:**
- Lending protocols on rollups (e.g., Compound on OP Stack on Celestia)
- Liquidators need historical price data to verify collateral
- Archival retrieval cost is normally negligible ($<1)
- Attacker can trigger network congestion and archival pricing spike

**Attack Narrative: "The Liquidation Trap"**

```
Setup:
  Attacker deposits $10M of correlated collateral (e.g., stETH)
  Adds 100x leverage
  Exposes the protocol to $1B liquidation scenario
  
Day 0:
  Protocol is healthy. Liquidation market works.
  Liquidation cost: $100 (archival retrieval) + slippage
  Liquidation profit: $500k (1% of $50M position)
  
Day 1 (Market Moves):
  ETH price drops 15%
  Attacker's position becomes liquidatable
  
Day 1 - 2PM (Attack Begins):
  Attacker: submits 1000 spam transactions to Celestia
  Fills blockspace, triggers network congestion
  (Legitimate-looking: just appears as normal activity spike)
  
Day 1 - 2:05PM (Archival Effect):
  Archival node operators see fee spikes incoming
  Increase retrieval pricing: $0.01/GB → $1/GB (100x)
  Announcement: "Network congestion fee multiplier: 100x"
  
Day 1 - 2:10PM (Liquidation Fails):
  Liquidators try to trigger liquidation
  Need to verify collateral via historical price feeds
  Archival retrieval cost: $100 → $10,000
  Liquidation profit: $500k
  Liquidation cost: $10k (retrieval) + slippage = still profitable?
  
  BUT: Multiple liquidations compete for same archival bandwidth
  Each additional liquidation costs another $10k
  First 50 liquidations consume $500k
  Cost exhausts profit pool
  Remaining 950 liquidations at risk
  
Day 1 - 2:15PM (Cascade):
  Liquidators back off (economics no longer work)
  Position remains undercollateralized
  
Day 1 - 3PM (Clean Up):
  Attacker cancels spam transactions
  Network congestion clears
  Archival fees normalize
  But position has already decayed
  Attacker's position is now worth $200M (down from $300M)
  Instead of $100M loss, only $100M loss to leverage
  
Day 1 - 4PM (Repeat):
  Next opportunity: attacker repeats with 5x leverage
  Eventually: attacker extracts value through repeated denial-of-service
```

**Numeric Reality:**
```
Attack cost: 1000 spam txs × $0.01/tx = $10 (on Celestia)
Benefit: Delays liquidations for 1 hour
Attacker's position avoids $500k loss through that delay
ROI: 50,000x
```

**Why this is NOT a bug but breaks the system:**
- Attacker doesn't steal funds (not a hack)
- Network is technically working (congestion is "normal")
- Archival pricing is "correct" (market-responsive)
- But: lending protocol's liquidation model breaks
- Risk model assumes "liquidators can always act quickly"
- Attacker weaponizes that assumption

---

## HYPOTHESIS 3: SEQUENCER CENSORSHIP BECOMES PERMANENT IF DA FAILS

**The Setup:**
- OP Stack (or similar) uses Celestia for DA
- Sequencer is centralized (common in OP Stack v2)
- Sequencer can censor transactions (exclude from blocks)
- DA proves transaction existed (prevents censorship escaping notice)
- If DA recovery fails, censorship becomes undetectable and permanent

**Attack Narrative: "The Censorship Trap"**

```
Setup:
  User is a whale with tokens in rollup
  User wants to withdraw $50M to mainnet
  Sequencer operator is run by entity X
  Entity X competes with User in DeFi
  
Day 0 (The Censorship):
  User: submits withdrawal transaction to rollup sequencer
  Sequencer operator sees transaction in mempool
  Entity X: "This withdrawal is bad for us, let's censor it"
  Sequencer: Builds blocks WITHOUT the withdrawal
  Users can verify: "My txn is on Celestia DA"
  Proof exists: DA light node confirms txn is there
  
Day 1 (Challenge Emerges):
  User: "My withdrawal is censored, I can prove it on DA"
  Sequencer: "Fine, we'll include it"
  Sequencer adds withdrawal to block (seems resolved)
  
Day 2-6 (Data Exists, Within Archival Window):
  Everything is fine, DA is queryable
  User can always go to fraud proof if needed
  
Day 7 (The Trap Activates):
  7-day archival window closes
  Old data is pruned from light nodes
  Archival provider goes offline (or raises prices to $100k)
  
Day 8+ (Permanent Censorship):
  User no longer has access to original censored transaction
  DA is "proven" to exist, but unrecoverable
  If sequencer never included withdrawal, there's no proof that sequencer censored it
  If sequencer claims "we included it but you missed it", user can't prove otherwise
  
  Withdrawal is permanently lost.
```

**Why this is NOT a bug:**
- Sequencer was always trusted to order transactions (by design)
- DA works correctly (proved data exists)
- Archival is market-dependent (as documented)
- Each component works as intended
- But: The combination breaks the invariant "censorship is detectable and reversible"

**Escalation: Censorship-as-a-Service**
```
Sequencer operator realizes: "We can censor transactions, wait 7+ days, then act innocent"
Business model: Offer to "remove competitor's transactions" for a fee
Charging $10k to censor a withdrawal
Victim has no recourse after day 7
```

---

## HYPOTHESIS 4: ROLLUP ECONOMIC TRAP (Forced Pricing Dependency)

**The Setup:**
- Rollup launches on Celestia with low initial archival costs
- Early adopters get locked in via ecosystem effects
- After 7 days, rollup realizes archival costs are non-negotiable
- Rollup is now trapped with archival provider

**Attack Narrative: "The Bait-and-Switch"**

```
Month 0 (Launch):
  Rollup launches on Celestia
  Archival cost estimates: $100/month (trivial)
  Business plan: Celestia gives us "free or cheap DA"
  Revenue model: $10M/month (high volume, small fees)
  
Week 2:
  Rollup has $500M TVL
  Day 7 archival window is approaching
  Rollup needs to make decision: run own archival or use provider
  
Week 3 (The Realization):
  Cost to run own Celestia archival node: $50k/month infrastructure + $20k/month operator
  Cost to use external archival: starts at $200/month, but...
  Fine print: "Pricing subject to change based on market conditions"
  
Month 2 (The Squeeze):
  Network grows, archival usage increases
  Archival providers notice: all rollups are now dependent
  QuickNode raises fees: $200/month → $2k/month (10x)
  
Month 3:
  Rollup A is paying $2k/month and it's sustainable
  Rollup B is paying $2k/month, but it's tight
  Rollup C: "This is unsustainable, we'll run our own nodes"
  
  Cost reality: Running own nodes costs $70k/month
  Rollup C can't afford it
  Rollup C is stuck at $2k/month provider pricing
  
Month 4:
  Major provider (QuickNode) gets acquired by entity X
  Entity X sees: all Celestia rollups depend on us now
  Pricing becomes: $5k/month, take it or leave it
  (Or get deprioritized, slow service, unreliable SLA)
  
  Rollups are trapped. No good options.
  Some rollups migrate to Ethereum L1 (defeats Celestia value prop)
  Some pay premium pricing (reduces competitiveness)
  Some rollups fail (can't maintain economics)
```

**Why this is NOT a bug:**
- Celestia works fine, publishes data correctly
- Archival is market-dependent (disclosed)
- Providers are rational (economics are sound)
- But: Celestia's value prop ("cheap DA") only holds for ~7 days
- After that, rollups face permanent forced monopoly pricing
- Long-term adoption is damaged by this economics

---

## HYPOTHESIS 5: FINALITY COLLAPSE (Challenge Window + Archival Failure)

**The Setup:**
- OP Stack uses fraud proofs + Celestia DA for security
- Fraud challenger needs original data to construct proof
- If DA recovery fails, fraud proofs can't be generated
- Optimistic assumption ("challenger can always prove fraud") breaks
- Security model collapses

**Attack Narrative: "The Unchallengeable Fraud"**

```
Setup:
  OP Stack rollup on Celestia
  Fraud challenge window: 7 days
  
Day 0:
  Sequencer/proposer submits false state root
  Proposes: "Account X has balance $100M" (false)
  Reality: Account X has balance $1M
  Proposer has stolen $99M through state manipulation
  
Day 1-6:
  Challenger can see DA data
  Can reconstruct blocks and generate fraud proof
  Proposer can't escape accountability
  
Day 6.5:
  Proposer realizes fraud was detected
  Tries to trigger archival failure:
    - Buys out QuickNode, shuts down historical retrieval
    - Triggers network congestion to spike archival fees to $1M
    - Coordinates with other providers to go offline
  
Day 7:
  Challenge window closes
  State root is finalized
  Challenger can no longer generate fraud proof (no data access)
  
Day 8+:
  Fraud is now canonical
  Proposer has successfully stolen $99M
  Challenger has no recourse
  Users have no way to recover
  Rollup is insolvent
```

**Why this is NOT a bug:**
- DA proved the data (light nodes saw it)
- Challenge window operated as designed
- Archival is market-dependent (disclosed)
- But: The finality guarantee breaks
- Assumption "fraud can be proven" is false
- Optimistic rollup security model collapses

**Severity: CRITICAL**
```
This is worse than a hack because:
- You can't detect the fraud (no access to proof)
- You can't compensate users (they're locked in)
- You can't recover the rollup (state is poisoned)
- It's technically "working as designed" but security is broken
```

---

## HYPOTHESIS 6: CORRELATED ROLLUP FAILURE (Bank Run on Archival)

**The Setup:**
- Multiple rollups use Celestia (OP Stack, Arbitrum, custom rollups)
- All depend on the same 3-5 archival providers
- If one rollup fails to recover data, it signals archival infrastructure is failing
- Triggers panic across all rollups
- Bank run on archival services

**Attack Narrative: "The Cascade"**

```
Day 0:
  Rollup A gets hit with large fraud challenge
  Rollup A tries to recover 7-day historical data
  Archival provider is slow/overloaded
  Recovery takes 15 hours (challenge window is 12 hours)
  Rollup A: Fails to respond to challenge
  Fraudster's claim is accepted
  Rollup A loses $100M TVL, insolvent
  
Day 1:
  News spreads: "Celestia rollup failed because archival data is unreliable"
  Rollup B notices: Same archival provider, same risk
  Rollup B's users see the news
  Fear: "If Rollup A lost $100M to archival failure, am I next?"
  Users start withdrawing from Rollup B
  
Day 2:
  Run starts on archival providers
  Rollups compete for priority access
  Providers raise fees 10x (emergency pricing)
  All rollups experience degraded archival service
  All rollup users panic
  Mass exodus from Celestia rollups
  
Day 3:
  Cascading insolvencies
  Rollup B, C, D fail due to archival unavailability
  Rollup E tries to migrate to Ethereum L1
  (Realizes Ethereum is too expensive, fails anyway)
  
Day 4:
  Celestia DA is technically fine (light nodes still work)
  But: All dependent rollups are dead
  Celestia is now "DA layer with no rollups"
  Value collapse
```

**Numeric Trigger:**
```
Rollup A failure event: 1 rollup × $100M TVL = $100M loss
Probability of contagion: ~50% (market assumes infrastructure is shared)
Correlated loss across ecosystem: 5 rollups × $200M TVL × 50% = $500M ecosystem loss
```

**Why this matters:**
- Individual rollup failure is contained risk
- Correlated failure across multiple rollups is systemic
- Triggers loss of confidence in entire DA layer
- Not a "bug" but an incentive misalignment: archival infrastructure is not dimensioned for correlated demand spikes

---

## HYPOTHESIS 7: INSURANCE MODEL COLLAPSE (Risk Pricing Was Wrong)

**The Setup:**
- Rollups buy insurance against "DA availability risk"
- Insurance companies price policy assuming "DA is 99%+ reliable"
- Pricing is set low because DA is "proven by light nodes"
- Insurance doesn't cover archival infrastructure failure (considered "act of god")

**Attack Narrative: "The Insurance Gap"**

```
Insurance company (Nexus Mutual, etc.):
  Prices Celestia DA insurance at 0.1% annual premium
  Assumes: "DA never fails, risk is negligible"
  Sells $100M in coverage to rollups
  Expected payout: near zero
  
Rollup A loses $100M to archival failure
  Files insurance claim: "DA infrastructure failed"
  Insurance denies: "Archival nodes are your responsibility, not ours"
  Fine print: "We cover cryptographic failures only"
  
Rollup A gets $0 payout
  Rollup A is now insolvent
  Users lose $100M
  Insurance company keeps premiums (collected on $100M coverage)
  Insurance company profit: $100k/year free money
  
Market impact:
  Insurance products for Celestia DA become worthless
  No insurance company will cover rollups on Celestia
  Rollups now carry full risk (uninsurable)
  Risk of catastrophic loss is now clearly visible
  Users lose confidence in Celestia rollups
```

**Why this is NOT a bug:**
- Insurance company was explicit: "Archival is not covered"
- Risk model was disclosed
- But: The risk was underpriced because everyone assumed "archival won't fail"
- When it does fail, the system has no safety net
- Uninsurable tail risk becomes visible and collapses adoption

---

## HYPOTHESIS 8: CHALLENGE WINDOW GAMING (Weaponized Timing)

**The Setup:**
- OP Stack fraud challenge window is rigid (e.g., 7 days)
- Fraudster can time the challenge submission to maximize recovery difficulty

**Attack Narrative: "The Perfect Crime"**

```
Friday 2 PM (Fraud Committed):
  Proposer submits false state root
  Everyone is busy with end-of-week
  
Friday 3 PM (Strategy):
  Challenger sees fraud and prepares fraud proof
  But: Challenger knows recovery will take time
  Challenger: "Let me wait and see what the proposer does"
  
Saturday-Sunday (Waiting):
  Proposer has 7 days to prepare
  Proposer's game: "Wait until day 6.5, assume archival infrastructure is under stress"
  
Monday 5 PM (Day 6.5 - Challenge Submitted):
  Fraud challenge submitted: "Prove this state root is correct"
  This is Tuesday evening for Western teams, Wednesday morning for Asia
  
Monday 5:05 PM (Archival Attack):
  Proposer: triggers network congestion (spam transactions)
  Archival fees spike 100x
  Data is technically available but pricing is now $500k per GB
  
Tuesday 2 AM (Recovery Attempt):
  Challenger wakes up (it's Wednesday morning in Asia)
  Tries to recover data for fraud proof
  Cost: $5M
  Time: 15 hours (challenge window is 12 hours)
  
Tuesday 2 AM (Conclusion):
  Challenger cannot afford recovery ($5M > fraud bounty of $1M)
  Challenger times out
  Fraudster's claim is accepted
  Proposer has successfully committed theft
```

**Weaponized timing elements:**
```
1. Time of submission: Friday (fewer engineers on call)
2. Geographic timing: Asian morning (timezone advantage)
3. Coincidence with network congestion: Coordinated with MEV bot spam
4. Archival provider is friendly: Slow responses to "emergency" requests
```

**Why this is NOT a bug:**
- System works as designed
- Fraud challenge window is enforced
- Archival is market-responsive
- But: Timing asymmetry favors fraudsters
- Proposer has information advantage (knows challenge deadline)
- Can trigger archival failure at strategic moment
- Challenger is at permanent disadvantage

---

## HYPOTHESIS 9: THE EXTORTION MODEL (Pay or Die)

**The Setup:**
- Rollup has $500M TVL on Celestia
- Archival infrastructure is controlled by entity X
- Entity X realizes: rollup is completely dependent

**Attack Narrative: "Protection Racket"**

```
Week 1:
  Entity X: Acquires majority stake in QuickNode (Celestia archival provider)
  Or: Coordinates with existing providers
  
Week 2:
  Entity X approaches Rollup A operator
  Entity X: "Your rollup depends on archival infrastructure"
  "Current provider (QuickNode) has pricing power"
  "If we choose to raise rates or go offline, you lose everything"
  "We can offer protection... for a fee"
  
Week 3:
  Entity X offers: "Premium archival SLA: guaranteed uptime, capped pricing"
  Cost: $500k/month (or 1% of weekly revenue)
  "Competitors aren't getting this offer yet"
  
Week 4 (The Threat):
  Rollup A declines the offer
  Entity X: Acquires another archival provider
  Now controls 2 out of 3 major providers
  Entity X: "Your archival will have degraded service starting tomorrow"
  Implement: Latency + rate limiting
  Rollup A's users experience slow withdrawals
  Users panic, start exiting
  
Week 5:
  Rollup A's TVL drops to $300M (users leaving)
  Entity X: "The price just went up to $1M/month"
  Rollup A: "This is extortion"
  Entity X: "We call it market pricing"
  
Week 6:
  Rollup A pays $1M/month to keep lights on
  Or: Rollup A collapses
  Rollup B, C, D all face same ultimatum
  All paying extortion fees
  Entity X is now the gatekeeper for all Celestia rollups
```

**Numeric Reality:**
```
Entity X's profit model:
  - Buy 2 archival providers: $50M (acquisition cost)
  - Implement pricing: $500k/month per rollup
  - Assume 5 major rollups pay: $2.5M/month = $30M/year
  - ROI: 60% annually (breaks even in 2 years, then pure profit)
  - Upside: If rollups collapse, buy them out at bankruptcy prices
```

**Why this is NOT a bug:**
- Archival is market-dependent (disclosed)
- Providers are allowed to raise prices (capitalism)
- Rollups chose to use Celestia (informed choice)
- But: System creates natural monopoly in archival
- Creates protection racket economics
- Celestia's "decentralization" claim is compromised

---

## HYPOTHESIS 10: SHARED SEQUENCER CENSORSHIP ACROSS MULTIPLE ROLLUPS

**The Setup:**
- Multiple rollups use a shared sequencer (e.g., MEV-Boost-style)
- Sequencer is run by entity X
- Entity X has economic incentives in DeFi
- Shared sequencer can censor transactions across multiple rollups simultaneously

**Attack Narrative: "The Shared Sequencer War"**

```
Setup:
  Shared sequencer runs on top of Celestia
  Sequencer is operated by venture capital firm VC Corp
  VC Corp also owns stakes in DeFi protocols (Aave, Curve, Compound)
  
Day 0 (The Strategy):
  Competitor launches competing protocol on OP Stack (also using same shared sequencer)
  VC Corp: "We can censor transactions on the competing protocol"
  Plan: Censor all transactions for competing protocol for 7 days
  Let DA capture transactions, but sequencer never includes them
  
Day 1-7:
  Competing protocol's transactions are on Celestia DA
  But sequencer doesn't finalize them
  Transactions are stuck in mempool indefinitely
  Users can't interact with competing protocol
  
Day 7 (Archival Failure):
  VC Corp triggers archival failure (buys it out, goes offline)
  Original transactions are no longer recoverable
  
Day 8+ (Censorship is Permanent):
  Competing protocol is permanently broken
  Transactions were censored, but evidence is gone
  VC Corp: "We never censored anything, archival was just unavailable"
  Impossible to prove otherwise
  
Result:
  Competing protocol is dead
  VC Corp's investments are now worth more
  VC Corp made a $100M-$1B profit through censorship + archival manipulation
```

**Why this is NOT a bug:**
- Shared sequencer was always trusted (by design)
- DA works correctly (proved transactions exist)
- Archival failure is market-dependent
- But: Sequencer gets weaponized against competing protocols
- Creates oligopoly at the sequencer layer
- Celestia DA doesn't protect against sequencer capture

---

## META-ANALYSIS: What Makes These Attacks Uncomfortable?

**Pattern 1: Responsibility Gaps**
- Celestia: "We provide DA"
- Archival: "Market will handle it"
- Rollups: "We'll rely on archival"
- Users: "Someone will keep my data safe"
- **Reality:** When all layers shift responsibility, nobody is accountable

**Pattern 2: Economics Inversion**
- Design assumption: "Competition keeps archival prices low"
- Reality: "Only 3-5 providers → natural monopoly → cartel pricing"
- Design assumption: "Rollups can migrate away"
- Reality: "After 7 days, switching cost is so high, rollups are trapped"

**Pattern 3: Time Horizons Mismatch**
- Celestia: Proves data for 7 days
- Fraud challenges: Need data for 7+ days (edge case)
- Rollups assume: "7 days is forever" (it's not)
- Market realizes: "Day 8 onwards is unprotected"

**Pattern 4: Uninsurable Risk**
- Insurance assumes: "Archival infrastructure is reliable"
- Reality: "Archival is a single point of failure"
- When failure happens: "Insurance doesn't cover it"
- Result: "No one will insure Celestia rollups"

**Pattern 5: Information Asymmetry**
- Celestia documents: "Archival is market-dependent"
- Rollups understand: "This means variable pricing"
- Rollups don't expect: "Providers can coordinate on pricing"
- Providers realize: "We can raise prices 10x, rollups have no escape"

---

## SUMMARY: 10 SYSTEMIC FAILURE MODES

| ID | Attack | Trigger | Impact | Exploitability |
|:--|:--|:--|:--|:--|
| 1 | Archival Cartel | Provider coordination | Rollup economics collapse | EASY (natural monopoly) |
| 2 | Liquidation DoS | Pricing attack + congestion | Lending protocol broken | MEDIUM (requires coordination) |
| 3 | Sequencer Censorship | DA recovery failure + censorship | User funds trapped | EASY (built-in sequencer power) |
| 4 | Economic Trap | Forced dependency after 7 days | Rollup margins squeezed | INEVITABLE (design flaw) |
| 5 | Finality Collapse | Challenge window + archival failure | Fraudsters escape | MEDIUM (requires timing) |
| 6 | Correlated Failure | Bank run on archival | Ecosystem collapse | HIGH (cascade effect) |
| 7 | Insurance Collapse | Risk mispricinig | Uninsured tail risk | HIGH (no one will insure) |
| 8 | Challenge Timing | Weaponized timing + congestion | Fraud becomes canonical | MEDIUM (requires coordination) |
| 9 | Extortion Model | Archival provider monopoly | Protection racket economics | INEVITABLE (incentive-driven) |
| 10 | Shared Sequencer War | Multi-rollup censorship | Protocol competition broken | MEDIUM (requires sequencer capture) |

---

## UNCOMFORTABLE TRUTHS

**Statement 1:**
> "Celestia's DA works perfectly. But the system around it (archival + rollups + challenge windows) is NOT designed to handle coordinated attacks on responsibility gaps."

**Statement 2:**
> "The 7-day pruning window is not a security choice; it's an admission that Celestia cannot guarantee long-term availability. Everything beyond day 7 is a rollup's problem."

**Statement 3:**
> "Rollups that think they're 'secured by Celestia' are actually secured by 'random market providers who can leave at any time.' That's a difference in kind, not degree."

**Statement 4:**
> "The only rollups that will survive on Celestia are ones that can afford $1M+/month in archival infrastructure. This means Celestia becomes 'DA for the wealthy only.'"

**Statement 5:**
> "If a shared sequencer + Celestia DA + challenge windows get captured by a single entity, that entity can censorship-proof fraud indefinitely. Celestia's DA doesn't prevent this."

---

## RECOMMENDATIONS FOR PROTOCOL TEAMS

**For Celestia:**
1. Explicitly document archival as "non-guaranteed" in threat model
2. Create protocol-level slashing for archival node unavailability (if you want to guarantee it)
3. OR: Accept that long-term DA is a rollup responsibility, not Celestia's

**For OP Stack (and Rollups):**
1. Make challenge windows < 7 days to stay safe (currently 7 days is edge case)
2. Run own archival infrastructure if economically viable
3. OR: Accept that you are now dependent on archival cartel pricing
4. Insurance: Explicitly exclude archival failure (it's tail risk, won't be insured)

**For Users:**
1. Understand that "using Celestia rollup" means "trusting archival infrastructure market"
2. If rollup migrates to different archival provider, your safety margin decreases
3. Best safety: Use rollups with < 1 day challenge window + owned archival nodes

---

## NEXT STEPS

**Due Diligence Questions (Before Immunefi Submission):**
1. Are any of these hypotheses already known to Celestia/OP Stack?
2. Have auditors (Certora, Trail of Bits, etc.) covered these scenarios?
3. Are they considered "acceptable trade-offs" (not bugs)?
4. Is the research novel or just better articulation of known limitations?

**If submitting:** Frame as "systemic vulnerability class" not "bug"
- Severity: HIGH to CRITICAL (depending on rollup fund size)
- Type: "Economic incentive misalignment" + "Uninsurable tail risk"
- Target: Celestia Foundation OR OP Stack (depends on scope)

