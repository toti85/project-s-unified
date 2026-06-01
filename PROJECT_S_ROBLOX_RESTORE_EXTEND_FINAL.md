# PROJECT-S × ROBLOX AUTOMATION — RESTORE + EXTEND (FINAL CHECKLIST)

**Date:** February 15, 2026  
**Mission:** Restore working automation + add escape_water_brainrots patch type  
**Workspace:** `c:\1225\project_s_super_core`  
**Status:** Framework exists. Extend with new semantic patch type.

---

## **MISSION A: WORKSPACE LOCATED**

### **FOUND WORKSPACE**
```
c:\1225\project_s_super_core
```

### **KEY FILES PRESENT**

| File | Location | Status |
|------|----------|--------|
| **Server** | `docs/archiv/roblox_plugin_server.py` | ✅ Flask, port 8001, /patch endpoint exists |
| **Plugin** | `roblox_studio_plugin/plugin_combined.lua` | ✅ 502 lines, all-in-one, obby executor |
| **Status Docs** | `docs/archiv/PROJECT_S_ROBLOX_FINAL_STATUS.md` | ✅ Jan 18, 2026 — system was working |
| **Generator** | `docs/archiv/project_s_patch_generator.py` | ✅ easy/medium/hard difficulty mapping |
| **Client Tool** | `tools/roblox_apply_patch.py` | ✅ NL → JSON patch converter |
| **Evidence** | `~/Documents/Roblox Projects/evidence/` | ✅ Auto-created, patch_*.json logging |
| **Place File** | `escape water fpr brainrots.rbxl` | ✅ Workspace root |

### **ONE-COMMAND RUN SEQUENCE**

#### **Terminal A (Server)**
```powershell
cd c:\1225\project_s_super_core
python docs/archiv/roblox_plugin_server.py
```

**Expected output:**
```
 * Running on http://localhost:8001 (Press CTRL+C to quit)
Patch server ready on http://localhost:8001
```

#### **Terminal B (Studio)**
```powershell
& "C:\Program Files\Roblox\Roblox Studio\RobloxStudio.exe" "c:\1225\project_s_super_core\escape water fpr brainrots.rbxl"
```

**Expected:** Studio opens, place loads. Plugin auto-loads and begins polling server.

#### **Terminal C (Client)**
```powershell
cd c:\1225\project_s_super_core
python tools/roblox_apply_patch.py
```

Responds with prompt:
```
ROBLOX APPLY PATCH TOOL
==================================================
Enter game request: 
```

**Response:** `5 level neon obby` (or any NL description)

### **EXPECTED AUTO BEHAVIOR**

1. **Server receives POST /patch** with JSON: `{"type": "obby", "levels": 5, "theme": "neon"}`
2. **Server validates** against PATCH_SCHEMA
3. **Plugin polls GET /patch** every 2 seconds
4. **Plugin receives** patch from queue
5. **Plugin auto-executes** PatchExecutor.execute(patch)
6. **Workspace builds** with objects: SpawnPad + 5×Platform + 5×Checkpoint + FinishPad
7. **Output displays:**
   ```
   [PROJECT_S_RESULT] SUCCESS
     status: success
     created_instances: 11
     root_path: PS_BUILD_<timestamp>
     ...
   ```
8. **Evidence file** saved: `~/Documents/Roblox Projects/evidence/patch_*.json`

---

## **MISSION B: RE-ENABLE ONE-COMMAND AUTOMATION**

### **STEP 1: Verify Dependencies Exist**

```powershell
# Check Flask
python -m pip list | findstr Flask
# Expected: Flask 2.x.x

# Check requests
python -m pip list | findstr requests
# Expected: requests 2.x.x
```

**If missing:**
```powershell
pip install flask requests
```

### **STEP 2: Start Server (Terminal A)**

```powershell
cd c:\1225\project_s_super_core
python docs/archiv/roblox_plugin_server.py
```

