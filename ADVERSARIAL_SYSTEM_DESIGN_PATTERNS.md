# ADVERSARIAL SYSTEM DESIGN PATTERNS
## Attack Strategies on Deadline-Dependent Security

**Role:** System design attacker (not blockchain researcher)  
**Focus:** Security = Protocol + Off-Chain Infra + Economic Assumptions + Time  
**Goal:** Find where ANY component fails at the wrong moment → catastrophic failure  
**Domains:** Not limited to blockchain (also bridges, governance, cloud, AI, insurance, keepers)

---

## PATTERN 1: THE SLEEP CYCLE ATTACK

**System:** Liquidation keeper network (crypto lending, futures platforms)

**Claim:** "Keepers monitor positions 24/7 and liquidate undercollateralized loans"

**Story:**
```
Friday 4 PM (US East Coast):
  Keeper network is run by 5 teams spread across timezones
  US: Going into weekend (low monitoring, shift ends)
  Europe: Evening (home time, skeleton crew)
  Asia: Early morning (night shift, tired operators)
  
Friday 4:05 PM:
  Large position becomes undercollateralized
  Liquidation threshold: 80% LTV
  Position enters "unsafe" state
  
Friday 4:06 PM:
  Keepers should trigger liquidation
  US team: "It's Friday, I'm not touching anything"
  Europe team: "Not our shift anymore"
  Asia team: "It's 4 AM, let me sleep"
  No one responds.
  
Friday 4:10 PM – Sunday 6 PM (62 hours):
  Position is undercollateralized for 62 hours
  Market moves: Collateral loses 30% (weekend low liquidity)
  Position becomes massively insolvent
  
Sunday 6 PM (Asia Monday morning):
  First keeper notices: "Oh no, we're down $100M"
  Protocol is bankrupt.
  
Attacker strategy: Watch for the position creation timing.
Position was deposited at 3:50 PM Friday.
Attacker knows keepers won't monitor weekend.
Attacker waits for market to move against collateral during weekend.
No liquidation happens.
Attacker extracts value through this timing window.
```

**Weaponized:** Time (weekend/sleep cycles), human monitoring, coordination gaps

**Why audits miss it:**
- Audits test "keeper network functions correctly"
- They don't test "what happens when keepers are asleep"
- Live testing is done M-F 9-5, not weekends
- "Obviously keepers should monitor weekends" is assumed but not enforced

**Vulnerable systems:**
- Any 24/7 system relying on human-operated keepers
- Liquidation networks
- Price feed operators
- Emergency response (governance, bridges, DA recovery)
- Cloud failover (on-call engineers, PagerDuty rotations)

**Severity:** CRITICAL (hits when no one is watching)

---

## PATTERN 2: THE RPC NODE RETIREMENT ATTACK

**System:** Rollup / Bridge that depends on "always-available" RPC nodes

**Claim:** "RPC nodes are decentralized, operated by community, always accessible"

**Story:**
```
Setup:
  Bridge needs to finalize withdrawal
  Proof is on rollup A
  Finalization requires Ethereum mainnet RPC query
  RPC is provided by: Infura, Alchemy, QuickNode, custom RPC
  
Day 1 (Normal):
  Proof is ready
  RPC responds: "Block X contains proof"
  Finalization happens

Day 100 (The Failure):
  Ethereum moves to PoS 2.0 protocol
  Old RPC nodes using old protocol specification
  Infura: "We're deprecating our old API"
  Alchemy: "API v2 no longer supported"
  QuickNode: "Old contract calls won't work"
  
  Bridge tries to finalize
  Calls: "eth_call to contract X"
  All major RPC providers: "This method is deprecated"
  Bridge gets: "Deprecated API error"
  
  Fallback: Use community RPC
  Community RPC: Offline (operator quit, server crashed)
  
Day 101:
  Bridge cannot finalize
  User funds are locked
  No way to recover

Attacker strategy:
  Wait for Ethereum protocol update
  Don't update bridge RPC integration
  Watch bridge get stuck when old API calls fail
  No one owns the bridge anymore (abandoned)
  Funds remain locked indefinitely
```

**Weaponized:** Protocol evolution, API deprecation, operator abandonment

**Why audits miss it:**
- Code audit checks "does RPC call work?" (yes, today)
- Doesn't check "what happens if RPC provider changes protocol?"
- Assumes "upgradeable contracts" but doesn't test upgrade scenarios
- Doesn't test long-lived recovery scenarios (> 1 year)

**Vulnerable systems:**
- Bridges (Wormhole, Stargate, Across)
- Cross-chain governance
- Asset recovery systems
- Any system with "fallback RPC list" that becomes stale

**Severity:** HIGH (funds permanently locked, no protocol bug)

---

## PATTERN 3: THE GOVERNANCE TIMEOUT TRAP

**System:** Multi-signature governance (DAO + emergency council)

**Claim:** "Governance can respond to exploits with emergency actions within 24 hours"

