import argparse
from pathlib import Path

import config
from crawler import MyketCrawler


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Crawl public Myket app metadata into a local SQLite database."
    )
    parser.add_argument(
        "--section",
        choices=("all", "apps", "games"),
        default="all",
        help="Which Myket section to crawl (default: all).",
    )
    parser.add_argument(
        "--max-apps",
        type=int,
        default=None,
        help="Stop after saving this many unique apps. Useful for smoke tests.",
    )
    parser.add_argument(
        "--category-limit",
        type=int,
        default=None,
        help="Limit categories per section.",
    )
    parser.add_argument(
        "--subcategory-limit",
        type=int,
        default=None,
        help="Limit 'all apps' groups per category.",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=config.RESULT_FILE,
        help=f"SQLite output path (default: {config.RESULT_FILE}).",
    )
    parser.add_argument(
        "--headful",
        action="store_true",
        help="Show the Chrome window instead of running headless.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    for option, value in (
        ("--max-apps", args.max_apps),
        ("--category-limit", args.category_limit),
        ("--subcategory-limit", args.subcategory_limit),
    ):
        if value is not None and value <= 0:
            raise SystemExit(f"{option} must be greater than zero")

    config.ensure_data_dir()
    sections = ("apps", "games") if args.section == "all" else (args.section,)

    crawler = MyketCrawler(
        args.db,
        headless=not args.headful,
        max_apps=args.max_apps,
        category_limit=args.category_limit,
        subcategory_limit=args.subcategory_limit,
    )
    try:
        stats = crawler.crawl(sections)
    except KeyboardInterrupt:
        print("\nInterrupted by user; data already written to SQLite is preserved.")
        stats = crawler.stats
    finally:
        crawler.close()

    print(
        "== Crawl summary == "
        f"discovered={stats.discovered} "
        f"saved={stats.saved} "
        f"failed={stats.failed} "
        f"duplicates={stats.skipped_duplicates}"
    )
    return 0 if stats.saved or stats.failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