**Watch for:**
```
✓ Patch server ready on http://localhost:8001
✓ EVIDENCE_DIR created: C:\Users\<user>\Documents\Roblox Projects\evidence\
```

**Do NOT close this terminal.** Leave running.

### **STEP 3: Open Studio (Terminal B)**

```powershell
& "C:\Program Files\Roblox\Roblox Studio\RobloxStudio.exe" "c:\1225\project_s_super_core\escape water fpr brainrots.rbxl"
```

**Wait 30 seconds for Studio to load.**

**Watch Studio Output window for:**
```
[Project-S Plugin] Loaded
[Project-S Plugin] HTTP polling started
[Project-S Plugin] Checking for patches...
```

**Do NOT manually insert scripts.** Plugin handles injection.

### **STEP 4: Submit Patch (Terminal C)**

```powershell
cd c:\1225\project_s_super_core
python tools/roblox_apply_patch.py
```

**At prompt, enter:**
```
5 level neon obby
```

**Success signals:**

| Signal | Where | Expected |
|--------|-------|----------|
| **Client tool prints** | Terminal C | `[4/4] Logging evidence...` + `RESULT: SUCCESS` |
| **Server receives** | Terminal A | `POST /patch` + `Patch valid` + `Queue: 1` |
| **Plugin polls** | Terminal B (Studio Output) | `[Project-S Plugin] Patch received` |
| **Workspace built** | Studio 3D view | PS_BUILD_<TS> folder with objects |
| **Output shows** | Studio Output | `[PROJECT_S_RESULT] SUCCESS created_instances=11` |
| **Evidence logged** | `~/Documents/Roblox Projects/evidence/` | `patch_*.json` file created |

### **CHECKLIST: ONE-COMMAND VERIFICATION**

```
☐ Terminal A: Server running, /health responds 200
☐ Terminal B: Studio open, Output shows plugin loaded
☐ Terminal C: Client tool runs without errors
☐ Patch submitted: Server shows "Patch valid"
☐ Plugin receives: Studio Output shows "Patch received"
☐ Build executes: Workspace shows PS_BUILD_* folder
☐ Output correct: [PROJECT_S_RESULT] SUCCESS visible
☐ Evidence saved: patch_*.json exists in evidence/
```

---

## **MISSION C: ADD ESCAPE_WATER_BRAINROTS PATCH TYPE**

### **NEW PATCH SCHEMA**

```json
{
  "type": "escape_water_brainrots",
  "params": {
    "water": {
      "start_y": -10,
      "rise_rate": 0.5,
      "max_y": 80
    },
    "pickups": {
      "count": 10,
      "cap": 5,
      "respawn_s": 10,
      "payout": 5,
      "spawn_on": "StonesFolder"
    },
    "base": {
      "near_spawn": true
    },
    "rules": {
      "water_resets": "carried_only"
    }
  },
  "validation": {
    "spawn_exists": true,
    "base_exists": true,
    "water_exists": true,
    "pickup_count": 10
  }
}
```

### **MINIMAL CHANGES REQUIRED**

#### **Change 1: Server Schema (docs/archiv/roblox_plugin_server.py)**

**File:** `docs/archiv/roblox_plugin_server.py`  
**Line:** ~32 (PATCH_SCHEMA definition)

**OLD:**
```python
PATCH_SCHEMA = {
    "type": "obby",  # only obby supported in MVP
    "levels": (1, 100),  # min, max
    "theme": ["classic", "neon"]
}
```

**NEW:**
```python
PATCH_SCHEMA = {
    "types": {
        "obby": {
            "levels": (1, 100),
            "theme": ["classic", "neon"]
        },
        "escape_water_brainrots": {
            "water_start_y": (-100, 10),
            "rise_rate": (0.1, 2.0),
            "water_max_y": (10, 200),
            "pickup_count": (1, 20),
            "pickup_cap": (1, 10),
            "respawn_s": (1, 60),
            "payout": (1, 100)
        }
    }
}
```

