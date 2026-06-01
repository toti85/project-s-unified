# AUTOMATED ROBLOX EXECUTION FLOW — RESTORATION GUIDE

**Date:** February 15, 2026  
**Objective:** Return to one-command automated execution without manual copy-paste

---

## **DISCOVERED AUTOMATION ARCHITECTURE**

### **Component 1: Plugin HTTP Server**
- **File:** `docs/archiv/roblox_plugin_server.py`
- **Purpose:** Flask server on `localhost:8001`
- **Function:** 
  - Receives patch submissions via HTTP POST
  - Queues patches in deque
  - Roblox Studio plugin polls this server
  - Validates patch schema, logs evidence

### **Component 2: Roblox Studio Plugin**
- **Location:** `roblox_studio_plugin/` folder
- **File:** `plugin.lua`
- **Function:**
  - Loads when Studio opens
  - Makes HTTP requests to localhost:8001
  - Polls for patches from server
  - Injects patches into ServerScriptService automatically
  - Reports results via `[PROJECT_S_RESULT]` output

### **Component 3: Client Tool (Python)**
- **File:** `tools/roblox_apply_patch.py`
- **Purpose:** Submits patch requests to server
- **Function:**
  - Accepts natural language input (e.g., "5 level neon obby")
  - Converts to JSON patch
  - Validates schema
  - POSTs to localhost:8001/patch
  - Logs evidence

### **Component 4: Roblox Studio Launcher**
- **File:** `tools/tools/implementations/roblox_studio_tool.py`
- **Purpose:** Launches Studio seamlessly
- **Function:**
  - Discovers Roblox Studio.exe location
  - Opens Studio with specified place file

---

## **COMPLETE AUTOMATION SEQUENCE**

### **Terminal A: Start Plugin Server**

```powershell
cd c:\1225\project_s_super_core
python docs/archiv/roblox_plugin_server.py
```

**Wait for output:**
```
Starting server on http://localhost:8001
Running on http://localhost:8001
```

**Do NOT close this terminal.** Server must stay running.

---

### **Terminal B: Open Studio with Place File**

```powershell
cd c:\1225\project_s_super_core
& "C:\Program Files\Roblox\Roblox Studio\RobloxStudio.exe" "c:\1225\project_s_super_core\escape water fpr brainrots.rbxl"
```

**Wait 30 seconds for Studio to fully load.**

Studio will:
- Load the place file
- Auto-load the Project-S plugin from `roblox_studio_plugin/`
- Plugin will start polling localhost:8001 for patches
- Print to Output: `[Project-S] Plugin loaded` or similar

**Do NOT insert scripts manually.** The plugin does this automatically.

---

### **Terminal C: Submit Patch (from Terminal A's directory)**

```powershell
cd c:\1225\project_s_super_core
python tools/roblox_apply_patch.py
```

**When prompted, enter natural language description:**
```
5 level neon obby
```

Or provide as inline argument (if supported):
```powershell
python -c "
import sys
sys.path.insert(0, 'tools')
from roblox_apply_patch import RobloxApplyPatchTool
tool = RobloxApplyPatchTool()
result = tool.apply_patch('5 level neon obby')
print(result)
"
```

---

## **WHAT HAPPENS AUTOMATICALLY**

1. **Server receives patch** → validates → queues it
2. **Studio plugin polls server** → gets patch from queue
3. **Plugin generates Lua script** from patch
4. **Plugin injects LocalScript into ServerScriptService** automatically
5. **Script auto-executes** on game load
6. **Output shows** `[PROJECT_S_RESULT] SUCCESS ...`
7. **Workspace builds** with objects (platforms, spawn, etc.)

**NO MANUAL COPY-PASTE NEEDED.** The plugin handles all injection.

---

## **WHAT NOT TO TOUCH MANUALLY**

| Action | Reason |
|--------|--------|
| **Do NOT insert scripts into ServerScriptService** | Plugin does this automatically |
| **Do NOT copy-paste Lua code** | Plugin injects from server |
| **Do NOT click Play while server is down** | Plugin won't get patch, game won't build |
| **Do NOT close server terminal** | Server must stay running to accept submissions |
| **Do NOT manually edit place file while server is open** | Risk of conflicts with plugin edits |

---

## **WHAT SHOULD BE AUTOMATIC**

✅ **Server startup** → Flask app runs  
✅ **Studio plugin load** → Loads on Studio startup  
✅ **Patch polling** → Plugin polls every N seconds  
✅ **Script injection** → Plugin creates LocalScript in ServerScriptService  
✅ **Script execution** → Script runs on game load  
✅ **Output logging** → `[PROJECT_S_RESULT]` printed to Output  
✅ **Evidence logging** → JSON files saved to `~/Documents/Roblox Projects/evidence/`

---

## **CHECKLIST: WHAT MIGHT BE MISSING**

If automation doesn't work, check:

### **Missing 1: Plugin Auto-Load**
- **Check:** Does `roblox_studio_plugin/plugin.lua` exist?
- **Check:** Is plugin location configured in Studio → Plugins settings?
- **Fix:** 
  ```
  Studio → File → Settings → Studio → Plugin Security
  → Add plugin path: c:\1225\project_s_super_core\roblox_studio_plugin\
  ```

### **Missing 2: Server Auto-Start**
- **Check:** Is Flask installed?
  ```powershell
  python -m pip list | findstr Flask
  ```
- **Fix (if missing):**
  ```powershell
  pip install flask
  ```

### **Missing 3: HTTP Communication**
- **Check:** Can plugin reach server?
  ```powershell
  curl http://localhost:8001/health
  ```
- **Expected:** JSON response with `"status": "healthy"`
- **Fix:** If fails, server not running (Terminal A)

