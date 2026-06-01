"""
test_toml_parser.py — Unit tests for toml_parser.py
"""

import unittest

from toml_parser import parse_toml_keys


class TestTomlParser(unittest.TestCase):

    def test_parses_simple_key_value_pairs(self):
        text = "title = \"My App\"\nversion = 1\nhost = localhost"
        result = parse_toml_keys(text)
        self.assertEqual(result["title"], "My App")
        self.assertEqual(result["version"], "1")
        self.assertEqual(result["host"], "localhost")

    def test_ignores_comments_and_blank_lines(self):
        text = "# Database settings\n\nport = 5432\n\n# End"
        result = parse_toml_keys(text)
        self.assertEqual(len(result), 1)
        self.assertEqual(result["port"], "5432")

    def test_stops_at_section_header(self):
        text = "name = test\n\n[database]\nhost = localhost"
        result = parse_toml_keys(text)
        self.assertEqual(len(result), 1)
        self.assertEqual(result["name"], "test")


if __name__ == "__main__":
    unittest.main()