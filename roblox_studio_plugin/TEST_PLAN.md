# Plugin Test Plan

## Overview
This document outlines the test procedure for the Project-S Roblox Studio Plugin.

**Total Tests:** 3  
**Expected Duration:** ~5 minutes per test  
**Requirements:** Roblox Studio + plugin installed

---

## TEST 1: Basic Execution (Empty Baseplate)

### Setup
1. Open Roblox Studio
2. Create a new **Blank Baseplate** place
3. Enable the Project-S plugin (if not already)
4. Open **Output window** (View → Output)

### Execution Steps
1. Click the **"Apply Patch"** button in Project-S toolbar
2. Wait 2-3 seconds for execution
3. Check Output window for result

### Expected Output (in Output window)
```
[Project-S] Patch execution started...
[Project-S Plugin] Loaded successfully - click 'Apply Patch' to start
[PROJECT_S_RESULT] SUCCESS
  status: success
  created_instances: 7
  root_path: PS_BUILD_<timestamp>
  summary: Created obby with 3 levels (0.XX s)
  created_at: 2026-01-17 HH:MM:SS
  execution_time_ms: XX
[Project-S] Patch execution completed successfully
```

### Expected Changes in Workspace
1. New **Folder** created with name pattern `PS_BUILD_1705430000` (timestamp varies)
2. Inside folder:
   - **3 Platform parts** (Platform_1, Platform_2, Platform_3)
   - **3 Checkpoint parts** (Checkpoint_1, Checkpoint_2, Checkpoint_3) - small green balls
   - **1 FinishPad part** - larger red platform
3. Total: **7 instances** in the folder

### Expected Changes in ReplicatedStorage
1. Folder created: `ReplicatedStorage/ProjectS/`
2. StringValue created: `ReplicatedStorage/ProjectS/LastResult`
3. Contains the full result report as text

### Verification
- [ ] Output shows `[PROJECT_S_RESULT] SUCCESS`
- [ ] Workspace has new `PS_BUILD_*` folder
- [ ] Folder contains 7 instances
- [ ] Platforms are colored (neon theme)
- [ ] Checkpoints are green spheres
- [ ] Finish pad is red
- [ ] ReplicatedStorage has ProjectS folder
- [ ] LastResult contains full report

### Pass Criteria
✅ **PASS** if all 8 verification points are true

---

## TEST 2: Multiple Executions (No Collisions)

### Setup
1. Use same place from TEST 1 (keep the first PS_BUILD folder)
2. Output window still open
3. Confirm you can see the first obby in Workspace

### Execution Steps
1. Click **"Apply Patch"** button again
2. Wait 2-3 seconds
3. Check Output for result
4. Examine Workspace for changes

### Expected Output
```
[PROJECT_S_RESULT] SUCCESS
  status: success
  created_instances: 7
  root_path: PS_BUILD_<NEW_TIMESTAMP>
  summary: Created obby with 3 levels (0.XX s)
```

Note: Timestamp will be different from TEST 1

### Expected Changes
1. **Second folder** created with different timestamp
2. First folder remains unchanged
3. Both folders visible in Workspace simultaneously
4. Total folders: 2, Total instances created: 14

### Verification
- [ ] Second `PS_BUILD_*` folder created
- [ ] Timestamps are different
- [ ] First folder still present
- [ ] Second folder has 7 instances
- [ ] No errors in Output
- [ ] Both folders independently functional

### Pass Criteria
✅ **PASS** if folders don't overlap and both are created successfully

---

## TEST 3: Invalid Patch (Error Handling)

### Setup
1. Open **Studio Script Editor**
2. Create a new **LocalScript** in ServerScriptService
3. This script will test the plugin's error handling

### Execution Approach
Note: For MVP, we cannot directly pass invalid patches through UI. Instead, this test documents what SHOULD happen if invalid data is passed.

**Expected behavior when invalid patch is processed:**

### Test Case 3a: Missing Required Field
```lua
-- This patch is missing "levels" field
local invalidPatch = {
  type = "obby"
  -- Missing: levels
}
```