**Story:**
```
Setup:
  Protocol governance: 5-of-9 multisig
  Each signer operates in different timezone / jurisdiction
  Exploit is discovered: Friday 11 PM UTC
  Emergency response required: Within 24 hours
  
Timeline:
  Friday 11 PM: Exploit discovered in US (6 PM ET, evening)
  Friday 11:15 PM: Slack alert sent to 9 signers
  
  Signers' status:
    Signer 1 (US East): Just left office, in car
    Signer 2 (US East): Dinner plans, phone on silent
    Signer 3 (US East): Already asleep
    Signer 4 (Europe): Middle of night (5 AM Saturday)
    Signer 5 (Singapore): Early afternoon Saturday
    Signer 6 (Australia): Evening Saturday
    Signer 7 (Japan): Early evening Saturday
    Signer 8 (India): Night Saturday
    Signer 9 (South Africa): Midnight Saturday
  
  Saturday 2 AM UTC (3 hours after exploit):
    Signer 1 reaches office: "I'll review"
    Signer 5 checks Slack: "I'll review"
    But: Need 5 signatures, only 2 online
    Waiting for 3 more...
  
  Saturday 6 AM UTC (7 hours after exploit):
    Signer 3 wakes up, sees alert
    Reviews proposal, votes YES
    Signer 4 also votes YES
    Signer 6 votes YES
    Total: 5 signatures ✓
  
  Saturday 6:05 AM: Emergency pause is executed
  Exploit has had 7 hours to drain funds
  $50M is already gone
  
  Attacker strategy:
    Exploit is timed for Friday evening (US timezone)
    Knows governance multisig spans 9 people across 6 timezones
    Knows that getting 5 signatures takes 6-8 hours minimum
    Exploit runs for 6-8 hours, drains funds
    By the time governance responds, damage is done
```

**Weaponized:** Timezone coordination, meeting latency, async decision-making

