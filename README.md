# myket-crawler

A product-ready Python crawler that collects public app metadata from Myket and stores the results in a local SQLite database.

The project is intentionally aligned with [`cafebazaar-crawler`](https://github.com/AlirezaBelal/cafebazaar-crawler), including a compatible `app_details` schema. That makes the two crawlers useful as a pair for Iranian Android market research and cross-store analysis.

## What it does

- Crawls both Myket **apps** and **games**
- Walks category and "all apps" listing pages
- Collects unique app detail URLs
- Extracts app, developer, install, rating, category, description, price, version, and update metadata
- Stores one row per `package_name + source` in SQLite
- Updates existing rows instead of creating duplicates
- Runs headless by default
- Uses Selenium Manager, so no hardcoded ChromeDriver path is required
- Supports small controlled smoke tests with CLI limits
- Preserves data already written when interrupted
- Prints a crawl summary when finished

## Requirements

- Python 3.9+
- Google Chrome / Chromium
- `selenium`
- `jdatetime`
- SQLite (included with Python)

## Quick start

```bash
git clone https://github.com/AlirezaBelal/myket-crawler.git
cd myket-crawler
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python src/main.py --max-apps 20
```

macOS / Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
python src/main.py --max-apps 20
```

`--max-apps 20` is the recommended first run. Remove the option for a larger crawl.

## Usage

Crawl apps and games:

```bash
python src/main.py
```

Crawl only apps:

```bash
python src/main.py --section apps
```

Small controlled run:

```bash
python src/main.py \
  --section apps \
  --category-limit 1 \
  --subcategory-limit 1 \
  --max-apps 20
```

Write to a custom database:

```bash
python src/main.py --max-apps 20 --db data/test.db
```

Show Chrome while crawling:

```bash
python src/main.py --max-apps 20 --headful
```

Show all CLI options:

```bash
python src/main.py --help
```

## Output

By default, data is stored at:

```text
data/myket_results.db
```

The `app_details` table uses `(package_name, source)` as its primary key. Re-crawling an app refreshes its row instead of duplicating it.

The schema is designed to stay compatible with `cafebazaar-crawler`, so downstream analysis can combine both stores with minimal transformation.

## Database fields

The table includes:

`name`, `package_name`, developer contact fields, `homepage_url`, install count, average score, review counts, star distribution, category/subcategory, update timestamp, tags, price, source, descriptions, and version.

## Configuration

Environment variables:

| Variable | Default | Purpose |
| --- | ---: | --- |
| `MYKET_PAGE_DELAY_MS` | `1200` | Delay after page navigation |
| `MYKET_APP_DELAY_MS` | `250` | Delay between app detail pages |
| `MYKET_PAGE_LOAD_TIMEOUT` | `30` | Selenium page-load timeout in seconds |
| `MYKET_DATA_DIR` | `./data` | Default data directory |
| `MYKET_DB_PATH` | `./data/myket_results.db` | Exact SQLite output path |

Defaults are intentionally conservative. Increase delays if Myket responds slowly or if you are running larger crawls.

## Tests

Run local unit tests:

```bash
python -m unittest discover -s tests -v
```

GitHub Actions runs the same test suite on pushes and pull requests.

The unit tests intentionally avoid live Myket traffic. They cover deterministic parsing and database behavior; a real crawl is the end-to-end smoke test.

## Operational notes

- The crawler depends on Myket's public web pages and CSS/DOM structure, which can change over time.
- Selenium Manager resolves a compatible driver automatically when supported by the local Selenium/Chrome setup.
- Individual page failures are logged and the crawl continues where possible.
- `Ctrl+C` stops the crawl without removing rows already saved to SQLite.
- Database files, logs, virtual environments, and local environment files are excluded from Git.

## Product direction

This repository is most valuable as one collector in a broader **Iranian app-market intelligence pipeline**. Paired with `cafebazaar-crawler`, the shared schema can support:

- cross-store app availability and metadata comparison
- install/rating/category benchmarking
- developer portfolio discovery
- update-frequency monitoring
- historical snapshots and trend analysis

See [ROADMAP.md](ROADMAP.md) for the next product-oriented milestones.

## Responsible use

Use this project in accordance with Myket's terms, applicable laws, robots/access policies, and reasonable request rates. Crawl only public information you are permitted to collect.

This project is not affiliated with or endorsed by Myket.

## License

MIT — see [LICENSE](LICENSE).
