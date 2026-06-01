"""
ini_parser.py - INI Config Parser Helper

Reads an .ini file and returns a dictionary of sections and keys.
"""
from pathlib import Path


def parse_ini(file_path: str) -> dict:
    """
    Parse an INI file and return a dictionary of sections and keys.

    Args:
        file_path: Path to the INI file

    Returns:
        Dictionary like {'section': {'key': 'value'}}

    Raises:
        FileNotFoundError: If file does not exist
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    result = {}
    current_section = None

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith(";"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current_section = line[1:-1].strip()
            result[current_section] = {}
        elif "=" in line and current_section is not None:
            key, value = line.split("=", 1)
            result[current_section][key.strip()] = value.strip()

    return result