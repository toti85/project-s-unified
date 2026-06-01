"""
env_parser.py — Simple .env file parser

Parses KEY=VALUE lines from .env files.
Ignores blank lines and comments (lines starting with #).
"""


def parse_env(text: str) -> dict[str, str]:
    """
    Parse .env format text into a dictionary.

    Args:
        text: Raw .env file content

    Returns:
        Dictionary of KEY=VALUE pairs

    Raises:
        ValueError: If text is empty
    """
    result: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        # Skip blank lines and comments
        if not line or line.startswith("#"):
            continue
        # Split on first = only
        if "=" in line:
            key, value = line.split("=", 1)
            result[key.strip()] = value.strip()
    return result


def parse_env_file(path: str) -> dict[str, str]:
    """
    Parse a .env file from disk.

    Args:
        path: Path to .env file

    Returns:
        Dictionary of KEY=VALUE pairs
    """
    from pathlib import Path
    text = Path(path).read_text(encoding="utf-8")
    return parse_env(text)