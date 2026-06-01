"""
test_md_lister.py — Unit Tests for Markdown File Lister

3 unit tests using Python's unittest framework.
"""

import os
import tempfile
import unittest
from pathlib import Path
from md_lister import list_markdown_files


class TestListMarkdownFiles(unittest.TestCase):

    def test_list_md_files_in_temp_dir(self):
        """Create a temp dir with mixed files, verify only .md files returned."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create .md files
            Path(tmpdir, "readme.md").touch()
            Path(tmpdir, "notes.md").touch()
            Path(tmpdir, "guide.MD").touch()
            # Create non-.md files
            Path(tmpdir, "script.py").touch()
            Path(tmpdir, "data.json").touch()
            Path(tmpdir, "image.png").touch()

            result = list_markdown_files(tmpdir)
            self.assertEqual(result, ["guide.MD", "notes.md", "readme.md"])

    def test_empty_directory(self):
        """Verify empty list returned for directory with no .md files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "script.py").touch()
            Path(tmpdir, "data.json").touch()

            result = list_markdown_files(tmpdir)
            self.assertEqual(result, [])

    def test_nonexistent_directory(self):
        """Verify FileNotFoundError is raised for invalid path."""
        with self.assertRaises(FileNotFoundError):
            list_markdown_files("/this/path/does/not/exist/12345")


if __name__ == "__main__":
    unittest.main()