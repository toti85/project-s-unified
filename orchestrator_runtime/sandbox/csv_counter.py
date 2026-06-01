"""
csv_counter.py - CSV Row Counter

Counts data rows in a CSV file, excluding the header.
"""
import csv
from pathlib import Path


def count_data_rows(file_path: str) -> int:
    """
    Count data rows in a CSV file, excluding the header row.

    Args:
        file_path: Path to the CSV file

    Returns:
        Number of data rows (excluding header)

    Raises:
        FileNotFoundError: If file does not exist
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f'File not found: {file_path}')
    with open(path, 'r', encoding='utf-8', newline='') as f:
        reader = csv.reader(f)
        rows = list(reader)
    return max(0, len(rows) - 1)