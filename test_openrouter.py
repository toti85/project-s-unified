#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OpenRouter API Configuration Test"""

import sys
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, 'src')
from integrations.ai_models.multi_model_ai_client import AIClient

async def main():
    client = AIClient()
    models = client.list_available_models()
    
    print('═' * 70)
    print('OPENROUTER MODELLEK')
    print('═' * 70)
    
    openrouter_models = [m for m in models if m.get('provider') == 'openrouter']
    print(f'✅ OpenRouter modellek talált: {len(openrouter_models)} db')
    print()
    
    for model in openrouter_models[:5]:
        print(f"  • {model.get('name')} ({model.get('model_id')}) - {model.get('description')}")
    
    print()
    print('═' * 70)
    print('TESZT: OpenRouter AI válasz')
    print('═' * 70)
    
    try:
        result = await client.generate_response(
            prompt='Say hello in Hungarian in one sentence.',
            task_type='analysis',
            provider='openrouter'
        )
        print(f'✅ Válasz típusa: {type(result).__name__}')
        print(f'📝 Válasz: {result}')
        return True
    except Exception as e:
        print(f'❌ Hiba: {str(e)[:200]}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
