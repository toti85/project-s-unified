# Jupiter Lend: Absorbed Bucket Lifecycle

## 1. ABSORB-ONLY AFTER STATE

### 1.1 vault_state.topmost_tick értéke

**Összefüggés: absorb() befejezés (user.rs:1050-1053)**

```rust
// Update vault state based on next tick and branch status
if next_tick >= branch_data.minima_tick {
    // New top tick is not liquidated
    if next_tick > COLD_TICK {
        vault_state.topmost_tick = next_tick;  // Line 1051
    } else {
        vault_state.reset_top_tick();          // Line 1052
    }
} else {
    // New top tick is liquidated
    vault_state.update_state_at_liq_end(branch_data.minima_tick, branch_data.id)?;
    // topmost_tick = branch_data.minima_tick
}
```

**Eredmény: topmost_tick = next_tick (az absorb() által számított következő nyitott tick)**

```
where:
- next_tick := fetch_next_tick_absorb(
      max_tick = oracle_max_tick,
      start_from = vault_state.topmost_tick + 1
  )
```

**Szó szerinti: Az absorb() a `max_tick` felett összes branch/tick-et lezár, majd új topmost_tick = legmagasabb nyitott tick az absorb után.**

---

### 1.2 Highest active tick?

**Definíció: A vault-ban lévő legmagasabb tick, amely:**
- status != LIQUIDATED (nem zárt branch)
- raw_debt > 0 (van tartozása)
- tick < topmost_tick + 1 (az absorb() alatt nem érintes)

**Technikailag: Minden tick < topmost_tick után az absorb() ezek biztosan "active" (még nem liquidált).**

**Szó szerinti: Nincs explicit "highest active tick" tárolt érték - csak `topmost_tick` amely az absorb() után az összes felette lévő branch/tick zárásának eredménye.**

---

### 1.3 Nettó hatás az absorb-only után

| Komponens | Előtte | Utána |
|-----------|---------|----------|
| `vault_state.topmost_tick` | T₁ (pl. 1050) | T₂ (pl. 900, új active max) |
| `vault_state.total_borrow` | 1000e18 | **1000e18 (NEM CSÖKKENT!)** |
| `vault_state.absorbed_debt_amount` | 0 | +850e18 |
| Closed branches (debt_liquidity readable) | 150e18 | 150e18 + 850e18 = 1000e18 |
| **Invariant I4** | ✓ (1000 = 150+850) | **✗ (1000 ≠ 150 active + 1000 closed+absorbed)** |

---

## 2. LIQUIDATE(debt_amt>0, absorb=false) UTÁN

### 2.1 Belép-e a main liquidation loop?

**Feltételek (user.rs:656):**
```rust
if current_data.tick > liquidation_tick && current_data.debt_remaining > 0 {
    // Main liquidation loop
    loop { ... }
}
```

**Válasz: IGEN, HA:**
1. `current_data.tick > liquidation_tick` (vault topmost tick az oracle threshold felett)
2. `current_data.debt_remaining > 0` (még van liquidálni való)

**Az absorb flag NINCS HATÁSSAL a main loop végrehajtására.**

---

### 2.2 Eléri-e az absorbed bucketet?

**Code path az absorb==false esetén:**

```rust
// Line 643 - absorb() hívás
if vault_state.topmost_tick > max_tick {
    let (col_absorbed, debt_absorbed) = absorb(...)?;
    
    if debt_amt == 0 {
        return Ok((0, 0));  // Early return csak absorb-only
    }
}

// Line 643 - Absorbed bucket feldolgozás
if absorb {  // <-- absorb==false-nél SKIP
    vault_state.absorb_dust_amount_for_liquidate(&mut current_data)?;
}

// Main loop starts, line 656
if current_data.tick > liquidation_tick && current_data.debt_remaining > 0 {
    loop { ... }  // ABSORBED BUCKET soHA NEM ÉRINTI
}
```

**Válasz: NEM - az absorbed bucket teljesen figyelmen kívül hagyva.**

**Mechanizmus:**
- `absorb_dust_amount_for_liquidate()` csak akkor futna, ha `absorb==true` (line 643-645)
- Ha `absorb==false`, a main loop 0 kapacitással indít az absorbed bucket felhasználása nélkül
- Az `absorbed_debt_amount` és `absorbed_col_amount` bennmaradnak az `vault_state`-ben

