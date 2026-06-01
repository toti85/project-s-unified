-- Roblox Studio Plugin: Project-S Build System
-- Entry point for the plugin
-- Installs toolbar button and handles patch execution

local PatchExecutor = require(script:WaitForChild("PatchExecutor"))
local ResultReporter = require(script:WaitForChild("ResultReporter"))
local PatchSchema = require(script:WaitForChild("PatchSchema"))

local plugin = plugin
local toolbar = plugin:CreateToolbar("Project-S")
local button = toolbar:CreateButton(
	"Apply Patch",
	"Execute Project-S build patch in Workspace",
	"rbxasset://textures/Workspace.png"
)

local function getDefaultPatch()
	return {
		type = "obby",
		levels = 3,
		theme = "neon"
	}
end

local function onButtonClicked()
	local success, errorMsg = pcall(function()
		print("[Project-S] Patch execution started...")
		
		-- Get default patch for MVP
		local patch = getDefaultPatch()
		
		-- Validate patch schema
		local isValid, validationError = PatchSchema.validate(patch)
		if not isValid then
			error("Patch validation failed: " .. tostring(validationError))
		end
		
		-- Execute patch
		local result = PatchExecutor.execute(patch)
		
		-- Report results
		ResultReporter.report(result)
		
		print("[Project-S] Patch execution completed successfully")
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

button.Click:Connect(onButtonClicked)

print("[Project-S Plugin] Loaded successfully - click 'Apply Patch' to start")
