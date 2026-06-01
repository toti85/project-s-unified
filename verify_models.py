#!/usr/bin/env python3
"""Verify that AIClient can load all 7 models from corrected models.yaml"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from integrations.ai_models.multi_model_ai_client import AIClient
    
    print("=" * 60)
    print("TESTING MODELS.YAML WITH AIClient")
    print("=" * 60)
    
    # Initialize client
    client = AIClient()
    
    # Get available models
    available_models = client.list_available_models()
    
    print(f"\n✅ AIClient initialized successfully")
    print(f"\n📊 Available Models: {len(available_models)} total\n")
    
    # Expected models
    expected = [
        "gpt-4o-mini", "gpt-3.5-turbo", "claude-sonnet-4",
        "qwen3-235b", "deepseek-v3", "llama3", "mistral"
    ]
    
    for model in available_models:
        if model in expected:
            print(f"  ✅ {model}")
        else:
            print(f"  ⚠️  {model} (unexpected)")
    
    print(f"\n{'✅ SUCCESS' if len(available_models) == 7 else '❌ FAILED'}")
    print(f"Expected 7 models, found {len(available_models)}")
    
    if len(available_models) < 7:
        print("\n🔍 DEBUGGING INFO:")
        print(f"Config keys: {list(client.config.keys())}")
        for provider, config in client.config.items():
            if provider in ["openai", "anthropic", "openrouter", "ollama"]:
                print(f"  {provider}: enabled={config.get('enabled')}, models={len(config.get('models', {}))}")
    
    print("\n" + "=" * 60)
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
