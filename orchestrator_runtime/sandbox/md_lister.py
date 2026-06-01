"""
md_lister.py — Markdown File Lister Helper

Lists all .md files in a given folder (non-recursive).
"""

import os
from pathlib import Path


def list_markdown_files(folder_path: str) -> list[str]:
    """
    List all .md files in the given folder (non-recursive).

    Args:
        folder_path: Path to the directory to scan

    Returns:
        Sorted list of markdown filenames (not full paths)

    Raises:
        FileNotFoundError: If folder_path does not exist
        NotADirectoryError: If folder_path is not a directory
    """
    path = Path(folder_path)

    if not path.exists():
        raise FileNotFoundError(f"Directory not found: {folder_path}")

    if not path.is_dir():
        raise NotADirectoryError(f"Not a directory: {folder_path}")

    md_files = [f.name for f in path.iterdir() if f.is_file() and f.suffix.lower() == '.md']
    return sorted(md_files)