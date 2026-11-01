# myket-crawler

A Python crawler for collecting public Myket app metadata into a local SQLite database. Live extraction depends on Myket's evolving pages and requires periodic validation.

The project is intentionally aligned with [`cafebazaar-crawler`](https://github.com/AlirezaBelal/cafebazaar-crawler), including a compatible `app_details` schema. That makes the two crawlers useful as a pair for Iranian Android market research and cross-store analysis.

## What it does

- Crawls both Myket **apps** and **games**
- Discovers category pages from stable `/apps/<category>` and `/games/<category>` URL patterns
- Discovers collection pages from `/list/...` URLs and app details from `/app/<package>` URLs
- Avoids relying on presentation-only CSS classes for listing discovery
- Collects unique app detail URLs
- Extracts app, developer, install, rating, category, description, price, version, and update metadata
- Validates core detail metadata and requires the expected package identity after navigation before writing a row
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

`--max-apps 20` is the recommended first run. Remove the option for a larger crawl. Limit options (`--max-apps`, `--category-limit`, and `--subcategory-limit`) must be positive integers when supplied.

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

Run deterministic local unit tests:

```bash
python -m unittest discover -s tests -v
```

Run the small live end-to-end smoke crawl:

```bash
python tests/live_smoke.py
```

The live smoke validates a known public Myket app, then discovers and persists additional apps through the normal category flow. It is deliberately bounded to three saved apps.

GitHub Actions runs offline unit tests on Python 3.9–3.12 for pull requests and pushes to `master`. The bounded live smoke can be started manually (`workflow_dispatch`) and runs weekly to detect upstream changes; **opening or updating a pull request does not launch a live Myket crawl**. The live smoke contacts a third-party website, so run it manually only when appropriate.

## Operational notes

- Listing discovery relies on Myket's public URL contracts (`/apps/`, `/games/`, `/list/`, `/app/`) rather than historical CSS class names.
- Detail extraction still depends on semantic labels and parts of Myket's detail-page DOM, so the scheduled live smoke acts as an upstream contract check.
- Selenium Manager resolves a compatible driver automatically when supported by the local Selenium/Chrome setup.
- The crawler only accepts HTTPS links on `myket.ir`/`www.myket.ir`; off-domain redirects and unexpected package changes are rejected before writing SQLite data.
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
