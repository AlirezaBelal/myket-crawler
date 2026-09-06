import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from html_parser import (  # noqa: E402
    normalize_digits,
    parse_installation_count,
    parse_last_update_to_epoch,
    parse_price,
)


class ParserTests(unittest.TestCase):
    def test_normalize_digits(self):
        self.assertEqual(normalize_digits("۱۲۳٤٥"), "12345")

    def test_parse_installation_count(self):
        self.assertEqual(parse_installation_count("۲ میلیون+"), 2_000_000)
        self.assertEqual(parse_installation_count("12 هزار"), 12_000)
        self.assertEqual(parse_installation_count("1.5 میلیون"), 1_500_000)

    def test_parse_price(self):
        self.assertEqual(parse_price("رایگان"), 0)
        self.assertEqual(parse_price("۱۲,۰۰۰ تومان"), 12000)

    def test_parse_jalali_date(self):
        self.assertGreater(parse_last_update_to_epoch("۱۴۰۵/۰۶/۱۵"), 0)
        self.assertEqual(parse_last_update_to_epoch("N/A"), 0)


if __name__ == "__main__":
    unittest.main()
