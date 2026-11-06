# Myket Crawler

**A lightweight, local-first tool for exploring public Myket Android app metadata.**

Collect permitted public listings with Selenium, save them to SQLite, inspect them in a modern **standalone Persian RTL dashboard**, or export CSV for analysis. This is an independent research tool, not an official Myket product.

The app is designed to complement [CafeBazaar Crawler](https://github.com/AlirezaBelal/cafebazaar-crawler); both use the same `app_details` SQLite schema.

**Product guides:** [راهنمای سریع فارسی](QUICKSTART.fa.md) · [Delivery status and supported scope](PRODUCT.md) · [Roadmap](ROADMAP.md).

## Start with an offline demo — no installation beyond Python

Requires **Python 3.9+**.

**Windows:** Double-click `scripts/desktop-demo.cmd` to generate fictional records and open your report in a browser.

**Windows, macOS, Linux:**

```bash
python src/main.py --demo
```

Open `data/demo-report.html`. This produces **12 clearly fictional sample apps** and does not launch Selenium, open Myket or make any network request. If `data/demo.db` exists, choose a different path with `--db data/demo-2.db`. Existing databases are never overwritten by the demo.

The Persian-first dashboard supports search, category filters, sorting by installs or rating, responsive mobile cards, visible demo-data badges at mobile sizes, accessible controls and light/dark mode. Exports are written atomically and cannot overwrite the source SQLite file or its recovery files. CSS and JavaScript are embedded into one local HTML file; no hosting, analytics, fonts, servers or CDNs are required.

## Work with an existing SQLite dataset (offline)

```bash
python src/main.py --report data/myket-report.html
python src/main.py --export-csv data/myket-apps.csv

# Your own database:
python src/main.py --db data/my-run.db --report data/my-run-report.html
```

The report displays up to 500 rows by default (`--report-limit` may be 1–1000). CSV exports selected metadata for all rows, using UTF-8 with a BOM and protection against spreadsheet formula injection. **Developer phone and email are never included in the dashboard or CSV.** Do not distribute raw databases without assessing personal-data obligations.

## Analyze an authorized local export in the browser

The hosted and generated reports accept CSV or JSON files using this project's `app_details` fields. Files are read with browser APIs and processed in the current tab only; nothing is uploaded, stored in browser storage, or sent to a marketplace. The importer is capped at 5 MiB and 5,000 rows, ignores unrecognized columns (including developer contact fields), and validates identifiers and numeric values. Search, category filtering, sorting, and summary visualizations update for the selected file. Use **Reset to report** to discard the in-memory view.

SQLite files are not parsed in the browser. Generate a CSV locally with `python src/main.py --db data/my-run.db --export-csv data/apps.csv`, then select that CSV. JSON is accepted as an array of rows or an object with an `app_details` or `records` array. The bundled Pages report remains fictional sample data until a file is explicitly selected.

## Run a small, permitted live crawl

Only crawl public data that you are authorized to access. Respect Myket's terms, robots/access rules, login barriers and sensible request rates. Do not bypass restrictions.

**Live requirements:** Python 3.9+, Chrome/Chromium, Selenium and jdatetime. Selenium Manager finds ChromeDriver on most supported systems.

```bash
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# macOS / Linux: source .venv/bin/activate
python -m pip install -r requirements.txt

python src/main.py --section apps --category-limit 1 --subcategory-limit 1 --max-apps 3 --max-navigations 20
```

Your local database defaults to `data/myket_results.db`. The app scans Myket's public app and game listings, collects unique packages and saves metadata to SQLite. Captured fields include install counts, category, version, rating, update date, descriptions, and optional developer contacts **in the local raw database only**.

An unqualified `python src/main.py` intentionally does **not** crawl anything. A bounded run has a **default safety budget of 100 Selenium page navigations**, shared across discovery, category, collection, and detail pages. Use `--max-navigations N` (positive integer) to lower or raise it. `--max-apps` limits successful saves, not page navigations. The crawler stops *before* issuing the first navigation beyond the budget, preserves saved records, and exits nonzero when stopped early. The result summary reports attempted `navigations`, including failed browser loads.

**Scope of the budget:** it counts calls to Selenium `driver.get()`, **not** individual HTTP subresource requests, automatic redirects, or loads initiated by the page itself. Browser access permissions and conservative delays still matter. Use `--full` only after confirming large collection is permitted: without `--max-navigations`, it deliberately disables the default navigation cap. Even with `--full`, you can supply `--max-navigations N`. No network request or browser startup occurs in default, demo, report or CSV modes.

Use `--headful` to see Chrome or `--db data/custom.db` to select your output file. Numeric crawl limits must be strictly positive when present. Exit status is `0` for a completed crawl that saves at least one app with no recorded detail failures, `1` for empty/partial/budget-stopped runs, `2` for CLI/input errors and `130` for interruption. A successful CLI exit is not evidence of complete Myket catalogue coverage.

### Opt-in live smoke

```bash
python tests/live_smoke.py --yes-live
```

The live test uses a temporary SQLite database and attempts a bounded public-app crawl; it needs network access and Chrome. It is never run for PRs. The live contract check is available only through explicit manual workflow dispatch (not weekly or on PRs); do not run it until the source's permissions and access terms are verified. A successful live check is only evidence for the tested flow, not proof of unlimited crawling reliability. The crawler stops after **three consecutive app-detail failures** to avoid repeatedly requesting broken pages. Any recorded detail failure makes the crawl exit nonzero, including partial runs below the circuit-breaker threshold, and preserves previously saved records. Discovery stops if navigation leaves the allowed HTTPS Myket hosts.

## Tests and project layout

```bash
python -m compileall -q src tests
python -m unittest discover -s tests -v
```

Offline deterministic tests run in GitHub Actions across supported Python versions, plus browser visual QA for responsive report changes. To run the visual smoke locally, first install Playwright and its browser:

```bash
python -m pip install playwright
python -m playwright install chromium
python tests/visual_qa.py
```

The visual test checks mobile and desktop layout, local-only loading, search, category filtering, sorting and dark mode. Screenshots are saved to ignored local artifacts.

```text
src/main.py                Safe offline-first command-line interface
src/crawler.py             Selenium network adapter
src/html_parser.py         Myket HTML metadata parser
src/models/AppDetails.py   Compatible local SQLite persistence
src/local_report.py        Offline demo, HTML report and CSV
src/report_template.html   Semantic RTL report template
src/report_style.css       Responsive light/dark visual system
src/report_interactions.js Local interactive filters and theme
scripts/desktop-demo.cmd   Double-click offline Windows demo
tests/                     Offline tests, visual QA and opt-in live smoke
data/                      Ignored local databases and reports
```

Environment variables include `MYKET_PAGE_DELAY_MS` (default 1200), `MYKET_APP_DELAY_MS` (250), `MYKET_PAGE_LOAD_TIMEOUT` (30 seconds), `MYKET_DATA_DIR` and `MYKET_DB_PATH`. Keep request intervals conservative and increase them if necessary.

## Status, privacy and licensing

- Offline demo and reports do not require an Internet connection.
- Live extraction is best-effort and sensitive to Myket's markup, access conditions and service availability.
- All user datasets, databases, HTML reports, logs and virtual environments must remain outside version control.
- No login credentials, personal datasets or API bypass methods are included.
- Do not misrepresent fictional sample records as live Myket data.
- [Roadmap](ROADMAP.md): history, incremental collection and cross-store analysis are potential later phases, not shipped functionality.

Licensed under [MIT](LICENSE).

## Live browser demo

[Open the GitHub Pages demo](https://alirezabelal.github.io/myket-crawler/)

The browser demo is an offline report built from fictional app listings. It supports search, category filters, sorting, details, visual summaries, and light/dark mode; it does not launch Selenium or fetch Myket.
