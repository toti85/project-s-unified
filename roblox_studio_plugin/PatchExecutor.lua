-- Patch Executor
-- Creates deterministic obby structure in Workspace

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
	
	-- Add spawn location
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
	
	local success, errorMsg = pcall(function()
		-- Create root folder with timestamp
		local rootName = "PS_BUILD_" .. os.time()
		local rootFolder = Instance.new("Folder")
		rootFolder.Name = rootName
		rootFolder.Parent = game:GetService("Workspace")
		
		-- Create spawn pad
		local spawn = createSpawn(rootFolder)
		createdCount = createdCount + 1
		
		-- Create platforms
		for i = 1, patch.levels do
			local platform = createPlatform(rootFolder, i, patch.theme or "classic")
			createdCount = createdCount + 1
		end
		
		-- Create checkpoints (one per level)
		for i = 1, patch.levels do
			local checkpoint = createCheckpoint(rootFolder, i)
			createdCount = createdCount + 1
		end
		
		-- Create finish pad
		local finishPad = createFinishPad(rootFolder, patch.levels)
		createdCount = createdCount + 1
		
		-- Add touch detector to finish pad
		local finishTouched = false
		finishPad.Touched:Connect(function(hit)
			if not finishTouched then
				local humanoid = hit.Parent:FindFirstChild("Humanoid")
				if humanoid then
					finishTouched = true
					game:GetService("Workspace").CurrentCamera.CFrame = finishPad.CFrame + Vector3.new(0, 5, 20)
				end
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

return PatchExecutor
