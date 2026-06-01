#!/usr/bin/env python3
"""
legacy_golden_recovery/tests/test_browser_pipeline_dryrun.py

Dry-run: ellenőrzi a 2026-02-19 pipeline minden komponensét
NEM nyit böngészőt. Csak importok, példányosítás, config ellenőrzés.

Futtatás:
  cd C:\ProjectS-Unified
  python legacy_golden_recovery\tests\test_browser_pipeline_dryrun.py

Output: legacy_golden_recovery\reports\dryrun_report.md
"""

import sys
import os
import asyncio
from pathlib import Path
from datetime import datetime

WORKSPACE_ROOT = Path(__file__).parent.parent.parent
LEGACY_ROOT = Path(__file__).parent.parent
REPORTS_DIR = LEGACY_ROOT / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

sys.path.insert(0, str(WORKSPACE_ROOT / "src"))
sys.path.insert(0, str(WORKSPACE_ROOT))

results = []
start_time = datetime.now()

def check(name, fn):
    try:
        val = fn()
        results.append(("PASS", name, str(val) if val is not None else "OK"))
        print(f"  ✓ PASS  {name}" + (f" → {val}" if val else ""))
    except Exception as e:
        import traceback
        tb = traceback.format_exc().strip().split('\n')[-1]
        results.append(("FAIL", name, tb))
        print(f"  ✗ FAIL  {name}")
        print(f"         → {tb}")

print("=" * 72)
print("DRY-RUN: BROWSER PIPELINE DEPENDENCY CHECK")
print(f"Timestamp: {start_time.isoformat()}")
print("=" * 72)
print()

# --- 1. OPENROUTER KEY ---
print("[1] OpenRouter API key")

