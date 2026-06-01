# Plugin Debug Checklist

## Quick Diagnosis Guide

Use this checklist when something isn't working.

---

## ISSUE: Plugin doesn't appear in toolbar

### Symptom
- No "Apply Patch" button visible in toolbar
- Project-S menu not in top menu

### Diagnosis Steps
1. **Check if files are in correct location:**
   ```
   C:\Users\{User}\AppData\Local\Roblox\Plugins\ProjectSBuild\
   ```
   - [ ] plugin.lua exists
   - [ ] PatchSchema.lua exists
   - [ ] PatchExecutor.lua exists
   - [ ] ResultReporter.lua exists

2. **Check if plugin is enabled:**
   - Open Roblox Studio
   - Go to Plugins → Manage Plugins
   - Look for "Project-S" in list
   - [ ] Is checkbox CHECKED?
   - If unchecked, check it and click OK

3. **Check Roblox Studio Output:**
   - View → Output
   - Search for errors containing "ProjectSBuild"
   - [ ] Any errors visible?

### Solutions
- **Files missing:** Copy all 4 Lua files to correct folder
- **Plugin disabled:** Enable in Manage Plugins
- **File permissions:** Ensure Roblox Studio can read the folder
- **Old version cached:** Restart Roblox Studio completely
- **Typo in folder name:** Folder MUST be named `ProjectSBuild` (exact case)

### Verify Fix
- [ ] Restart Roblox Studio completely
- [ ] Plugin appears in toolbar
- [ ] "Apply Patch" button visible

---

## ISSUE: Button doesn't respond when clicked

### Symptom
- Button appears but clicking has no effect
- No output in Output window
- No new objects created

### Diagnosis Steps
1. **Check Output window:**
   - View → Output
   - [ ] Can you see it?
   - [ ] Is anything logged?

2. **Check plugin load status:**
   - Look for: `[Project-S Plugin] Loaded successfully`
   - [ ] Is this message visible?

3. **Check file structure:**
   - All Lua files require each other correctly
   - Look for: `cannot require script` errors
   - [ ] Any require errors?

### Solutions
- **Plugin didn't load:** Check file paths in require statements
  - plugin.lua should have: `require(script:WaitForChild("PatchSchema"))`
  - All module files must be children of plugin.lua
- **Dependencies missing:** Ensure PatchSchema.lua in same folder
- **Syntax error:** Check Lua files for typos

### Verify Fix
- [ ] Restart Roblox Studio
- [ ] Open different place
- [ ] Try clicking button again

---

## ISSUE: Output shows error instead of result

### Symptom
- [PROJECT_S_RESULT] shows ERROR status
- Error message in output

### Diagnosis Steps
1. **Read the error message carefully:**
   - Look for: `ERROR: <message>`
   - Note the exact message
   - [ ] What does it say?

2. **Check common errors:**

   **"Patch validation failed"**
   - Patch structure is invalid
   - Check PatchSchema.lua validation rules
   - Solution: Ensure type="obby", levels is number, levels between 1-100

   **"Cannot require script"**
   - Module file is missing
   - [ ] All 4 files present?
   - Solution: Copy missing file to plugin folder

   **"nil value"** or **"attempt to index nil"**
   - Plugin tried to access service that doesn't exist
   - Likely: game:GetService("Workspace") failed
   - Solution: Restart Studio, try again

3. **Check Workspace service:**
   - In Command bar (or new LocalScript):
   ```lua
   print(game:GetService("Workspace"))
   ```
   - [ ] Returns a service object?

### Solutions
- **Validation error:** Fix patch structure (type, levels fields)
- **Module error:** Ensure all 4 Lua files in correct folder
- **Service error:** Restart Roblox Studio
- **Workspace missing:** This is very rare; restart Studio

### Verify Fix
- [ ] No more error messages
- [ ] Next click shows SUCCESS

---

## ISSUE: Objects created but in wrong place

### Symptom
- [PROJECT_S_RESULT] shows success
- Objects exist but not in Workspace
- Or objects in wrong folder

### Diagnosis Steps
1. **Check Workspace:**
   - In Explorer, expand Workspace
   - [ ] Do you see PS_BUILD_* folder?
   - [ ] Is it directly under Workspace?

2. **Check object hierarchy:**
   - Expand PS_BUILD_* folder
   - [ ] Do you see Platform_1, Platform_2, etc?
   - [ ] Are they at top level (not nested)?

