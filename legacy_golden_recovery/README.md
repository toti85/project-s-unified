# legacy_golden_recovery

**Cél:** A bizonyítottan valaha működő pipeline izolált visszahozása a jelenlegi workspacebe.

## Forrás

| Fájl | Forrás | Eredeti dátum | Sorok |
|---|---|---|---|
| `golden_components/smart_orchestrator.py` | `C:\project_s_agent0603\core\smart_orchestrator.py` | 2025-07-09 | 928 |
| `golden_components/workflow_engine.py` | `C:\project_s_agent0603\core\workflow_engine.py` | 2025-07-09 | 958 |
| `golden_components/advanced_decision_router.py` | `C:\project_s_agent0603\integrations\advanced_decision_router.py` | 2025-07-09 | 584 |
| `launchers/meta_launcher_browser.py` | `C:\1225\project_s_super_core\meta_launcher_browser.py` | 2026-02-19 | ~350 |

## Bizonyíték

`browser_automation_report_20260219_081337.md` (C:\ProjectS-Unified):
- Success=True
- Execution Time=190.2s
- Browser=Chromium Playwright
- Model=openai/gpt-4o-mini via OpenRouter

## Struktúra

```
legacy_golden_recovery/
  README.md
  golden_components/
    smart_orchestrator.py       ← Golden Age orchestrator (928 sor)
    workflow_engine.py          ← Enhanced Workflow Engine (958 sor)
    advanced_decision_router.py ← Advanced Decision Router (584 sor)
  launchers/
    meta_launcher_browser.py    ← Bizonyított AI+browser launcher
    run_example_browser_test.py ← Minimális élő teszt (ha dry-run pass)
  reports/
    dryrun_report.md            ← Dry-run eredmény
    browser_test_report.md      ← Élő teszt eredmény (ha lefutott)
  tests/
    test_imports.py             ← Import kompatibilitás teszt
    test_browser_pipeline_dryrun.py ← Dry-run (böngésző nélkül)
  GOLDEN_RECOVERY_STATUS.md     ← Végső státusz riport
```

## SZABÁLYOK

- NE módosítsd a `golden_components/` fájlokat — csak olvasd és vizsgáld
- NE írj át meglévő AgentLoop fájlokat a workspace-ben
- NE integráld main.py-ba amíg GOLDEN_RECOVERY_STATUS.md nem mutat PASS-t
