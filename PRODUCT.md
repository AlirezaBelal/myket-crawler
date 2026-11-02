# Myket Crawler — product handoff

**Delivery scope:** local-first Myket metadata research tool, with opt-in Selenium collection. This document records what is shipped and what remains outside the completed product scope; it is not a claim of a verified, unrestricted production scraping service.

## Supported user workflows

1. **Try without network:** `python src/main.py --demo` creates 12 explicitly fictional records and a standalone Persian RTL HTML report; Windows also has `scripts/desktop-demo.cmd`.
2. **Inspect existing data:** `--db path/to/apps.db --report output.html` produces an offline, searchable, filterable, responsive report; `--export-csv output.csv` creates a spreadsheet-safe export without developer contacts.
3. **Collect a permitted sample:** use `--section apps --category-limit 1 --subcategory-limit 1 --max-apps 3 --max-navigations 20`, after independently verifying access permissions.

Data is stored in the documented `app_details` SQLite schema, shared with `cafebazaar-crawler`. Export destinations are atomic and cannot target the main database or its `-wal`, `-shm`, `-journal` files. Raw SQLite datasets may contain optional developer contacts and must remain private unless obligations have been reviewed.

## Collection safety contract

- Running without arguments, with `--demo`, `--report`, or `--export-csv` does **not** start Selenium or connect to Myket.
- Ordinary bounded crawls default to **100 attempted Selenium `driver.get()` navigations** in total, spanning sections, categories, collections, and details. `--max-navigations N` overrides the limit. Limits must be positive. Counted attempts include browser navigation failures.
- The cap stops a new navigation **before it starts**. Previously saved rows are preserved. If the crawler needs more pages than the cap, the run is reported incomplete with a nonzero exit.
- `--max-apps N` caps successful app saves, **not** browser requests. If that target is met exactly at the navigation limit, reaching the requested target is not falsely marked as budget exhaustion.
- `--full` deliberately allows an uncapped navigation run unless `--max-navigations N` is supplied; do not use it without permission and independent rate controls.
- The navigation budget **does not count** Chrome subresources, automatic redirects, background fetches, or total HTTP requests. It is a bounded application navigation mechanism, not a guarantee of a total network request limit.
- Navigation and parsed package URLs are validated against allowed Myket HTTPS hosts/routes; discovery stops on unexpected final hosts. Three consecutive app-detail failures stop crawling; any recorded detail failure also causes a nonzero exit.
- Live smoke is opt-in/manual only. Never bypass a site's access controls or robots/terms requirements.

## Exit codes

| Exit | Meaning |
| --- | --- |
| `0` | Offline operation succeeded, or live run saved at least one app with no recorded detail failure and without exhausting the budget |
| `1` | Empty, partially failed, or budget-exhausted crawl |
| `2` | Invalid input, missing/incompatible local data or other handled CLI error |
| `130` | Interrupted live crawl; saved data retained |

These are local workflow exit codes, not a guarantee of marketplace completeness.

## Acceptance and verification

Required checks for delivery:

```bash
python -m compileall -q src tests
python -m unittest discover -s tests -v
```

GitHub Actions runs the offline suite on Ubuntu/Python 3.9 and 3.14 and Windows/Python 3.12. The visual workflow runs browser QA on Pull Requests affecting report code. The tests use mock browsers/temporary databases: **no Myket requests** or actual user datasets are necessary. Confirm the final master CI after merging the product-hardening PR; do not mistake a successful PR build for final-master validation.

## Known limitations and out-of-scope features

- Myket's current DOM, access restrictions, source permissions, and real Chrome/Selenium collection are **not live-verified** as part of this handoff. A successful offline test cannot prove live collection correctness.
- Network subrequests and redirects may exceed a navigation cap. Live collection still requires deliberate permission and conservative request intervals.
- History/snapshots, scheduled production collection, resumable crawling, real-time health metrics, and cross-store intelligence are **future optional extensions**, not delivered features. See `ROADMAP.md`.
- Selector updates, controlled retry/backoff, and any live service hardening should be based on independently verified authorized live fixtures. No aggressive retries were added.

## Completion decision

The **local-first offline research product and guarded, opt-in collection interface** are the completed delivery. The repository remains public with `master` as the default branch, without archiving or changing visibility. No actual Myket data or user datasets are included. Future live-crawler improvements require separate scope and permission; they do not block using the offline demo/report/export product today.
