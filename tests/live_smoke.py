import argparse
import sqlite3
from contextlib import closing
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crawler import MyketCrawler  # noqa: E402


KNOWN_APP_URL = "https://myket.ir/app/ir.filmnet.android"


def read_rows(db_path: Path):
    with closing(sqlite3.connect(db_path)) as connection:
        return connection.execute(
            "SELECT package_name, name, installation_count, category, source "
            "FROM app_details ORDER BY package_name"
        ).fetchall()


def main() -> int:
    parser = argparse.ArgumentParser(description="Opt-in small Myket live smoke test")
    parser.add_argument("--yes-live", action="store_true",
                        help="I authorize limited public Myket network requests.")
    args = parser.parse_args()
    if not args.yes_live:
        parser.error("To run live requests, pass --yes-live explicitly")
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "live-smoke.db"
        crawler = MyketCrawler(
            db_path,
            headless=True,
            max_apps=3,
            category_limit=1,
            subcategory_limit=1,
        )
        try:
            crawler.crawl_app_url(KNOWN_APP_URL)
            if crawler.stats.saved != 1:
                raise RuntimeError(
                    f"Known app smoke failed: saved={crawler.stats.saved}, "
                    f"failed={crawler.stats.failed}"
                )

            rows = read_rows(db_path)
            filmnet = [row for row in rows if row[0] == "ir.filmnet.android"]
            if not filmnet:
                raise RuntimeError("Known Filmnet app was not persisted")
            package_name, name, installs, category, source = filmnet[0]
            if not name or installs <= 0 or not category or source != "myket":
                raise RuntimeError(
                    "Known app metadata is incomplete: "
                    f"package={package_name!r}, name={name!r}, installs={installs!r}, "
                    f"category={category!r}, source={source!r}"
                )

            crawler.crawl(("apps",))
            rows = read_rows(db_path)
            if crawler.stats.saved < 2 or len(rows) < 2:
                raise RuntimeError(
                    "Discovery smoke did not persist an additional app: "
                    f"stats={crawler.stats}, rows={len(rows)}"
                )

            print("Live smoke passed")
            print(f"stats={crawler.stats}")
            for row in rows:
                print(row)
            return 0
        finally:
            crawler.close()


if __name__ == "__main__":
    raise SystemExit(main())
