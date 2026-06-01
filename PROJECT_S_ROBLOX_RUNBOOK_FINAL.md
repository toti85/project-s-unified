# PROJECT-S × ROBLOX — RESTORE + EXTEND (RUNBOOK)

**Dátum:** 2026-02-15  
**Workspace:** `c:\1225\project_s_super_core`  
**Fázis:** Restore E2E + Add escape_water_brainrots patch type

---

## MISSION A — RESTORE (3-TERMINAL RUNBOOK)

### Restore Run Order

#### **Terminal A: Server Start**

```powershell
cd c:\1225\project_s_super_core
python docs/archiv/roblox_plugin_server.py
```

**Expected output in Terminal A:**
```
 * Serving Flask app 'app'
 * Debug mode: off
WARNING: This is a development server. Do not use it in production.
 * Running on http://localhost:8001
Project-S Roblox Plugin Server started
Patch queue ready
Evidence directory: C:\Users\Admin\Documents\Roblox Projects\evidence
```

**Success signal:** Line contains `Running on http://localhost:8001`  
**Do NOT close this terminal.** Keep running.

---

#### **Terminal B: Open Studio with Place**

```powershell
& "C:\Program Files\Roblox\Roblox Studio\RobloxStudio.exe" "c:\1225\project_s_super_core\escape water fpr brainrots.rbxl"
```

**Wait 30 seconds for Studio to fully load.**

**Expected output in Terminal B (Studio Output window):**
```
[Project-S Plugin] Initializing...
[Project-S Plugin] HTTP endpoint: http://localhost:8001/patch
[Project-S Plugin] Polling thread started
[Project-S Plugin] Checking for patches (2 sec interval)
```

**Success signals:**
- Studio window is open
- Place file is loaded (title bar shows filename)
- Output tab at bottom shows above messages
- **Do NOT manually insert any scripts.** Plugin does it automatically.

---

#### **Terminal C: Submit Patch**

```powershell
cd c:\1225\project_s_super_core
python tools/roblox_apply_patch.py
```

**At prompt, type:**
```
5 level neon obby
```

**Expected output in Terminal C:**
```
================================================================================
ROBLOX APPLY PATCH TOOL
================================================================================
Input: 5 level neon obby

[1/4] Converting to patch...
  Type: obby
  Levels: 5
  Theme: neon
  Difficulty: medium

[2/4] Validating patch...
  OK

[3/4] Sending to Roblox Plugin Server...
  Status: success
  Metrics: {...}

[4/4] Logging evidence...
  Logged to: C:\Users\Admin\Documents\Roblox Projects\evidence\tool_execution_20260215_143500.json

================================================================================
RESULT: SUCCESS
================================================================================
```

**Success signal:** Last line is `RESULT: SUCCESS`

---

### Success Signals (WHERE to look)

| Component | Location | Expected Sign |
|-----------|----------|---|
| **Server health** | Terminal A log | `Running on http://localhost:8001` (first 10 seconds) |
| **Plugin load** | Studio Output tab | `[Project-S Plugin] Polling thread started` (after place loads) |
| **Patch received** | Terminal A log | `POST /patch - {"type": "obby", "levels": 5, ...}` |
| **Server validation** | Terminal A log | `Patch valid. Added to queue.` |
| **Plugin polls** | Studio Output tab | `[Project-S Plugin] Patch received: obby, 5 levels, neon theme` |
| **Plugin executes** | Studio Output tab | `[PROJECT_S_RESULT] SUCCESS status=success created_instances=11 root_path=PS_BUILD_<timestamp>` |
| **Workspace built** | Studio Explorer (left panel) | `Workspace/` → look for `PS_BUILD_<number>` folder with: SpawnPad, Platform_1..5, Checkpoint_1..5, FinishPad |
| **Evidence logged** | File system | File created: `C:\Users\Admin\Documents\Roblox Projects\evidence\patch_<timestamp>.json` |

---

### Success Verification Checklist

```
☐ Terminal A: Server running, shows "Running on http://localhost:8001"
☐ Terminal B: Studio loaded, Output shows "[Project-S Plugin] Polling thread started"
☐ Terminal C: Client tool prints "[4/4] Logging evidence" + "RESULT: SUCCESS"
☐ Studio Output: "[PROJECT_S_RESULT] SUCCESS" visible
☐ Studio Workspace: PS_BUILD_<timestamp> folder with 11 objects
☐ File system: evidence/patch_*.json created
```

---

### Minimal Debug Checklist (IF restore fails)

