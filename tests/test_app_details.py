import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from models import AppDetails, Source  # noqa: E402


class AppDetailsTests(unittest.TestCase):
    def test_save_replaces_same_package_and_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "apps.db"

            AppDetails(
                name="First",
                package_name="ir.example.app",
                installation_count=100,
                source=Source.MYKET,
            ).save_to_db(str(db))
            AppDetails(
                name="Updated",
                package_name="ir.example.app",
                installation_count=200,
                source=Source.MYKET,
            ).save_to_db(str(db))

            connection = sqlite3.connect(db)
            try:
                count = connection.execute(
                    "SELECT COUNT(*) FROM app_details"
                ).fetchone()[0]
                row = connection.execute(
                    "SELECT name, installation_count, source FROM app_details"
                ).fetchone()
            finally:
                connection.close()

            self.assertEqual(count, 1)
            self.assertEqual(row, ("Updated", 200, "myket"))


if __name__ == "__main__":
    unittest.main()
