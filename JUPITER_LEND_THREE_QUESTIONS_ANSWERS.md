# Jupiter Lend: Három Kérdés - Konkrét Válaszok

## KÉRDÉS 1: Absorb-only után

### Mi a vault_state.topmost_tick?

**Válasz: `topmost_tick = next_tick` az absorb() végén kiszámított érték**

#### Code Evidence (user.rs:1047-1055)
```rust
// Update vault state based on next tick and branch status
if next_tick >= branch_data.minima_tick {
    // New top tick is not liquidated
    if next_tick > COLD_TICK {
        vault_state.topmost_tick = next_tick;  // ← ANSWER: This value
    } else {
        vault_state.reset_top_tick();
    }
} else {
    // New top tick is liquidated
    vault_state.update_state_at_liq_end(branch_data.minima_tick, branch_data.id)?;
}
```

#### Definíció: next_tick
```
next_tick = fetch_next_tick_absorb(
    start_from = vault_state.topmost_tick + 1,
    max_tick = oracle_max_tick,
    find = first tick with raw_debt > 0
)
```

**Szó szerinti:** Az absorb() végig iterál az összes branch-en a `max_tick` felett, összecsukja őket (status=CLOSED), majd keres egy nyitott ticket az absorb utáni tartományban. Ez lesz az új `topmost_tick`.

**Folyamat:**
1. Összes branch > max_tick: lezárva (set_state_after_absorb())
2. Keresés: legmagasabb nyitott tick < max_tick
3. Szövetsz: topmost_tick = ez az érték

---

### Mi a highest active tick?

**Válasz: Nincs explicit érték - az összes tick < (topmost_tick + 1) után az absorb() active**

#### Code Evidence
```rust
// Az absorb() loop:
while branch_data.minima_tick > max_tick {
    // Close this branch
    branch_to_update.set_state_after_absorb(&branch_data.data);
    // Find next branch above max_tick
    ...
}

// Ha nincs több branch > max_tick:
// topmost_tick = next_tick (az első nyitott tick)
// Minden tick < topmost_tick = guaranteed ACTIVE
```

**Interpretáció:**
- Az absorb() nem végez részleges liquidációt
- Csak "zárva vagy nyitott" státuszok vannak
- Nyitott tickek = mindezek < topmost_tick után az absorb

**Gyakorlati:**
```
Before absorb:
- topmost_tick = 1050
- Ticks: 1050, 1040 (active), 1020 (active), 900 (active), 500

After absorb (max_tick=1030):
- Closed: 1050, 1040, 1020 (> max_tick)
- Active: 900, 500 (< max_tick)
- topmost_tick = 900 (új maximum)
- Highest active tick = 900
```

---

## KÉRDÉS 2: Liquidate(debt_amt>0, absorb=false) után

### Belép-e a main liquidation loop?

**Válasz: ÉS, HA `current_data.tick > liquidation_tick` ÉS `debt_remaining > 0`**

#### Code Evidence (user.rs:656-657)
```rust
if current_data.tick > liquidation_tick && current_data.debt_remaining > 0 {
    // Main liquidation loop starts here
    loop { ... }
}
```

#### Feltételek
```
current_data.tick = vault_state.topmost_tick (line 640)
liquidation_tick = Oracle-ből számított (line 567)
debt_remaining = debt_amt * PRECISION / exchange_price (line 651-654)
```

**Szó szerinti:** Az `absorb` flag NINCS HATÁSSAL a loop belépésére. Csak az oracle és vault ticks közötti viszonya számít.

**Felépítés:**
```
If oracle (max_tick) < vault (topmost_tick):
  ↓
  liquidation_tick < topmost_tick
  ↓
  Main loop RUNS ✓

If oracle (max_tick) > vault (topmost_tick):
  ↓
  liquidation_tick > topmost_tick
  ↓
  Current tick check FAILS
  ↓
  Main loop BLOCKED ✗
```

---

### Eléri-e az absorbed bucketet?

**Válasz: NEM - soha nem és semmilyen módon, ha `absorb=false`**

#### Code Path (user.rs:640-655)
```rust
// Handle absorbed liquidity first if requested
if absorb {  // ← Key condition
    vault_state.absorb_dust_amount_for_liquidate(&mut current_data)?;
}
// Line 643-645: Absorbed bucket consumption

// current tick should be greater than liquidationTick and it cannot be greater than maxTick as absorb will run
if current_data.tick > liquidation_tick && current_data.debt_remaining > 0 {
    // Main liquidation loop
    loop {
        // ... NOT using absorbed bucket
    }
}
```

**Mechanizmus:**
- `absorb_dust_amount_for_liquidate()` **csak** ha `absorb==true`
- Main loop **semmilyen** felt azt nem tölt az absorbed bucket-ből
- `absorbed_debt_amount` és `absorbed_col_amount` bennmaradnak az `vault_state`-ben

#### absorb_dust_amount_for_liquidate() Logika (vault_state.rs:403-428)
```rust
pub fn absorb_dust_amount_for_liquidate(
    &mut self,
    current_data: &mut CurrentLiquidity,
) -> Result<()> {
    let absorbed_debt: u128 = self.absorbed_debt_amount;
    
    if absorbed_debt > current_data.debt_remaining {
        // Proportionate consumption
        self.absorbed_col_amount = absorbed_col.safe_sub(current_data.total_col_liq)?;
        self.absorbed_debt_amount = absorbed_debt.safe_sub(current_data.debt_remaining)?;
    } else {
        // Full consumption
        self.reset_absorbed_amounts();  // ← Nullify
        current_data.debt_remaining = ...remaining...
    }
    Ok(())
}
```

**Kritikus:** Ha `absorb==false`, ez a függvény **soha nem hívódik**, ezért az accumulated absorbed_debt_amount **érintetlen marad**.