3. **Check wrong services:**
   - Look in ReplicatedStorage
   - Look in ServerScriptService
   - Look in StarterPlayer
   - [ ] Objects accidentally created elsewhere?

### Solutions
- **Objects in wrong service:** Check PatchExecutor.lua line with `.Parent = rootFolder`
  - Should be: `platform.Parent = rootFolder`
  - Not: `platform.Parent = game:GetService("ServerScriptService")`
- **Objects nested wrong:** Verify folder hierarchy in PatchExecutor
- **Not created at all:** Check if error was suppressed

### Verify Fix
- [ ] Click "Apply Patch" again
- [ ] New PS_BUILD_* folder appears in Workspace root
- [ ] All 7 objects inside it

---

## ISSUE: Result not stored in ReplicatedStorage

### Symptom
- [PROJECT_S_RESULT] shows success
- But ReplicatedStorage.ProjectS.LastResult doesn't exist or empty

### Diagnosis Steps
1. **Check ReplicatedStorage:**
   - Expand ReplicatedStorage in Explorer
   - [ ] Do you see "ProjectS" folder?
   - [ ] Do you see "LastResult" StringValue inside?

2. **Check LastResult content:**
   - Click on LastResult
   - Look at Properties → Value
   - [ ] Is it empty or has text?

### Solutions
- **Folder doesn't exist:** Plugin didn't reach storage code
  - Check console for errors
  - Verify ResultReporter.lua syntax
- **LastResult doesn't exist:** Check storeInReplicatedStorage function
  - Should create it if missing
  - May need plugin restart
- **Content is empty:** ResultReporter.report() not called
  - Check PatchExecutor return value
  - Verify error didn't occur

### Verify Fix
- [ ] ReplicatedStorage.ProjectS created
- [ ] LastResult StringValue exists
- [ ] LastResult.Value contains full report

---

## ISSUE: Plugin crashes or freezes

### Symptom
- Roblox Studio becomes unresponsive
- Button click causes freeze
- Studio must be force-closed

### Diagnosis Steps
1. **Check Output window:**
   - View → Output before clicking button
   - [ ] Any error messages before freeze?

2. **Check for infinite loops:**
   - Review PatchExecutor.lua for while loops
   - [ ] Any without break conditions?

3. **Check for pcall issues:**
   - plugin.lua wraps execution in pcall
   - [ ] Is error handling working?

### Solutions
- **Infinite loop:** Check PatchExecutor.lua for unbounded loops
  - For loop should have definite range: `for i = 1, patch.levels`
- **Memory issue:** Too many objects being created
  - Check if patch.levels is large (should be 1-100)
- **Deadlock:** Two parts of code waiting for each other
  - Unlikely in this simple plugin

### Verify Fix
- [ ] Force-close Roblox Studio
- [ ] Delete one of the 4 Lua files (to clear cache)
- [ ] Copy it back
- [ ] Restart Studio
- [ ] Try again (should work)

---

## ISSUE: Output prefix [PROJECT_S_RESULT] not found

### Symptom
- Plugin seems to run but no [PROJECT_S_RESULT] in output
- Can't find result

### Diagnosis Steps
1. **Check Output window is open:**
   - View → Output
   - [ ] Output window visible?

2. **Search in Output:**
   - Ctrl+F in Output window
   - Search for: `PROJECT_S`
   - [ ] Any matches?

3. **Check result was actually reported:**
   - Look for: `[Project-S]` (note: Project-S, not PROJECT_S)
   - [ ] Load messages visible?

### Solutions
- **Output window not open:** View → Output
- **Output scrolled up:** Scroll to bottom (or search)
- **Plugin not running:** Button didn't click or error before reporting
  - Check "Button doesn't respond" section above
- **Result reported but prefix wrong:** Check ResultReporter.lua string format
  - Should print: `print("[PROJECT_S_RESULT]")`

### Verify Fix
- [ ] Output window open
- [ ] Search for [PROJECT_S_RESULT]
- [ ] Result visible in output

---

## ISSUE: Multiple tests create too many objects

### Symptom
- After TEST 2, Workspace is cluttered
- Hundreds of objects created
- Studio becomes slow

### Diagnosis Steps
1. **Count PS_BUILD folders:**
   - Expand Workspace in Explorer
   - Count folders starting with PS_BUILD_
   - [ ] How many are there?

2. **Check folder contents:**
   - Expand one PS_BUILD_* folder
   - [ ] Does it have 7 objects?
   - Or does it have hundreds?

