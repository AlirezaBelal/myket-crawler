# Myket Crawler

**A lightweight, local-first tool for exploring public Myket Android app metadata.**

Collect permitted public listings with Selenium, save them to SQLite, inspect them in a modern **standalone Persian RTL dashboard**, or export CSV for analysis. This is an independent research tool, not an official Myket product.

The app is designed to complement [CafeBazaar Crawler](https://github.com/AlirezaBelal/cafebazaar-crawler); both use the same `app_details` SQLite schema.

## Start with an offline demo — no installation beyond Python

Requires **Python 3.9+**.

**Windows:** Double-click `scripts/desktop-demo.cmd` to generate fictional records and open your report in a browser.

**Windows, macOS, Linux:**

```bash
python src/main.py --demo
```

Open `data/demo-report.html`. This produces **12 clearly fictional sample apps** and does not launch Selenium, open Myket or make any network request. If `data/demo.db` exists, choose a different path with `--db data/demo-2.db`. Existing databases are never overwritten by the demo.

The Persian-first dashboard supports search, category filters, sorting by installs or rating, responsive mobile cards, accessible controls and light/dark mode. CSS and JavaScript are embedded into one local HTML file; no hosting, analytics, fonts, servers or CDNs are required.

## Work with an existing SQLite dataset (offline)

```bash
python src/main.py --report data/myket-report.html
python src/main.py --export-csv data/myket-apps.csv

# Your own database:
python src/main.py --db data/my-run.db --report data/my-run-report.html
```

The report displays up to 500 rows by default (`--report-limit` may be 1–1000). CSV exports selected metadata for all rows, using UTF-8 with a BOM and protection against spreadsheet formula injection. **Developer phone and email are never included in the dashboard or CSV.** Do not distribute raw databases without assessing personal-data obligations.

## Run a small, permitted live crawl

Only crawl public data that you are authorized to access. Respect Myket's terms, robots/access rules, login barriers and sensible request rates. Do not bypass restrictions.

**Live requirements:** Python 3.9+, Chrome/Chromium, Selenium and jdatetime. Selenium Manager finds ChromeDriver on most supported systems.

```bash
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# macOS / Linux: source .venv/bin/activate
python -m pip install -r requirements.txt

python src/main.py --section apps --category-limit 1 --subcategory-limit 1 --max-apps 3
```

Your local database defaults to `data/myket_results.db`. The app scans Myket's public app and game listings, collects unique packages and saves metadata to SQLite. Captured fields include install counts, category, version, rating, update date, descriptions, and optional developer contacts **in the local raw database only**.

An unqualified `python src/main.py` intentionally does **not** crawl anything. Full, potentially unbounded collection requires `python src/main.py --full` and should not be used as your first test. Even a `--max-apps` run is not a global request budget: discovery and retries can generate additional requests.

Use `--headful` to see Chrome or `--db data/custom.db` to select your output file. Numeric crawl limits must be strictly positive when present.

### Opt-in live smoke

```bash
python tests/live_smoke.py --yes-live
```

The live test uses a temporary SQLite database and attempts a bounded public-app crawl; it needs network access and Chrome. It is never run for PRs. Existing CI schedules a weekly live contract check or it can be dispatched explicitly; those runs should be monitored because Myket's pages can change. A successful live check is only evidence for the tested flow, not proof of unlimited crawling reliability.

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
