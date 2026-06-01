"""
test_sample_fixed_code.py — Same tests but importing sample_fixed_code (model output).
Run this to verify the model's fix passes all tests.
"""
import pytest
from sample_fixed_code import count_words, calculate_average


def test_count_words_normal():
    assert count_words("hello world") == 2


def test_count_words_double_space():
    assert count_words("hello  world") == 2


def test_count_words_triple_space():
    assert count_words("a   b   c") == 3


def test_count_words_empty():
    assert count_words("") == 0


def test_count_words_none():
    assert count_words(None) == 0


def test_calculate_average_normal():
    assert calculate_average([1, 2, 3]) == 2.0


def test_calculate_average_single():
    assert calculate_average([42]) == 42.0


def test_calculate_average_empty():
    with pytest.raises(ValueError):
        calculate_average([])
