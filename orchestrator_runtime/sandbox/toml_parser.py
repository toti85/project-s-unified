"""
toml_parser.py — Simple TOML-like key=value parser

Parses simple key=value lines from TOML-like files.
Ignores blank lines and comments (lines starting with #).
Does NOT support sections, arrays, or nested structures.
"""


def parse_toml_keys(text: str) -> dict[str, str]:
    """
    Parse simple key=value lines from TOML-like text.

    Args:
        text: Raw TOML-like content

    Returns:
        Dictionary of key=value pairs (top-level only)

    Raises:
        ValueError: If text is empty
    """
    result: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        # Skip blank lines and comments
        if not line or line.startswith("#"):
            continue
        # Skip section headers
        if line.startswith("["):
            break
        # Split on first = only
        if "=" in line:
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                result[key] = value
    return result


def parse_toml_file(path: str) -> dict[str, str]:
    """
    Parse a TOML-like file from disk.

    Args:
        path: Path to file

    Returns:
        Dictionary of key=value pairs
    """
    from pathlib import Path
    text = Path(path).read_text(encoding="utf-8")
    return parse_toml_keys(text)