### **Missing 4: Patch Queue in Place.rbxl**
- **Check:** Does place file have the plugin pre-installed as toolbar?
- **Issue:** If place was created before plugin existed
- **Fix:** 
  ```
  In Studio, manually load plugin once:
  Plugins → Manage Plugins → Install from file
  → Select roblox_studio_plugin/plugin.lua
  → Save place file
  ```

### **Missing 5: Evidence Directory**
- **Check:** Does `~/Documents/Roblox Projects/evidence/` exist?
- **Fix (if missing):**
  ```powershell
  mkdir "$env:USERPROFILE\Documents\Roblox Projects\evidence"
  ```

---

## **SINGLE-COMMAND RESTORATION (Ideal)**

Once everything is wired, the flow becomes:

**Terminal A:**
```powershell
cd c:\1225\project_s_super_core && python docs/archiv/roblox_plugin_server.py
```

**Terminal B:**
```powershell
cd c:\1225\project_s_super_core && & "C:\Program Files\Roblox\Roblox Studio\RobloxStudio.exe" "escape water fpr brainrots.rbxl"
```

**Terminal C:**
```powershell
cd c:\1225\project_s_super_core && python -c "from tools.roblox_apply_patch import RobloxApplyPatchTool; RobloxApplyPatchTool().apply_patch('5 level medium neon obby')"
```

**Result:** Game automatically builds inside Studio without any manual UI interaction.

---

## **TRAFFIC FLOW DIAGRAM**

```
Terminal C (Client)
    |
    | HTTP POST /patch
    | {"type": "obby", "levels": 5, "theme": "neon"}
    v
Terminal A (Server: roblox_plugin_server.py)
    |
    | Validates + Queues in PENDING_PATCHES deque
    v
Studio (Plugin: plugin.lua)
    |
    | HTTP GET /patches (polling)
    | Receives patch from queue
    |
    | Generates LocalScript Lua code
    |
    | Injects into ServerScriptService
    |
    | [PROJECT_S_RESULT] SUCCESS printed to Output
    v
Workspace
    | Game objects created: PS_BUILD_*, platforms, spawn
    v
Play Success

```

---

## **INTEGRATION REQUIREMENTS**

### **For Full Automation to Work:**

1. **Server must be running** (`roblox_plugin_server.py`)
2. **Plugin must be loaded** in Studio (toolbar visible)
3. **Studio must be open** with the place file
4. **Client tool must be executable** (`roblox_apply_patch.py`)
5. **HTTP requests must work** (no firewall blocks, ports 8001, etc.)
6. **Flask + requests libraries must be installed**
   ```powershell
   pip install flask requests
   ```

---

## **EXPECTED OUTPUT SEQUENCE**

### **Terminal A (Server):**
```
 * Running on http://localhost:8001
2026-02-15 14:32:45,123 - POST /patch - {"levels": 5, "theme": "neon"}
2026-02-15 14:32:45,134 - Patch validated ✓
2026-02-15 14:32:45,145 - Patch queued for Studio plugin
```

### **Terminal B (Studio Output):**
```
[Project-S] Plugin loaded
[Project-S] Polling server...
[Project-S] Patch received: obby, 5 levels, neon theme
[Project-S] Creating LocalScript...
[PROJECT_S_RESULT] SUCCESS
  status: success
  created_instances: 11
  root_path: PS_BUILD_1739650323
  ...
```

### **Terminal C (Client):**
```
ROBLOX APPLY PATCH TOOL
Input: 5 level medium neon obby

[1/4] Converting to patch...
  Type: obby
  Levels: 5
  Theme: neon
  Difficulty: medium

[2/4] Validating patch...
  OK

[3/4] Sending to Roblox Plugin Server...
  Status: success
  Metrics: {...}

[4/4] Logging evidence...
  Logged to: C:\Users\Admin\Documents\Roblox Projects\evidence\tool_execution_20260215_143245.json

RESULT: SUCCESS
```

---

## **RESTORATION COMMAND (QUICK REFERENCE)**

| Step | Terminal | Command |
|------|----------|---------|
| **1** | A | `cd c:\1225\project_s_super_core && python docs/archiv/roblox_plugin_server.py` |
| **2** | B | `& "C:\Program Files\Roblox\Roblox Studio\RobloxStudio.exe" "c:\1225\project_s_super_core\escape water fpr brainrots.rbxl"` |
| **3** | C | `cd c:\1225\project_s_super_core && python tools/roblox_apply_patch.py` |
| **4** | C | Enter: `5 level neon obby` |

---

## **SMALLEST FIX (If Something Breaks)**

**If plugin doesn't receive patches:**
1. Check Terminal A still running
2. Verify localhost:8001 is accessible: `curl http://localhost:8001/health`
3. Restart Terminal A (kill and restart roblox_plugin_server.py)
4. Resubmit patch from Terminal C

**If Studio doesn't show Output:**
1. View → Output (should be at bottom)
2. If not visible, View → Dockable Widgets → Output

**If no script injection:**
1. Check Studio toolbar has "Project-S" button with "Apply Patch"
2. If missing, Studio plugin didn't load
3. Manually install: Plugins → Manage Plugins → Install from file → select `plugin.lua`

---

## **STATUS: READY TO DEPLOY**

All components identified:
- ✅ Server: `docs/archiv/roblox_plugin_server.py`
- ✅ Plugin: `roblox_studio_plugin/plugin.lua`
- ✅ Client: `tools/roblox_apply_patch.py`
- ✅ Launcher: `tools/tools/implementations/roblox_studio_tool.py`

**Execute three commands in different terminals and automation is live.**