**Expected Output:**
```
[Project-S] ERROR: Patch validation failed: Missing or invalid field: levels (must be number)
[PROJECT_S_RESULT] ERROR
  status: error
  created_instances: 0
  root_path: N/A
  summary: Patch execution failed: Patch validation failed...
  errors:
    [1] Patch validation failed: Missing or invalid field: levels (must be number)
```

### Test Case 3b: Invalid Type
```lua
-- This patch has unsupported type
local invalidPatch = {
  type = "invalid_type",
  levels = 3
}
```

**Expected Output:**
```
[Project-S] ERROR: Patch validation failed: Unsupported patch type: invalid_type
```

### Test Case 3c: Invalid Levels Value
```lua
-- This patch has levels outside valid range
local invalidPatch = {
  type = "obby",
  levels = 200  -- exceeds max of 100
}
```

**Expected Output:**
```
[Project-S] ERROR: Patch validation failed: Field 'levels' must be between 1 and 100
```

### Verification
- [ ] Plugin doesn't crash on invalid input
- [ ] Error message is descriptive
- [ ] No instances created on error
- [ ] Result status is "error"
- [ ] Errors array is populated
- [ ] Graceful recovery

### Pass Criteria
✅ **PASS** if error handling works as documented

---

## Quick Verification Checklist

After each test, use this checklist:

```
Output Window:
  [ ] [PROJECT_S_RESULT] visible
  [ ] Status is success or error (as expected)
  [ ] Summary line present
  [ ] No exception stack traces

Workspace:
  [ ] PS_BUILD_* folder created (or not, if expecting error)
  [ ] Instance count matches (0 for error, 7 for success)
  [ ] No duplicate folder names

ReplicatedStorage:
  [ ] ProjectS folder exists
  [ ] LastResult StringValue exists
  [ ] LastResult.Value contains report text

Execution:
  [ ] No freezing or hangs
  [ ] Button responsive after completion
  [ ] Output clean (no garbage logs)
```

---

## Expected Instance Structure (TEST 1 & 2)

```
Workspace
└── PS_BUILD_1705430000
    ├── Platform_1 (Part, cyan/color1)
    ├── Platform_2 (Part, magenta/color2)
    ├── Platform_3 (Part, yellow/color3)
    ├── Checkpoint_1 (Part, green ball)
    ├── Checkpoint_2 (Part, green ball)
    ├── Checkpoint_3 (Part, green ball)
    └── FinishPad (Part, red platform)
```

---

## Timing Expectations

| Operation | Expected Time |
|-----------|----------------|
| Plugin load | < 1 second |
| Button click → execution start | < 0.5 seconds |
| Obby creation (7 instances) | 0.05-0.2 seconds |
| Result output to Output window | < 0.1 seconds |
| Result storage to ReplicatedStorage | < 0.1 seconds |
| Total per execution | 0.2-1.0 seconds |

---

## Logging Points

The plugin logs at these points (all visible in Output):

1. **Plugin load:** `[Project-S Plugin] Loaded successfully...`
2. **Execution start:** `[Project-S] Patch execution started...`
3. **Result output:** `[PROJECT_S_RESULT] SUCCESS/ERROR`
4. **Execution end:** `[Project-S] Patch execution completed successfully` (success only)
5. **Errors:** `[Project-S] ERROR: <message>` (on failure)

---

## Test Execution Matrix

| Test | Input | Expected Status | Expected Instances | Expected Folders |
|------|-------|-----------------|-------------------|------------------|
| 1 | Valid patch | success | 7 | 1 |
| 2 | Valid patch (again) | success | 7 (total: 14) | 2 |
| 3a | Missing levels | error | 0 | 0 |
| 3b | Invalid type | error | 0 | 0 |
| 3c | Out of range | error | 0 | 0 |

---

## Success Criteria Summary

✅ All tests pass if:
1. Valid patches create correct instance count
2. Multiple runs don't collide
3. Invalid patches fail gracefully with clear errors
4. Output is always machine-readable
5. Results stored in both Output and ReplicatedStorage
6. No crashes or exceptions

---

**Version:** 1.0  
**Date:** January 17, 2026  
**Status:** Ready for execution
