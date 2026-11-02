"""Offline security and CLI regression tests; no browser or Myket access."""
import io
import sys
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from types import SimpleNamespace
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


    def test_three_consecutive_detail_failures_stop_all_further_requests(self):
        links = [f"https://myket.ir/app/ir.example.{i}" for i in range(6)]
        driver = MagicMock()
        driver.get.side_effect = lambda url: setattr(driver, "current_url", url)
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(MyketCrawler, "_build_driver", return_value=driver):
                crawler = MyketCrawler(Path(tmp) / "apps.db", max_apps=1)
            with patch.object(crawler, "_sleep_ms"):
                with patch("crawler.create_app_details_from_html", side_effect=ValueError("Broken markup")) as parser:
                    crawler._crawl_links(links)
                    crawler._crawl_links(links[3:])
            self.assertEqual(driver.get.call_count, 3)
            self.assertEqual(parser.call_count, 3)
            self.assertEqual(crawler.stats.failed, 3)
            self.assertEqual(crawler.stats.discovered, 3)
            self.assertTrue(crawler.stopped_due_to_failures)
            self.assertFalse((Path(tmp) / "apps.db").exists())
            crawler.close()

    def test_success_resets_consecutive_failure_counter(self):
        links = [f"https://myket.ir/app/ir.example.{i}" for i in range(7)]
        driver = MagicMock()
        driver.get.side_effect = lambda url: setattr(driver, "current_url", url)
        saved_app = MagicMock()
        saved_app.package_name = "ir.example.2"
        saved_app.name = "Valid"
        saved_app.version = "1"
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(MyketCrawler, "_build_driver", return_value=driver):
                crawler = MyketCrawler(Path(tmp) / "apps.db")
            with patch.object(crawler, "_sleep_ms"):
                with patch("crawler.create_app_details_from_html", side_effect=[
                    ValueError("bad 0"), ValueError("bad 1"), saved_app,
                    ValueError("bad 3"), ValueError("bad 4"), ValueError("bad 5"),
                ]):
                    crawler._crawl_links(links)
            self.assertEqual(driver.get.call_count, 6)
            self.assertEqual(crawler.stats.saved, 1)
            self.assertEqual(crawler.stats.failed, 5)
            self.assertTrue(crawler.stopped_due_to_failures)
            saved_app.save_to_db.assert_called_once()
            crawler.close()

    def test_driver_quits_when_timeout_configuration_fails(self):
        driver = MagicMock()
        driver.set_page_load_timeout.side_effect = RuntimeError("setup failed")
        with patch("crawler.webdriver.Chrome", return_value=driver):
            with self.assertRaisesRegex(RuntimeError, "setup failed"):
                MyketCrawler._build_driver(headless=True)
        driver.quit.assert_called_once()


class CliBoundednessTests(unittest.TestCase):
    def test_nonpositive_limits_rejected_before_browser_launch(self):
        for option in ("--max-apps", "--category-limit", "--subcategory-limit"):
            for value in ("0", "-3"):
                with self.subTest(option=option, value=value):
                    with patch.object(sys, "argv", ["myket", option, value]):
                        with patch.object(cli, "run_crawler") as browser:
                            with self.assertRaises(SystemExit) as err:
                                cli.main()
                        browser.assert_not_called()
                        self.assertEqual(err.exception.code, 2)

    def test_aborted_crawl_returns_nonzero_even_with_prior_saves(self):
        args = SimpleNamespace(
            section="apps", db=Path("unused.db"), headful=False,
            max_apps=10, category_limit=1, subcategory_limit=1,
        )
        stats = SimpleNamespace(
            discovered=4, saved=1, failed=3, skipped_duplicates=0,
        )
        with patch("crawler.MyketCrawler") as factory:
            fake = factory.return_value
            fake.crawl.return_value = stats
            fake.stopped_due_to_failures = True
            fake.budget_exhausted = False
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(cli.run_crawler(args), 1)
            fake.close.assert_called_once()



if __name__ == "__main__":
    unittest.main()
