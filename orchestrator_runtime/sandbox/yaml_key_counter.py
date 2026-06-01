"""
yaml_key_counter.py - YAML Key Counter Helper

Counts top-level keys in a YAML-like file (simple parser).
"""
from pathlib import Path


def count_top_level_keys(file_path: str) -> int:
    """
    Count top-level keys in a YAML-like file.

    Top-level keys have no leading whitespace.
    Lines starting with # are comments.

    Args:
        file_path: Path to the YAML-like file

    Returns:
        Number of top-level keys

    Raises:
        FileNotFoundError: If file does not exist
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    count = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        # Top-level key: no leading whitespace and contains :
        if not line.startswith(" ") and not line.startswith("\t") and ":" in stripped:
            count += 1
    return count