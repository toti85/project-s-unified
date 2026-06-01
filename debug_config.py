#!/usr/bin/env python3
"""Debug config loading"""
import sys
import yaml
from pathlib import Path

sys.path.insert(0, '.')

# Manually test YAML loading
config_path = Path("src/config/models.yaml")
print(f"Config path: {config_path}")
print(f"Exists: {config_path.exists()}")

if config_path.exists():
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    print(f"Loaded config keys: {list(config.keys())}")
    
    if 'models' in config:
        print(f"Models in config: {len(config['models'])}")
        for model_id, model_data in list(config['models'].items())[:3]:
            print(f"   - {model_id}: {model_data.get('display_name', 'N/A')}")
    else:
        print(f"No 'models' key in config!")
        print(f"Config structure: {list(config.keys())}")
