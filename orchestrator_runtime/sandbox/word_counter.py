"""
word_counter.py - TXT Word Counter

Counts words in a text file, ignoring extra spaces and blank lines.
"""
from pathlib import Path


def count_words(file_path: str) -> int:
    """
    Count words in a text file, ignoring extra spaces and blank lines.

    Args:
        file_path: Path to the text file

    Returns:
        Number of words

    Raises:
        FileNotFoundError: If file does not exist
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    total = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped:
            total += len(stripped.split())
    return total