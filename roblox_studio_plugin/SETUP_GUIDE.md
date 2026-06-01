# Roblox Studio Plugin Setup Guide

## Plugin Installation Steps

### Step 1: Find the Plugin Directory
Roblox Studio plugins are stored in a local directory. The location depends on your OS:

**Windows:**
```
C:\Users\{YourUsername}\AppData\Local\Roblox\Plugins
```

**macOS:**
```
~/Library/Application Support/Roblox/Plugins
```

**Linux:**
```
~/.local/share/Roblox/Plugins
```

### Step 2: Copy Plugin Files
1. Navigate to the plugin folder above
2. Create a new folder called `ProjectSBuild`
3. Copy all four Luau files into that folder:
   - `plugin.lua` (entry point)
   - `PatchSchema.lua`
   - `PatchExecutor.lua`
   - `ResultReporter.lua`

**Folder Structure:**
```
Plugins/
└── ProjectSBuild/
    ├── plugin.lua
    ├── PatchSchema.lua
    ├── PatchExecutor.lua
    └── ResultReporter.lua
```

### Step 3: Enable the Plugin in Roblox Studio

1. **Open Roblox Studio**
2. Go to **Plugins** menu → **Manage Plugins**
3. Look for **"Project-S"** in the plugin list
4. Check the box to **enable** it
5. Close the Manage Plugins dialog

### Step 4: Verify Installation

1. Look for a **"Project-S"** toolbar in the top menu bar
2. You should see a button labeled **"Apply Patch"**
3. If you see it, the plugin is installed successfully

### Step 5: Test the Plugin

1. **Open or create a new place file** in Roblox Studio (blank baseplate is fine)
2. Click the **"Apply Patch"** button in the Project-S toolbar
3. **Check the Output window** (View → Output):
   - You should see logs starting with `[Project-S]`
   - Look for `[PROJECT_S_RESULT] SUCCESS`
4. **Check the Workspace**:
   - A new folder should appear named `PS_BUILD_<timestamp>`
   - Inside should be platforms, checkpoints, and a finish pad

---

## Plugin Structure Explained

### `plugin.lua` (Entry Point)
- Creates toolbar and button
- Orchestrates patch execution
- Error handling wrapper
- Prints to Output

### `PatchSchema.lua` (Validation)
- Validates patch structure
- Checks required fields (type, levels)
- Range validation on numeric fields

### `PatchExecutor.lua` (Core Logic)
- Creates obby structure deterministically
- Creates platforms with themed colors
- Creates checkpoints (green balls)
- Creates finish pad (red platform)
- Returns detailed result object

### `ResultReporter.lua` (Output)
- Formats results with `[PROJECT_S_RESULT]` prefix
- Stores results in ReplicatedStorage.ProjectS.LastResult
- Prints to Output window

---

## File Format Details

### Result Object Structure
```
{
  status: "success" | "error",
  created_instances_count: number,
  root_path: "PS_BUILD_<timestamp>" | "N/A",
  errors: string[],
  summary: string,
  created_at: string (ISO format),
  execution_time_ms: number
}
```

### Output Format
Results are printed with prefix: `[PROJECT_S_RESULT]`

Example:
```
[PROJECT_S_RESULT] SUCCESS
  status: success
  created_instances: 7
  root_path: PS_BUILD_1705430000
  summary: Created obby with 3 levels (0.12s)
  created_at: 2026-01-17 10:30:00
  execution_time_ms: 120
```

---

## Troubleshooting

### Plugin doesn't appear in toolbar
- **Cause:** Plugin wasn't enabled in Manage Plugins
- **Solution:** Go to Plugins → Manage Plugins and check the box for Project-S

### "Cannot require script" error in Output
- **Cause:** Module files not in same directory as plugin.lua
- **Solution:** Ensure all 4 Lua files are in the ProjectSBuild folder

### Objects appear in wrong location
- **Cause:** Workspace service not found (rare in Studio)
- **Solution:** Restart Roblox Studio

### Output prefix not found
- **Cause:** Plugin loaded but button not clicked
- **Solution:** Click "Apply Patch" button explicitly

---

## File Paths Reference

**Plugin Root:** `C:\Users\{User}\AppData\Local\Roblox\Plugins\ProjectSBuild\`

**Files:**
- Entry: `plugin.lua`
- Config: `PatchSchema.lua`
- Logic: `PatchExecutor.lua`
- Output: `ResultReporter.lua`

**Result Storage:**
- Output: Studio Output window (search for `[PROJECT_S_RESULT]`)
- ReplicatedStorage: `ReplicatedStorage/ProjectS/LastResult` (StringValue)

---

## Enabling/Disabling the Plugin

### To Enable
1. Plugins → Manage Plugins
2. Find "Project-S"
3. Check the box
4. Click OK

### To Disable
1. Plugins → Manage Plugins
2. Find "Project-S"
3. Uncheck the box
4. Click OK

### To Uninstall
1. Navigate to `C:\Users\{User}\AppData\Local\Roblox\Plugins\`
2. Delete the `ProjectSBuild` folder
3. Restart Roblox Studio

---

## Manual Verification Checklist

After installation:
- [ ] Plugin appears in Manage Plugins list
- [ ] Plugin toolbar button is visible
- [ ] Button click opens Output window
- [ ] Output shows `[PROJECT_S_RESULT] SUCCESS`
- [ ] New folder created in Workspace
- [ ] Folder name matches `PS_BUILD_<number>` pattern
- [ ] Contains platforms, checkpoints, and finish pad
- [ ] ReplicatedStorage.ProjectS.LastResult exists
- [ ] No permission errors in Output

---

**Version:** 1.0  
**Date:** January 17, 2026  
**Status:** Ready for testing
