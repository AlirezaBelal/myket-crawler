# Myket Crawler

**A local Python and Selenium tool for collecting permitted public Myket app metadata into SQLite.**

[Product website](https://alirezabelal.github.io/myket-crawler/) · [Source repository](https://github.com/AlirezaBelal/myket-crawler) · [Portfolio overview](https://alirezabelal.github.io/work/lab/myket-crawler/) · [راهنمای سریع فارسی](QUICKSTART.fa.md)

Myket Crawler runs on your computer. It is an independent project, not an official Myket service. The hosted product website documents the software; it does not run a crawler, accept datasets, or connect to the marketplace.

## Try it offline

Requires Python 3.9 or newer. The demo creates 12 fictional app records in a local SQLite database and a Persian right-to-left report. It does not launch Selenium or make a network request.

```bash
git clone https://github.com/AlirezaBelal/myket-crawler.git
cd myket-crawler
```

Create an environment and install dependencies:

**Windows PowerShell**

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe src\main.py --demo
```

**macOS or Linux**

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python src/main.py --demo
```

Open `data/demo-report.html`. To use a different output path on a later demo run, provide a new database path, such as `--db data/demo-2.db`. The demo will not overwrite an existing default database.

## Run a small permitted collection

Live collection requires Chrome or Chromium. Selenium Manager can find a compatible browser driver on supported systems. Before collecting anything, verify that your intended access and use comply with Myket's current terms and access rules.

**Windows PowerShell**

```powershell
.venv\Scripts\python.exe src\main.py --section apps --category-limit 1 --subcategory-limit 1 --max-apps 3 --max-navigations 20
```

**macOS or Linux** (with the virtual environment activated)

```bash
python src/main.py --section apps --category-limit 1 --subcategory-limit 1 --max-apps 3 --max-navigations 20
```

This requests at most three successful saves and permits at most 20 Selenium `driver.get()` navigations across discovery, category, collection, and detail pages. It is not a total HTTP request cap: browser subresources, redirects, and page-initiated requests are outside that counter. The ordinary bounded-run default is 100 navigations; do not use `--full` without permission and independent rate controls. Running without arguments never starts a crawl.

The default database is `data/myket_results.db`. A partial or budget-stopped run exits nonzero while preserving saved rows. A successful exit does not establish complete catalogue coverage.

## Local outputs

Generate an offline report or a spreadsheet-safe CSV from a database you control:

```bash
python src/main.py --db data/my-run.db --report data/my-report.html
python src/main.py --db data/my-run.db --export-csv data/my-apps.csv
```

Reports are standalone Persian RTL HTML with search, category filtering, sorting, and theme controls. Exports are written atomically and omit developer phone and email fields. Raw SQLite data may contain optional developer contacts; keep it private and assess obligations before sharing. The hosted product website is documentation, not an online analytics tool.

## Supported behavior

- Selenium browser navigation for public app or game listings, when deliberately invoked.
- Category, subcategory, app-count, and navigation limits.
- Package validation, duplicate handling, failure-aware stopping, and SQLite persistence.
- Offline synthetic demo, local HTML report, and CSV export.
- Python 3.9+ support, with deterministic tests on Ubuntu and Windows in GitHub Actions.

Myket markup and access conditions can change. The collector is best-effort and does not promise exhaustive coverage. Never bypass authentication, CAPTCHA, rate limits, or anti-bot controls.

## Documentation and development

- [Product scope, safety contract, and known limitations](PRODUCT.md)
- [Persian quickstart](QUICKSTART.fa.md)
- [Product roadmap](ROADMAP.md)
- [MIT license](LICENSE)

Run the offline checks:

```bash
python -m compileall -q src tests
python -m unittest discover -s tests -v
node --test tests/test_report_import.cjs tests/test_product_site.mjs
```

The optional live smoke test is not run by CI and requires an explicit local decision: `python tests/live_smoke.py --yes-live`. Do not run it until access permission has been checked.

## Project layout

```text
src/                  Python CLI, Selenium adapter, parser, SQLite, local reports
tests/                Offline regression, importer, product-site and visual checks
site/                 Static product website published through GitHub Pages
scripts/              Local launch helpers
data/                 Ignored local databases and generated reports
```

The Pages site uses only local static assets and browser navigation to public documentation links. It adds no telemetry, analytics, runtime package, or backend.

Licensed under [MIT](LICENSE).
