# Myket Crawler — product scope

Myket Crawler is local-first Python software for collecting supported public Myket app metadata with Selenium and saving records into SQLite. This document describes implemented behavior and its boundaries; it is not a claim of an unrestricted or continuously verified marketplace integration.

## Product surfaces

- **Local crawler:** the primary product. Users install and run it on their own computer with an explicitly bounded command.
- **Local outputs:** SQLite persistence, an optional standalone Persian RTL HTML report, and spreadsheet-safe CSV export.
- **Standalone product website:** [alirezabelal.github.io/myket-crawler](https://alirezabelal.github.io/myket-crawler/). It is static documentation and installation guidance. It does not run Selenium, retrieve live marketplace data, accept uploads, or provide online analytics.
- **Portfolio overview:** [Myket Crawler project page](https://alirezabelal.github.io/work/lab/myket-crawler/).

## Supported workflows

1. **Offline demo:** `python src/main.py --demo` creates 12 fictional records and a standalone local HTML report. It does not start Selenium or access the network.
2. **Review local data:** `--db path/to/apps.db --report output.html` or `--export-csv output.csv` reads a local SQLite dataset. Reports and CSV exports omit developer phone and email fields.
3. **Permitted collection:** choose a small section/category/app scope and an explicit navigation budget only after independently verifying the access and use you intend are permitted.

The shared SQLite `app_details` schema is compatible with the sibling CafeBazaar Crawler. The default database path is `data/myket_results.db`. Local demo data defaults to a separate `data/demo.db` and will not replace the production-named database.

## Collection safety contract

- Running with no arguments, `--demo`, `--report`, or `--export-csv` does **not** start Selenium or connect to Myket.
- Ordinary bounded runs default to **100 attempted Selenium `driver.get()` navigations** total across discovery, category, collection, and detail pages. `--max-navigations N` overrides that cap. Values must be positive.
- The cap blocks the next application navigation before it starts. Previously saved rows remain intact. Hitting the cap or recording any detail failure returns a nonzero result.
- `--max-apps N` caps successful saves, not navigation attempts. `--full` removes the default cap unless an explicit `--max-navigations N` is supplied.
- The navigation budget does not count browser subresources, automatic redirects, or requests initiated by page scripts. It is not a total HTTP request cap.
- URLs are constrained to permitted HTTPS Myket hosts and expected app routes; package identity is checked after redirects. Repeated app-detail failures stop the run.
- Live collection is never part of routine CI. The live-smoke workflow is manual-dispatch only and must not be run without checking access permission.

## Data and privacy

Raw local SQLite records may include optional developer contact fields. Keep databases and logs private unless their handling and sharing obligations have been assessed. HTML reports and CSV exports omit those contact fields. CSV output protects against spreadsheet formula injection. Demo records are fictional and labeled as such.

The site is independent and is not operated or endorsed by Myket. Never bypass authentication, CAPTCHA, rate limits, anti-bot controls, or other access restrictions. Limit requests and stop when access is refused. The code's application-navigation counter does not control the browser's subrequests.

## Exit statuses

| Exit | Meaning |
| --- | --- |
| `0` | An offline operation succeeded, or a live run saved at least one app without detail failures or budget exhaustion |
| `1` | Empty, partially failed, or budget-exhausted crawl |
| `2` | Invalid input, missing/incompatible local data, or another handled CLI error |
| `130` | Interrupted live crawl; saved data is retained |

These are local command outcomes, not evidence of complete marketplace coverage.

## Verification

Run:

```bash
python -m compileall -q src tests
python -m unittest discover -s tests -v
node --test tests/test_report_import.cjs tests/test_product_site.mjs
```

GitHub Actions also runs the Python suite on Ubuntu/Python 3.9, Windows/Python 3.12, and Ubuntu/Python 3.14. The product-site workflow tests the static publication and deploys only on pushes to `master`. Tests use synthetic data and local fixtures; they do not require Myket access.

## Known limitations

- Current Myket DOM behavior, real browser collection, and current access conditions are not established by offline tests.
- Browser redirects and subrequests are not included in the Selenium navigation counter.
- History/snapshots, scheduled collection, resumable crawling, and cross-store analysis are not shipped.
- Live collection may be incomplete because of markup changes, access restrictions, or transient failures.
