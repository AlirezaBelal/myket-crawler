"""Production audit regressions. Fake browsers and temporary SQLite only."""
import io
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing, redirect_stdout, redirect_stderr
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import main as cli
from crawler import MyketCrawler, is_app_url
from html_parser import create_app_details_from_html
from local_report import create_report, export_csv
from models import AppDetails


class AuditTests(unittest.TestCase):
    def test_discovery_redirect_stops_before_extracting_or_following_links(self):
        for entry in ('section', 'category', 'collection'):
            with self.subTest(entry=entry):
                driver = MagicMock()
                driver.current_url = 'https://untrusted.test/login'
                with patch.object(MyketCrawler, '_build_driver', return_value=driver):
                    crawler = MyketCrawler(Path('unused.db'))
                with patch.object(crawler, '_sleep_ms'), patch.object(crawler, '_extract_app_links', return_value=[] ) as apps, patch.object(crawler, '_extract_category_links') as categories:
                    if entry == 'collection':
                        driver.current_url = 'https://myket.ir/apps/tools'
                        driver.get.side_effect = lambda url: setattr(driver, 'current_url', 'https://untrusted.test/login' if '/list/' in url else url)
                        with patch.object(crawler, '_extract_collection_links', return_value=['https://myket.ir/list/tools']):
                            with self.assertRaises(ValueError):
                                crawler._crawl_category_page('https://myket.ir/apps/tools')
                        self.assertEqual(apps.call_count, 1)
                    else:
                        with self.assertRaises(ValueError):
                            if entry == 'section':
                                crawler.crawl(('apps', 'games'))
                            else:
                                crawler._crawl_category_page('https://myket.ir/apps/tools')
                        apps.assert_not_called()
                    categories.assert_not_called()
                self.assertEqual(driver.get.call_count, 2 if entry == 'collection' else 1)
                crawler.close()

    def test_package_identity_ignores_query_slashes_and_fragments(self):
        driver = MagicMock()
        driver.find_elements.return_value = []
        for suffix in ('?ref=/campaign/other', '#details', '/?ref=x'):
            url = 'https://myket.ir/app/ir.example.app' + suffix
            self.assertEqual(create_app_details_from_html(driver, url).package_name, 'ir.example.app')
        for path in ('ir.example.app/reviews', 'ir.example.app/../ir.other', 'ir.example.app%2Freviews'):
            self.assertFalse(is_app_url('https://myket.ir/app/' + path))

    def test_partial_failures_exit_nonzero_without_open_circuit(self):
        args = SimpleNamespace(section='apps', db=Path('unused.db'), headful=False, max_apps=3, category_limit=1, subcategory_limit=1)
        with patch('crawler.MyketCrawler') as factory:
            fake = factory.return_value
            fake.stopped_due_to_failures = False
            fake.crawl.return_value = SimpleNamespace(discovered=3, saved=2, failed=1, skipped_duplicates=0)
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(cli.run_crawler(args), 1)
            fake.close.assert_called_once()

    def test_exports_reject_reserved_recovery_names_even_when_not_open(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder) / 'apps.db'
            AppDetails(name='Keep', package_name='ir.example.app').save_to_db(str(db))
            for exporter in (create_report, export_csv):
                for suffix in ('-journal', '-wal', '-shm'):
                    recovery = Path(str(db) + suffix)
                    with self.assertRaisesRegex(ValueError, 'recovery files'):
                        exporter(db, recovery)
                    self.assertFalse(recovery.exists())

    def test_exports_preserve_active_wal_and_recovery_paths(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder) / 'apps.db'
            AppDetails(name='Before', package_name='ir.example.app').save_to_db(str(db))
            connection = sqlite3.connect(db)
            try:
                connection.execute('PRAGMA journal_mode=WAL')
                connection.execute('UPDATE app_details SET name=?', ('Committed in WAL',))
                connection.commit()
                wal = Path(str(db) + '-wal')
                original = wal.read_bytes()
                for exporter in (create_report, export_csv):
                    for suffix in ('-wal', '-shm', '-journal'):
                        with self.assertRaisesRegex(ValueError, 'recovery files'):
                            exporter(db, Path(str(db) + suffix))
                self.assertEqual(wal.read_bytes(), original)
                with closing(sqlite3.connect(db)) as reader:
                    self.assertEqual(reader.execute('SELECT name FROM app_details').fetchone()[0], 'Committed in WAL')
            finally:
                connection.close()


if __name__ == '__main__':
    unittest.main()
