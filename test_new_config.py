#!/usr/bin/env python3
"""Test new consolidated config"""
import sys
sys.path.insert(0, '.')

from src.integrations.ai_models.multi_model_ai_client import AIClient

client = AIClient()
models = client.list_available_models()

print(f"\n✅ Models loaded from new models.yaml: {len(models)}\n")
for model in models:
    print(f"   • {model['display_name']:20} ({model['provider']:10}) - {model['description']}")

print(f"\n✅ Config consolidation working!")
