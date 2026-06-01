RULES
=====

1. Entry points:
   - super_intelligent_launcher.py
   - TEST_D_META_LEARNING_PROOF.py
   - TEST_E_REGRESSION_LEARNING_PROOF.py

2. No changes to:
   - core/super_intelligent_ai.py
   - tools/registry/*
   - integrations/ai_models/*

3. Memory paths (auto-created):
   - memory/intelligence/
   - memory/state/
   - memory/logs/

4. Configuration:
   - config/multi_model_config.json
   - config/optimization_rules.json
   - config/resource_limits.json

5. Tests use execution_events.jsonl:
   - Not human-writable
   - Not to be deleted during test runs

6. Archive folder:
   - archive/ - old demos/reports
   - archive/remove_later/ - temp files safe to delete
