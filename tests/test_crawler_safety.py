"""Offline security and CLI regression tests; no browser or Myket access."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import main as cli
from crawler import MyketCrawler, is_app_url, is_myket_url


class SafeNavigationTests(unittest.TestCase):
    def test_only_https_myket_hosts_are_accepted(self):
        self.assertTrue(is_myket_url("https://myket.ir/app/ir.example"))
        self.assertTrue(is_app_url("https://www.myket.ir/app/ir.example"))
        for url in (
            "http://myket.ir/app/ir.example",
            "ftp://myket.ir/app/ir.example",
            "https://myket.ir.evil.test/app/ir.example",
            "https://user@myket.ir/app/ir.example",
            "https://myket.ir:444/app/ir.example",
        ):
            with self.subTest(url=url):
                self.assertFalse(is_myket_url(url))
                self.assertFalse(is_app_url(url))

    def test_rejects_external_redirect_before_parser_or_db(self):
        driver = MagicMock()
        driver.current_url = "https://example.org/app/ir.example"
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(MyketCrawler, "_build_driver", return_value=driver):
                crawler = MyketCrawler(Path(tmp) / "apps.db", max_apps=1)
            with patch.object(crawler, "_sleep_ms"):
                with patch("crawler.create_app_details_from_html") as parser:
                    stats = crawler.crawl_app_url("https://myket.ir/app/ir.example")
            parser.assert_not_called()
            self.assertEqual(stats.saved, 0)
            self.assertEqual(stats.failed, 1)
            self.assertFalse((Path(tmp) / "apps.db").exists())
            crawler.close()

    def test_rejects_redirect_to_different_myket_package(self):
        driver = MagicMock()
        driver.current_url = "https://myket.ir/app/ir.different"
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(MyketCrawler, "_build_driver", return_value=driver):
                crawler = MyketCrawler(Path(tmp) / "apps.db", max_apps=1)
            with patch.object(crawler, "_sleep_ms"):
                with patch("crawler.create_app_details_from_html") as parser:
                    stats = crawler.crawl_app_url("https://myket.ir/app/ir.expected")
            parser.assert_not_called()
            self.assertEqual(stats.saved, 0)
            self.assertEqual(stats.failed, 1)
            crawler.close()

    def test_rejects_page_with_mismatched_parsed_package(self):
        driver = MagicMock()
        driver.current_url = "https://myket.ir/app/ir.expected"
        app = MagicMock()
        app.package_name = "ir.other"
        app.name = "Other"
        app.version = "1.0"
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(MyketCrawler, "_build_driver", return_value=driver):
                crawler = MyketCrawler(Path(tmp) / "apps.db", max_apps=1)
            with patch.object(crawler, "_sleep_ms"):
                with patch("crawler.create_app_details_from_html", return_value=app):
                    stats = crawler.crawl_app_url("https://myket.ir/app/ir.expected")
            app.save_to_db.assert_not_called()
            self.assertEqual(stats.saved, 0)
            self.assertEqual(stats.failed, 1)
            crawler.close()


class CliBoundednessTests(unittest.TestCase):
    def test_nonpositive_limits_rejected_before_browser_launch(self):
        for option in ("--max-apps", "--category-limit", "--subcategory-limit"):
            for value in ("0", "-3"):
                with self.subTest(option=option, value=value):
                    with patch.object(sys, "argv", ["myket", option, value]):
                        with patch.object(cli, "MyketCrawler") as browser:
                            with self.assertRaises(SystemExit) as err:
                                cli.main()
                        browser.assert_not_called()
                        self.assertIn(option, str(err.exception))


if __name__ == "__main__":
    unittest.main()
