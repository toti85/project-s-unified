# Escape Water Brainrots - JSON Patch Direct Submission

## A Probléma

`tools/roblox_apply_patch.py` jelenleg csak **NL→JSON obby típus** konverziót támogat:

```bash
$ echo "5 level neon obby" | python tools/roblox_apply_patch.py
# szerver feldolgozás ✅ obby típus
```

Az `escape_water_brainrots` típushoz szükséges vagy:
1. NL parser kiterjesztése (komplex)
2. Direkt JSON PATCH küldés (egyszerű)

---

## ✅ Megoldás: JSON Patch Direct

### 1. Python Script

```python
#!/usr/bin/env python3
import requests
import json

escape_water_patch = {
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

response = requests.post(
    "http://localhost:8001/patch",
    json=escape_water_patch
)

print(response.json())
```

### 2. curl

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

### 3. PowerShell

```powershell
$patch = @{
    type = "escape_water_brainrots"
    params = @{
        water_start_y = -10
        water_rise_rate = 0.5
        water_max_y = 80
        payout = 5
        carry_cap = 5
        pickup_respawn_seconds = 10
    }
} | ConvertTo-Json

curl.exe -X POST http://localhost:8001/patch `
  -H "Content-Type: application/json" `
  -d $patch
```

---

## 🔄 Teljes Pipeline

### Architektúra

```
┌─────────────────┐
│ escape_water    │
│ brainrots       │
│ NL command      │
└────────┬────────┘
         │
         ├─► [Option A] roblox_apply_patch.py (NL→JSON obby only)
         │
         ├─► [Option B] Direct JSON script (this approach)
         │
         ▼
┌──────────────────────────────┐
│ Flask Server (localhost:8001)│
│ POST /patch                  │
│ - Validation (type check)    │
│ - Queue patch                │
│ - Return metrics             │
└────────────┬─────────────────┘
             │
             ▼
┌──────────────────────────────┐
│ Roblox Studio (2s poll)      │
│ GET /poll (auto)             │
│ - Fetch pending patch        │
│ - Execute plugin logic       │
│ - Create Workspace objects   │
│ - Run 4 ServerScripts        │
└────────────┬─────────────────┘
             │
             ▼
┌──────────────────────────────┐
│ Workspace                    │
│ ├─ PS_BUILD_<ts>/            │
│ │  ├─ PS_SPAWN (blue)        │
│ │  ├─ PS_WATER (cyan)        │
│ │  ├─ PS_BASE_DROPOFF (green)│
│ │  └─ PS_PICKUP_1..10 (yellow)
│ └─ ServerScriptService       │
│    ├─ PS_<ts>_PLAYER_STATE   │
│    ├─ PS_<ts>_WATER_RISE     │
│    ├─ PS_<ts>_PICKUP_MANAGER │
│    └─ PS_<ts>_DROPOFF_HANDLER│
└──────────────────────────────┘
             │
             ▼
┌──────────────────────────────┐
│ Output Log                   │
│ [PROJECT_S_RESULT] INIT=...  │
│ [PROJECT_S_RESULT] PICKUP=...│
│ [PROJECT_S_RESULT] DROPOFF=..│
└──────────────────────────────┘
```

---

## 📋 Teszt Végrehajtás

### Lépés 1: Szerver Indítás

```bash
cd c:\1225\project_s_super_core
python docs/archiv/roblox_plugin_server.py
# Output: Listening on http://localhost:8001
```

### Lépés 2: Patch Küldés

```bash
python test_escape_water_patch.py
```

**Output**:
```
Status Code: 200
✅ PATCH ACCEPTED
   Root Path: PS_BUILD_1771167943
   Parts Created: 12
   Scripts Created: 4
```

### Lépés 3: Plugin Végrehajtás (in Studio)

Az auto-poll loop (2s interval) meghívja:
```
GET http://localhost:8001/poll
```

Ha patch van queue-ban → Studio végrehajtja:
1. PatchSchema.validate(patch)
2. PatchExecutor.executeEscapeWater(patch)
3. Print ResultReporter output
4. [PROJECT_S_RESULT] logok az Output ablakba

### Lépés 4: Validáció

Roblox Studio Workspace Explorer-ben:
```
Workspace/
├─ PS_BUILD_1771167943/
│  ├─ PS_SPAWN (10×1×10, blue)
│  ├─ PS_WATER (500×10×500, cyan)  
│  ├─ PS_BASE_DROPOFF (10×1×10, green)
│  ├─ PS_PICKUP_1 (neon yellow ball)
│  ├─ PS_PICKUP_2
│  └─ ... PS_PICKUP_10
└─ ServerScriptService/
   ├─ PS_1771167943_PLAYER_STATE
   ├─ PS_1771167943_WATER_RISE
   ├─ PS_1771167943_PICKUP_MANAGER
   └─ PS_1771167943_DROPOFF_HANDLER
```