---

### Csökkenti-e total_borrow-t?

**Válasz: ÉS - DE CSAK ha main loop fut és debt gyűjt**

#### Code Path (user.rs:908-970)
```rust
// After main liquidation loop ends (around line 908)

// Update vault balances if debt was collected
if actual_debt_amt > 0 {
    vault_state.reduce_total_borrow(actual_debt_amt)?;  // Line ~967
}
```

#### Chain of Operations
```
1. Main loop: actual_debt_amt += debt from ticks/branches
2. Finalization: vault_state.reduce_total_borrow(actual_debt_amt)
3. If loop never runs: actual_debt_amt = 0
4. If loop never runs: reduce_total_borrow() skipped OR called with 0
```

**Specifikáció:**
```
If main loop runs:
  total_borrow -= collected_debt ✓

If main loop blocked (tick check fails):
  total_borrow unchanged ✗
  absorbed_debt_amount unchanged ✗
```

#### Absorbflag hatása
```
absorb=false:
  - absorb_dust_amount_for_liquidate() SKIP
  - absorbed_debt_amount still unprocessed
  - BUT main loop still runs (if tick check passes)
  - BUT main loop DOES NOT pull from absorbed bucket
  - total_borrow reduced from ACTIVE debt only
```

---

## KÉRDÉS 3: Van-e olyan állapot, ahol absorbed_debt_amount > 0 DE main loop soha nem fut?

### Válasz: IGEN - ORPHAN STATE

#### Konkrét Szcenário
```
STATE A: Post-absorb
- vault_state.topmost_tick = 800
- vault_state.total_borrow = 1000e18
- vault_state.absorbed_debt_amount = 850e18 ← stored from absorb()
- Closed branches (readable via debt_liquidity): 850e18
- Active positions: 150e18

STATE B: New liquidation call
- Oracle price moves UP (asset devalued)
- liquidation_tick = 850 (new oracle threshold)
- Call liquidate(debt_amt=100e18, absorb=false)

RESULT:
- current_data.tick = 800 (from topmost_tick)
- Check: 800 > 850? NO ✗
- Main loop entry BLOCKED
- absorbed_debt_amount = 850e18 ORPHANED
- total_borrow = 1000e18 (untouched)
```

#### Code Flow
```rust
// Line 640: Read topmost_tick
current_data.tick = vault_state.topmost_tick;  // = 800

// Line 656: Check entry condition
if current_data.tick > liquidation_tick && current_data.debt_remaining > 0 {
    // 800 > 850? Is this true?
    // NO → Main loop SKIPPED
}

// Result: vault state unchanged until liquidate returns
```

---

### Mikor nem fut a main loop?

#### Ok 1: Oracle-Vault misalignment
```
topmost_tick < liquidation_tick
↓
Vault is BELOW liquidation threshold
↓
Main loop condition FAILS
↓
No liquidation, no absorbed bucket processing
```

**Kiváltók:**
- Asset price rises rapidly → liquidation_tick increases
- Vault empty or low positions → topmost_tick drops to COLD_TICK
- Previous absorb() removed all top ticks

---

#### Szcenárió Táblázat

| Case | topmost_tick | liquidation_tick | Main loop? | absorbed_debt | Status |
|------|--------------|------------------|-----------|---------------|---------| 
| **Normal** | 900 | 700 | ✓ YES | Consumed (dust) | OK |
| **Orphen A** | **700** | **800** | **✗ NO** | **ORPHANED** | **STUCK** |
| **Orphan B** | **-2^31+1** (COLD) | **0** | **✗ NO** | **ORPHANED** | **STUCK** |
| **Early Exit** | — | — | — | **ORPHANED** | **absorb-only skip** |

---

### Invariant Violation Detail

#### Pre-Orphan State (Consistent)
```
Active positions: 150e18
Closed branches: 850e18
Total borrow: 1000e18

Check: 150 + 850 = 1000 ✓
```

#### Orphan State (After topmost_tick < liquidation_tick)
```
Active: 150e18
Closed (readable): 850e18
Absorbed (explicit): 850e18
Total borrow (claimed): 1000e18

Check: 150 + 850 + 850 = 1850 ≠ 1000 ✗
AND: Main loop will never fix it (tick check fails)
AND: absorb_dust_amount_for_liquidate() won't run (absorb==false)
```

---

## SYNTHESIS: THREE INDEPENDENT FAILURE PATHS

### Path A: Absorb Early Return
```
liquidate(debt_amt=0, absorb=true)
  → absorb() runs, stores debt
  → Line 629: return Ok((0, 0))
  → reduce_total_borrow() NOT CALLED
  → absorbed_debt_amount > 0, total_borrow unchanged
```

### Path B: Oracle-Vault Divergence
```
liquidate(debt_amt>0, absorb=false)
  → topmost_tick (600) < liquidation_tick (700)
  → Main loop entry fails
  → Main loop never runs
  → absorbed_debt_amount untouched
```

### Path C: Dust Consumption Skip
```
liquidate(debt_amt>0, absorb=false)
  → Main loop might run
  → But absorb_dust_amount_for_liquidate() SKIP
  → absorbed_debt_amount remains
```

---

## CRITICAL CONCLUSION

**The absorbed_debt_amount field has THREE independent paths to orphandom:**

1. **Code-level:** Early return skips vault updates
2. **Oracle-level:** Tick misalignment prevents main loop execution  
3. **Flag-level:** absorb=false skips bucket consumption

**All can trigger simultaneously**, creating a state where:
- `absorbed_debt_amount > 0` (e.g., 850e18)
- `total_borrow` unchanged (e.g., 1000e18)
- **Main liquidation loop never executes**
- **Debt is uncollectible and unforgettable**