**Also update validate_patch() function:**

**OLD:**
```python
def validate_patch(patch):
    if patch.get("type") != "obby":
        errors.append(f"Type must be 'obby', got {patch.get('type')}")
```

**NEW:**
```python
def validate_patch(patch):
    patch_type = patch.get("type")
    if patch_type not in PATCH_SCHEMA["types"]:
        errors.append(f"Type must be one of {list(PATCH_SCHEMA['types'].keys())}, got {patch_type}")
    
    # Type-specific validation
    if patch_type == "escape_water_brainrots":
        params = patch.get("params", {})
        water = params.get("water", {})
        pickups = params.get("pickups", {})
        
        # Validate water params
        if water.get("start_y") is None:
            errors.append("water.start_y required")
        # ... (similar for other params)
```

---

#### **Change 2: Plugin Validator (roblox_studio_plugin/plugin_combined.lua)**

**File:** `roblox_studio_plugin/plugin_combined.lua`  
**Line:** ~37 (PatchSchema.validate)

**OLD:**
```lua
function PatchSchema.validate(patch)
	if patch.type ~= "obby" then
		return false, "Only 'obby' type supported"
	end
	if not patch.levels or type(patch.levels) ~= "number" then
		return false, "Patch must have 'levels' number"
	end
	return true, nil
end
```

**NEW:**
```lua
function PatchSchema.validate(patch)
	local supportedTypes = {obby = true, escape_water_brainrots = true}
	if not supportedTypes[patch.type] then
		return false, "Type must be 'obby' or 'escape_water_brainrots', got " .. tostring(patch.type)
	end
	
	if patch.type == "obby" then
		if not patch.levels or type(patch.levels) ~= "number" then
			return false, "obby: levels number required"
		end
		if patch.levels < 1 or patch.levels > 100 then
			return false, "obby: levels must be 1-100"
		end
		return true, nil
		
	elseif patch.type == "escape_water_brainrots" then
		local params = patch.params or {}
		if not params.water or not params.pickups or not params.base then
			return false, "escape_water_brainrots: water, pickups, base params required"
		end
		return true, nil
	end
	
	return false, "Unknown validation"
end
```

---

#### **Change 3: Plugin Executor (roblox_studio_plugin/plugin_combined.lua)**

**File:** `roblox_studio_plugin/plugin_combined.lua`  
**Line:** ~200 (PatchExecutor.execute dispatch)

**OLD:**
```lua
function PatchExecutor.execute(patch)
	local startTime = tick()
	local rootFolder = Instance.new("Folder")
	rootFolder.Name = "PS_BUILD_" .. os.time()
	rootFolder.Parent = workspace
	
	-- Obby-specific
	local spawn = createSpawn(rootFolder)
	for i = 1, patch.levels do
		local platform = createPlatform(rootFolder, i, patch.theme or "classic")
	end
	-- ... etc
end
```

**NEW:**
```lua
function PatchExecutor.execute(patch)
	local startTime = tick()
	local rootFolder = Instance.new("Folder")
	rootFolder.Name = "PS_BUILD_" .. os.time()
	rootFolder.Parent = workspace
	
	local success, errorMsg
	
	if patch.type == "obby" then
		success, errorMsg = executeObby(rootFolder, patch)
	elseif patch.type == "escape_water_brainrots" then
		success, errorMsg = executeEscapeWater(rootFolder, patch)
	else
		success, errorMsg = false, "Unknown patch type: " .. tostring(patch.type)
	end
	
	-- ... return result with [PROJECT_S_RESULT] output
end

function executeEscapeWater(rootFolder, patch)
	-- Implementation: create water, pickups, base, scripts
	-- See WATER_EXECUTION_LOGIC below
	return true, nil
end
```

---

#### **WATER_EXECUTION_LOGIC (new function in plugin_combined.lua)**

