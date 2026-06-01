-- Result Reporter
-- Produces machine-readable results and stores them

local ResultReporter = {}

local function resultToString(result)
	local lines = {
		"[PROJECT_S_RESULT] " .. result.status:upper(),
		"  status: " .. result.status,
		"  created_instances: " .. result.created_instances_count,
		"  root_path: " .. result.root_path,
		"  summary: " .. result.summary
	}
	
	if result.created_at then
		table.insert(lines, "  created_at: " .. result.created_at)
	end
	
	if result.execution_time_ms then
		table.insert(lines, "  execution_time_ms: " .. result.execution_time_ms)
	end
	
	if result.errors and #result.errors > 0 then
		table.insert(lines, "  errors:")
		for i, err in ipairs(result.errors) do
			table.insert(lines, "    [" .. i .. "] " .. tostring(err))
		end
	end
	
	return table.concat(lines, "\n")
end

local function storeInReplicatedStorage(result)
	local replicatedStorage = game:GetService("ReplicatedStorage")
	
	-- Create ProjectS folder if needed
	local projectSFolder = replicatedStorage:FindFirstChild("ProjectS")
	if not projectSFolder then
		projectSFolder = Instance.new("Folder")
		projectSFolder.Name = "ProjectS"
		projectSFolder.Parent = replicatedStorage
	end
	
	-- Create or update LastResult
	local lastResult = projectSFolder:FindFirstChild("LastResult")
	if lastResult then
		lastResult:Destroy()
	end
	
	lastResult = Instance.new("StringValue")
	lastResult.Name = "LastResult"
	lastResult.Value = resultToString(result)
	lastResult.Parent = projectSFolder
	
	return lastResult
end

function ResultReporter.report(result)
	-- Option A: Write to Output with prefix
	local reportString = resultToString(result)
	print(reportString)
	
	-- Option B: Store in ReplicatedStorage
	local stored = storeInReplicatedStorage(result)
	print("[Project-S] Result also stored in ReplicatedStorage.ProjectS.LastResult")
	
	return reportString
end

return ResultReporter
