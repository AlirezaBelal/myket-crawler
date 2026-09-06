import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crawler import (  # noqa: E402
    is_app_url,
    is_category_url,
    is_collection_url,
    is_myket_url,
)


class UrlDiscoveryTests(unittest.TestCase):
    def test_app_url(self):
        self.assertTrue(is_app_url("https://myket.ir/app/ir.filmnet.android"))
        self.assertFalse(is_app_url("https://myket.ir/apps/weather"))

    def test_category_url(self):
        self.assertTrue(is_category_url("https://myket.ir/apps/weather", "apps"))
        self.assertTrue(is_category_url("https://myket.ir/games/action", "games"))
        self.assertFalse(is_category_url("https://myket.ir/list/foo", "apps"))

    def test_collection_url(self):
        self.assertTrue(
            is_collection_url("https://myket.ir/list/most-useful-android-apps-in-daily-life")
        )
        self.assertFalse(is_collection_url("https://myket.ir/apps"))

    def test_rejects_external_hosts(self):
        self.assertFalse(is_myket_url("https://example.com/app/foo"))
        self.assertFalse(is_app_url("https://example.com/app/foo"))


if __name__ == "__main__":
    unittest.main()
