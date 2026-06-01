"""
sample_buggy_code.py — Intentionally buggy module for local Cline benchmark.

This file contains 3 deliberate bugs for the model to identify and fix.
DO NOT fix these bugs manually — the model should find and fix them.
"""


def read_config(path):
    """Read a config file and return its full contents as a string."""
    f = open(path, "r")          # BUG 1: resource leak — file handle is never closed
    contents = f.read()
    return contents


def count_words(text):
    """Count the number of words in a string.

    Expected: 'hello  world' → 2 words
    Actual:   'hello  world' → 3 (empty string between double spaces counts as a word)
    """
    if not text:
        return 0
    words = text.split(" ")      # BUG 2: logic bug — str.split(" ") doesn't collapse multiple spaces
    return len(words)


def calculate_average(numbers):
    """Return the arithmetic average of a list of numbers.

    Raises ZeroDivisionError on an empty list instead of a descriptive ValueError.
    """
    total = sum(numbers)
    return total / len(numbers)  # BUG 3: no empty-list guard → ZeroDivisionError


if __name__ == "__main__":
    print(count_words("hello world"))       # → 2 (correct)
    print(count_words("hello  world"))      # → 3 (wrong — should be 2)
    print(calculate_average([1, 2, 3]))     # → 2.0 (correct)
    # calculate_average([]) would crash here
