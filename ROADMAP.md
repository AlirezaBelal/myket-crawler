# Product roadmap

`myket-crawler` should evolve from a one-off scraper into a reliable data collector that can sit beside `cafebazaar-crawler` in a repeatable app-market research workflow.

## Product goal

Create a dependable, reproducible source of public Myket app metadata with a schema compatible with CafeBazaar data.

The product is the **dataset and collection workflow**, not Selenium itself.

## Phase 1 — Reliable collector

- [x] Standalone repository structure
- [x] Headless execution without a hardcoded driver path
- [x] SQLite output with stable `package_name + source` identity
- [x] CLI controls for smoke tests and bounded runs
- [x] Unit tests for deterministic parsing and persistence
- [x] CI for every push and pull request
- [ ] Add a live smoke-test checklist against a small Myket category
- [ ] Harden selectors when Myket changes its DOM
- [ ] Add structured logging and explicit retry/backoff behavior

## Phase 2 — Historical data

- [ ] Store crawl timestamp / snapshot date
- [ ] Preserve changes instead of only replacing the latest row
- [ ] Track install-count, rating, version, price, and update changes over time
- [ ] Produce a simple change report after each crawl

## Phase 3 — Cross-store intelligence

- [ ] Define one shared schema contract with `cafebazaar-crawler`
- [ ] Match packages available on both stores
- [ ] Compare ratings, installs, categories, versions, and update recency
- [ ] Export analysis-ready CSV/Parquet datasets
- [ ] Add a small notebook or dashboard example

## Phase 4 — Operable data product

- [ ] Scheduled collection
- [ ] Crawl health metrics and failure-rate reporting
- [ ] Resume/checkpoint support for large crawls
- [ ] Configurable rate limits and retry policy
- [ ] Optional Docker image for reproducible runs
- [ ] Versioned dataset releases or an API layer

## Success metrics

Useful product-level measures:

- **coverage:** number of unique Myket packages collected
- **freshness:** age of the latest successful crawl
- **reliability:** successful detail pages / attempted detail pages
- **duplication:** duplicate package rate during collection
- **cross-store match rate:** packages that can be matched with CafeBazaar
- **change yield:** apps with meaningful metadata changes per crawl

These metrics make crawler quality visible without tying success to implementation details.
