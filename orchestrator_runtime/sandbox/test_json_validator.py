"""
test_json_validator.py - Unit Tests for JSON Key Validator
"""
import json, os, tempfile, unittest
from json_validator import validate_json_keys

class TestValidateJsonKeys(unittest.TestCase):
    def test_valid_json_with_both_keys(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"name": "test", "value": 42}, f)
            tmpfile = f.name
        try:
            self.assertTrue(validate_json_keys(tmpfile))
        finally:
            os.unlink(tmpfile)

    def test_json_missing_value_key(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"name": "test"}, f)
            tmpfile = f.name
        try:
            self.assertFalse(validate_json_keys(tmpfile))
        finally:
            os.unlink(tmpfile)

    def test_nonexistent_file(self):
        with self.assertRaises(FileNotFoundError):
            validate_json_keys("/no/such/file.json")

if __name__ == "__main__":
    unittest.main()