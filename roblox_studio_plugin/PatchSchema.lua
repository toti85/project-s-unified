-- Patch Schema Validation
-- Validates that patches conform to required structure

local PatchSchema = {}

function PatchSchema.validate(patch)
	-- Type check
	if not patch or type(patch) ~= "table" then
		return false, "Patch must be a table"
	end
	
	-- Required fields
	if not patch.type then
		return false, "Missing required field: type"
	end
	
	if patch.type ~= "obby" then
		return false, "Unsupported patch type: " .. tostring(patch.type)
	end
	
	if not patch.levels or type(patch.levels) ~= "number" then
		return false, "Missing or invalid field: levels (must be number)"
	end
	
	if patch.levels < 1 or patch.levels > 100 then
		return false, "Field 'levels' must be between 1 and 100"
	end
	
	-- Optional fields with defaults
	if patch.theme and type(patch.theme) ~= "string" then
		return false, "Field 'theme' must be string"
	end
	
	return true
end

return PatchSchema