| Issue | Check | Fix |
|-------|-------|-----|
| **Port 8001 in use** | `netstat -ano \| findstr :8001` | Kill process: `taskkill /PID <PID> /F` |
| **HttpService disabled** | Studio Output shows error about HTTP | Enable: Studio → File → Settings → Security → HttpService: ON |
| **Plugin not loading** | Studio Output shows no `[Project-S Plugin]` messages | Manually load: Studio → Plugins → Manage → Install → select `roblox_studio_plugin\plugin_combined.lua` |

---

## MISSION B — EXTEND (escape_water_brainrots)

### Minimal Diffs List

#### **File 1: docs/archiv/roblox_plugin_server.py**

**Section:** PATCH_SCHEMA definition (around line 32)  
**Change:**
- Expand `PATCH_SCHEMA` to support `"type": "escape_water_brainrots"` in addition to `"obby"`
- Add schema for water, pickups, base, rules parameters
- Update `validate_patch()` function to handle both types

**Summary:** One dict update + one if/elif branch in validate_patch()

---

#### **File 2: roblox_studio_plugin/plugin_combined.lua**

**Section 2a:** PatchSchema.validate() function (around line 37)  
**Change:**
- Accept both `"obby"` and `"escape_water_brainrots"` types
- For escape_water: validate params.water, params.pickups, params.base exist

**Summary:** Add `or patch.type == "escape_water_brainrots"` check

**Section 2b:** PatchExecutor.execute() function (around line 140)  
**Change:**
- Add dispatcher: `if patch.type == "obby" then ... elseif patch.type == "escape_water_brainrots" then executeEscapeWater(rootFolder, patch) end`

**Summary:** One if/elseif branch

**Section 2c:** New function `executeEscapeWater(rootFolder, patch)` (add after line 140)  
**Change:**
- Create PS_SPAWN, PS_WATER, PS_BASE_DROPOFF parts in rootFolder
- Create PS_PICKUP_1..N by finding Workspace/Stones/Stone_1..N and placing pickups 2 studs above
- If Stones folder missing: print `[PROJECT_S_RESULT] STATUS=FAIL reason=missing_stones_folder`
- If successful: print `[PROJECT_S_RESULT] STATUS=PASS escape_water_brainrots_setup created_instances=<N> pickups=<count>`

**Summary:** ~50 lines of Lua to create objects + error handling

---

#### **File 3: tools/roblox_apply_patch.py**

**Section:** natural_language_to_patch() function (optional, for later NL support)  
**Change (optional, not required now):**
- Detect keywords like "water", "rising", "brainrot" → map to `type: "escape_water_brainrots"`

**Current manual approach (sufficient):**
- User can directly POST JSON to `http://localhost:8001/patch` with `type: "escape_water_brainrots"`
- See E2E test below for example

**Summary:** No change required now (manual JSON submission works)

---

### Validation Success Criteria

**Server-side (docs/archiv/roblox_plugin_server.py):**
```
✓ POST /patch accepts type="escape_water_brainrots"
✓ validate_patch() checks:
  - params.water.start_y exists and is number
  - params.water.rise_rate exists and is number (0.1-2.0)
  - params.water.max_y exists and is number
  - params.pickups.count exists (1-20)
  - params.pickups.cap exists (1-10)
  - params.pickups.respawn_s exists (1-60)
  - params.pickups.payout exists (1-100)
  - params.base exists
  - params.rules.water_resets == "carried_only"
✓ Returns 200 with patch added to queue
```

**Plugin-side (roblox_studio_plugin/plugin_combined.lua):**
```
✓ PatchSchema.validate() accepts type="escape_water_brainrots"
✓ Dispatcher calls executeEscapeWater()
✓ executeEscapeWater() creates all objects OR prints [PROJECT_S_RESULT] STATUS=FAIL
✓ Output format: [PROJECT_S_RESULT] STATUS=PASS escape_water_brainrots_setup created_instances=<N> pickups=<count>
```

---

### E2E Test Steps (New Patch Type)

#### **Setup (same as MISSION A)**

Terminal A:
```powershell
python docs/archiv/roblox_plugin_server.py
```

Terminal B:
```powershell
& "C:\Program Files\Roblox\Roblox Studio\RobloxStudio.exe" "c:\1225\project_s_super_core\escape water fpr brainrots.rbxl"
```

#### **Step 1: Verify Stones folder exists**

In Studio Explorer, check:
```
Workspace/
└── Stones/
    ├── Stone_1
    ├── Stone_2
    └── ... Stone_10
```

If missing: Create manually (right-click Workspace → Insert Object → Folder, name "Stones", then create 10 Part children)

#### **Step 2: Submit new patch type**

