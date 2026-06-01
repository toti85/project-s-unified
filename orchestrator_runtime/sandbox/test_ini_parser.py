"""
test_ini_parser.py - Unit Tests for INI Config Parser
"""
import os, tempfile, unittest
from ini_parser import parse_ini


class TestIniParser(unittest.TestCase):
    def test_parses_sections_and_keys(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ini", delete=False) as f:
            f.write("[database]\nhost = localhost\nport = 5432\n\n[app]\nname = test\n")
            tmpfile = f.name
        try:
            result = parse_ini(tmpfile)
            self.assertEqual(result["database"]["host"], "localhost")
            self.assertEqual(result["database"]["port"], "5432")
            self.assertEqual(result["app"]["name"], "test")
        finally:
            os.unlink(tmpfile)

    def test_ignores_comments(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ini", delete=False) as f:
            f.write("# comment\n[section]\n; another comment\nkey = val\n")
            tmpfile = f.name
        try:
            result = parse_ini(tmpfile)
            self.assertEqual(result["section"]["key"], "val")
            self.assertNotIn("# comment", result)
        finally:
            os.unlink(tmpfile)

    def test_nonexistent_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            parse_ini("/no/such/file.ini")


if __name__ == "__main__":
    unittest.main()