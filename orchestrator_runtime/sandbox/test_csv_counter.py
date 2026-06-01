"""
test_csv_counter.py - Unit Tests for CSV Row Counter
"""
import csv, os, tempfile, unittest
from csv_counter import count_data_rows

class TestCsvCounter(unittest.TestCase):
    def test_counts_data_rows_excluding_header(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['name', 'value'])
            writer.writerow(['a', 1])
            writer.writerow(['b', 2])
            writer.writerow(['c', 3])
            tmpfile = f.name
        try:
            self.assertEqual(count_data_rows(tmpfile), 3)
        finally:
            os.unlink(tmpfile)

    def test_empty_csv_returns_zero(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['name', 'value'])
            tmpfile = f.name
        try:
            self.assertEqual(count_data_rows(tmpfile), 0)
        finally:
            os.unlink(tmpfile)

    def test_nonexistent_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            count_data_rows('/no/such/file.csv')

if __name__ == '__main__':
    unittest.main()