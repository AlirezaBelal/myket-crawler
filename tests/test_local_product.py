"""End-to-end offline product tests: no Myket requests or credentials."""

import csv
from contextlib import closing
import io
import os
import sqlite3
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import main as cli
from local_report import create_demo, create_report, export_csv
from models.AppDetails import AppDetails, Source


class LocalProductTests(unittest.TestCase):
    def test_demo_creates_twelve_fictional_apps_and_a_searchable_report(self):
        with tempfile.TemporaryDirectory() as folder:
            database = Path(folder) / "demo.db"
            report = Path(folder) / "demo-report.html"
            with patch.object(cli, "run_crawler") as network:
                with patch.object(sys, "argv", [
                    "main.py", "--demo", "--db", str(database),
                ]):
                    with redirect_stdout(io.StringIO()):
                        self.assertEqual(cli.main(), 0)
                network.assert_not_called()
            self.assertTrue(database.is_file())
            self.assertTrue(report.is_file())
            page = report.read_text(encoding="utf-8")
            self.assertIn("گزارش برنامه‌های مایکت", page)
            self.assertIn("id=\"search\"", page)
            self.assertNotIn("__REPORT_ROWS__", page)
            with closing(sqlite3.connect(database)) as conn:
                self.assertEqual(
                    conn.execute("SELECT COUNT(*) FROM app_details").fetchone()[0],
                    12,
                )
            # Rerunning --demo must not append synthetic rows to an existing DB.
            with patch.object(sys, "argv", [
                "main.py", "--demo", "--db", str(database),
            ]):
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(cli.main(), 2)

    def test_html_escapes_api_content_and_excludes_contacts(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder) / "records.db"
            output = Path(folder) / "report.html"
            AppDetails(
                name="<script>alert(1)</script>",
                package_name="ir.test.fake",
                category="Productivity & Tools",
                author_email="not-for-the-report@example.test",
                author_phone_number="PRIVATE-CONTACT",
                installation_count=1234,
                average_score=4.3,
                source=Source.MYKET,
            ).save_to_db(str(db))
            self.assertEqual(create_report(db, output), 1)
            page = output.read_text(encoding="utf-8")
            self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", page)
            self.assertNotIn("<script>alert(1)</script>", page)
            self.assertIn("Productivity &amp; Tools", page)
            self.assertNotIn("PRIVATE-CONTACT", page)
            self.assertNotIn("not-for-the-report@example.test", page)
            self.assertIn("1,234", page)

    def test_csv_is_utf8_and_formula_safe(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder) / "app.db"
            output = Path(folder) / "apps.csv"
            AppDetails(name="=HYPERLINK(1)", package_name="ir.demo",
                       source=Source.MYKET).save_to_db(str(db))
            self.assertEqual(export_csv(db, output), 1)
            with output.open(encoding="utf-8-sig", newline="") as handle:
                items = list(csv.DictReader(handle))
            self.assertEqual(items[0]["name"], "'=HYPERLINK(1)")
            self.assertEqual(items[0]["package_name"], "ir.demo")
            self.assertNotIn("author_email", items[0])

    def test_relative_demo_path_works_for_windows_launcher(self):
        with tempfile.TemporaryDirectory() as folder:
            previous = Path.cwd()
            try:
                os.chdir(folder)
                db = Path("data") / "demo-relative.db"
                self.assertEqual(create_demo(db), 12)
                report = Path("data") / "demo-relative-report.html"
                self.assertEqual(create_report(db, report), 12)
                self.assertTrue(report.exists())
            finally:
                os.chdir(previous)

    def test_exports_never_overwrite_the_input_database(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder) / "important.db"
            AppDetails(name="Keep me", package_name="ir.safe", source=Source.MYKET).save_to_db(str(db))
            original = db.read_bytes()
            with self.assertRaisesRegex(ValueError, "must not overwrite"):
                export_csv(db, db)
            with self.assertRaisesRegex(ValueError, "must not overwrite"):
                create_report(db, db)
            self.assertEqual(db.read_bytes(), original)
            with closing(sqlite3.connect(db)) as connection:
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM app_details").fetchone()[0], 1)

    def test_corrupt_numeric_fields_cannot_break_local_report(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder) / "malformed.db"
            report = Path(folder) / "report.html"
            AppDetails(name="Damaged", package_name="ir.bad",
                       source=Source.MYKET).save_to_db(str(db))
            with closing(sqlite3.connect(db)) as connection:
                connection.execute(
                    "UPDATE app_details SET installation_count=?, average_score=?",
                    ("not-a-number", "NaN"),
                )
                connection.commit()
            self.assertEqual(create_report(db, report), 1)
            page = report.read_text(encoding="utf-8")
            self.assertIn("Damaged", page)
            self.assertNotIn("nan", page.lower())

    def test_template_markers_inside_source_fields_are_not_expanded(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder) / "records.db"
            out = Path(folder) / "report.html"
            AppDetails(name="Example __REPORT_COUNT__",
                       package_name="ir.marker",
                       source=Source.MYKET).save_to_db(str(db))
            create_report(db, out)
            markup = out.read_text(encoding="utf-8")
            self.assertIn("Example __REPORT_COUNT__", markup)
            self.assertIn("ir.marker", markup)

    def test_missing_db_rejected_without_creating_it(self):
        with tempfile.TemporaryDirectory() as folder:
            missing = Path(folder) / "missing.db"
            with self.assertRaises(ValueError):
                export_csv(missing, Path(folder) / "out.csv")
            self.assertFalse(missing.exists())

    def test_report_limit_is_enforced(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder) / "data.db"
            AppDetails(name="A", package_name="a", source=Source.MYKET).save_to_db(str(db))
            AppDetails(name="B", package_name="b", source=Source.MYKET).save_to_db(str(db))
            out = Path(folder) / "report.html"
            self.assertEqual(create_report(db, out, limit=1), 1)
            self.assertIn("تنها 1 ردیف", out.read_text(encoding="utf-8"))
            for limit in (0, 1001):
                with self.assertRaises(ValueError):
                    create_report(db, out, limit=limit)

    def test_without_arguments_does_not_start_crawler(self):
        with patch.object(sys, "argv", ["main.py"]):
            with patch.object(cli, "run_crawler") as fetch:
                with redirect_stdout(io.StringIO()) as stdout:
                    self.assertEqual(cli.main(), 0)
                fetch.assert_not_called()
                self.assertIn("No network requests made", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
