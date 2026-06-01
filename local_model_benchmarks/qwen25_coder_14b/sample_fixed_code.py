"""
sample_buggy_code.py - Intentionally buggy module for local Cline benchmark.

This file contains 3 deliberate bugs for the model to identify and fix.
DO NOT fix these bugs manually - the model should find and fix them.
"""

def read_config(path):
    """Read a config file and return its full contents as a string."""
    with open(path, "r") as f:  # FIXED: resource leak - file handle is now properly closed
        contents = f.read()
    return contents


def count_words(text):
    """Count the number of words in a string.

    Expected: 'hello  world' -> 2 words
    Actual:   'hello  world' -> 3 (empty string between double spaces counts as a word)
    """
    if not text:
        return 0
    words = text.split()  # FIXED: logic bug - str.split() collapses multiple spaces
    return len(words)


def calculate_average(numbers):
    """Return the arithmetic average of a list of numbers.

    Raises ZeroDivisionError on an empty list instead of a descriptive ValueError.
    """
    if not numbers:  # FIXED: empty-list guard
        raise ValueError("Cannot calculate average of an empty list")
    total = sum(numbers)
    return total / len(numbers)


if __name__ == "__main__":
    print(count_words("hello world"))       # -> 2 (correct)
    print(count_words("hello  world"))      # -> 2 (correct)
    print(calculate_average([1, 2, 3]))     # -> 2.0 (correct)
    # calculate_average([]) would raise ValueError here
