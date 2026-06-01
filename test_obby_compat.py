#!/usr/bin/env python3
"""Test backward compatibility with obby patch"""

import requests
import json

# Classic obby patch
patch = {
    "type": "obby",
    "levels": 5,
    "theme": "neon"
}

print("\n" + "=" * 80)
print("BACKWARD COMPATIBILITY TEST: OBBY PATCH")
print("=" * 80 + "\n")

try:
    response = requests.post("http://localhost:8001/patch", json=patch, timeout=5)
    result = response.json()
    
    print(f"✅ Status: {result.get('status')}")
    print(f"   Type: {result.get('type')}")
    print(f"   Parts: {result['metrics'].get('parts_created')}")
    print(f"   Root: {result['metrics'].get('root_path')}")
    print(f"   Summary: {result.get('summary')}")
    
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 80)