---

### 2.3 Csökkenti-e total_borrow-t?

**Code path a liquidate() alatt:**

```rust
// Line 773-907: Main liquidation loop
loop {
    // Debt collection
    additional_debt = ... (branch vagy tick-ből)
    current_data.debt = current_data.debt.safe_add(additional_debt)?;
    
    // ... ratio computation, etc ...
}

// Line 908-973: Liquidation finalization
// reduce_total_borrow() hívás a liquidáció végén
vault_state.reduce_total_borrow(actual_debt_amt)?;  // Az absorb() path-ben SKIP!
```

**Válasz: IGEN, HA main loop fut + absorb==false**

**BUT CRITICAL:** Az absorb==false mellett is csak a main loop-ban összegyűjtött debt csökken:
- Ha main loop 0 debt-et gyűjt (nincs active tick), total_borrow nem csökken
- Ha main loop 200e18-et gyűjt, akkor 200e18 csökken

---

## 3. ORPHANED ABSORBED BUCKET STATE

### 3.1 Van-e olyan állapot, ahol absorbed_debt_amount > 0 DE main loop NEM FUT?

**IGEN. Kritikus forgatókönyv:**

**Állapot A: Post-absorb configuration**
```
- vault_state.topmost_tick = 800 (absorb után az új maximum)
- vault_state.total_borrow = 1000e18
- vault_state.absorbed_debt_amount = 850e18 (az 800 felett zárt branches)
- Closed branches debt_liquidity = 850e18 (még olvasható!)
```

**Liquidate() meghívás: debt_amt=100e18, absorb=false**

```
- max_tick (oracle) = 850 (újra fent van az absorb limit)
- topmost_tick = 800 (< max_tick, szóval absorb flag elkerül!)
- liquidation_tick = 700

Current data setup:
- current_data.tick = 800  (topmost_tick értéke)
- current_data.debt_remaining = 100e18

Loop entry check (line 656):
- current_data.tick (800) > liquidation_tick (700) ✓
- current_data.debt_remaining > 0 ✓

MAIN LOOP RUNS: Liquidálódik 800-as tick → total_borrow csökken 100e18-ral
```

---

**Állapot B: ORPHANED CASE**

```
- vault_state.topmost_tick = 600 (absorb után minden kifolyt)
- vault_state.total_borrow = 1000e18
- vault_state.absorbed_debt_amount = 850e18
- liquidation_tick = 750 (новый oracle max)
- liquidation_tick > topmost_tick!
```

**Liquidate() meghívás: debt_amt=100e18, absorb=false**

```
Loop entry check (line 656):
- current_data.tick = 600 (topmost_tick)
- current_data.tick (600) > liquidation_tick (750)? ✗ FALSE!

MAIN LOOP DOES NOT RUN
- absorbed_dust_amount_for_liquidate() SKIP (absorb==false)
- No debt collected
- total_borrow not reduced
- absorbed_debt_amount = 850e18 REMAINS ORPHANED
```

---

### 3.2 Konkrét kiváltók: Mikor nem fut a main loop?

```rust
if current_data.tick > liquidation_tick && current_data.debt_remaining > 0 {
    // Main loop
}
```

**A loop SOHA nem fut, ha:**

1. **Case 1: topmost_tick < liquidation_tick** (oracle above vault)
   - Előfordulhat: Alacsony volatilitás, vault alatt marad az oracle
   - Hatás: Zárt ágak (absorb()) soha nem likvidálódnak

2. **Case 2: current_data.debt_remaining == 0**
   - Előfordulhat: Külső hiba vagy 0 debt_amt paraméter
   - Technikai: Nem érinti az absorbed bucket-et (már az absorb() végző)

3. **Case 3: Early return az absorb==true && debt_amt==0 után**
   - Line 629: `return Ok((0, 0))`
   - Hatás: Nem érinti az external absorbed bucket-et (az ezt megelőzően létrehozottat)

---

### 3.3 Summary: Az orphaned bucket szcenáriók

| Szcenário | topmost_tick | liquidation_tick | Main loop? | Absorbed bucket |
|-----------|--------------|------------------|-----------|-----------------|
| Normal absorb + liquidate | 800 | 700 | ✓ YES | Feldolgozva (dust) |
| **Orphaned Case 1** | **600** | **750** | **✗ NO** | **ORPHANED** |
| Absorb-only | N/A | N/A | — | Stored (nem fut liquidate) |
| Multiple absorb cycles | 500 | 400 | ✓ YES | Stacked (nem azonnali feldolgozás) |

