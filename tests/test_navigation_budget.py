"""Global navigation budget regressions: synthetic browser, no network access."""
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import main as cli
from crawler import DEFAULT_NAVIGATION_BUDGET, MyketCrawler, NavigationBudgetExceeded


def fake_driver():
    driver = MagicMock()
    driver.get.side_effect = lambda url: setattr(driver, "current_url", url)
    return driver


def valid_app(package):
    app = MagicMock()
    app.package_name = package
    app.name = "Sample app"
    app.version = "1.0"
    return app


class NavigationBudgetTests(unittest.TestCase):
    def make_crawler(self, folder, driver, **kwargs):
        with patch.object(MyketCrawler, "_build_driver", return_value=driver):
            return MyketCrawler(Path(folder) / "apps.db", **kwargs)

    def test_budget_blocks_extra_detail_and_preserves_prior_saves(self):
        driver = fake_driver()
        links = [
            "https://myket.ir/app/ir.example.first",
            "https://myket.ir/app/ir.example.second",
        ]
        with tempfile.TemporaryDirectory() as folder:
            crawler = self.make_crawler(folder, driver, max_navigations=2)
            with patch.object(crawler, "_sleep_ms"), \
                 patch.object(crawler, "_extract_category_links", return_value=[]), \
                 patch.object(crawler, "_extract_app_links", return_value=links), \
                 patch.object(crawler, "_extract_collection_links", return_value=[]), \
                 patch("crawler.create_app_details_from_html", return_value=valid_app("ir.example.first")) as parser:
                with redirect_stdout(io.StringIO()):
                    stats = crawler.crawl(("apps", "games"))
            self.assertEqual(driver.get.call_count, 2)  # section + one detail
            self.assertEqual(parser.call_count, 1)
            self.assertEqual(stats.saved, 1)
            self.assertEqual(stats.failed, 0)
            self.assertEqual(crawler.navigations, 2)
            self.assertTrue(crawler.budget_exhausted)
            crawler.close()

    def test_budget_equal_to_required_pages_is_not_reported_as_truncated(self):
        driver = fake_driver()
        with tempfile.TemporaryDirectory() as folder:
            crawler = self.make_crawler(folder, driver, max_navigations=2, max_apps=1)
            with patch.object(crawler, "_sleep_ms"), \
                 patch.object(crawler, "_extract_category_links", return_value=[]), \
                 patch.object(crawler, "_extract_app_links", return_value=["https://myket.ir/app/ir.example.app"]), \
                 patch.object(crawler, "_extract_collection_links", return_value=[]), \
                 patch("crawler.create_app_details_from_html", return_value=valid_app("ir.example.app")):
                with redirect_stdout(io.StringIO()):
                    stats = crawler.crawl(("apps", "games"))
            self.assertEqual(stats.saved, 1)
            self.assertEqual(driver.get.call_count, 2)
            self.assertFalse(crawler.budget_exhausted)
            crawler.close()

    def test_budget_is_global_across_sections(self):
        driver = fake_driver()
        with tempfile.TemporaryDirectory() as folder:
            crawler = self.make_crawler(folder, driver, max_navigations=1)
            with patch.object(crawler, "_sleep_ms"), \
                 patch.object(crawler, "_extract_category_links", return_value=[]), \
                 patch.object(crawler, "_extract_app_links", return_value=[]), \
                 patch.object(crawler, "_extract_collection_links", return_value=[]):
                with redirect_stdout(io.StringIO()):
                    stats = crawler.crawl(("apps", "games"))
            self.assertEqual(stats.saved, 0)
            self.assertEqual(driver.get.call_count, 1)
            self.assertEqual(driver.get.call_args.args[0], "https://myket.ir/apps")
            self.assertTrue(crawler.budget_exhausted)
            crawler.close()

    def test_failed_navigation_is_counted_without_retry(self):
        driver = MagicMock()
        driver.get.side_effect = OSError("fake browser failure")
        with tempfile.TemporaryDirectory() as folder:
            crawler = self.make_crawler(folder, driver, max_navigations=1)
            with patch.object(crawler, "_sleep_ms"):
                with self.assertRaises(OSError):
                    crawler._open("https://myket.ir/apps")
                with self.assertRaises(NavigationBudgetExceeded):
                    crawler._open("https://myket.ir/games")
            self.assertEqual(crawler.navigations, 1)
            self.assertEqual(driver.get.call_count, 1)
            self.assertTrue(crawler.budget_exhausted)
            crawler.close()

    def test_direct_caller_rejects_nonpositive_budget_before_browser(self):
        with patch.object(MyketCrawler, "_build_driver") as browser:
            for value in (0, -1):
                with self.subTest(value=value), self.assertRaises(ValueError):
                    MyketCrawler(Path("unused.db"), max_navigations=value)
            browser.assert_not_called()

    def test_cli_reports_truncated_run_as_failure_even_with_saves(self):
        args = SimpleNamespace(
            section="apps", db=Path("unused.db"), headful=False,
            max_apps=10, max_navigations=2, full=False,
            category_limit=1, subcategory_limit=1,
        )
        with patch("crawler.MyketCrawler") as factory:
            fake = factory.return_value
            fake.crawl.return_value = SimpleNamespace(
                discovered=1, saved=1, failed=0, skipped_duplicates=0,
            )
            fake.navigations = 2
            fake.budget_exhausted = True
            fake.stopped_due_to_failures = False
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as errors:
                self.assertEqual(cli.run_crawler(args), 1)
            self.assertIn("budget reached", errors.getvalue().lower())
            factory.assert_called_once()
            self.assertEqual(factory.call_args.kwargs["max_navigations"], 2)
            fake.close.assert_called_once()

    def test_cli_defaults_to_bounded_mode_unless_full_opted_in(self):
        with patch("crawler.MyketCrawler") as factory:
            fake = factory.return_value
            fake.crawl.return_value = SimpleNamespace(
                discovered=1, saved=1, failed=0, skipped_duplicates=0,
            )
            fake.navigations = 1
            fake.budget_exhausted = False
            fake.stopped_due_to_failures = False
            for full, expected in ((False, DEFAULT_NAVIGATION_BUDGET), (True, None)):
                args = SimpleNamespace(
                    section="apps", db=Path("unused.db"), headful=False,
                    max_apps=1, max_navigations=None, full=full,
                    category_limit=1, subcategory_limit=1,
                )
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(cli.run_crawler(args), 0)
                self.assertEqual(factory.call_args.kwargs["max_navigations"], expected)

    def test_cli_rejects_invalid_budget_and_accepts_explicit_budget_mode(self):
        for value in ("0", "-9"):
            with self.subTest(value=value):
                with patch.object(sys, "argv", ["myket", "--max-navigations", value]):
                    with patch.object(cli, "run_crawler") as browser:
                        with redirect_stderr(io.StringIO()):
                            with self.assertRaises(SystemExit) as exc:
                                cli.main()
                    self.assertEqual(exc.exception.code, 2)
                    browser.assert_not_called()
        with patch.object(sys, "argv", ["myket", "--max-navigations", "2"]):
            with patch.object(cli, "run_crawler", return_value=0) as browser:
                self.assertEqual(cli.main(), 0)
                browser.assert_called_once()


if __name__ == "__main__":
    unittest.main()