Terminal C:
```powershell
cd c:\1225\project_s_super_core
python -c "
import requests
import json

patch = {
    'type': 'escape_water_brainrots',
    'params': {
        'water': {'start_y': -10, 'rise_rate': 0.5, 'max_y': 80},
        'pickups': {'count': 10, 'cap': 5, 'respawn_s': 10, 'payout': 5, 'spawn_on': 'StonesFolder'},
        'base': {'near_spawn': True},
        'rules': {'water_resets': 'carried_only'}
    }
}

response = requests.post('http://localhost:8001/patch', json=patch)
print('Server response:')
print(json.dumps(response.json(), indent=2))
"
```

**Expected Terminal C output:**
```
Server response:
{
  "status": "success",
  "message": "Patch received and queued",
  "patch_type": "escape_water_brainrots",
  "validation": "passed",
  "queue_position": 1
}
```

#### **Step 3: Check Studio Output**

Watch Terminal B (Studio Output) for:
```
[Project-S Plugin] Patch received: escape_water_brainrots
[PROJECT_S_RESULT] STATUS=PASS escape_water_brainrots_setup created_instances=13 pickups=10
```

#### **Step 4: Verify Workspace**

Studio Explorer should show new folder:
```
Workspace/
├── PS_BUILD_<timestamp>/
│   ├── PS_SPAWN (Part, blue, at 0,10,0)
│   ├── PS_WATER (Part, cyan, at 0,-10,0, 500×10×500)
│   ├── PS_BASE_DROPOFF (Part, green, at 10,11,0, 8×1×8)
│   ├── PS_PICKUP_1 (Part, yellow, at Stone_1+2Y)
│   ├── PS_PICKUP_2 (Part, yellow, at Stone_2+2Y)
│   └── ... PS_PICKUP_10
└── Stones/
    └── Stone_1..10 (unchanged)
```

#### **Step 5: Verify Evidence**

Check file:
```
C:\Users\Admin\Documents\Roblox Projects\evidence\patch_*.json
```

Should contain:
```json
{
  "timestamp": "2026-02-15T14:35:00...",
  "patch": {
    "type": "escape_water_brainrots",
    "params": { ... }
  },
  "response": {
    "status": "success",
    "validation": "passed"
  },
  "status": "success"
}
```

---

### Validation Failure Cases (TEST)

#### **Case 1: Missing Stones folder**

Terminal C:
```powershell
# First, delete or rename Stones folder in Studio
# Then submit same patch
```

**Expected Studio Output:**
```
[PROJECT_S_RESULT] STATUS=FAIL reason=stones_folder_not_found pickup_count=0 created=3
```

#### **Case 2: Invalid params**

Terminal C:
```powershell
python -c "
import requests
patch = {
    'type': 'escape_water_brainrots',
    'params': {
        'water': {'start_y': -10},  # MISSING rise_rate, max_y
        'pickups': {'count': 10},
        'base': {'near_spawn': True},
        'rules': {'water_resets': 'carried_only'}
    }
}
response = requests.post('http://localhost:8001/patch', json=patch)
print(response.json())
"
```

**Expected Terminal C output:**
```json
{
  "status": "error",
  "errors": [
    "escape_water_brainrots: water.rise_rate required",
    "escape_water_brainrots: water.max_y required"
  ]
}
```

---

## SUMMARY TABLE

| Milestone | Terminal | Command | Success Signal |
|-----------|----------|---------|---|
| **Server start** | A | `python docs/archiv/roblox_plugin_server.py` | `Running on http://localhost:8001` |
| **Studio open** | B | `RobloxStudio.exe escape\ water\ ...rbxl` | `[Project-S Plugin] Polling thread started` |
| **Old patch type** | C | `python tools/roblox_apply_patch.py` → `5 level neon obby` | `[PROJECT_S_RESULT] SUCCESS` + PS_BUILD_* in Workspace |
| **New patch type** | C | `python -c "... escape_water_brainrots JSON ..."` | `[PROJECT_S_RESULT] STATUS=PASS escape_water_brainrots_setup created_instances=13` |

---

## FILES MODIFIED (CHECKLIST)

```
☐ docs/archiv/roblox_plugin_server.py
  └─ PATCH_SCHEMA dict: add escape_water_brainrots schema
  └─ validate_patch() function: add escape_water_brainrots branch

☐ roblox_studio_plugin/plugin_combined.lua
  └─ PatchSchema.validate(): accept escape_water_brainrots type
  └─ PatchExecutor.execute(): add if/elseif dispatcher
  └─ New executeEscapeWater(rootFolder, patch) function

☐ tools/roblox_apply_patch.py
  └─ No changes required (manual JSON submission sufficient)
```

---

**DONE. Apply diffs from MISSION B, run E2E test, verify success signals.**
