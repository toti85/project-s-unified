#!/usr/bin/env python3
"""Test escape_water_brainrots patch"""

import requests
import json

# Escape water brainrots patch
patch = {
    "type": "escape_water_brainrots",
    "params": {
        "water_start_y": -4,
        "water_rise_rate": 0.9,
        "water_max_y": 120,
        "payout": 5,
        "carry_cap": 5,
        "pickup_respawn_seconds": 10
    }
}

print("=" * 80)
print("ESCAPE_WATER_BRAINROTS PATCH TEST")
print("=" * 80)
print("\nSending patch:")
print(json.dumps(patch, indent=2))
print()

try:
    response = requests.post(
        "http://localhost:8001/patch",
        json=patch,
        timeout=5
    )
    
    print(f"Status Code: {response.status_code}")
    print("\nServer Response:")
    result = response.json()
    print(json.dumps(result, indent=2))
    
    if result.get("status") == "success":
        print("\n✅ PATCH ACCEPTED")
        print(f"   Root Path: {result['metrics']['root_path']}")
        print(f"   Parts Created: {result['metrics']['parts_created']}")
        print(f"   Scripts Created: {result['metrics'].get('scripts_created', 4)}")
        print(f"   Water Params: {result['metrics'].get('water_params')}")
        print(f"   Game Params: {result['metrics'].get('game_params')}")
    else:
        print("\n❌ PATCH FAILED")
        if result.get("errors"):
            for error in result["errors"]:
                print(f"   - {error}")
        
except Exception as e:
    print(f"❌ Error sending patch: {e}")

print("\n" + "=" * 80)
