"""
test_sample_buggy_code.py — pytest tests for the benchmark sandbox.

Test status before model fixes:
  test_count_words_double_space   → FAILS  (returns 3, expects 2)
  test_calculate_average_empty    → FAILS  (raises ZeroDivisionError, expects ValueError)
  test_count_words_normal         → PASSES
  test_calculate_average_normal   → PASSES
  test_count_words_none           → PASSES
"""
import pytest
from sample_buggy_code import count_words, calculate_average


# --- count_words ---

def test_count_words_normal():
    """Single spaces between words: straightforward case."""
    assert count_words("hello world") == 2


def test_count_words_double_space():
    """Double space must not create a phantom empty-string token."""
    assert count_words("hello  world") == 2   # FAILS before fix: returns 3


def test_count_words_triple_space():
    """Multiple spaces in a row must still yield correct word count."""
    assert count_words("a   b   c") == 3      # FAILS before fix: returns 7


def test_count_words_empty():
    """Empty string returns 0."""
    assert count_words("") == 0


def test_count_words_none():
    """None returns 0 (falsy guard)."""
    assert count_words(None) == 0


# --- calculate_average ---

def test_calculate_average_normal():
    """Basic average of three numbers."""
    assert calculate_average([1, 2, 3]) == 2.0


def test_calculate_average_single():
    """Single element average equals that element."""
    assert calculate_average([42]) == 42.0


def test_calculate_average_empty():
    """Empty list must raise ValueError, not ZeroDivisionError."""
    with pytest.raises(ValueError):           # FAILS before fix: raises ZeroDivisionError
        calculate_average([])
