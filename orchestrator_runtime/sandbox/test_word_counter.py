"""
test_word_counter.py - Unit Tests for TXT Word Counter
"""
import os, tempfile, unittest
from word_counter import count_words


class TestWordCounter(unittest.TestCase):
    def test_counts_words_ignoring_extra_spaces(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("  hello   world  \n  foo    bar   baz  \n")
            tmpfile = f.name
        try:
            self.assertEqual(count_words(tmpfile), 5)
        finally:
            os.unlink(tmpfile)

    def test_ignores_blank_lines(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("hello\n\n\nworld\n   \nfoo\n")
            tmpfile = f.name
        try:
            self.assertEqual(count_words(tmpfile), 3)
        finally:
            os.unlink(tmpfile)

    def test_nonexistent_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            count_words("/no/such/file.txt")


if __name__ == "__main__":
    unittest.main()