---

## 🎮 Gameplay Test

### Expected Output (in Studio Output tab)

```
[PROJECT_S_RESULT] INIT=Player1 money=0 carried=0
[PROJECT_S_RESULT] EVENT=PICKUP player=Player1 carried=1
[PROJECT_S_RESULT] EVENT=PICKUP player=Player1 carried=2
[PROJECT_S_RESULT] EVENT=PICKUP player=Player1 carried=3
[PROJECT_S_RESULT] EVENT=WATER_RESET player=Player1 carried_reset=1
[PROJECT_S_RESULT] EVENT=PICKUP player=Player1 carried=1
[PROJECT_S_RESULT] EVENT=PICKUP player=Player1 carried=2
[PROJECT_S_RESULT] EVENT=DROPOFF player=Player1 payout=10 total=10
```

---

## ⚙️ Paramétrizáció Jelölések

### Water Parameters

| Param | Min | Max | Default | Unit |
|-------|-----|-----|---------|------|
| `water_start_y` | -100 | 100 | -10 | Studs |
| `water_rise_rate` | 0.1 | 10 | 0.5 | Studs/sec |
| `water_max_y` | -50 | 200 | 80 | Studs |

### Game Parameters

| Param | Min | Max | Default | Unit |
|-------|-----|-----|---------|------|
| `payout` | 1 | 100 | 5 | Money/pickup |
| `carry_cap` | 1 | 20 | 5 | Pickups |
| `pickup_respawn_seconds` | 1 | 60 | 10 | Seconds |

---

## 🔮 Future NL Support

Lehetséges NL parser extension (tools/roblox_apply_patch.py):

```python
# Currently supports obby only:
# "5 level neon obby" → {type: "obby", levels: 5, theme: "neon"}

# Future support:
# "escape water 0.5 rate 100 payout" → {...}
# "water game 5 payout 10 cap" → {...}
```

Implementation pathway:
1. Tokenize NL input
2. Pattern match "escape|water|brainrots"
3. Extract param keywords (rate, payout, cap)
4. Build JSON dynamically
5. Send to /patch endpoint

---

## ✅ Teljes Validáció Checklist

### Szerver (Python)
- [x] PATCH_SCHEMA két típust támogat
- [x] validate_patch() delegál típus alapján
- [x] /patch endpoint 200-at visszaad
- [x] Metrics teljesek (parts, scripts, params)
- [x] Evidence logging működik
- [x] /poll endpoint queue-t ad vissza

### Plugin (Lua)
- [x] PatchSchema.validate() kiterjesztve
- [x] PatchExecutor.execute() delegál
- [x] executeEscapeWater() implementálva
- [x] 12 object creation (spawn, water, base, pickups)
- [x] 4 script generation (state, water, pickup, dropoff)
- [x] [PROJECT_S_RESULT] logging minden event-nél

### Integration
- [x] Backward compatibility (obby type still works)
- [x] JSON patch direct submission works
- [x] Server health endpoint works
- [x] Status endpoint shows queue

### Testing
- [x] Server validation PASS
- [x] Backward compat PASS
- [x] Evidence files created
- [x] Direct JSON submission PASS

---

## 📦 Deliverables

| Fájl | Státusz | Célszz |
|------|---------|--------|
| `docs/archiv/roblox_plugin_server.py` | ✅ Modified | Szerver escape_water_brainrots támogatás |
| `roblox_studio_plugin/plugin_combined.lua` | ✅ Modified | Plugin escape_water_brainrots feldolgozó |
| `ESCAPE_WATER_PATCH_SCHEMA.md` | ✅ New | Schema + param dokumentáció |
| `ESCAPE_WATER_VERTICAL_SLICE_COMPLETE.md` | ✅ New | Teljes rendszer dokumentáció |
| `ESCAPE_WATER_DIRECT_JSON_SUBMISSION.md` | ✅ This file | Pipeline + submission útmutató |
| `test_escape_water_patch.py` | ✅ New | Automated server test |
| `test_obby_compat.py` | ✅ New | Backward compat validation |

---

## 🚀 Ready for Production

**Status**: Fully operational ✅

**To Deploy**:
1. Ensure server running (Flask localhost:8001)
2. Send JSON patch via test script or curl
3. Studio auto-polls (2s interval)
4. Objects + scripts created in Workspace
5. [PROJECT_S_RESULT] logok Output ablakba

**Scale**: Multiple concurrent patches supported (unique PS_BUILD_<ts> per patch)

