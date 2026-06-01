# SAI REAL OUTPUT VALIDATION — 2026-04-30

**Task:** List all Python files in `C:\ProjectS-Unified\witness` recursively and return exact relative paths.  
**Entry point:** `interactive_task.py` → `SuperIntelligentAI(use_meta_controller=True)`  
**Test file:** `sai_valid.log` / `sai_valid.err`

---

## 1. Ground Truth (PowerShell)

```powershell
Get-ChildItem C:\ProjectS-Unified\witness -Recurse -Filter *.py |
  ForEach-Object { $_.FullName.Replace("C:\ProjectS-Unified\", "") }
```

**Eredmény — 7 fájl:**

```
witness\evidence_diagnostic.py
witness\evidence_reader.py
witness\learning_diagnostic.py
witness\__init__.py
witness\bridges\organism_to_meta.py
witness\bridges\state_reader.py
witness\bridges\__init__.py
```

---

## 2. SAI Output

```
Status: True
Task type: meta_controller_execution

Output:
[OK] MetaController completed goal in 1 iterations
```

**A fájllista az outputban: NINCS.**

---

## 3. Összehasonlítás

| Metrika | Érték |
|---|---|
| Ground truth fájlok | 7 |
| SAI outputban talált ground truth fájlok | **0** |
| Match count | **0 / 7** |
| Missing files | mind a 7 |
| Extra / hallucinated files | 0 (az output üres, sem extra sem valódi) |
| Status: True | igen |
| Output tartalmaz fájllistát | **nem** |

---

## 4. Tool Selection analízis

### Kiválasztott tool: `web_page_fetch` (ROSSZ)

A `sai_valid.err` tanúsága:

```
ERROR  Real tool execution failed for web_page_fetch:
       WebPageFetchTool.execute() missing 1 required positional argument: 'url'
WARNING All real execution attempts failed for web_page_fetch, using mock result
```

A SmartOrchestrator `web_page_fetch`-t választott — egy web-lekérő toolt — egy helyi fájlrendszer-listázó feladathoz.

### Miért?

`smart_orchestrator.py` `_analyze_task()` módszer, L1024–1059:

```python
# Keyword→task_type mapping:
"search", "find", "locate", "grep", "look for", "containing" → file_search
"create", "generate", "build"                                → creation
"analyze", "examine", "check", "review"                     → analysis
"fix", "debug", "repair"                                     → problem_solving
"test", "run", "execute", "validate"                         → execution
# (semmi más) → "general" (default)
```

A task (`"list all python files ... recursively and return exact relative paths"`) egyik keyword-listával sem egyezik — **`"list"`, `"recursively"`, `"return"` nem szerepelnek**.

Eredmény: `task_type = "general"` → `_select_tools()` nem kezeli a `"general"` esetet → `selected_tools = []` → **default fallback: `web_page_fetch`**.

### Helyes tool lett volna:
- `FileSearchTool` (file_search típus)  
- `file_content_search` tool  
- `system_command` tool: `Get-ChildItem` / `find`

---

## 5. Második strukturális probléma: az output elvész

Még ha a helyes tool futott volna és visszaadta volna a 7 fájlt, **az output akkor sem jelenne meg** a felhasználónak.

Az ok: a `super_intelligent_ai.py` MetaController branch (`~L379–393`) a tényleges execution result tartalmat **teljesen elveti**, és helyette egy generikus wrapper üzenetet ad vissza:

```python
# execute_intelligent_task(), MetaController branch:
if meta_result.get("status") in ("success", "passed"):
    return {
        "success": True,
        "output": f"[OK] MetaController completed goal in {meta_result.get('iterations', 1)} iterations",
        # ↑ A tényleges fájllista NINCS IDE ÁTADVA — meta_result nem tartalmazza
        ...
    }
```

A MetaController `run_goal()` visszatérési dict-je (`meta_result`) nem tartalmazza az executor által előállított outputot — a belső `execution_result["output"]` nem kerül fel a végső válaszba.

**Ez azt jelenti:** a pipeline képes megtalálni a fájlokat, de az eredményt nem adja vissza a hívónak.

---

## 6. meta_evidence before/after

| | Rekordszám |
|---|---|
| BEFORE | 403,889 |
| AFTER | **403,894** |
| Delta | **+5** |

A pipeline futott és logolt — de ez önmagában nem igazolja a helyes output-ot.

---

## 7. Verdikt

```
PARTIAL
```

**Részletek:**

| Ellenőrzési pont | Eredmény |
|---|---|
| Pipeline fut (Status: True) | PASS |
| MetaController + StrategyCouncil + Evaluator futott | PASS |
| meta_evidence gyarapodott | PASS |
| Helyes tool választva | **FAIL** — `web_page_fetch` (default fallback), nem `file_search` |
| Tényleges fájllista az outputban | **FAIL** — 0/7 fájl |
| Output tartalom helyes | **FAIL** — generikus wrapper |

---

> **Status True is not sufficient; content validation failed.**
>
> A `Status: True` csak azt bizonyítja, hogy a MetaController pipeline végigfutott és a `deterministic_pass` logika (`has_output = True`) teljesült — nem azt, hogy a feladatot megoldotta.

---

## 8. A két gyökérok

### 8.1 Tool selection bug (`smart_orchestrator.py`)

**Hely:** `_analyze_task()`, L1047 (file_search keywords lista)  
**Probléma:** `"list"`, `"recursively"`, `"return"` nem szerepelnek a `file_search` keyword-listában.  
**Minimális fix:**

```python
# Jelenlegi (L1047):
elif any(keyword in task_lower for keyword in ["search", "find", "locate", "grep", "look for", "file content", "filesearch", "filecontentsearch", "containing", "contains", "pattern"]):

# Javított (+3 keyword):
elif any(keyword in task_lower for keyword in ["search", "find", "locate", "grep", "look for", "file content", "filesearch", "filecontentsearch", "containing", "contains", "pattern", "list", "recursively", "*.py", "*.js"]):
```

### 8.2 Output propagation bug (`super_intelligent_ai.py`)

**Hely:** `execute_intelligent_task()` MetaController branch, L379–393  
**Probléma:** A MetaController `meta_result` nem tartalmazza az executor által visszaadott outputot.  
**Minimális fix:** A `meta_result` visszatérési dict-ben propagálni az executor eredményt, és a SAI branch-ben ezt surfaceolni — vagy a `meta_result` dict-ből kiolvasni az execution_result-ot.

**Megjegyzés:** Ez az architektúrális rés a MetaController-ből ered: a `run_goal()` visszatér a magas szintű státusszal (`passed`/`failed`/stb.), de az executor által kiadott tartalom nem kerül a visszatérési értékbe — az csak belső state-ben él.

---

## 9. Következő lépés (ha javítást akarsz)

1. **`smart_orchestrator.py` L1047 patch:** `"list"`, `"recursively"`, `"*.py"` hozzáadása a `file_search` keywords-höz — 1 soros javítás
2. **Output propagation fix:** A `_ExecutorAdapter.execute()` által visszaadott `execution_result["output"]` tartalmát be kell emelni a `meta_result`-ba, hogy a SAI surfaceolni tudja

**Prioritás:** A (1) önmagában nem elégséges (a (2) nélkül a fájllista elvész). Mindkét fix együtt szükséges a valódi content delivery-hez.

---

*Generálva: 2026-04-30 | Test: sai_valid.log | Ground truth: 7 fájl | Match: 0/7*
