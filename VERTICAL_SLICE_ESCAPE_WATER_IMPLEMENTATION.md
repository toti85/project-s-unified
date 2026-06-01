# VERTICAL SLICE IMPLEMENTATION — ESCAPE WATER + PICKUPS + DROPOFF + MONEY

**Date:** February 15, 2026  
**Target:** `c:\1225\project_s_super_core\escape water fpr brainrots.rbxl`  
**Language:** Lua (Roblox Server Scripts)  
**Status:** Ready to Deploy

---

## **STEP 1: Pre-flight Setup**

Before running scripts, manually create in Workspace:

1. **Create folder** `Workspace/Stones` 
   - Right-click Workspace → Insert Object → Folder
   - Name it `Stones`

2. **Create 10 stone parts** inside Stones folder named `Stone_1` through `Stone_10`
   - Right-click `Stones` → Insert Object → Part
   - Name: `Stone_1`
   - Position: (0, 20, 0)
   - Size: (2, 1, 2)
   - Color: Gray
   - Repeat for `Stone_2` through `Stone_10`, spacing +5 studs along X axis
   - Final positions: (0, 20, 0), (5, 20, 0), (10, 20, 0), ..., (45, 20, 0)

These will be the anchor points for pickups.

---

## **STEP 2: Create Static Objects in Workspace**

Manually create these three parts:

### **PS_SPAWN (SpawnLocation)**
- **Position:** (0, 10, 0)
- **Size:** (6, 1, 6)
- **Color:** Bright blue
- **CanCollide:** true

### **PS_BASE_DROPOFF (Part)**
- **Position:** (10, 11, 0)  ← next to spawn
- **Size:** (8, 1, 8)
- **Color:** Bright green
- **CanCollide:** true

### **PS_WATER (Part)**
- **Position:** (0, -20, 0)
- **Size:** (500, 10, 500)
- **Color:** Cyan
- **CanCollide:** true
- **Transparency:** 0.3

---

## **STEP 3: Insert All 6 Scripts into ServerScriptService**

**Procedure:**
1. Right-click ServerScriptService
2. Insert Object → **Script** (NOT LocalScript)
3. Double-click to open editor
4. Copy-paste code below for each script

---

### **Script 1: PS_PLAYER_STATE_INIT**

**Copy entire code block below:**

```lua
-- PS_PLAYER_STATE_INIT
-- Initialize player state on join

local Players = game:GetService("Players")

local function setupPlayer(player)
	local leaderstats = Instance.new("Folder")
	leaderstats.Name = "leaderstats"
	leaderstats.Parent = player
	
	local money = Instance.new("IntValue")
	money.Name = "Money"
	money.Value = 0
	money.Parent = leaderstats
	
	local carried = Instance.new("IntValue")
	carried.Name = "Carried"
	carried.Value = 0
	carried.Parent = player
	
	print("[PROJECT_S_RESULT] STATUS=PLAYER_INIT player=" .. player.Name .. " money=0 carried=0")
end

Players.PlayerAdded:Connect(setupPlayer)

print("[PROJECT_S_RESULT] STATUS=PASS player_state_system_loaded")
```

---

### **Script 2: PS_WATER_RISE**

**Copy entire code block below:**

```lua
-- PS_WATER_RISE
-- Water physics, rising, and kill/respawn

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local WATER = workspace:WaitForChild("PS_WATER")
local SPAWN = workspace:WaitForChild("PS_SPAWN")
local RISE_RATE = 0.5  -- studs per second
local MAX_HEIGHT = 80  -- studs above starting position
local INITIAL_HEIGHT = WATER.Position.Y

print("[PROJECT_S_RESULT] STATUS=PASS water_system_loaded initial_height=" .. INITIAL_HEIGHT)

-- Water rise loop
local function riseWater()
	while true do
		wait(0.05)  -- ~1/20 second
		if WATER.Position.Y < INITIAL_HEIGHT + MAX_HEIGHT then
			WATER.Position = WATER.Position + Vector3.new(0, RISE_RATE / 20, 0)
		end
	end
end

-- Spawn coroutine for water rise
coroutine.wrap(riseWater)()

-- Kill/respawn on water contact
local function checkPlayerDrowning()
	while true do
		wait(0.5)
		for _, player in pairs(Players:GetPlayers()) do
			if player.Character and player.Character:FindFirstChild("HumanoidRootPart") then
				local root = player.Character.HumanoidRootPart
				local carried = player:FindFirstChild("Carried")
				
				-- If player is below water level + 2 studs
				if root.Position.Y < (WATER.Position.Y + 2) then
					-- Kill humanoid
					local humanoid = player.Character:FindFirstChild("Humanoid")
					if humanoid then
						humanoid.Health = 0
						-- Reset carried to 0
						if carried then
							carried.Value = 0
						end
						print("[PROJECT_S_RESULT] EVENT=WATER_KILL player=" .. player.Name .. " carried_reset=true")
					end
				end
			end
		end
	end
end

-- Spawn coroutine for drowning check
coroutine.wrap(checkPlayerDrowning)()
```

