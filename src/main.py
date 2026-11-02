"""Local-first command line interface for Myket market research.

Offline commands intentionally avoid importing Selenium or contacting Myket.
"""
import argparse
import sqlite3
import sys
from pathlib import Path

import config
from local_report import create_demo, create_report, export_csv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Explore local Myket metadata or explicitly run a bounded crawler."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--demo", action="store_true",
        help="Generate fictional apps and an offline HTML dashboard (no network).",
    )
    mode.add_argument(
        "--report", metavar="REPORT.html",
        help="Generate a searchable, standalone HTML report from --db (no network).",
    )
    mode.add_argument(
        "--export-csv", metavar="APPS.csv",
        help="Export selected metadata as UTF-8 CSV (no network).",
    )
    mode.add_argument(
        "--full", action="store_true",
        help="Explicitly request an unbounded Myket crawl.",
    )
    parser.add_argument(
        "--report-limit", type=int, default=500,
        help="Maximum HTML report rows (1..1000; default: 500).",
    )
    parser.add_argument(
        "--section", choices=("all", "apps", "games"), default="all",
        help="Which Myket section to crawl (default: all).",
    )
    parser.add_argument(
        "--max-apps", type=int, default=None,
        help="Stop after saving this many unique apps.",
    )
    parser.add_argument(
        "--max-navigations", type=int, default=None,
        help="Maximum Selenium page navigations across discovery and details "
             "(default: 100 for bounded crawls; --full has no default cap).",
    )
    parser.add_argument(
        "--category-limit", type=int, default=None,
        help="Limit categories per section.",
    )
    parser.add_argument(
        "--subcategory-limit", type=int, default=None,
        help="Limit 'all apps' groups per category.",
    )
    parser.add_argument(
        "--db", type=Path, default=config.RESULT_FILE,
        help="SQLite output path (default: {}).".format(config.RESULT_FILE),
    )
    parser.add_argument(
        "--headful", action="store_true",
        help="Show the Chrome window while crawling.",
    )
    return parser


def run_crawler(args) -> int:
    # Selenium is an optional dependency for offline demo/report/CSV commands.
    from crawler import DEFAULT_NAVIGATION_BUDGET, MyketCrawler

    requested_budget = getattr(args, "max_navigations", None)
    max_navigations = (
        requested_budget if requested_budget is not None
        else None if getattr(args, "full", False) else DEFAULT_NAVIGATION_BUDGET
    )
    sections = ("apps", "games") if args.section == "all" else (args.section,)
    crawler = MyketCrawler(
        args.db,
        headless=not args.headful,
        max_apps=args.max_apps,
        category_limit=args.category_limit,
        subcategory_limit=args.subcategory_limit,
        max_navigations=max_navigations,
    )
    interrupted = False
    try:
        stats = crawler.crawl(sections)
    except KeyboardInterrupt:
        interrupted = True
        print("Interrupted; all previously saved SQLite data is preserved.")
        stats = crawler.stats
    finally:
        crawler.close()

    print(
        "== Crawl summary == "
        "discovered={} saved={} failed={} duplicates={} navigations={}".format(
            stats.discovered, stats.saved, stats.failed, stats.skipped_duplicates,
            getattr(crawler, "navigations", 0),
        )
    )
    if interrupted:
        return 130
    if crawler.budget_exhausted:
        print("Navigation budget reached; saved records are intact.", file=sys.stderr)
        return 1
    if crawler.stopped_due_to_failures:
        print("Crawl stopped after repeated failures; saved records are intact.", file=sys.stderr)
        return 1
    # Do not advertise a completely empty or unsuccessful crawl as successful.
    return 0 if stats.saved > 0 and stats.failed == 0 else 1


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not 1 <= args.report_limit <= 1000:
        parser.error("--report-limit must be between 1 and 1000")
    for option, value in (
        ("--max-apps", args.max_apps),
        ("--max-navigations", args.max_navigations),
        ("--category-limit", args.category_limit),
        ("--subcategory-limit", args.subcategory_limit),
    ):
        if value is not None and value <= 0:
            parser.error("{} must be greater than zero".format(option))

    try:
        if args.demo:
            # Do not put synthetic records into the default real-data database.
            db_path = args.db if args.db != config.RESULT_FILE else config.DATA_DIR / "demo.db"
            count = create_demo(db_path)
            report = db_path.with_name(db_path.stem + "-report.html")
            create_report(db_path, report, limit=args.report_limit)
            print("Created {} fictional demo apps in {}".format(count, db_path))
            print("Open the standalone local report:", report)
            return 0
        if args.report:
            count = create_report(args.db, Path(args.report), limit=args.report_limit)
            print("Saved report with {} apps to {}".format(count, args.report))
            return 0
        if args.export_csv:
            count = export_csv(args.db, Path(args.export_csv))
            print("Exported {} apps to {}".format(count, args.export_csv))
            return 0

        if not args.full and not any((
            args.max_apps, args.max_navigations,
            args.category_limit, args.subcategory_limit
        )):
            print("No network requests made. Start with --demo or a small crawl:")
            print("python src/main.py --section apps --category-limit 1 "
                  "--subcategory-limit 1 --max-apps 3")
            print("Use --full only after confirming unrestricted collection is permitted.")
            return 0
        return run_crawler(args)
    except (OSError, ValueError, sqlite3.DatabaseError, ImportError) as exc:
        print("Myket Crawler error: {}".format(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