**Why audits miss it:**
- Audits test "can governance execute emergency action?" (yes, theoretically)
- Don't test "how long does it actually take?" (6-12 hours, not theoretical minimum)
- Assumes "signers are always responsive" (no, they're sleeping)
- Doesn't account for meeting fatigue, context-switching time

**Vulnerable systems:**
- DAOs with distributed governance
- Multi-signature wallets (especially 5-of-9 or higher)
- Emergency protocols (freezing, pausing, circuit breakers)
- Any system requiring "consensus in < 6 hours"

**Severity:** CRITICAL (governance is rendered slow, funds drain during "fast response" window)

---

## PATTERN 4: THE SHARED INFRASTRUCTURE CAPTURE

**System:** "Decentralized" network that uses centralized cloud (AWS, GCP)

**Claim:** "Network is decentralized, operated by 50+ independent nodes"

**Story:**
```
Topology:
  Network has 50 validator nodes
  50 nodes are "independent" (different operators)
  Nodes are hosted on: 
    AWS: 35 nodes (70%)
    GCP: 10 nodes (20%)
    Azure: 3 nodes (6%)
    Self-hosted: 2 nodes (4%)

What's actually true:
  AWS has 35 nodes controlled by 35 operators
  But: All 35 run on us-east-1 region
  All 35 share same power grid, internet backbone
  All 35 use same AWS S3 for data
  All 35 use same RDS for database

Attacker's move:
  Target: AWS us-east-1 region
  Attack method: BGP hijacking (redirect traffic)
  Or: File a complaint with AWS → take down all 35 nodes for "ToS violation"
  Or: Trigger AWS DDoS protection that blacklists the region

  Friday 3 PM: BGP hijack affects us-east-1
  Network loses: 70% of validators
  Consensus: Requires 66%, network has 30% remaining = BROKEN
  
  Network halts.
  Users' transactions are stuck.
  No fallback, no recovery.

Attacker doesn't even need to be sophisticated:
  Just file a complaint with AWS
  "These 35 nodes are running a blockchain protocol"
  AWS ToS: "Validators can't run on AWS"
  AWS: Shuts down 35 accounts simultaneously
  Network: HALTED
  
  This is not a hack. This is following the cloud provider's policy.
```

**Weaponized:** Infrastructure dependencies, hidden correlations, cloud provider policy

**Why audits miss it:**
- Node audits test "node software is correct" (yes)
- Geographic redundancy audit tests "nodes are in different regions" (no, they're on AWS us-east-1)
- Assumes "50 independent operators" means "independent infrastructure" (wrong)
- Doesn't check: cloud provider ToS, region dependencies, shared services

**Vulnerable systems:**
- Layer 1 blockchains (Solana, Cosmos, Polkadot)
- Rollups (OP Stack, Arbitrum)
- Bridges
- Oracles
- Any "decentralized" network with >50% nodes on same cloud

**Severity:** CRITICAL (entire network halts, not a code bug)

---

## PATTERN 5: THE ORACLE CARTEL TIMEOUT

**System:** Decentralized oracle network (Chainlink, Pyth, API3)

**Claim:** "Oracle is decentralized, 30+ independent operators provide prices"

**Story:**
```
Oracle setup:
  Price feed: ETH/USD
  Providers: 30 independent operators
  Consensus rule: Median of 30 prices
  Timeout rule: If no update in 1 hour, use stale price
  
Setup day:
  Operator 1 (major keeper): Gets paid $1000/day to provide prices
  Operator 2-30 (small operators): Get paid $100/day total combined
  
  Operator 1 makes 98% of the actual price updates
  Operators 2-30: Passive, copy Operator 1's price

Day 100 (The Cartel Forms):
  Operator 1 realizes: "I'm the real oracle"
  Talks to operators 2-5 (other major operators)
  Cartel proposal: "Let's require $10k/day to provide prices"
  DeFi protocol: "That's too expensive, we'll find alternative oracle"
  Protocol: Migrates to oracle network 2
  
Day 101:
  Oracle 1 network loses DeFi protocol customer
  Operator 1: "OK, new strategy: Let's squeeze remaining customers"
  Raises price to $5k/day
  Remaining customers: Either pay or find alternative

Attacker (external to oracle):
  Realizes: The oracle has an alternative path to stop providing prices
  What if operators are incentivized to NOT provide prices?
  
  Attack: Create competition
  Attacker: Launches oracle network 2
  Offers: "Free prices, no fees"
  Oracle 1 operators: "We'll join network 2"
  
  Oracle 1 network: Operators leave
  Remaining operators: Not enough for consensus (need 66% quorum)
  
  Oracle 1 response:
    Tries to use timeout rule: "Use stale price"
    But: Stale price is from 2 days ago
    Market has moved 50%
    DeFi protocol: liquidations fail, system is broken
  
This is not "oracle manipulation" (technical attack).
This is "oracle participants have perverse incentives".
```

**Weaponized:** Economic incentives, cartel coordination, incentive misalignment

**Why audits miss it:**
- Technical audit: "Oracle consensus mechanism is cryptographically sound" (yes)
- Doesn't check: "Are operators economically incentivized to provide prices?"
- Assumes: "Operators will always participate" (no, they will defect if more profitable elsewhere)
- Doesn't model: "What if oracle has a viable alternative?"

**Vulnerable systems:**
- Decentralized price feeds
- Keeper networks
- Validator networks
- Any system where "participation" is economically voluntary

**Severity:** HIGH (oracle goes stale, system breaks without technical bug)

---

## PATTERN 6: THE BRIDGE FINALITY RACE

**System:** Cross-chain bridge with "fast finality" option

**Claim:** "Bridge can finalize in 20 minutes, secure finality in 2 days"

**Story:**
```
Bridge design:
  User deposits 100 ETH on Ethereum
  Fast finality: Relayers finalize after 20 minutes
  Secure finality: Ethereum full finality + withdrawal window (2 days)
  Users can choose: Fast (20 min) or Secure (2 days)

The math:
  Fast finality: Relayer says "I saw this deposit"
  Assumption: If relayer finalized it, it's "probably safe"
  But: Relayer might be finality-agnostic (doesn't check Ethereum finality)
  
Day 1:
  User deposits 100 ETH
  Uses fast finality (20 minutes)
  Receives 100 bridge tokens on chain B
  Sells for $300k USDC
  User is happy.

Day 1 (evening):
  Ethereum experiences fork (MEV attack, 51% attack attempt, consensus bug)
  Original block is reorg'd
  Deposit transaction is no longer on Ethereum mainnet
  Bridge deposit: INVALID
  
Day 2 (morning):
  Bridge team realizes: "100 ETH deposit was reorg'd"
  Protocol: "We need to withdraw 100 ETH from bridge vault"
  But: Bridge has already paid out 100 bridge tokens to user
  User spent those tokens
  Bridge vault is now -100 ETH

User: "My deposit was reorg'd, I should get a refund"
Bridge: "Our fast finality is your risk"
Bridge vault: -$300k

Attacker strategy:
  Wait for large ETH deposit
  User chooses fast finality
  Attacker triggers reorg attack on Ethereum (51% attack or consensus exploit)
  Deposit is reversed
  Bridge is now insolvent
  Attacker extracts value via liquidation cascade
  
Note: This is NOT a bug in the bridge code.
This is a design flaw: "Fast finality" doesn't account for reorgs.
Ethereum's finality is 2 days, but bridge claims 20 minutes.
Mismatch = catastrophic failure.
```

**Weaponized:** Finality assumptions, protocol interaction, game theory

**Why audits miss it:**
- Bridge code audit: "Finality check is correct" (checks for 1 condition)
- Doesn't check: "What if Ethereum undergoes finality disruption?"
- Assumes: "Ethereum is always 2-day final" (it can reorg under attack)
- Doesn't test: "Stress test with finality disruption scenario"

**Vulnerable systems:**
- Cross-chain bridges (all of them, if using "fast finality")
- Multi-chain protocols
- Cross-chain governance
- Atomic swaps

**Severity:** CRITICAL (bridge becomes insolvent without code bug)

---

## PATTERN 7: THE GOVERNANCE ATTACK WINDOW

**System:** Governance timelock (proposal submitted, 2-day waiting period, then execution)

**Claim:** "Governance timelocks ensure community can review proposals before execution"

**Story:**
```
Governance design:
  Proposal submitted: Friday
  Voting period: 3 days (Friday, Saturday, Sunday)
  Execution: 2-day timelock (Monday, Tuesday)
  Execution happens: Wednesday

Setup:
  Proposal: "Upgrade contract to allow minting 1M new tokens"
  Governance token holders: See proposal on Friday
  Community: Has 5 days to review and discuss

Day 1 (Friday):
  Proposal is submitted
  Community: "Wait, this looks suspicious"
  Community votes: NO (majority against)
  But: Proposal is already queued for execution
  
Wait... actually in this system:
  Voting happens BEFORE timelock
  If voting fails: Execution is cancelled
  So this scenario doesn't work.

Let's try again:

Scenario 2: Governance attack with misdirection

Day 1 (Friday):
  Proposal A: "Minor upgrade to fee structure" (benign)
  Voting: PASSES (99% approval)
  Timelock starts: 2 days
  
  Real proposal B (hidden): "Also include token minting exploit"
  But proposal B is embedded in proposal A's code
  Community didn't notice the hidden code

Day 3 (Sunday):
  Community realizes: "Oh no, there's an exploit in proposal A"
  But: Timelock already expired (Friday + 2 days = Sunday)
  Execution is imminent
  
Day 3 (Sunday evening):
  Execution happens
  Exploit is activated
  Governance is powerless to stop it

Alternative scenario 3: The delayed attack

Day 1 (Friday):
  Proposal: "Upgrade to new smart contract"
  New contract: Has a time-delayed exploit
  Exploit doesn't trigger until day 30
  Community: Approves upgrade (looks fine)
  
Day 3: Execution
Day 30: Exploit triggers
Day 31: By the time community notices, it's too late to use emergency pause
        (Protocol is designed for fast response, not day-30 surprises)

Attacker's advantage:
  Embed exploit that doesn't trigger immediately
  Community can't detect exploit until it's too late
  Timelock is designed for 2-3 day governance, not 30-day exploits
```

**Weaponized:** Information asymmetry, time-delayed exploits, review bandwidth

**Why audits miss it:**
- Governance audit: "Timelock period is sufficient for community review" (assumes review happens)
- Doesn't test: "Can community actually review all proposals in time?"
- Assumes: "Exploit will be visible in code review" (no, time-delayed exploits are hard to detect)
- Doesn't account for: Community engagement drops on weekends, fatigue

**Vulnerable systems:**
- DAOs (all of them)
- Governance timelocks
- Protocol upgrades
- Any system with "community review period"

**Severity:** CRITICAL (governance is bypassed by time-delayed exploits)

---

## PATTERN 8: THE FALLBACK PROVIDER EXTINCTION

**System:** Decentralized service with "fallback provider" list

**Claim:** "If primary provider fails, system uses fallback provider"

**Story:**
```
Design:
  Service: "Decentralized data availability"
  Primary providers: Celestia, EigenDA, Avail
  Fallback: Arweave, Filecoin

Week 1 (Normal):
  Primary provider is Celestia
  Data is posted to Celestia
  Fallback providers: Not used

Week 8:
  Celestia has a protocol upgrade
  Celestia temporarily halts data acceptance (5 hours)
  Service: Falls back to Arweave
  
Week 10:
  Arweave is now "primary" in fallback list
  But: Only has data from week 8-10 (2 weeks of data)
  Historical data (weeks 1-7): Only on Celestia
  
Week 15:
  Celestia is under attack
  Long-term Celestia failure (multiple days)
  Service: "Let's migrate to Arweave completely"
  
  Realization: Historical data is ONLY on Celestia
  Arweave doesn't have it
  To recover history, need Celestia
  But Celestia is down
  
  System has a dependency:
    Modern data: Arweave ✓
    Historical data: Celestia ✗
  
  Service: Can't serve historical queries
  Users: "Where's my data from week 3?"
  System: "It was on Celestia, which is down"
  
Attacker strategy:
  Attack Celestia (not to steal, just to make it unavailable)
  System falls back to Arweave
  But fallback is incomplete (missing history)
  System gradually becomes less reliable
  Eventually: System is useless because it can't access history

This is not a "bug", it's an assumption:
  "Fallback providers will have data" → FALSE
  Fallback providers only have recent data
  Historical data is on primary provider
  If primary fails: History is lost
```

**Weaponized:** Data migration gaps, fallback incompleteness, dependency chains

**Why audits miss it:**
- System audit: "Fallback provider is implemented" (yes, code exists)
- Doesn't check: "Does fallback provider have HISTORICAL data?"
- Assumes: "Each provider is independent" (no, there are data dependencies)
- Doesn't test: "Multi-week historical queries against fallback provider"

**Vulnerable systems:**
- Multi-provider data systems
- Decentralized storage (IPFS, Arweave, Filecoin)
- Archival systems
- Any system with "primary + fallback" providers

**Severity:** HIGH (system degrades to useless state without bug)

---

## PATTERN 9: THE LIQUIDATION PRICE ATTACK

**System:** Liquidation system that uses AMM prices

**Claim:** "Liquidators trigger when collateral price drops to 80% LTV"

**Story:**
```
Setup:
  Position: 100 ETH collateral, $3M borrowed
  Liquidation trigger: ETH falls to $30k (from $40k)
  Liquidator: Executes liquidation, buys ETH at $30k market price
  Realizes: 30% haircut = $900k profit

Week 1 (Normal):
  ETH trades $38k-$40k
  Position is safe

Week 2 (Attack):
  Attacker: Wants to prevent liquidation (protecting partner's position)
  Strategy: Block liquidators
  
Day 1:
  ETH price drops to $32k (approaching liquidation)
  Liquidator: Prepares to liquidate
  
Day 1 (2 PM):
  Attacker: Executes this sequence:
    1. Buys 1000 ETH at $32k (spend $32M)
    2. Holds it (temporarily removes supply from market)
    3. ETH price spikes to $35k (low supply)
    4. Liquidation uses AMM price: $35k (not $32k)
    5. At $35k, position is NOT liquidatable (LTV is safe)
  
  Attacker: Sells 1000 ETH back at $35k
  Attacker profit: $3M (1000 * ($35k - $32k))
  
  Liquidation: Fails because price was manipulated
  Partner's position: Survives

Attacker strategy:
  Attacker and victim are partners (implicit cartel)
  Victim profits: Avoids liquidation
  Attacker profits: Flash loan fee or direct payment
  
  Cost: $32M to manipulate price for 10 minutes
  Benefit: $3-10M (avoid liquidation for victim)
  Attacker's cut: Partner pays attacker $5M
  Net cost to attacker: $32M - $5M payout = $27M
  But attacker already had $32M, so cost is just opportunity cost
  
  This is worth it for protecting a $100M+ position

Why it works:
  System assumes: "AMM price is fair and can't be manipulated"
  Reality: Price can be manipulated by anyone with capital
  Flash loans: Allow manipulation with no capital (borrow, manipulate, repay)
  
  This isn't a code bug, it's a game theory issue:
  Liquidation systems are vulnerable to price manipulation
  If you have enough capital, you can prevent liquidations
```

**Weaponized:** Price manipulation, flash loans, market microstructure

**Why audits miss it:**
- System audit: "AMM price feed is used" (yes)
- Doesn't check: "Is AMM price vulnerable to manipulation?"
- Assumes: "AMM is liquid enough that manipulation is expensive" (during low-liquidity periods, manipulation is cheap)
- Doesn't model: "What if attacker has $32M capital?"

**Vulnerable systems:**
- Lending protocols (Compound, Aave, Curve)
- Liquidation networks
- Derivatives exchanges
- Any system that relies on AMM price + liquidation

**Severity:** HIGH (liquidations can be prevented by wealthy actors)

---

## PATTERN 10: THE SUPPLY CHAIN TIMING ATTACK

**System:** Hardware-based security (hardware wallets, HSMs, secure enclaves)

**Claim:** "Hardware security module protects keys, prevents unauthorized access"

**Story:**
```
Setup:
  Enterprise bridge uses HSM (hardware security module)
  HSM is made by Manufacturer X
  Supply chain: Manufacturer → Distributor → Company
  Delivery time: 2 weeks
  Bridge setup: "Install HSM, load keys, test"

Attacker's angle:
  Attacker: Works at Manufacturer X OR convinces Distributor to cooperate
  Attacker: Modifies HSM firmware during manufacturing
  Modification: Add backdoor that logs all private keys
  HSM still functions normally (no detection)

Timeline:
  Week 0: Attacker modifies firmware
  Week 2: HSM is delivered to bridge company
  Week 3: Bridge company installs HSM
  Week 3: Bridge company loads private keys into HSM
  Week 4: Bridge company tests, everything works
  
  Week 4-52: Attacker reads all private keys from logs
  Week 52: Attacker uses keys to sign fraudulent bridge transactions
  
Bridge compromise: Complete, undetectable

Why this is hard to defend:
  Company tests HSM: "Does it work?" YES
  Company doesn't test: "Is it logging keys to backdoor?"
  Company trusts manufacturer: "They wouldn't backdoor their own hardware"
  
  But:
  - Manufacturer is in country with government pressure
  - Manufacturer has competitor who paid them
  - Manufacturer has dissatisfied employee
  - Supply chain has multiple parties with access

Attacker's advantage:
  This attack is done BEFORE bridge goes live
  By the time bridge is operational, compromise is months old
  Attacker has keys, just waiting to use them
  When attacker does use keys, it looks like legitimate operation
  No forensic evidence of tampering
```

**Weaponized:** Supply chain trust, physical access, manufacturing, timing

**Why audits miss it:**
- Security audit: "HSM is properly configured" (yes, software side)
- Doesn't check: "Was HSM backdoored during manufacturing?"
- Assumes: "Manufacturer is trustworthy" (may not be, under pressure)
- Doesn't perform: Hardware forensics (expensive, rarely done)
- Doesn't account for: Nation-state level attackers (very rare, but possible)

**Vulnerable systems:**
- Hardware wallets (Ledger, Trezor, etc.)
- Bridge operators
- Exchange operators
- Any system with HSM or trusted hardware
- Validators / stakers with hardware security

**Severity:** CRITICAL (no on-chain detection, complete compromise)

---

## PATTERN 11: THE GOVERNANCE TOKEN INFLATION TRAP

**System:** Governance token with inflation schedule

**Claim:** "Governance token is minted at fixed rate, inflating by X% annually"

**Story:**
```
Token design:
  Total supply: 1B tokens
  Inflation: 2% per year (20M new tokens annually)
  Use: Staking, governance voting

Year 1:
  1B + 20M = 1.02B tokens
  Staker who owns 10M tokens: Voting power 0.98% (lost power due to dilution)
  Large stakeholder: Diluted
  
Year 5:
  Cumulative inflation: 10% (100M tokens)
  Total supply: 1.1B tokens
  Original stakeholder's 10M tokens: Now 0.91% voting power
  Original stakeholder's voting power is halved

Year 10:
  Cumulative inflation: 20% (200M tokens)
  Total supply: 1.2B tokens
  Original stakeholder's voting power: Severely diluted

Attacker's strategy:
  Attacker: Owns 100M tokens (10% of original)
  Attacker: Joins governance
  Attacker: Proposes: "Change inflation to 5% per year"
  Original stakeholders: Affected by dilution, don't vote (too busy/apathetic)
  Attacker: Easily passes proposal with 10% + apathy votes
  
  New inflation: 5% = 50M tokens per year
  Attacker: Gets diluted more, but CONTROLS the governance
  Attacker: Next proposal: "Let's mint 100M tokens for 'development fund'"
  Attacker: Development fund goes to attacker's address
  Governance: Captured by minority stakeholder

This is not "governance is buggy".
This is "inflation creates dilution, which creates governance apathy, which enables capture".

Attacker achieves:
  Minority control (10% stake)
  Full treasury access (100M+ tokens)
  No technical hack
```

**Weaponized:** Inflation, dilution, voting apathy, governance capture

**Why audits miss it:**
- Token audit: "Inflation schedule is correct" (yes, code is accurate)
- Doesn't test: "What happens to voting power over time?"
- Assumes: "Large stakeholders will always vote" (no, dilution creates apathy)
- Doesn't model: "What if minority actor captures governance?"
- Doesn't simulate: "10-year horizon with inflation + apathy"

**Vulnerable systems:**
- DAOs (most of them)
- Governance tokens
- Proof-of-Stake networks
- Any token with inflation

**Severity:** HIGH (governance is gradually captured without technical exploit)

---

## PATTERN 12: THE EMERGENCY PAUSE FAILURE

**System:** Protocol with "emergency pause" for security

**Claim:** "Admins can pause the protocol within minutes if exploit is detected"

**Story:**
```
Design:
  Emergency pause: Stops all transactions
  Trigger: Requires 5-of-9 multisig
  Expected response time: 5 minutes
  Fail-safe: Protocol halts, funds are safe

Day 100 (Exploit discovered):
  Exploit: Smart contract bug allows token minting
  Time: Friday 10 PM UTC
  
Timeline:
  10:00 PM: Exploit is discovered
  10:01 PM: Alert sent to 9 multisig holders
  
  Multisig holders' status:
    Holder 1: In meeting, phone in drawer
    Holder 2: Driving, no data connection
    Holder 3: Asleep (timezone)
    Holder 4: On airplane, not responding
    Holder 5: In another meeting
    Holder 6: Checking Slack, can sign
    Holder 7: Checking Slack, can sign
    Holder 8: Internet connection is down
    Holder 9: Traveling, no access to signing device
  
  10:05 PM: Only 2 signatures (need 5)
  Wait for 3 more...
  
  10:15 PM: Holder 1 checks phone after meeting
  10:18 PM: Holder 1 reviews proposal, signs
  10:22 PM: Holder 5 signs (after meeting)
  10:25 PM: Holder 3 wakes up (in Asia), signs
  Total: 5 signatures ✓
  
  10:26 PM: Emergency pause is executed
  
Damage during 26 minutes:
  Attacker: Minted 1M tokens in 5 minutes
  Attacker: Sold tokens to DEX for $50M in 20 minutes
  By the time pause is executed: $50M is already drained
  
This is not "emergency pause is broken", it's:
  "Expected response time (5 minutes) ≠ Actual response time (26 minutes)"
  Reality: Multi-signature response time is 20-30 minutes, not 5
  But protocol was designed assuming 5-minute response
```

**Weaponized:** Multi-sig latency, timezone distribution, honest-but-slow response

**Why audits miss it:**
- Security audit: "Emergency pause exists" (yes)
- Doesn't test: "How long does pause actually take?"
- Assumes: "Signers are always responsive" (no, they have meetings, sleep, travel)
- Doesn't model: "26-minute window for exploit to run"
- Doesn't account for: "Signers' honest latency in group decision"

**Vulnerable systems:**
- Protocol with emergency controls
- Smart contract upgradeable contracts
- Multi-sig wallets
- Any system with "human-in-the-loop" security

**Severity:** CRITICAL (emergency control is slower than exploit execution)

---

## PATTERN 13: THE DERIVATIVE EXPIRY TIMING ATTACK

**System:** Derivatives exchange with contract expirations

**Claim:** "Contracts expire automatically, settlement is atomic"

**Story:**
```
Derivative design:
  ETH futures contract
  Expiry date: Friday 8 PM UTC
  Settlement: Uses spot price at 8 PM
  Traders: Both long and short positions

Setup:
  Trader A: Long 1000 contracts, needs ETH price > $30k at expiry
  Trader B: Short 1000 contracts, needs ETH price < $30k at expiry
  Current price: $31k (Trader A is winning)

Attacker's move:
  Attacker: Has capital and wants to manipulate spot price
  Goal: Push price below $30k just at expiry
  
Friday 7:50 PM (10 minutes before expiry):
  Attacker: Sells 1000 ETH on DEX (flash crash attack)
  Spot price: $31k → $29k (in 2 minutes)
  Attacker: Buys back at $29.2k profit
  
Friday 8:00 PM (expiry):
  Settlement uses spot price from 8 PM
  Price at 8 PM: $29.5k (depressed)
  Trader A (long): Gets $29.5k (lost money)
  Trader B (short): Gets $29.5k (made money)
  
Attacker's profit:
  If Trader B is attacker's partner: $800k (1000 contracts × $0.8k profit)
  If Trader B is just a lucky stranger: Attacker still dumped and recovered
  
Why it's hard to defend:
  Attacker's flash crash lasts only 2 minutes
  Exchanges don't have time to detect manipulation
  Settlement timestamp is hardcoded (8 PM)
  No way to defer settlement if price is "suspicious"
  
Attacker weaponizes:
  Time (expiry is fixed)
  Price (spot market can be temporarily moved)
  Information (only attacker knows this is going to happen)
```

**Weaponized:** Timing (expiry windows), price manipulation, flash crashes

**Why audits miss it:**
- Exchange audit: "Settlement logic is correct" (yes, code is fine)
- Doesn't test: "What if spot price is manipulated 10 minutes before expiry?"
- Assumes: "Spot price is fair" (it's not, under manipulation)
- Doesn't account for: "10-minute window before expiry where liquidity is thin"

**Vulnerable systems:**
- Derivatives exchanges (CME, Deribit, dYdX, Hyperliquid)
- Options expiry settlements
- AMM-based contracts
- Any system with time-based triggers + spot prices

**Severity:** HIGH (traders lose money to manipulation, no exchange bug)

---

## PATTERN 14: THE KEYSPLITTING RATIONALITY TRAP

**System:** Keysplitting / multisig with "must respond within timeout"

**Claim:** "Private keys are split, requires 3-of-3 signers to sign, each signer is incentivized"

**Story:**
```
Setup:
  Valuable bridge: Controls $100M in assets
  Bridge security: Requires 3-of-3 signature quorum
  Signers: 3 independent operators
  Each signer: Receives $100k/year for signing honest transactions

Day 1:
  Legitimate bridge transaction
  Signer A, B, C: All sign (normal operation)

Day 100:
  Attacker: Proposes fraudulent transaction to signers
  Attacker: Offers $50M to any 2 signers who sign
  
Signer A's decision:
  Sign: $50M personal profit
  Don't sign: $100k/year (official salary)
  Rational choice: SIGN
  
Signer B's decision:
  If A signs: I need to sign to not be the "holdout"
  If I don't sign, I get blamed for "refusing to process transactions"
  Pressure: SIGN (collusion with A)
  
Signer C's decision:
  A and B are already signing
  If C doesn't sign: C appears to be "blocking legitimate transaction"
  Social pressure: SIGN
  
Transaction: Approved by 3-of-3 (attacker + all signers)

What happened:
  3-of-3 design was supposed to prevent fraud
  But each signer was individually incentivized to accept the fraud
  Signer incentives: $100k/year (small) vs $50M (huge)
  
Bridge: Compromised, $50M stolen
  Not due to "key theft", but due to "signer rationality"

This is game theory, not cryptography:
  If you pay signers X and attacker can offer 500x,
  Don't expect signers to refuse.
```

**Weaponized:** Economics, individual incentives, rationality

**Why audits miss it:**
- Security audit: "3-of-3 multisig is required" (yes)
- Doesn't check: "Are signers economically incentivized to stay honest?"
- Assumes: "Signers will refuse 500x offers" (no, humans are rational)
- Doesn't model: "What if attacker can offer more than annual salary?"

**Vulnerable systems:**
- Bridges with multisig security
- Exchanges with key custodians
- Enterprise wallets
- Any system with "trusted signers"

**Severity:** CRITICAL (signers are economically vulnerable)

---

## PATTERN 15: THE NETWORK PARTITION TIMEOUT CASCADE

**System:** Consensus protocol with timeout-based leader election

**Claim:** "If leader is unresponsive, network elects new leader after 5 seconds"

**Story:**
```
Setup:
  Network: 100 validators
  Leader: Proposes blocks
  Timeout: If no block in 5 seconds, elect new leader
  Network: 99% of communication works, 1% packets are dropped

Day 1:
  Leader: Proposes block at T=0
  Block propagates to 99% of validators
  
Day 2:
  Network experiences partial partition
  Leader (node A): Can reach 60% of validators
  Remaining 40% of validators: Can't reach node A
  
  T=0: Leader A proposes block
  60% of validators: See block
  40% of validators: Don't see block
  
  T=5s: Timeout triggers
  40% of validators: "Leader is dead, elect new leader"
  40% elect: Leader B
  60% of validators: "Leader A still responding, block is valid"
  60% still follow: Leader A
  
  Network: Split into two consensus chains
  Leader A chain: 60% validators
  Leader B chain: 40% validators
  
  T=10s: First fork (60% chain)
    Validators: Propose block 2 on top of block 1
    Fork height: 2
  
  T=10s: Second fork (40% chain)
    Validators: Propose block 2' (different block)
    Fork height: 2
    
  T=15s: Network heals
  Now: Two competing chains of equal length
  Consensus: BROKEN, which chain is canonical?
  
This is not "consensus is buggy", it's:
  "Timeout-based leader election is vulnerable to network partitions"
  "5-second timeout is too aggressive for a 100-validator network"
  "Validators don't have time to detect partition before timeout fires"

Result:
  Network forks
  Transactions on one fork don't reach other fork
  Users: "Which chain is real?"
  No recovery path (no re-merging logic)
```

**Weaponized:** Timing (timeouts), network partitions, cascade effects

**Why audits miss it:**
- Consensus audit: "Leader election is correct" (yes, code is fine)
- Doesn't test: "What happens during network partition?"
- Assumes: "5-second timeout is adequate" (it is in ideal conditions, not in partitions)
- Doesn't model: "Cascading timeout failures"
- Doesn't simulate: "100-validator network under partition stress"

**Vulnerable systems:**
- Proof-of-Stake networks (Ethereum, Solana, Cosmos)
- Consensus protocols with timeouts
- Multi-node systems with failure detection
- Any distributed system with "leader election"

**Severity:** CRITICAL (network forks without technical bug)

---

## SUMMARY: ATTACK PATTERN TYPOLOGY

| Pattern | Weaponizes | Target | Severity |
|---------|-----------|--------|----------|
| Sleep cycle | Time | Keepers, monitors | CRITICAL |
| RPC retirement | Protocol change | Bridges, fallback systems | HIGH |
| Governance timeout | Timezone + async | DAOs, governance | CRITICAL |
| Shared infra | Hidden correlation | "Decentralized" networks | CRITICAL |
| Oracle cartel | Incentives | Price feeds, oracles | HIGH |
| Bridge finality | Assumption mismatch | Cross-chain bridges | CRITICAL |
| Governance attack window | Time-delayed exploit | DAOs, upgrades | CRITICAL |
| Fallback provider | Data migration gap | Multi-provider systems | HIGH |
| Liquidation price | Price manipulation | Lending, liquidation | HIGH |
| Supply chain | Manufacturing timing | Hardware security | CRITICAL |
| Token inflation | Dilution + apathy | Governance tokens | HIGH |
| Emergency pause | Multi-sig latency | Protocol controls | CRITICAL |
| Derivative expiry | Timing + manipulation | Futures, options | HIGH |
| Keysplitting rationality | Economic incentives | Multisig wallets | CRITICAL |
| Network partition | Timeout cascade | Consensus protocols | CRITICAL |

---

## UNCOMFORTABLE TRUTHS

**Statement 1:**
> "Most security failures happen not in the code, but at the intersection of: deadline + market + humans."

**Statement 2:**
> "If a system requires 'someone' to do something before time T, the attack surface is: How do you make 'someone' unavailable?"

**Statement 3:**
> "Auditors test 'does the happy path work?' They don't test 'do signers stay honest when offered 500x their salary?'"

**Statement 4:**
> "Inflation, dilution, apathy, and capture are not bugs; they're features of how human incentives work at scale."

**Statement 5:**
> "The only systems that are truly resilient are the ones that don't depend on time, humans, or money being available when needed."

**Statement 6:**
> "Network partitions, midnight launches, weekend emergencies, and supply chain attacks are not 'edge cases'—they're the normal operation of systems at scale."

---

## ATTACK SURFACE SUMMARY

**Where do systems fail?**

1. **Time boundaries:**
   - Sleep cycles (24h clock)
   - Weekends (human availability drops)
   - Timezones (coordination latency)
   - Deadlines (immovable constraints)

2. **Economic incentives:**
   - Salaries vs. attack rewards (small vs. huge)
   - Cartel pricing (monopoly extraction)
   - Inflation + apathy (governance capture)
   - Manipulation margins (flash crashes)

3. **Hidden dependencies:**
   - All nodes on AWS (cloud provider capture)
   - Historical data only on primary (fallback incomplete)
   - Signers economically vulnerable (individual rationality)
   - Supply chain access (manufacturing backdoor)

4. **Assumption mismatches:**
   - DA layer proves availability ≠ guaranteed recovery
   - Fast finality ≠ Ethereum's 2-day finality
   - Emergency pause exists ≠ actually responds in 5 minutes
   - Keysplitting is secure ≠ if signers are bribeable

5. **Cascade effects:**
   - One provider fails → triggers bank run on all providers
   - Liquidations can't happen → undercollateralized positions survive
   - Network partition → fork cascades → consensus breaks
   - Governance captured → minority control for decade

---

## FINAL OBSERVATION

**The systems that survive are not the ones with perfect code.**

**The systems that survive are the ones where:**
- No single human can compromise it (fully automated or 7-of-7 multisig, not 5-of-9)
- Economic incentives point toward security, not against it
- Time boundaries are conservative (plan for 10x latency, not expected latency)
- Dependencies are graceful (system degrades, doesn't fail)
- No hidden infrastructure correlations (actual redundancy, not pretend)

**All other systems are waiting for the right timing attack.**

