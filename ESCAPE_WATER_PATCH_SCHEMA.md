# Escape Water Brainrots Patch Schema

## Patch Type: `escape_water_brainrots`

Complete vertical slice patch for rising water + pickup collection + money conversion game mode.

---

## JSON Schema

```json
{
  "type": "escape_water_brainrots",
  "params": {
    "water_start_y": -10,
    "water_rise_rate": 0.5,
    "water_max_y": 80,
    "payout": 5,
    "carry_cap": 5,
    "pickup_respawn_seconds": 10
  }
}
```

---

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `water_start_y` | float | -10 | Initial Y position of water (below spawn) |
| `water_rise_rate` | float | 0.5 | Studs per second water rises |
| `water_max_y` | float | 80 | Maximum Y position water reaches |
| `payout` | int | 5 | Money per pickup (Carried × payout = total) |
| `carry_cap` | int | 5 | Maximum pickups player can carry |
| `pickup_respawn_seconds` | int | 10 | Seconds before picked-up respawns |

---

## Created Instances

### Workspace Objects (under PS_BUILD_<timestamp>/)

| Name | Type | Color | Purpose |
|------|------|-------|---------|
| `PS_SPAWN` | Part | Blue | Player spawn location |
| `PS_WATER` | Part | Cyan | Rising water block (500×10×500) |
| `PS_BASE_DROPOFF` | Part | Green | Touch to convert Carried→Money |
| `PS_PICKUP_1..10` | Part (Ball) | Yellow | Collectible items (respawn-able) |

### Scripts (in ServerScriptService)

| Name | Purpose |
|------|---------|
| `PS_<timestamp>_PLAYER_STATE` | Initialize leaderstats.Money + Carried |
| `PS_<timestamp>_WATER_RISE` | Water rising loop + respawn on drown |
| `PS_<timestamp>_PICKUP_MANAGER` | Touch → Carried += 1 (cap), respawn timer |
| `PS_<timestamp>_DROPOFF_HANDLER` | Touch → Money += (Carried × payout), reset |

---

## Runtime Behavior

### Player Initialization
```
[PROJECT_S_RESULT] INIT=<username> money=0 carried=0
```

### Pickup Collection
```
[PROJECT_S_RESULT] EVENT=PICKUP player=<username> carried=<1..5>
```

### Dropoff Conversion
```
[PROJECT_S_RESULT] EVENT=DROPOFF player=<username> payout=<amount> total=<new_money>
```

### Water Respawn
```
[PROJECT_S_RESULT] EVENT=WATER_RESET player=<username> carried_reset=1
```

### Validation Complete
```
[PROJECT_S_RESULT] STATUS=PASS escape_water_brainrots_runtime_ready created_instances=<12+scripts> scripts=4
```

---

## Example Usage

### Send patch via HTTP

```bash
curl -X POST http://localhost:8001/patch \
  -H "Content-Type: application/json" \
  -d '{
    "type": "escape_water_brainrots",
    "params": {
      "water_start_y": -10,
      "water_rise_rate": 0.5,
      "water_max_y": 80,
      "payout": 5,
      "carry_cap": 5,
      "pickup_respawn_seconds": 10
    }
  }'
```

### Server Response

```json
{
  "status": "success",
  "type": "escape_water_brainrots",
  "metrics": {
    "parts_created": 12,
    "root_path": "PS_BUILD_1771164999",
    "execution_time_ms": 15,
    "scripts_created": 4,
    "water_params": {
      "start_y": -10,
      "rise_rate": 0.5,
      "max_y": 80
    },
    "game_params": {
      "payout": 5,
      "carry_cap": 5,
      "pickup_respawn_seconds": 10
    }
  },
  "errors": [],
  "summary": "Generated escape_water_brainrots with rising water, pickups, dropoff (payout=5)",
  "evidence_file": "/path/to/evidence/patch_20260215_160630.json"
}
```

---

## Validation Rules

### Server-side (Python)
- `water_rise_rate` must be positive float
- `payout` must be positive integer
- `carry_cap` must be positive integer
- All params are optional (use defaults if missing)

### Plugin-side (Lua)
- Both `type` and `params` checked for valid types
- Workspace/Stones folder checked for pickup placement
- Error handling on missing PS_SPAWN or PS_WATER

---

## Determinism

- Each patch creates unique root folder: `PS_BUILD_<unix_timestamp>`
- Scripts named with root folder ID to avoid collisions when multiple patches run
- All instance cleanup isolated within PS_BUILD folder (see PS_DETERMINISTIC_CLEANUP)
- Player lookup uses `Players:GetPlayerFromCharacter(character)` (nil-safe)

---

## Backward Compatibility

Existing `obby` patch type unchanged. New `escape_water_brainrots` type coexists:

```python
PATCH_SCHEMA = {
    "obby": {...},  
    "escape_water_brainrots": {...}
}
```

Validation delegates by `patch.type` field.
