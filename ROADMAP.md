# Product roadmap

Myket Crawler is a local Python/Selenium product. The public website is its static product and installation guide; crawler execution, persistence, and data handling stay on the user's computer. See [PRODUCT.md](PRODUCT.md) for shipped scope, tests, safety boundaries, and limitations.

## Shipped foundation

- Python CLI with a safe no-argument behavior.
- Selenium navigation constrained to expected Myket HTTPS routes, with an adjustable application-navigation budget.
- Category and app limits, duplicate handling, parser validation, and failure-aware stopping.
- SQLite persistence using the shared `app_details` schema.
- Twelve-record offline demo, Persian RTL local report, and formula-safe CSV export.
- Deterministic offline CI for supported Python versions and Windows.
- Static GitHub Pages product site with installation guidance and no online crawler or dataset processing.
- English README, maintained Persian quickstart, scope handoff, and MIT license.

## Maintenance priorities

- Revisit selectors only against authorized, reproducible fixtures when Myket changes its markup.
- Add explicit retry/backoff behavior only with a conservative, documented traffic policy.
- Keep supported platform instructions synchronized with the CI matrix.
- Continue testing export safety, SQLite persistence, navigation budgets, and clean offline paths.

## Possible future work

These are ideas, not promises or current functionality:

- Preserve crawl snapshots and report changes across separate local runs.
- Resume large permitted runs without repeating completed package work.
- Compare Myket records against a compatible local CafeBazaar dataset.
- Add structured local run summaries for diagnostics.

Any future feature must remain local-first, respect access controls, avoid collecting more data than needed, and stay out of the public demonstration unless it can be described accurately and safely.
