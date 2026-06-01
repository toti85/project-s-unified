"""
test_env_parser.py — Unit tests for env_parser.py
"""

import os
import tempfile
import unittest

from env_parser import parse_env, parse_env_file


class TestEnvParser(unittest.TestCase):

    def test_parses_key_value_pairs(self):
        text = "DB_HOST=localhost\nDB_PORT=5432"
        result = parse_env(text)
        self.assertEqual(result["DB_HOST"], "localhost")
        self.assertEqual(result["DB_PORT"], "5432")

    def test_ignores_blank_lines_and_comments(self):
        text = "# This is a comment\n\nAPI_KEY=secret123\n\n# Another comment"
        result = parse_env(text)
        self.assertEqual(len(result), 1)
        self.assertEqual(result["API_KEY"], "secret123")

    def test_values_with_equals_preserved(self):
        text = "CONNECTION=host=localhost;port=5432"
        result = parse_env(text)
        self.assertEqual(result["CONNECTION"], "host=localhost;port=5432")


if __name__ == "__main__":
    unittest.main()