---

### **Script 3: PS_PICKUP_MANAGER**

**Copy entire code block below:**

```lua
-- PS_PICKUP_MANAGER
-- Pickup collection and respawn loop

local Stones = workspace:WaitForChild("Stones")
local Pickups = workspace:FindFirstChild("Pickups") or Instance.new("Folder")
if Pickups.Parent == nil then
	Pickups.Name = "Pickups"
	Pickups.Parent = workspace
end

local PICKUP_RESPAWN_TIME = 10
local CARRIED_CAP = 5

-- Map of pickup to its stone anchor
local pickups = {}
local pickupStates = {}  -- {visible, touchDebounce}

-- Create pickups on each stone
for i = 1, 10 do
	local stone = Stones:FindFirstChild("Stone_" .. i)
	if stone then
		local pickup = Instance.new("Part")
		pickup.Name = "PS_PICKUP_" .. i
		pickup.Shape = Enum.PartType.Ball
		pickup.Size = Vector3.new(1, 1, 1)
		pickup.BrickColor = BrickColor.new("Bright yellow")
		pickup.CanCollide = true
		pickup.Anchored = true
		pickup.Position = stone.Position + Vector3.new(0, 2, 0)  -- 2 studs above stone
		pickup.Parent = Pickups
		
		pickups[pickup] = stone
		pickupStates[pickup] = {visible = true, lastTouch = 0}
		
		print("[PROJECT_S_RESULT] STATUS=PICKUP_CREATE pickup=PS_PICKUP_" .. i .. " stone=Stone_" .. i)
	end
end

-- Handle pickup touches
local function onPickupTouched(pickup, hit)
	if not pickupStates[pickup] then return end
	if not pickupStates[pickup].visible then return end
	
	-- Debounce: 0.5 sec between touches
	if tick() - pickupStates[pickup].lastTouch < 0.5 then
		return
	end
	pickupStates[pickup].lastTouch = tick()
	
	-- Check if hit by humanoid
	local humanoid = hit.Parent:FindFirstChild("Humanoid")
	local player = game:GetService("Players"):GetPlayerFromCharacter(hit.Parent)
	
	if humanoid and player then
		local carried = player:FindFirstChild("Carried")
		if carried and carried.Value < CARRIED_CAP then
			carried.Value = carried.Value + 1
			
			-- Hide pickup
			pickupStates[pickup].visible = false
			pickup.Transparency = 1
			pickup.CanCollide = false
			
			if carried.Value >= CARRIED_CAP then
				print("[PROJECT_S_RESULT] EVENT=PICKUP player=" .. player.Name .. " carried=" .. carried.Value .. " status=max")
			else
				print("[PROJECT_S_RESULT] EVENT=PICKUP player=" .. player.Name .. " carried=" .. carried.Value)
			end
			
			-- Respawn after delay
			coroutine.wrap(function()
				wait(PICKUP_RESPAWN_TIME)
				if pickup and pickup.Parent then
					pickup.Transparency = 0
					pickup.CanCollide = true
					pickupStates[pickup].visible = true
					print("[PROJECT_S_RESULT] EVENT=PICKUP_RESPAWN pickup=" .. pickup.Name)
				end
			end)()
		end
	end
end

-- Connect touch events
for pickup, _ in pairs(pickups) do
	pickup.Touched:Connect(function(hit)
		onPickupTouched(pickup, hit)
	end)
end

print("[PROJECT_S_RESULT] STATUS=PASS pickup_system_loaded pickups=10 respawn_time=" .. PICKUP_RESPAWN_TIME)
```

