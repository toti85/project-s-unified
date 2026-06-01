# CRYPTO BOUNTY HUNTING - ACTION PLAN

**Cél:** Valódi Solidity sérülékenységek keresése és exploitálása.
**Timeframe:** 2-3 hét (30-50 óra)
**Platform:** Immunefi, HackerOne
**Expected:** $5,000-$100,000

---

## TARGET: UNISWAP V3

**Repository:** `memory/bounty_audits/uniswap-v3-core/`
**Bounty:** https://immunefi.com/bounty/uniswap/
**Range:** $500-$100,000

### Azonosított sérülékenységek (5)

1. **Flash Swap Reentrancy** (CRITICAL) → $50K-$100K
2. **Precision Loss** (HIGH) → $5K-$20K
3. **Tick Bitmap Overflow** (HIGH) → $10K-$25K
4. **Flash Loan Oracle** (HIGH) → $10K-$50K
5. **MEV/Front-running** (HIGH) → $5K-$25K

---

## TERV: LÉPÉSRŐL LÉPÉSRE

### 1. HARDHAT SETUP (1-2 óra)
- Projekt létrehozása: `mkdir hardhat-uni-poc && cd hardhat-uni-poc`
- Hardhat installáció
- Solidity compiler beállítása (0.7.6)
- Sepolia testnet konfiguráció

**Output:** `hardhat.config.js`, `.env`, munkakönyvtár

### 2. RECON CODE (0-1 óra)
- Uniswap V3 kontraktok elemzése (UniswapV3Pool.sol, LiquidityMath.sol)
- Callback mechanizmusok tanulmányozása
- Reentrancy attack vektorok azonosítása

**Output:** Notes, code snippets

### 3. ATTACKER CONTRACT (2-3 óra)
Solidity kód, amely:
- Flashswap callback-et triggerel
- Nested call-t küld
- State mutation-t próbál módosítani
- Guard bypass-t tesztel

**Output:** `contracts/FlashSwapAttacker.sol`

### 4. TEST CASE (1-2 óra)
Hardhat test, amely:
- Deployol (Uniswap V3Pool mock + Attacker)
- Flashswap-ot indít
- Reentrancy-t tesztel
- Rezultátot ellenőrzi

**Output:** `test/reentrancy.test.ts`

### 5. SEPOLIA DEPLOY (1 óra)
- Faucet ETH igénylése
- Deploy wallet setup
- Teszt Sepolia-n
- Tx hash rögzítése

**Output:** Contract address, tx hash

### 6. DOKUMENTÁCIÓ (2-3 óra)
- Vulnerability report
- POC code + kommentek
- Impact analysis
- Mitigation recommendation

**Output:** `VULNERABILITY_REPORT.md`

### 7. SUBMIT (30 perc)
- Immunefi form kitöltés
- Dokumentumok feltöltés
- Monitoring (1-2 hét válaszidő)

---

##현실 CHECKPOINT

**Ha 1 hét múlva nem futó POC van:**
- Terv megújítás
- Könnyebb sérülékenység célba vétele
- Alternatív bounty (Aave, Curve)

---

## SZÜKSÉGES TUDÁS

- Solidity (intermediate) ✓
- Hardhat/Ethers.js (basic) ✓
- DeFi/AMM mechanika ✓
- Smart contract testing ✓

---

## RIZIKÓ

- **Mainnet kockázat:** NINCS (Sepolia csak)
- **Jogi:** Immunefi rules betartása
- **Etika:** Responsible disclosure

---

## TOOLS

- Hardhat (testing)
- Ethers.js (contract interaction)
- OpenZeppelin (utilities)
- Sepolia RPC (free Alchemy/Infura)
