"""
json_validator.py - JSON Key Validator

Validates that a JSON file contains both 'name' and 'value' keys.
"""

import json
from pathlib import Path


def validate_json_keys(file_path: str) -> bool:
    """
    Check if a JSON file contains both 'name' and 'value' keys.

    Args:
        file_path: Path to the JSON file

    Returns:
        True if both keys exist, False otherwise

    Raises:
        FileNotFoundError: If file does not exist
        json.JSONDecodeError: If file is not valid JSON
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return 'name' in data and 'value' in data