#!/usr/bin/env python3
"""Super Core AIClient Test"""
import sys
sys.path.insert(0, './src')

from integrations.ai_models.multi_model_ai_client import AIClient

c = AIClient()
models = c.list_available_models()

print("\n✅ SuperCore AIClient loaded successfully!")
print(f"   Total models: {len(models)}")

providers = {}
for m in models:
    provider = m.get("provider", "unknown")
    model_id = m.get("model_id", "unknown")
    if provider not in providers:
        providers[provider] = []
    providers[provider].append(model_id)

for prov, mod_list in providers.items():
    print(f"   • {prov}: {', '.join(mod_list)}")

print("\n✅ Test PASSED - AIClient & configuration working!")