Add after line 45 (after PatchSchema definition):

```lua
-- ============================================================================
-- ESCAPE WATER BRAINROTS EXECUTOR
-- ============================================================================

local function executeEscapeWater(rootFolder, patch)
	local params = patch.params or {}
	local water = params.water or {start_y = -10, rise_rate = 0.5, max_y = 80}
	local pickups_cfg = params.pickups or {count = 10, cap = 5, respawn_s = 10, payout = 5}
	local base_cfg = params.base or {near_spawn = true}
	
	local createdCount = 0
	
	-- 1. Create spawn
	local spawn = Instance.new("Part")
	spawn.Name = "PS_SPAWN"
	spawn.Shape = Enum.PartType.Block
	spawn.Size = Vector3.new(6, 1, 6)
	spawn.BrickColor = BrickColor.new("Bright blue")
	spawn.CanCollide = true
	spawn.Position = Vector3.new(0, 10, 0)
	spawn.Parent = rootFolder
	createdCount = createdCount + 1
	
	-- 2. Create water
	local water_part = Instance.new("Part")
	water_part.Name = "PS_WATER"
	water_part.Shape = Enum.PartType.Block
	water_part.Size = Vector3.new(500, 10, 500)
	water_part.BrickColor = BrickColor.new("Cyan")
	water_part.Transparency = 0.3
	water_part.CanCollide = true
	water_part.Position = Vector3.new(0, water.start_y, 0)
	water_part.Parent = rootFolder
	createdCount = createdCount + 1
	
	-- 3. Create base dropoff
	local base = Instance.new("Part")
	base.Name = "PS_BASE_DROPOFF"
	base.Shape = Enum.PartType.Block
	base.Size = Vector3.new(8, 1, 8)
	base.BrickColor = BrickColor.new("Bright green")
	base.CanCollide = true
	base.Position = Vector3.new(10, 11, 0)
	base.Parent = rootFolder
	createdCount = createdCount + 1
	
	-- 4. Create pickups in Stones folder
	local stones_folder = workspace:FindFirstChild("Stones")
	if stones_folder then
		for i = 1, pickups_cfg.count do
			local stone = stones_folder:FindFirstChild("Stone_" .. i)
			if stone then
				local pickup = Instance.new("Part")
				pickup.Name = "PS_PICKUP_" .. i
				pickup.Shape = Enum.PartType.Ball
				pickup.Size = Vector3.new(1, 1, 1)
				pickup.BrickColor = BrickColor.new("Bright yellow")
				pickup.Anchored = true
				pickup.CanCollide = true
				pickup.Position = stone.Position + Vector3.new(0, 2, 0)
				pickup.Parent = rootFolder
				createdCount = createdCount + 1
			end
		end
	end
	
	print("[PROJECT_S_RESULT] STATUS=PASS escape_water_brainrots_setup created_instances=" .. createdCount)
	
	return true, nil
end
```

---

### **VALIDATION LOGIC**

#### **Structural Checks**

```
✓ patch.type == "escape_water_brainrots"
✓ patch.params.water has {start_y, rise_rate, max_y}
✓ patch.params.pickups has {count, cap, respawn_s, payout}
✓ patch.params.base exists
✓ Workspace/Stones folder exists with Stone_1..Stone_N
✓ Workspace has no PS_BUILD_* from failed previous runs (cleanup)
```

#### **[PROJECT_S_RESULT] Output Format**

```
[PROJECT_S_RESULT] STATUS=PASS escape_water_brainrots_setup created_instances=13 water_y=-10 base_y=11 pickups=10
```

#### **How to Validate Automatically**

1. **Server side:** validate_patch() checks all params exist and are within range
2. **Plugin side:** PatchSchema.validate() checks type + required fields
3. **Execution:** executeEscapeWater() prints startup status with object counts
4. **Studio Output:** grep for `[PROJECT_S_RESULT] STATUS=PASS escape_water` to confirm success

