"""Offline acceptance checks for the premium Persian report UI."""
import sys
from contextlib import closing
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from local_report import create_demo, create_report
from models.AppDetails import AppDetails, Source


class SnapshotParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.inputs = []
        self.rows = 0
        self.statics = 0
        self.styles = 0

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if tag == "input":
            self.inputs.append(attrs)
        if tag == "tr" and "data-search" in attrs:
            self.rows += 1
        if tag == "script" and "src" in attrs:
            self.statics += 1
        if tag == "link" and attrs.get("rel") == "stylesheet":
            self.statics += 1
        if tag == "style":
            self.styles += 1


class ReportDesignTests(unittest.TestCase):
    def test_complete_demo_ui_and_local_interactions(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder) / "demo.db"
            report = Path(folder) / "demo.html"
            self.assertEqual(create_demo(db), 12)
            self.assertEqual(create_report(db, report), 12)
            markup = report.read_text(encoding="utf-8")
            parser = SnapshotParser()
            parser.feed(markup)
            self.assertEqual(parser.rows, 12)
            self.assertEqual(parser.statics, 0, "External CSS/JS is not allowed")
            self.assertEqual(parser.styles, 1)
            for identifier in (
                "overview", "categories", "inventory", "search", "category-filter",
                "sort-order", "reset-filters", "empty-reset", "empty",
                "results-count", "theme-toggle", "apps", "local-data-file", "local-data-status", "reset-local-data",
            ):
                self.assertIn(identifier, parser.ids)
            self.assertIn("دموی ساختگی · غیرواقعی", markup)
            self.assertIn("data-category=", markup)
            self.assertIn("data-rating=", markup)
            self.assertIn("data-installs=", markup)
            self.assertIn('dir="rtl"', markup)
            self.assertIn('aria-live="polite"', markup)
            self.assertIn('prefers-reduced-motion:reduce', markup)
            self.assertIn('min-width:0', markup)
            self.assertIn('document.documentElement', markup)
            self.assertIn('matchesCategory', markup)
            self.assertIn('rows.sort', markup)
            for token in (
                "__REPORT_STYLE__", "__REPORT_SCRIPT__", "__REPORT_ROWS__",
                "__REPORT_CATEGORY_BARS__", "__REPORT_CATEGORY_OPTIONS__",
                "__REPORT_MODE__",
            ):
                self.assertNotIn(token, markup)
            self.assertNotIn('src="https://', markup)
            self.assertNotIn('@import', markup)
            self.assertNotIn('fetch(', markup)
            self.assertIn("بدون بارگذاری یا ذخیره‌سازی", markup)
            self.assertIn("ReportImport", markup)

    def test_escaped_category_and_name_dont_create_html(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder) / "apps.db"
            report = Path(folder) / "apps.html"
            AppDetails(
                name='"><img src=x onerror=alert(1)>',
                package_name="ir.example.unsafe",
                category='<svg onload=alert(1)>',
                author_email="hidden@private.test",
                source=Source.MYKET,
            ).save_to_db(str(db))
            create_report(db, report)
            markup = report.read_text(encoding="utf-8")
            parser = SnapshotParser()
            parser.feed(markup)
            self.assertEqual(parser.rows, 1)
            self.assertNotIn('<img src=x', markup)
            self.assertNotIn('<svg onload=', markup)
            self.assertIn("&lt;svg onload=alert(1)&gt;", markup)
            self.assertNotIn("hidden@private.test", markup)

    def test_empty_report_has_helpful_state_and_no_zero_division(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder) / "blank.db"
            report = Path(folder) / "report.html"
            AppDetails(name="Temporary", package_name="temporary",
                       source=Source.MYKET).save_to_db(str(db))
            import sqlite3
            with closing(sqlite3.connect(db)) as connection:
                connection.execute("DELETE FROM app_details")
                connection.commit()
            self.assertEqual(create_report(db, report), 0)
            markup = report.read_text(encoding="utf-8")
            self.assertIn("هنوز برنامه‌ای برای نمایش وجود ندارد.", markup)
            self.assertIn("نتیجه‌ای پیدا نشد", markup)


if __name__ == "__main__":
    unittest.main()