---

### **Script 4: PS_DROPOFF_HANDLER**

**Copy entire code block below:**

```lua
-- PS_DROPOFF_HANDLER
-- Dropoff conversion and payout

local BASE = workspace:WaitForChild("PS_BASE_DROPOFF")
local PAYOUT_PER_ITEM = 5

local function onDropoffTouched(hit)
	local humanoid = hit.Parent:FindFirstChild("Humanoid")
	local player = game:GetService("Players"):GetPlayerFromCharacter(hit.Parent)
	
	if humanoid and player then
		local carried = player:FindFirstChild("Carried")
		local leaderstats = player:FindFirstChild("leaderstats")
		
		if carried and leaderstats then
			local money = leaderstats:FindFirstChild("Money")
			
			if carried.Value > 0 then
				local payout = carried.Value * PAYOUT_PER_ITEM
				money.Value = money.Value + payout
				local totalMoney = money.Value
				
				print("[PROJECT_S_RESULT] EVENT=DROPOFF player=" .. player.Name .. " carried_converted=" .. carried.Value .. " payout=" .. payout .. " total_money=" .. totalMoney)
				
				carried.Value = 0
			else
				print("[PROJECT_S_RESULT] EVENT=DROPOFF player=" .. player.Name .. " carried_converted=0 status=empty")
			end
		end
	end
end

-- Debounce per player
local dropoffCooldown = {}

BASE.Touched:Connect(function(hit)
	local player = game:GetService("Players"):GetPlayerFromCharacter(hit.Parent)
	if player then
		if not dropoffCooldown[player] then
			dropoffCooldown[player] = true
			onDropoffTouched(hit)
			wait(1)  -- 1 second cooldown per player
			dropoffCooldown[player] = false
		end
	end
end)

print("[PROJECT_S_RESULT] STATUS=PASS dropoff_system_loaded payout_per_item=" .. PAYOUT_PER_ITEM)
```

---

### **Script 5: PS_DETERMINISTIC_CLEANUP**

**Copy entire code block below:**

```lua
-- PS_DETERMINISTIC_CLEANUP
-- Cleanup only PS_BUILD_* objects, NOT general PS_*

local function cleanupBuilds()
	local cleanedCount = 0
	
	for _, obj in pairs(workspace:GetChildren()) do
		if obj.Name:match("^PS_BUILD_") then
			obj:Destroy()
			cleanedCount = cleanedCount + 1
		end
	end
	
	print("[PROJECT_S_RESULT] STATUS=CLEAN mode=PS_BUILD_ONLY removed=" .. cleanedCount)
end

-- Run once at startup
cleanupBuilds()

-- Also validate existing PS_* objects
local psCount = 0
for _, obj in pairs(workspace:GetChildren()) do
	if obj.Name:match("^PS_") then
		psCount = psCount + 1
	end
end

print("[PROJECT_S_RESULT] STATUS=VALIDATE existing_ps_objects=" .. psCount)
```

---

### **Script 6: PS_VALIDATION_STARTUP**

**Copy entire code block below:**

```lua
-- PS_VALIDATION_STARTUP
-- Validation output on startup

local WATER = workspace:WaitForChild("PS_WATER")
local BASE = workspace:WaitForChild("PS_BASE_DROPOFF")
local SPAWN = workspace:WaitForChild("PS_SPAWN")
local STONES = workspace:WaitForChild("Stones")

wait(1)  -- Wait for other systems to initialize

local waterPos = tostring(WATER.Position)
local basePos = tostring(BASE.Position)
local spawnPos = tostring(SPAWN.Position)
local stoneCount = #STONES:GetChildren()

print("[PROJECT_S_RESULT] STATUS=STARTUP all_systems=ready")
print("  water_position=" .. waterPos)
print("  base_position=" .. basePos)
print("  spawn_position=" .. spawnPos)
print("  stones_folder=" .. stoneCount)
print("  max_water_height=80")
print("  rise_rate=0.5")
print("  respawn_cooldown=10")
print("  payout_per_item=5")
```