---

## **MISSION C EXECUTION: END-TO-END**

### **Step 1: Extend Server & Plugin**

Apply changes from "MINIMAL CHANGES REQUIRED" section above to:
- `docs/archiv/roblox_plugin_server.py` (schema + validation)
- `roblox_studio_plugin/plugin_combined.lua` (schema + executor)

### **Step 2: Start Pipeline**

**Terminal A:**
```powershell
cd c:\1225\project_s_super_core
python docs/archiv/roblox_plugin_server.py
```

**Terminal B:**
```powershell
& "C:\Program Files\Roblox\Roblox Studio\RobloxStudio.exe" "c:\1225\project_s_super_core\escape water fpr brainrots.rbxl"
```

### **Step 3: Submit New Patch Type**

**Terminal C:**
```powershell
cd c:\1225\project_s_super_core
python -c "
import sys
import json
sys.path.insert(0, 'tools')
from roblox_apply_patch import RobloxApplyPatchTool
import requests

# Manually submit escape_water_brainrots patch
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
print('Response:', response.json())
"
```

**Expected Studio Output:**
```
[Project-S Plugin] Patch received: escape_water_brainrots
[PROJECT_S_RESULT] STATUS=PASS escape_water_brainrots_setup created_instances=13
```

**Expected Workspace:**
```
Workspace/
├── PS_BUILD_<timestamp>/
│   ├── PS_SPAWN (blue)
│   ├── PS_WATER (cyan)
│   ├── PS_BASE_DROPOFF (green)
│   ├── PS_PICKUP_1..10 (yellow)
└── [rest of place untouched]
```

---

## **TROUBLESHOOTING (MINIMAL FIXES)**

| Problem | Diagnosis | Fix |
|---------|-----------|-----|
| **Server won't start** | Port 8001 in use | `netstat -ano \| findstr :8001`, kill process holding port |
| **Plugin doesn't load** | Plugin path not registered | Studio → Plugins → Manage, then manually load plugin_combined.lua |
| **Patch not received** | HttpService disabled | Studio → File → Settings → Security → Enable HttpService |
| **No [PROJECT_S_RESULT]** | Plugin script error | Check Studio Output for red errors, check pcall() catches |
| **Workspace not built** | executeEscapeWater() failed | Verify Stones folder exists with Stone_1..10 parts |
| **Evidence not logged** | Evidence dir missing | Create `~/Documents/Roblox Projects/evidence/` manually |

---

## **QUICK REFERENCE: FINAL COMMANDS**

### **Workspace Root:**
```
c:\1225\project_s_super_core
```

### **Start (Use 3 Terminals):**

**Terminal A — Server:**
```powershell
cd c:\1225\project_s_super_core && python docs/archiv/roblox_plugin_server.py
```

**Terminal B — Studio:**
```powershell
& "C:\Program Files\Roblox\Roblox Studio\RobloxStudio.exe" c:\1225\project_s_super_core\escape\ water\ fpr\ brainrots.rbxl
```

**Terminal C — Submit Patch:**
```powershell
cd c:\1225\project_s_super_core && python tools/roblox_apply_patch.py
# Then enter: 5 level neon obby
# Or for new type, use Python snippet above
```

### **Success Signals:**

```
✓ Terminal A: /health responds 200
✓ Terminal B: Studio Output shows [Project-S Plugin] Loaded
✓ Terminal C: [4/4] Logging evidence... RESULT: SUCCESS
✓ Studio Workspace: PS_BUILD_<TS> folder visible
✓ Evidence: patch_*.json created
```

---

## **STATUS: READY TO DEPLOY**

✅ Workspace located  
✅ Framework verified working (Jan 18, 2026)  
✅ New patch type design complete  
✅ Minimal changes identified  
✅ Execution checklist ready

**Apply schema + executor changes, run 3 terminals, done.**