3. **Check if leaking objects:**
   - In each PS_BUILD folder, should be exactly:
     - 3 Platform parts
     - 3 Checkpoint parts
     - 1 FinishPad part
   - [ ] Any extra objects?

### Solutions
- **Too many folders:** This is expected after multiple runs
  - Either start with fresh place each time
  - Or manually delete old PS_BUILD_* folders before next test
- **Objects leaking into folder:** Check PatchExecutor.lua parent assignment
  - All instances should have: `.Parent = rootFolder`
- **Objects created multiple times:** Check for loop conditions
  - Should be: `for i = 1, patch.levels do` (not `while true`)

### Verify Fix
- [ ] Each PS_BUILD_* folder has exactly 7 objects
- [ ] No orphaned objects
- [ ] Multiple folders don't interfere with each other

---

## ISSUE: File Permission Errors

### Symptom
- "Permission denied" or "Access is denied" in output
- Can't create ReplicatedStorage folder
- Can't write results

### Diagnosis Steps
1. **Check folder permissions:**
   - Navigate to: `C:\Users\{User}\AppData\Local\Roblox\Plugins\ProjectSBuild\`
   - Right-click → Properties → Security
   - [ ] Is "Full Control" checked for your user?

2. **Check file attributes:**
   - Each .lua file → Properties
   - [ ] Is "Read-only" checkbox unchecked?

3. **Check Studio permissions:**
   - Is Roblox Studio running as Administrator?
   - [ ] Should it be?

### Solutions
- **Folder read-only:** Remove read-only attribute from folder and files
  - Right-click → Properties → uncheck "Read-only"
- **User lacks permissions:** Run Studio as Administrator
  - Right-click Roblox Studio → Run as Administrator
- **AppData folder locked:** This is very rare
  - Try restarting computer

### Verify Fix
- [ ] Restart Roblox Studio
- [ ] Try plugin again
- [ ] No permission errors

---

## Step-by-Step Debug Process

If something isn't working:

1. **Gather information:**
   - [ ] What exactly happens?
   - [ ] What's in Output window?
   - [ ] What's in Workspace?

2. **Narrow down:**
   - Is the problem with installation? → See "Plugin doesn't appear"
   - Is it with execution? → See "Button doesn't respond"
   - Is it with results? → See "Output shows error"

3. **Check file integrity:**
   - [ ] All 4 Lua files present?
   - [ ] No typos in file names?
   - [ ] Files not corrupted (readable in text editor)?

4. **Try basic fixes:**
   - [ ] Restart Roblox Studio
   - [ ] Rebuild plugin folder (delete and recopy)
   - [ ] Try on different place file

5. **If still broken:**
   - [ ] Check Output window for exact error message
   - [ ] Read the error message carefully
   - [ ] Match it to a section above
   - [ ] Follow the solutions

---

## Common Error Messages & Solutions

| Error Message | Cause | Solution |
|---------------|-------|----------|
| `cannot require script` | Module file missing | Copy all 4 Lua files |
| `nil value` or `attempt to index nil` | Service not available | Restart Studio |
| `Patch validation failed: Missing required field: type` | Patch structure wrong | Check PatchSchema.lua |
| `Permission denied` | File read-only or no permissions | Remove read-only attribute |
| `Attempt to yield in non-yielding function` | WaitForChild in wrong context | Unlikely; restart Studio |
| `Attempt to call a nil value` | Function not found | Check require statements |
| `Stack overflow` | Infinite recursion | Check loops in code |

---

## Quick Reference Checklist

**If nothing works:**
- [ ] All 4 Lua files in `C:\Users\{User}\AppData\Local\Roblox\Plugins\ProjectSBuild\`
- [ ] Plugin enabled in Manage Plugins
- [ ] Roblox Studio fully restarted (closed and reopened)
- [ ] Output window open (View → Output)
- [ ] Button visible in toolbar (Project-S → Apply Patch)
- [ ] Click button once and wait 3 seconds
- [ ] Check Output for `[PROJECT_S_RESULT]`
- [ ] Check Workspace for `PS_BUILD_*` folder

If all above are true and it still doesn't work:
- [ ] Verify no permission errors in Output
- [ ] Check if any other plugins are interfering
- [ ] Delete plugin folder and reinstall from scratch

---

**Version:** 1.0  
**Date:** January 17, 2026  
**Last Updated:** January 17, 2026
