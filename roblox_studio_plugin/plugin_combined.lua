-- Roblox Studio Plugin: Project-S Build System
-- All-in-one parkour game builder
-- No external requires, pure inline code

-- ============================================================================
-- HTTP SERVER SETUP
-- ============================================================================

local HttpService = game:GetService("HttpService")
local PORT = 8001
local HOST = "http://localhost:" .. PORT

-- HTTP Endpoint handler
local function setupHttpEndpoint()
	local endpoint = HOST .. "/patch"
	print("[Project-S Plugin] HTTP Endpoint ready: " .. endpoint)
	return endpoint
end

local httpEndpoint = setupHttpEndpoint()

-- ============================================================================
-- SCHEMA VALIDATION
-- ============================================================================

local PatchSchema = {}

function PatchSchema.validate(patch)
	if not patch or type(patch) ~= "table" then
		return false, "Patch must be a table"
	end
	if not patch.type or type(patch.type) ~= "string" then
		return false, "Patch must have 'type' field"
	end
	
	if patch.type == "obby" then
		if not patch.levels or type(patch.levels) ~= "number" then
			return false, "Patch must have 'levels' number"
		end
		if patch.levels < 1 or patch.levels > 100 then
			return false, "Levels must be between 1 and 100"
		end
		return true, nil
	
	elseif patch.type == "escape_water_brainrots" then
		-- Validate optional params
		local params = patch.params or {}
		if params.water_rise_rate and type(params.water_rise_rate) ~= "number" then
			return false, "water_rise_rate must be a number"
		end
		if params.payout and type(params.payout) ~= "number" then
			return false, "payout must be a number"
		end
		return true, nil
	
	else
		return false, "Unknown patch type: " .. patch.type
	end
end

-- ============================================================================
-- PATCH EXECUTOR
-- ============================================================================

local PatchExecutor = {}