def check_openrouter_key():
    # Betöltés .env-ből
    env_path = WORKSPACE_ROOT / ".env"
    key = None
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("OPENROUTER_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
    # Fallback: környezeti változó
    if not key:
        key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key or len(key) < 10:
        raise ValueError(f"OPENROUTER_API_KEY missing or too short (len={len(key)})")
    if not key.startswith("sk-or-"):
        raise ValueError(f"Key does not start with 'sk-or-' — may be wrong key type (prefix: {key[:8]}...)")
    return f"len={len(key)}, prefix={key[:12]}..."

check("OPENROUTER_API_KEY betöltés", check_openrouter_key)

# --- 2. AIClient példányosítás ---
print("\n[2] AIClient")

def check_aiclient():
    from src.integrations.ai_models.multi_model_ai_client import AIClient
    client = AIClient()
    return f"instance created, type={type(client).__name__}"

check("AIClient import + példányosítás", check_aiclient)

# --- 3. AIClient model config elérés ---
print("\n[3] AIClient model config")

def check_model_config():
    from src.integrations.ai_models.multi_model_ai_client import AIClient
    client = AIClient()
    # Próbáljuk meg a 2026-02-19 által használt modellt
    if hasattr(client, 'get_recommended_model'):
        model = client.get_recommended_model("analysis")
        return f"get_recommended_model('analysis') = {model}"
    if hasattr(client, 'config'):
        return f"config keys: {list(client.config.keys())[:5]}"
    return "AIClient has no get_recommended_model — check manually"

check("AIClient model config (analysis type)", check_model_config)

# --- 4. ToolRegistry példányosítás ---
print("\n[4] ToolRegistry_golden")

def check_tool_registry():
    from tools.tools.registry.tool_registry_golden import ToolRegistry
    registry = ToolRegistry()
    tool_count = len(registry.tools) if hasattr(registry, 'tools') else '?'
    return f"instance created, tools={tool_count}"

check("ToolRegistry_golden import + példányosítás", check_tool_registry)

# --- 5. BrowserAutomationTool megtalálható-e a registry-ben ---
print("\n[5] BrowserAutomationTool in registry")

def check_browser_in_registry():
    from tools.tools.registry.tool_registry_golden import ToolRegistry
    registry = ToolRegistry()
    if hasattr(registry, 'tools'):
        keys = list(registry.tools.keys())
        browser_keys = [k for k in keys if 'browser' in k.lower()]
        if browser_keys:
            return f"Found: {browser_keys}"
        else:
            raise KeyError(f"No browser tool in registry. Available: {keys[:10]}")
    raise AttributeError("ToolRegistry has no 'tools' attribute")

check("BrowserAutomationTool in ToolRegistry.tools", check_browser_in_registry)

# --- 6. BrowserAutomationTool direkt import ---
print("\n[6] BrowserAutomationTool direkt")

def check_browser_tool_direct():
    from tools.tools.implementations.browser_automation_tool import BrowserAutomationTool
    return f"class importálható: {BrowserAutomationTool.__name__}"

check("BrowserAutomationTool direkt import", check_browser_tool_direct)

# --- 7. Playwright telepítve ---
print("\n[7] Playwright")

def check_playwright():
    from playwright.async_api import async_playwright
    import playwright
    version = getattr(playwright, '__version__', 'unknown')
    return f"playwright version={version}"

check("Playwright import", check_playwright)

# --- 8. Playwright Chromium binary létezik-e ---
print("\n[8] Playwright Chromium binary")

def check_chromium_binary():
    import subprocess
    result = subprocess.run(
        ["python", "-c",
         "from playwright.sync_api import sync_playwright; p=sync_playwright().start(); "
         "print('chromium_exec:', p.chromium.executable_path); p.stop()"],
        capture_output=True, text=True, timeout=15,
        cwd=str(WORKSPACE_ROOT)
    )
    if result.returncode == 0:
        for line in result.stdout.splitlines():
            if 'chromium_exec' in line:
                path = line.split(':', 1)[1].strip()
                exists = Path(path).exists()
                return f"path={path}, exists={exists}"
        return f"stdout={result.stdout[:100]}"
    else:
        raise RuntimeError(f"playwright check failed: {result.stderr[:150]}")

check("Playwright Chromium binary", check_chromium_binary)

# --- 9. browser_use import ---
print("\n[9] browser_use")

def check_browser_use():
    from browser_use import Agent
    return f"Agent class importálható: {Agent.__name__}"

check("browser_use Agent import", check_browser_use)

# --- 10. FileWriteTool ---
print("\n[10] FileWriteTool")

def check_file_write_tool():
    from tools.tools.implementations.file_tools import FileWriteTool
    tool = FileWriteTool()
    return f"instance created, name={getattr(tool, 'name', type(tool).__name__)}"

check("FileWriteTool import + példányosítás", check_file_write_tool)

# --- 11. models.yaml tartalmaz-e openrouter + gpt-4o-mini config-ot ---
print("\n[11] models.yaml config")

def check_models_yaml():
    import yaml
    yaml_path = WORKSPACE_ROOT / "config" / "models.yaml"
    if not yaml_path.exists():
        yaml_path = WORKSPACE_ROOT / "src" / "config" / "models.yaml"
    if not yaml_path.exists():
        raise FileNotFoundError(f"models.yaml not found at {yaml_path}")
    data = yaml.safe_load(yaml_path.read_text(encoding='utf-8'))
    models_section = data.get('models', data)
    found = []
    for key, val in models_section.items():
        if isinstance(val, dict):
            provider = val.get('provider', '')
            if provider == 'openrouter':
                found.append(f"{key}(openrouter)")
    if found:
        return f"OpenRouter models: {found[:5]}"
    raise ValueError(f"No openrouter models found in {yaml_path.name}. Keys: {list(models_section.keys())[:8]}")

check("models.yaml OpenRouter config", check_models_yaml)

# --- Összesítés ---
elapsed = (datetime.now() - start_time).total_seconds()
passed = [r for r in results if r[0] == "PASS"]
failed = [r for r in results if r[0] == "FAIL"]

print()
print("=" * 72)
print(f"DRY-RUN RESULTS: {len(passed)}/{len(results)} PASS  ({elapsed:.2f}s)")
print("=" * 72)

# --- Report generálás ---
report_lines = [
    "# Dry-Run Report",
    f"**Timestamp:** {start_time.isoformat()}",
    f"**Duration:** {elapsed:.2f}s",
    f"**Result:** {len(passed)}/{len(results)} PASS",
    "",
    "## Részletes eredmények",
    "",
    "| # | Komponens | Státusz | Detail |",
    "|---|---|---|---|",
]
for i, (status, name, detail) in enumerate(results, 1):
    icon = "✓" if status == "PASS" else "✗"
    safe_detail = (detail or "").replace("|", "\\|")[:80]
    report_lines.append(f"| {i} | {name} | {icon} {status} | `{safe_detail}` |")

report_lines += [
    "",
    "## Összesítés",
    "",
]

# meta_launcher_browser kritikus függőségei
critical = [
    "OPENROUTER_API_KEY betöltés",
    "AIClient import + példányosítás",
    "ToolRegistry_golden import + példányosítás",
    "BrowserAutomationTool in ToolRegistry.tools",
    "BrowserAutomationTool direkt import",
    "Playwright import",
    "Playwright Chromium binary",
    "browser_use Agent import",
    "FileWriteTool import + példányosítás",
]
critical_results = {r[1]: r[0] for r in results}
critical_pass = all(critical_results.get(c) == "PASS" for c in critical)

if critical_pass:
    report_lines.append("**meta_launcher_browser PIPELINE: ✓ READY TO RUN**")
    report_lines.append("")
    report_lines.append("Minden kritikus függőség elérhető. Élő teszt futtatható.")
else:
    report_lines.append("**meta_launcher_browser PIPELINE: ✗ BLOCKERS FOUND**")
    report_lines.append("")
    for c in critical:
        s = critical_results.get(c, "NOT TESTED")
        if s != "PASS":
            detail = next((r[2] for r in results if r[1] == c), "")
            report_lines.append(f"- ✗ **{c}**: {detail}")

report_lines += [
    "",
    "## Következő lépés",
    "",
    "Ha **READY TO RUN**: futtasd `launchers/run_example_browser_test.py`",
    "Ha **BLOCKERS**: lásd a hiányzó függőségeket fentebb, és javítsd.",
]

report_path = REPORTS_DIR / "dryrun_report.md"
report_path.write_text("\n".join(report_lines), encoding="utf-8")
print(f"\nReport mentve: {report_path}")

if critical_pass:
    print("\n✓ DRY-RUN PASS — élő browser teszt futtatható")
else:
    print("\n✗ DRY-RUN FAIL — blokkolt függőségek")

sys.exit(0 if critical_pass else 1)