---

## **STEP 4: Test Procedure (10 minutes)**

### **Setup (2 min)**

1. Open `c:\1225\project_s_super_core\escape water fpr brainrots.rbxl` in Roblox Studio
2. Manually create in Workspace:
   - `Stones` folder with 10 stone parts (`Stone_1`–`Stone_10`)
   - `PS_SPAWN` (SpawnLocation, blue, at 0, 10, 0)
   - `PS_BASE_DROPOFF` (Part, green, at 10, 11, 0)
   - `PS_WATER` (Part, cyan transparent, at 0, -20, 0)
3. Insert all 6 scripts above into ServerScriptService

### **Play (8 min)**

1. **Minute 0-1: Startup**
   - Click **Play** in Studio toolbar
   - Open **View** → **Output** at bottom
   - Look for prints without errors:
     ```
     [PROJECT_S_RESULT] STATUS=PASS water_system_loaded ...
     [PROJECT_S_RESULT] STATUS=PASS pickup_system_loaded ...
     [PROJECT_S_RESULT] STATUS=STARTUP all_systems=ready
     ```
   - ✅ **PASS** if all three lines appear

2. **Minute 1-3: Water Rise (Visibly)**
   - Watch PS_WATER part in 3D view
   - Water should rise slowly (~1 stud per 2 seconds)
   - ✅ **PASS** if water moves upward consistently

3. **Minute 3-6: Pickup Collection**
   - Move character to Stones area (around X=0-45, Z=0, Y>20)
   - Walk into yellow pickup spheres
   - Output should show:
     ```
     [PROJECT_S_RESULT] EVENT=PICKUP player=Player1 carried=1
     [PROJECT_S_RESULT] EVENT=PICKUP player=Player1 carried=2
     [PROJECT_S_RESULT] EVENT=PICKUP player=Player1 carried=3
     ```
   - Check leaderstats panel: `Money: 0` (unchanged)
   - Check player.Carried value: should be 3
   - Pickups should disappear then respawn after 10 sec
   - ✅ **PASS** if carried increments and pickups respawn

4. **Minute 6-8: Dropoff Conversion**
   - Move character to PS_BASE_DROPOFF (green part at 10, 11, 0)
   - Walk into it while carrying items
   - Output should show:
     ```
     [PROJECT_S_RESULT] EVENT=DROPOFF player=Player1 carried_converted=3 payout=15 total_money=15
     ```
   - Check leaderstats: `Money: 15` (increased)
   - Check player.Carried: should reset to 0
   - ✅ **PASS** if money increments correctly and carried resets

5. **Minute 8-9: Water Kill + Respawn**
   - Let water rise until it reaches player
   - Player should be killed and respawn at spawn location
   - Output should show:
     ```
     [PROJECT_S_RESULT] EVENT=WATER_KILL player=Player1 carried_reset=true
     ```
   - Check player.Carried: should be 0 after drowning
   - ✅ **PASS** if player respawns at PS_SPAWN

6. **Minute 9-10: Second Cycle (No Duplicates)**
   - Pick up 2 more pickups (respawned from Phase 3)
   - Move to dropoff and deliver
   - Output:
     ```
     [PROJECT_S_RESULT] EVENT=DROPOFF player=Player1 carried_converted=2 payout=10 total_money=25
     ```
   - Check Workspace Explorer: should have only 1 set of `PS_PICKUP_*` objects
   - ✅ **PASS** if no collision/duplicate objects

---

## **SUCCESS CRITERIA**

| Criterion | Expected | Fail If |
|-----------|----------|---------|
| **Startup** | 3+ status lines in Output, no errors | Missing lines or red errors |
| **Water rises** | Visible upward movement in 3D view | Water static or jumps |
| **Pickup increment** | Carried value increases per touch, max 5 | Stays 0 or exceeds 5 |
| **Dropoff payout** | Money increases by (carried × 5) | Money stays 0 or wrong calc |
| **Respawn** | Player resets to spawn on water contact | Player disappears or walks through |
| **Respawn resets carried** | Carried becomes 0 after water kill | Carried keeps value |
| **No duplicates** | Second run creates no extra objects | Explorer shows 20+ pickups |
| **Output format** | All prints match `[PROJECT_S_RESULT] ...` | Missing prefix or broken format |

