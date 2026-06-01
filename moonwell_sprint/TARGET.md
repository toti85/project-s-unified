# TARGET.md – Moonwell (Code4rena Bug Bounty)

**Status:** ACTIVE SPRINT (2h hard cap)  
**Last Updated:** 2026-01-29  
**Bounty Type:** Continuous Code4rena Bug Bounty  
**Max Bounty:** $250,000 USD Critical (minimum $100k per critical)  

---

## Protocol Overview

**Name:** Moonwell  
**Blockchains:** Base, Optimism, Moonbeam, Moonriver (multichain lending)  
**Type:** Lending/Borrowing + Multi-Chain Governance  
**Contract Language:** Solidity (EVM)  
**Primary Repo:** https://github.com/moonwell-fi  
**Bounty Details:** https://code4rena.com/bounties/moonwell  
**GitHub Scope:** https://github.com/code-423n4/moonwell-bug-bounty  

---

## In-Scope Smart Contracts (Focus Areas)

### Core Lending
- **Unitroller/Comptroller** — Market management, risk parameters
- **mToken Markets** — Collateral accounting (mDAI, mUSDC, mWETH, mWstETH, etc.)
- **JumpRateModel** — Interest rate calculation
- **Maximillion** — Ether repayment helper

### Oracles
- **ChainlinkOracle** — Primary price feed integration
- **Composite Oracles** — cbETH, wstETH, rETH staked token pricing

### Governance & Multichain
- **Temporal Governor** — Time-locked execution (Base)
- **Multichain Governor** — Cross-chain proposal bridging
- **Vote Collection** — Wormhole-based vote aggregation

### Token & Rewards
- **Multi-Reward Distributor** — Reward accrual + claims
- **Native WELL** — Governance token (Wormhole bridge adapter)
- **stkWELL** — Staked governance token
- **Wormhole Bridge Adapter** — Cross-chain message bridging

---

## Out of Scope (Key Exclusions)

### Known Issues (NOT ELIGIBLE)
- **Reward Accrual:** Borrowing rewards don't accrue without claim() call (by design)
- **Reward Rate 0 → Non-Zero:** Rate changes treated retroactively (by design)
- **Unseized Collateral:** Assets without enterMarkets() call can still be seized (by design)
- **New Market Setup:** Must initialize with 0% collateral factor (by design)
- **Wormhole Dependency:** If Wormhole goes offline, multichain governor nonfunctional (by design)
- **Proposal Invariant:** Live proposals ≤ maxLiveProposals can temporarily violate if maxLiveProposals reduced
- **Governance Zero Quorum:** Quorum can be set to 0 (allows 1-vote pass)
- **Timestamp Drift > 45s:** Multi-chain timestamp >45s apart enables double voting (by design risk)

### Test Restrictions
- **NO mainnet testing** — use private testnets only
- **NO oracle testing** — 3rd party oracle contracts out of scope
- **NO social engineering, phishing, DoS, or automated traffic attacks**
- **NO privilege attacks** — governance/strategist roles assumed trusted
- **NO already-exploited attacks**

### Bounty Exclusions
- Issues from malicious governor (must prove code vulnerability independently)
- Wormhole bridge implementation issues
- SPL token or layer 1 issues
- Previous audit findings (see https://docs.moonwell.fi/moonwell/protocol-information/audits)

---

## Trusted Roles (Out of Scope)

- Governor / DAO (admin/owner)
- Pause Guardian (security council)
- Governance Guardian (bridge compromise recovery)

---

## Payout Structure

**For Smart Contract Vulnerabilities:**

| Funds at Risk | Payout % |
|---------------|----------|
| < $5M | 10% of bounty |
| $5M–$10M | 25% of bounty |
| $10M–$50M | 50% of bounty |
| $50M–$250M | 75% of bounty |
| > $250M | 100% of bounty |

**Minimum Critical Payout:** $100,000 USD

---

## Impact Categories Eligible

(From Code4rena bounty criteria)
- Loss of protocol or user funds
- Smart contract vulnerabilities
- Denial of service (on-chain logic)
- Infrastructure vulnerabilities
- Unauthorized governance actions

---

## Sprint Boundaries

**Duration:** 2 hours hard stop  
**Scope Focus:** Core lending invariants (mToken, comptroller, interest accrual)  
**Testing:** Unit tests only (Foundry); no mainnet/testnet  
**Proof Required:** Numeric delta; before/after state snapshot  

**Exit Criteria:**
- All 3 top TVs tested and CLOSED → EXIT and record clean findings
- 1+ TV finds invariant break → SUBMIT-ready exploit
- Time limit reached → PIVOT decision recorded