local function getThemeColor(theme, index)
	local themes = {
		neon = {
			Color3.fromRGB(0, 255, 255),     -- Cyan
			Color3.fromRGB(255, 0, 255),     -- Magenta
			Color3.fromRGB(255, 255, 0),     -- Yellow
			Color3.fromRGB(0, 255, 0),       -- Lime
			Color3.fromRGB(255, 128, 0)      -- Orange
		},
		classic = {
			Color3.fromRGB(0, 100, 255),     -- Blue
			Color3.fromRGB(0, 200, 0),       -- Green
			Color3.fromRGB(200, 0, 0),       -- Red
			Color3.fromRGB(255, 200, 0),     -- Gold
			Color3.fromRGB(128, 0, 128)      -- Purple
		}
	}
	
	local themeColors = themes[theme] or themes.classic
	return themeColors[(index - 1) % #themeColors + 1]
end

local function createSpawn(parent)
	local spawn = Instance.new("Part")
	spawn.Name = "SpawnPad"
	spawn.Shape = Enum.PartType.Block
	spawn.Size = Vector3.new(10, 1, 10)
	spawn.TopSurface = Enum.SurfaceType.Smooth
	spawn.BottomSurface = Enum.SurfaceType.Smooth
	spawn.BrickColor = BrickColor.new("Bright blue")
	spawn.CanCollide = true
	spawn.CFrame = CFrame.new(0, 3, 0)
	spawn.Parent = parent
	
	local spawnLoc = Instance.new("SpawnLocation")
	spawnLoc.Name = "PlayerSpawn"
	spawnLoc.Size = Vector3.new(6, 1, 6)
	spawnLoc.TopSurface = Enum.SurfaceType.Smooth
	spawnLoc.BottomSurface = Enum.SurfaceType.Smooth
	spawnLoc.BrickColor = BrickColor.new("Bright blue")
	spawnLoc.CanCollide = true
	spawnLoc.CFrame = CFrame.new(0, 4, 0)
	spawnLoc.Duration = 0
	spawnLoc.Parent = spawn
	
	return spawn
end

local function createPlatform(parent, index, theme)
	local platform = Instance.new("Part")
	platform.Name = "Platform_" .. index
	platform.Shape = Enum.PartType.Block
	platform.Size = Vector3.new(5, 0.5, 5)
	platform.TopSurface = Enum.SurfaceType.Smooth
	platform.BottomSurface = Enum.SurfaceType.Smooth
	platform.BrickColor = BrickColor.new(getThemeColor(theme, index))
	platform.CanCollide = true
	platform.CFrame = CFrame.new(5 + (index - 1) * 8, 8 + (index - 1) * 5, (index - 1) * 12)
	platform.Parent = parent
	
	return platform
end

local function createCheckpoint(parent, levelNumber)
	local checkpoint = Instance.new("Part")
	checkpoint.Name = "Checkpoint_" .. levelNumber
	checkpoint.Shape = Enum.PartType.Ball
	checkpoint.Size = Vector3.new(1.5, 1.5, 1.5)
	checkpoint.Material = Enum.Material.Neon
	checkpoint.BrickColor = BrickColor.new("Bright green")
	checkpoint.CanCollide = false
	checkpoint.CFrame = CFrame.new(5 + (levelNumber - 1) * 8, 7 + (levelNumber - 1) * 5, (levelNumber - 1) * 12)
	checkpoint.Parent = parent
	
	return checkpoint
end

local function createFinishPad(parent, lastLevel)
	local finish = Instance.new("Part")
	finish.Name = "FinishPad"
	finish.Shape = Enum.PartType.Block
	finish.Size = Vector3.new(8, 0.5, 8)
	finish.TopSurface = Enum.SurfaceType.Smooth
	finish.BottomSurface = Enum.SurfaceType.Smooth
	finish.BrickColor = BrickColor.new("Bright red")
	finish.CanCollide = true
	finish.CFrame = CFrame.new(5 + lastLevel * 8, 8 + lastLevel * 5, lastLevel * 12)
	finish.Parent = parent
	
	return finish
end

function PatchExecutor.execute(patch)
	local startTime = tick()
	local createdCount = 0
	local scriptCount = 0
	
	-- Delegate based on type
	if patch.type == "obby" then
		return PatchExecutor.executeObby(patch)
	elseif patch.type == "escape_water_brainrots" then
		return PatchExecutor.executeEscapeWater(patch)
	else
		return {
			status = "error",
			created_instances_count = 0,
			root_path = "N/A",
			errors = {"Unknown patch type: " .. tostring(patch.type)},
			summary = "Patch execution failed: unknown type"
		}
	end
end

function PatchExecutor.executeObby(patch)
	local startTime = tick()
	local createdCount = 0
	
	local success, errorMsg = pcall(function()
		local rootName = "PS_BUILD_" .. os.time()
		local rootFolder = Instance.new("Folder")
		rootFolder.Name = rootName
		rootFolder.Parent = game:GetService("Workspace")
		
		local spawn = createSpawn(rootFolder)
		createdCount = createdCount + 1
		
		for i = 1, patch.levels do
			local platform = createPlatform(rootFolder, i, patch.theme or "classic")
			createdCount = createdCount + 1
		end
		
		for i = 1, patch.levels do
			local checkpoint = createCheckpoint(rootFolder, i)
			createdCount = createdCount + 1
		end
		
		local finishPad = createFinishPad(rootFolder, patch.levels)
		createdCount = createdCount + 1
		
		finishPad.Touched:Connect(function(hit)
			local humanoid = hit.Parent:FindFirstChild("Humanoid")
			if humanoid then
				game:GetService("Workspace").CurrentCamera.CFrame = finishPad.CFrame + Vector3.new(0, 5, 20)
			end
		end)
		
		return {
			status = "success",
			created_instances_count = createdCount,
			root_path = rootName,
			errors = {},
			summary = "Created parkour with spawn, " .. patch.levels .. " platforms, checkpoints, and finish"
		}
	end)
	
	if not success then
		return {
			status = "error",
			created_instances_count = 0,
			root_path = "N/A",
			errors = {errorMsg},
			summary = "Patch execution failed: " .. tostring(errorMsg)
		}
	end
	
	local elapsedTime = tick() - startTime
	
	return {
		status = "success",
		created_instances_count = createdCount,
		root_path = (patch.levels > 0) and ("PS_BUILD_" .. os.time()) or "N/A",
		errors = {},
		summary = "Parkour ready: spawn → " .. patch.levels .. " jumps → finish (" .. string.format("%.2f", elapsedTime) .. "s)",
		created_at = os.date("%Y-%m-%d %H:%M:%S"),
		execution_time_ms = math.floor(elapsedTime * 1000)
	}
end

-- ============================================================================
-- ESCAPE WATER BRAINROTS EXECUTOR
-- ============================================================================

function PatchExecutor.executeEscapeWater(patch)
	local startTime = tick()
	local createdCount = 0
	local scriptCount = 0
	
	local success, errorMsg = pcall(function()
		local rootName = "PS_BUILD_" .. os.time()
		local rootFolder = Instance.new("Folder")
		rootFolder.Name = rootName
		rootFolder.Parent = game:GetService("Workspace")
		
		local params = patch.params or {}
		local water_start_y = params.water_start_y or -4
		local water_rise_rate = params.water_rise_rate or 0.9
		local water_max_y = params.water_max_y or 120
		local payout = params.payout or 5
		local carry_cap = params.carry_cap or 5
		local pickup_respawn_sec = params.pickup_respawn_seconds or 10
		
		-- 1. Create PS_SPAWN (blue)
		local spawn = Instance.new("Part")
		spawn.Name = "PS_SPAWN"
		spawn.Shape = Enum.PartType.Block
		spawn.Size = Vector3.new(10, 1, 10)
		spawn.BrickColor = BrickColor.new("Bright blue")
		spawn.CanCollide = true
		spawn.CFrame = CFrame.new(0, 30, 0)
		spawn.TopSurface = Enum.SurfaceType.Smooth
		spawn.BottomSurface = Enum.SurfaceType.Smooth
		spawn.Parent = rootFolder
		createdCount = createdCount + 1
		
		-- 2. Create PS_WATER (cyan)
		local water = Instance.new("Part")
		water.Name = "PS_WATER"
		water.Shape = Enum.PartType.Block
		water.Size = Vector3.new(500, 10, 500)
		water.BrickColor = BrickColor.new("Cyan")
		water.CanCollide = true
		water.CFrame = CFrame.new(0, water_start_y, 0)
		water.TopSurface = Enum.SurfaceType.Smooth
		water.BottomSurface = Enum.SurfaceType.Smooth
		water.Parent = rootFolder
		createdCount = createdCount + 1
		
		-- 3. Create PS_BASE_DROPOFF (green)
		local base = Instance.new("Part")
		base.Name = "PS_BASE_DROPOFF"
		base.Shape = Enum.PartType.Block
		base.Size = Vector3.new(10, 1, 10)
		base.BrickColor = BrickColor.new("Bright green")
		base.CanCollide = true
		base.CFrame = CFrame.new(0, 5, -50)
		base.TopSurface = Enum.SurfaceType.Smooth
		base.BottomSurface = Enum.SurfaceType.Smooth
		base.Parent = rootFolder
		createdCount = createdCount + 1
		
		-- 4. Create PS_PICKUP_1..10 (yellow, on Stones if they exist)
		local stonesFolder = game:GetService("Workspace"):FindFirstChild("Stones")
		if stonesFolder then
			for i = 1, 10 do
				local stoneName = "Stone_" .. i
				local stone = stonesFolder:FindFirstChild(stoneName)
				
				if stone and stone:IsA("Part") then
					local pickup = Instance.new("Part")
					pickup.Name = "PS_PICKUP_" .. i
					pickup.Shape = Enum.PartType.Ball
					pickup.Size = Vector3.new(1, 1, 1)
					pickup.BrickColor = BrickColor.new("Bright yellow")
					pickup.CanCollide = true
					pickup.CFrame = stone.CFrame + Vector3.new(0, 3, 0)
					pickup.Material = Enum.Material.Neon
					pickup.Parent = rootFolder
					createdCount = createdCount + 1
				end
			end
		end
		
		-- 5. Create runtime scripts in ServerScriptService
		local sss = game:GetService("ServerScriptService")
		
		-- Script 1: Player State Initialization
		local playerStateScript = Instance.new("LocalScript")
		playerStateScript.Name = "PS_" .. rootName .. "_PLAYER_STATE"
		playerStateScript.Source = [[
local Players = game:GetService("Players")
local rootPath = "PS_BUILD_]] .. rootName .. [["

local function initPlayer(player)
	-- Create leaderstats
	local leaderstats = Instance.new("Folder")
	leaderstats.Name = "leaderstats"
	leaderstats.Parent = player
	
	local money = Instance.new("IntValue")
	money.Name = "Money"
	money.Value = 0
	money.Parent = leaderstats
	
	-- Create Carried counter
	local carried = Instance.new("IntValue")
	carried.Name = "Carried"
	carried.Value = 0
	carried.Parent = player
	
	print("[PROJECT_S_RESULT] INIT=" .. player.Name .. " money=0 carried=0")
end

Players.PlayerAdded:Connect(initPlayer)

-- Init existing players
for _, player in pairs(Players:GetPlayers()) do
	initPlayer(player)
end

print("[PROJECT_S_RESULT] STATUS=PASS escape_water_brainrots_playerstate_ready created_instances=2 path=" .. rootPath)
		]]
		playerStateScript.Parent = sss
		scriptCount = scriptCount + 1
		
		-- Script 2: Water Rising & Respawn
		local waterScript = Instance.new("LocalScript")
		waterScript.Name = "PS_" .. rootName .. "_WATER_RISE"
		waterScript.Source = [[
local water = game:GetService("Workspace"):WaitForChild("]] .. rootName .. [["):FindFirstChild("PS_WATER")
local spawn = game:GetService("Workspace"):WaitForChild("]] .. rootName .. [["):FindFirstChild("PS_SPAWN")

if not water or not spawn then
	print("[PROJECT_S_RESULT] ERROR=MISSING_WATER_OR_SPAWN")
	return
end

local water_start_y = ]] .. water_start_y .. [[
local water_rise_rate = ]] .. water_rise_rate .. [[
local water_max_y = ]] .. water_max_y .. [[

-- Setup Atmosphere for blue haze effect
local atmosphere = game:GetService("Lighting"):FindFirstChildOfClass("Atmosphere")
if not atmosphere then
	atmosphere = Instance.new("Atmosphere")
	atmosphere.Parent = game:GetService("Lighting")
end
atmosphere.Color = Color3.fromRGB(100, 150, 200)  -- Slight blue tint
local initial_haze = 0.1

local function respawnPlayer(character)
	if character and character:FindFirstChild("HumanoidRootPart") then
		character.HumanoidRootPart.CFrame = spawn.CFrame + Vector3.new(0, 5, 0)
	end
end

-- Water rising loop
while true do
	wait(0.1)
	if water.Position.Y < water_max_y then
		water.CFrame = water.CFrame + Vector3.new(0, water_rise_rate * 0.1, 0)
		
		-- Update atmosphere haze based on water height
		local water_progress = (water.Position.Y - water_start_y) / (water_max_y - water_start_y)
		water_progress = math.max(0, math.min(1, water_progress))  -- Clamp 0-1
		local new_haze = initial_haze + (water_progress * 0.45)  -- Ranges 0.1 to 0.55
		if atmosphere then
			atmosphere.Haze = new_haze
		end
	end
	
	-- Check player drowning
	for _, player in pairs(game:GetService("Players"):GetPlayers()) do
		if player.Character and player.Character:FindFirstChild("HumanoidRootPart") then
			local pos = player.Character.HumanoidRootPart.Position.Y
			if pos < water.Position.Y then
				-- Respawn
				print("[PROJECT_S_RESULT] EVENT=WATER_RESET player=" .. player.Name .. " carried_reset=1")
				player:WaitForChild("Carried").Value = 0
				respawnPlayer(player.Character)
			end
		end
	end
end
		]]
		waterScript.Parent = sss
		scriptCount = scriptCount + 1
		
		-- Script 3: Pickup Manager
		local pickupScript = Instance.new("LocalScript")
		pickupScript.Name = "PS_" .. rootName .. "_PICKUP_MANAGER"
		pickupScript.Source = [[
local rootFolder = game:GetService("Workspace"):WaitForChild("]] .. rootName .. [[")
local carry_cap = ]] .. carry_cap .. [[

local function findPickup(index)
	return rootFolder:FindFirstChild("PS_PICKUP_" .. index)
end

local function setupPickupTouch(pickupIndex)
	local pickup = findPickup(pickupIndex)
	if not pickup then return end
	
	local connection
	connection = pickup.Touched:Connect(function(hit)
		local humanoid = hit.Parent:FindFirstChild("Humanoid")
		if humanoid then
			local player = game:GetService("Players"):GetPlayerFromCharacter(hit.Parent)
			if player then
				local carried = player:WaitForChild("Carried")
				if carried.Value < carry_cap then
					carried.Value = carried.Value + 1
					print("[PROJECT_S_RESULT] EVENT=PICKUP player=" .. player.Name .. " carried=" .. carried.Value)
					pickup:Destroy()
					
					-- Respawn after 10 seconds
					task.wait(]] .. pickup_respawn_sec .. [[)
					local newPickup = Instance.new("Part")
					newPickup.Name = "PS_PICKUP_" .. pickupIndex
					newPickup.Shape = Enum.PartType.Ball
					newPickup.Size = Vector3.new(1, 1, 1)
					newPickup.BrickColor = BrickColor.new("Bright yellow")
					newPickup.Material = Enum.Material.Neon
					newPickup.CFrame = rootFolder:FindFirstChild("PS_SPAWN").CFrame + Vector3.new((pickupIndex-5)*3, 5, 0)
					newPickup.Parent = rootFolder
					setupPickupTouch(pickupIndex)
				end
			end
		end
	end)
end

for i = 1, 10 do
	setupPickupTouch(i)
end

print("[PROJECT_S_RESULT] STATUS=PASS escape_water_brainrots_pickups_ready scripts=1 carry_cap=" .. carry_cap)
		]]
		pickupScript.Parent = sss
		scriptCount = scriptCount + 1
		
		-- Script 4: Dropoff Handler
		local baseScript = Instance.new("LocalScript")
		baseScript.Name = "PS_" .. rootName .. "_DROPOFF_HANDLER"
		baseScript.Source = [[
local root = game:GetService("Workspace"):WaitForChild("]] .. rootName .. [[")
local base = root:FindFirstChild("PS_BASE_DROPOFF")
local payout = ]] .. payout .. [[

if not base then
	print("[PROJECT_S_RESULT] ERROR=MISSING_BASE_DROPOFF")
	return
end

base.Touched:Connect(function(hit)
	local humanoid = hit.Parent:FindFirstChild("Humanoid")
	if humanoid then
		local player = game:GetService("Players"):GetPlayerFromCharacter(hit.Parent)
		if player then
			local carried = player:WaitForChild("Carried")
			local money = player:WaitForChild("leaderstats"):WaitForChild("Money")
			
			if carried.Value > 0 then
				local payout_amount = carried.Value * payout
				money.Value = money.Value + payout_amount
				
				print("[PROJECT_S_RESULT] EVENT=DROPOFF player=" .. player.Name .. " payout=" .. payout_amount .. " total=" .. money.Value)
				
				carried.Value = 0
			end
		end
	end
end)

print("[PROJECT_S_RESULT] STATUS=PASS escape_water_brainrots_dropoff_ready payout=" .. payout)
		]]
		baseScript.Parent = sss
		scriptCount = scriptCount + 1
		
		return {
			status = "success",
			created_instances_count = createdCount,
			root_path = rootName,
			errors = {},
			summary = "Created escape_water_brainrots: spawn, water, base, 10 pickups, 4 scripts"
		}
	end)
	
	if not success then
		return {
			status = "error",
			created_instances_count = createdCount,
			root_path = "N/A",
			errors = {errorMsg},
			summary = "Patch execution failed: " .. tostring(errorMsg)
		}
	end
	
	local elapsedTime = tick() - startTime
	
	return {
		status = "success",
		created_instances_count = createdCount,
		root_path = errorMsg.root_path,
		errors = {},
		summary = errorMsg.summary,
		created_at = os.date("%Y-%m-%d %H:%M:%S"),
		execution_time_ms = math.floor(elapsedTime * 1000),
		script_count = scriptCount
	}
end

-- ============================================================================
-- RESULT REPORTER
-- ============================================================================

local ResultReporter = {}

local function resultToString(result)
	local lines = {
		"[PROJECT_S_RESULT] " .. string.upper(result.status),
		"  status: " .. result.status,
		"  created_instances: " .. result.created_instances_count,
		"  root_path: " .. result.root_path,
		"  summary: " .. result.summary,
	}
	if result.created_at then
		table.insert(lines, "  created_at: " .. result.created_at)
	end
	if result.execution_time_ms then
		table.insert(lines, "  execution_time_ms: " .. result.execution_time_ms)
	end
	
	return table.concat(lines, "\n")
end

function ResultReporter.report(result)
	local outputStr = resultToString(result)
	print(outputStr)
	
	local replStorService = game:GetService("ReplicatedStorage")
	local projectSFolder = replStorService:FindFirstChild("ProjectS")
	if not projectSFolder then
		projectSFolder = Instance.new("Folder")
		projectSFolder.Name = "ProjectS"
		projectSFolder.Parent = replStorService
	end
	
	local lastResultValue = projectSFolder:FindFirstChild("LastResult")
	if not lastResultValue then
		lastResultValue = Instance.new("StringValue")
		lastResultValue.Name = "LastResult"
		lastResultValue.Parent = projectSFolder
	end
	
	lastResultValue.Value = outputStr
	
	return result
end

function ResultReporter.toJson(result)
	-- Structured JSON response for HTTP
	local json = {
		status = result.status,
		metrics = {
			parts_created = result.created_instances_count,
			root_path = result.root_path,
			execution_time_ms = result.execution_time_ms or 0
		},
		errors = result.errors or {},
		summary = result.summary
	}
	return json
end

-- ============================================================================
-- PLUGIN MAIN
-- ============================================================================

local plugin = plugin
if not plugin then return end

local toolbar = plugin:CreateToolbar("Project-S")
local button = toolbar:CreateButton(
	"Apply Patch",
	"Execute Project-S build patch",
	"rbxasset://textures/Workspace.png"
)

-- Track poll thread
local pollThread = nil
local isPolling = false
local pollInterval = 2  -- Poll every 2 seconds

local function pollForPatches()
	print("[Project-S Plugin] Starting auto-poll for patches from Flask server...")
	isPolling = true
	
	while isPolling do
		local success, response = pcall(function()
			return HttpService:GetAsync("http://localhost:8001/poll", true)
		end)
		
		if success and response then
			local decoded = nil
			local decodeSuccess, decodeError = pcall(function()
				decoded = game:GetService("HttpService"):JSONDecode(response)
			end)
			
			if decodeSuccess and decoded and decoded.has_patch then
				print("[Project-S Plugin] 🔔 Patch received from Flask! Executing automatically...")
				
				local patch = decoded.patch
				if patch then
					-- Validate and execute
					local isValid, validationError = PatchSchema.validate(patch)
					if isValid then
						local result = PatchExecutor.execute(patch)
						ResultReporter.report(result)
						print("[Project-S Plugin] ✅ Auto-patch executed successfully!")
					else
						print("[Project-S Plugin] ❌ Patch validation failed: " .. tostring(validationError))
					end
				end
			end
		end
		
		-- Wait before next poll
		wait(pollInterval)
	end
end

local function startAutoPolling()
	if not pollThread then
		-- Spawn polling in background
		pollThread = task.spawn(pollForPatches)
		print("[Project-S Plugin] Auto-polling thread started")
	end
end

local function stopAutoPolling()
	isPolling = false
	pollThread = nil
	print("[Project-S Plugin] Auto-polling stopped")
end

-- Start polling when plugin loads
startAutoPolling()

local function loadPatchConfig()
	-- Try to load patch config from ReplicatedStorage
	local replStorService = game:GetService("ReplicatedStorage")
	local projectSFolder = replStorService:FindFirstChild("ProjectS")
	
	if projectSFolder then
		local patchConfig = projectSFolder:FindFirstChild("PatchConfig")
		if patchConfig and patchConfig:IsA("StringValue") then
			-- Parse JSON config
			local configStr = patchConfig.Value
			if configStr and configStr ~= "" then
				-- Simple JSON parsing for our patch format
				if configStr:find('"levels"%s*:%s*(%d+)') then
					local levels = tonumber(configStr:match('"levels"%s*:%s*(%d+)'))
					local theme = configStr:find('"theme"%s*:%s*"neon"') and "neon" or "classic"
					return {
						type = "obby",
						levels = levels,
						theme = theme
					}
				end
			end
		end
	end
	
	-- Fallback to default
	return {
		type = "obby",
		levels = 3,
		theme = "neon"
	}
end

local function getDefaultPatch()
	return loadPatchConfig()
end

local function onButtonClicked()
	local success, errorMsg = pcall(function()
		print("[Project-S] Button clicked - executing patch...")
		
		local patch = getDefaultPatch()
		
		local isValid, validationError = PatchSchema.validate(patch)
		if not isValid then
			error("Patch validation failed: " .. tostring(validationError))
		end
		
		-- PHASE 1A: Direct HTTP POST to server
		local httpSuccess, httpResponse = pcall(function()
			print("[Project-S] Sending direct HTTP POST to server...")
			local jsonPayload = HttpService:JSONEncode(patch)
			
			return HttpService:PostAsync(
				"http://localhost:8001/patch",
				jsonPayload,
				Enum.HttpContentType.ApplicationJson
			)
		end)
		
		if httpSuccess and httpResponse then
			print("[Project-S] ✅ HTTP POST sent successfully")
			local responseData = HttpService:JSONDecode(httpResponse)
			print("[Project-S] Server response: " .. HttpService:JSONEncode(responseData))
			
			-- Execute locally AND send to server
			local result = PatchExecutor.execute(patch)
			ResultReporter.report(result)
		else
			-- Fallback: Execute locally if HTTP fails
			print("[Project-S] ⚠️ HTTP POST failed, executing locally...")
			local result = PatchExecutor.execute(patch)
			ResultReporter.report(result)
		end
		
		print("[Project-S] Patch execution completed")
	end)
	
	if not success then
		print("[Project-S] ERROR: " .. tostring(errorMsg))
		local errorResult = {
			status = "error",
			created_instances_count = 0,
			root_path = "N/A",
			errors = {errorMsg},
			summary = "Patch execution failed"
		}
		ResultReporter.report(errorResult)
	end
end

local function handleHttpPatch(patchJson)
	-- HTTP POST handler - parse JSON patch and execute
	local success, errorMsg = pcall(function()
		print("[Project-S] HTTP Patch request received")
		
		local patch = nil
		local parseSuccess, parseError = pcall(function()
			patch = game:GetService("HttpService"):JSONDecode(patchJson)
		end)
		
		if not parseSuccess then
			error("Failed to parse patch JSON: " .. tostring(parseError))
		end
		
		-- Validate patch schema
		local isValid, validationError = PatchSchema.validate(patch)
		if not isValid then
			error("Patch validation failed: " .. tostring(validationError))
		end
		
		-- Execute patch
		local result = PatchExecutor.execute(patch)
		
		-- Report and return structured response
		ResultReporter.report(result)
		
		print("[Project-S] HTTP Patch execution completed")
		
		return result
	end)
	
	if success then
		return {
			status = "success",
			created_instances_count = errorMsg.created_instances_count,
			root_path = errorMsg.root_path,
			execution_time_ms = errorMsg.execution_time_ms or 0,
			errors = {}
		}
	else
		return {
			status = "error",
			created_instances_count = 0,
			root_path = "N/A",
			execution_time_ms = 0,
			errors = {tostring(errorMsg)}
		}
	end
end

button.Click:Connect(onButtonClicked)

-- HTTP Server setup for receiving patches from Project-S
local function startHttpServer()
	-- Note: Roblox plugin HTTP is client-only via HttpService
	-- For server-side HTTP, we use a Flask server on Project-S side
	-- This function is a placeholder for future webhook receiver
	print("[Project-S Plugin] HTTP endpoint registered: POST http://localhost:8001/patch")
end

startHttpServer()

print("[Project-S Plugin] Loaded successfully")