---

## **Key Design Decisions**

| Aspect | Implementation | Reason |
|--------|---|---|
| **Scripts** | All 6 are `Script` in ServerScriptService (not LocalScript) | Server-authoritative |
| **Base location** | Adjacent to spawn at (10, 11, 0) | Easy access, clear design |
| **Pickup anchoring** | Fixed to `Workspace/Stones/Stone_N` positions | Manual control, no procedural generation |
| **Water kill** | Resets `Carried` to 0 on respawn | Fair penalty, prevents carry overflow |
| **Cleanup scope** | Only `PS_BUILD_*` deleted, not `PS_WATER`, `PS_PICKUP_*`, etc. | Preserves vertical slice, only removes build artifacts |
| **[PROJECT_S_RESULT] output** | All events tagged with prefix | Deterministic logging, easy validation |

---

## **Tuning Constants**

Located in script constants:

```
RISE_RATE = 0.5 studs/sec              (PS_WATER_RISE)
MAX_HEIGHT = 80 studs                  (PS_WATER_RISE)
PICKUP_RESPAWN_TIME = 10 sec           (PS_PICKUP_MANAGER)
PAYOUT_PER_ITEM = 5 money              (PS_DROPOFF_HANDLER)
CARRIED_CAP = 5 items                  (PS_PICKUP_MANAGER)
```

To adjust, edit the variables in the respective scripts.

---

## **File Structure After Implementation**

```
Workspace/
├── PS_SPAWN (SpawnLocation, Blue)
├── PS_BASE_DROPOFF (Part, Green)
├── PS_WATER (Part, Cyan, visible rising)
├── Stones/
│   ├── Stone_1
│   ├── Stone_2
│   └── ... Stone_10
├── Pickups/
│   ├── PS_PICKUP_1 (Part, Yellow, respawning)
│   ├── PS_PICKUP_2 (Part, Yellow, respawning)
│   └── ... PS_PICKUP_10 (Part, Yellow, respawning)
└── [original place objects untouched]

Players/
└── [PlayerName]/
    ├── leaderstats/
    │   ├── Money (IntValue = increases on dropoff)
    │   └── [visible in leaderboard]
    └── Carried (IntValue = 0-5, resets on water kill)

ServerScriptService/
├── PS_PLAYER_STATE_INIT (Script)
├── PS_WATER_RISE (Script)
├── PS_PICKUP_MANAGER (Script)
├── PS_DROPOFF_HANDLER (Script)
├── PS_DETERMINISTIC_CLEANUP (Script)
└── PS_VALIDATION_STARTUP (Script)
```

---

## **Troubleshooting**

| Issue | Cause | Fix |
|-------|-------|-----|
| **Scripts don't run / Output is empty** | Scripts not in ServerScriptService or syntax error | 1) Check all 6 scripts are `Script` type, not LocalScript 2) Double-click each to check for red squiggles 3) Check Output for error messages |
| **[PROJECT_S_RESULT] not printing** | Script execution failed before print | 1) Check `workspace:WaitForChild()` statements — make sure objects exist 2) Verify object names match exactly (case-sensitive) |
| **Pickups don't appear** | Stones folder missing or empty | 1) Create folder `Workspace/Stones` 2) Create 10 parts `Stone_1`–`Stone_10` inside |
| **Water not rising** | PS_WATER part missing or WaitForChild timeout | 1) Verify `PS_WATER` exists in Workspace 2) Check name spelling exactly |
| **Dropoff doesn't register** | PS_BASE_DROPOFF missing or player collision issue | 1) Verify `PS_BASE_DROPOFF` exists 2) Check player Humanoid has CanCollide=true |
| **Money not updating** | leaderstats structure wrong | 1) Check player has `leaderstats` folder with `Money` IntValue 2) PS_PLAYER_STATE_INIT should create this automatically |

---

**Ready to deploy. Open file and copy scripts into Studio.**
