"""
test_yaml_key_counter.py - Unit Tests for YAML Key Counter
"""
import os, tempfile, unittest
from yaml_key_counter import count_top_level_keys


class TestYamlKeyCounter(unittest.TestCase):
    def test_counts_top_level_keys(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("name: test\nversion: 1.0\nhost: localhost\n")
            tmpfile = f.name
        try:
            self.assertEqual(count_top_level_keys(tmpfile), 3)
        finally:
            os.unlink(tmpfile)

    def test_ignores_nested_keys(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("database:\n  host: localhost\n  port: 5432\napp: test\n")
            tmpfile = f.name
        try:
            self.assertEqual(count_top_level_keys(tmpfile), 2)
        finally:
            os.unlink(tmpfile)

    def test_nonexistent_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            count_top_level_keys("/no/such/file.yaml")


if __name__ == "__main__":
    unittest.main()