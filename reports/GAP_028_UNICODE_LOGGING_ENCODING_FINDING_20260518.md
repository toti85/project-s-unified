# GAP_028 — Unicode Logging Encoding Finding

**Date:** 2026-05-18
**Analysis Time:** 10:22 UTC+3
**Severity:** LOW (does not crash missions, but pollutes logs)

---

## 1. Problem

When Hungarian prompts are sent to the system, the Windows console logger throws:

```
UnicodeEncodeError: 'charmap' codec can't encode character '\xcd' in position 87
```

The character `\xcd` is "Í" from the Hungarian prompt "Írj 5 rövid pontot..."

---

## 2. Root Cause

The Windows console uses cp1251 (Cyrillic) encoding by default. When the Python logger tries to write Hungarian characters (which include "Í", "ö", "ü", "á", "é", "ű", "ó") to the console, cp1251 cannot encode them.

**Call chain:**
```
evaluator.py:628 → self.logger.info(f"Strategic AI (Qwen3 235B) analyzing task: {task}")
  → performance_monitor.py:54 → self.logger.info(message)
    → logging.StreamHandler.emit()
      → stream.write(msg)
        → cp1251.encode() → UnicodeEncodeError
```

**Location:** `src/utils/performance_monitor.py:54` — the logger inherits the default Windows console encoding.

---

## 3. Impact

- **Does NOT crash missions** — the error is caught by the logging framework and the mission continues
- **Pollutes logs** — UnicodeEncodeError tracebacks appear in console output
- **Blocks Hungarian development** — cannot cleanly test with Hungarian prompts
- **No data loss** — the message is logged via the INFO handler (UTF-8 capable), the error is only in the console stream handler

---

## 4. Fix

### Option A: Set PYTHONIOENCODING (Recommended)

Add to `.env` or set in the environment before starting the server:
```
PYTHONIOENCODING=utf-8
```

Or set in PowerShell:
```powershell
$env:PYTHONIOENCODING = "utf-8"
```

**Risk:** None — standard Python environment variable.

### Option B: Force UTF-8 in code

In `interactive_layer/main.py` (or `src/utils/performance_monitor.py`), add at the top:
```python
import sys
import io

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
```

**Risk:** None — standard Python UTF-8 encoding setup.

### Option C: Configure logging handler encoding

In `src/utils/performance_monitor.py`, configure the handler to use UTF-8:
```python
import logging

class UTF8StreamHandler(logging.StreamHandler):
    def __init__(self, stream=None):
        super().__init__(stream)
        self.stream = io.TextIOWrapper(
            self.stream.buffer if hasattr(self.stream, 'buffer') else self.stream,
            encoding='utf-8',
            errors='replace'
        )

# Replace the default handler
for handler in logger.handlers[:]:
    logger.removeHandler(handler)
logger.addHandler(UTF8StreamHandler())
```

**Risk:** Low — only affects this logger.

---

## 5. Recommended Fix

**Option A (PYTHONIOENCODING)** is the simplest and most robust. Add it to `.env`:

```
PYTHONIOENCODING=utf-8
```

This requires no code changes and works for all Python processes.

---

## 6. Verification

After applying the fix:
1. Restart the server
2. Send a Hungarian prompt: "Írj 5 rövid pontot arról, hogy mi a Project-S jelenlegi állapota."
3. Verify no UnicodeEncodeError in logs
4. Verify all Hungarian characters display correctly

---

*End of GAP_028 finding.*