---

## 4. VAULT ARITHMETIC DURING ORPHAN STATE

### Initial State
```
Active positions: 150e18
(Topmost tick = 1000, status = ACTIVE)

Closed branch debt (post-absorb):
(Ticks 1001-1050, status = CLOSED): 850e18

Vault totals:
- total_borrow = 1000e18 ✓ (150 + 850)
- absorbed_debt_amount = 850e18
- current_branch_id = still points to branch containing 1000
```

### After Main Liquidation Loop (if it runs)

```
Liquidate(100e18, absorb=false)

Main loop collects:
- 100e18 from active tickets

Finalization:
- total_borrow -= 100e18  → 900e18
- absorbed_debt_amount: UNCHANGED (absorb==false, so no dust consumption)

Result:
- Active: 50e18
- Closed: 850e18
- Absorbed explicit: 850e18
- total_borrow claim: 900e18
- Readable sum: 50 + 850 + 850 = 1750 ≠ 900 ✗
```

### After Liquidate in Orphaned Config

```
topmost_tick = 600, liquidation_tick = 750

Liquidate(100e18, absorb=false) call

Check: 600 > 750? NO
→ Main loop DOES NOT ENTER
→ No debt reduction
→ absorbed_debt_amount REMAINS 850e18

Result:
- total_borrow UNCHANGED: 1000e18
- absorbed_debt_amount: 850e18
- Closed branches still readable: 850e18
- Active (if any): Let's say 150e18

Readable sum: 150 + 850 + 850 = 1850 ≠ 1000
AND main loop never touched the absorbed bucket!
```

---

## 5. ROOT CAUSE PATH

### Why absorbed_debt_amount becomes orphaned:

1. **absorb() stores debt but doesn't reduce total_borrow** ✗
   ```rust
   vault_state.add_absorbed_debt_amount(debt_absorbed)?;  // Line 1101
   // ^^ No corresponding reduce_total_borrow()
   ```

2. **early return in liquidate() skips debt reduction**
   ```rust
   if debt_amt == 0 {
       return Ok((0, 0));  // Line 629 - absorb-only exit
       // ^^^ Skips reduce_total_borrow() at line ~967
   }
   ```

3. **Main liquidation loop may never run due to oracle-vault misalignment**
   ```rust
   if current_data.tick > liquidation_tick && current_data.debt_remaining > 0 {
       // If FALSE, loop doesn't run, absorbed bucket untouched
   }
   ```

4. **absorb_dust_amount_for_liquidate() only called if absorb==true**
   ```rust
   if absorb {  // Line 643
       vault_state.absorb_dust_amount_for_liquidate(&mut current_data)?;
   }
   // ^^^ Won't consume absorbed bucket if absorb==false
   ```

---

## 6. CONCLUSION

### Pervasive Orphan Risk

**Three independent paths to orphaned absorbed_debt:**

1. **Path A (Absorb Early Return):** `absorb-only → skip reduce_total_borrow`
2. **Path B (Main Loop Gap):** `topmost_tick < liquidation_tick → main loop never runs`
3. **Path C (Dust Skip):** `absorb==false → absorb_dust_amount_for_liquidate() never called`

**All three can occur simultaneously:**
- Absorb 850e18 (stores in absorbed_debt_amount, doesn't reduce total_borrow)
- Oracle moves above vault → liquidation_tick > topmost_tick
- Call liquidate(debt_amt>0, absorb=false)
- Main loop doesn't run (tick check fails)
- absorbed_debt_amount = 850e18 **PERMANENTLY ORPHANED**

**Result: Double-count + permanent debt exclusion from circulation.**

---

## 7. KEY INVARIANT VIOLATIONS

| Invariant | Before | After Orphan | Broken? |
|-----------|--------|--------------|---------|
| I4: total_borrow = sum(active) + sum(closed readable) | ✓ | ✗ | **YES** |
| I5: absorbed_debt ≤ total_borrow | ✓ | ✓ (absorbed ⊂ total) | — |
| I6: main loop handles all debt > liquidation_tick | ✓ | ✗ (orphaned > liq_tick) | **YES** |

