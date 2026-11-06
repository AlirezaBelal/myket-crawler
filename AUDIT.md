# Repository and product review

## Historical source audit

The earlier source-level audit dated 2026-11-02 is preserved below as historical evidence. It reviewed the local crawler, SQLite/output safety, navigation boundaries, and deterministic tests. It did not verify live Myket access. Its findings remain relevant to crawler maintenance; it predates the product-site migration described here.

## Product-site migration review — 2026-11-06

### Findings

- The previous Pages workflow published a synthetic marketplace report as the repository's front page, which positioned the project like an online analytics product.
- README language and links described the hosted dashboard and its browser CSV/JSON importer as the main user experience, despite the actual product being a local Python/Selenium crawler.
- The roadmap called the dataset, rather than the crawler, the product and described live smoke scheduling more broadly than the manual-only workflow.
- The public site could be presented as static installation guidance without changing the Python collection, SQLite, local report, or CSV export behavior.
- The existing Skills lock pins `design` and `web-ui-audit` to `yikZero/skills` ref `5e85045d96662605f33e12150cdc6d00cb04dc0a`; those revisions were used for this review.

### Changes in this release

- Replaced the Pages dashboard artifact with a self-contained static product site. The old browser import remains available only in locally generated reports; it is not published as the product website.
- Added local original SVG branding and an explicitly labeled architecture illustration; no live-data screenshot or fabricated operating metric is shown.
- Reframed README and roadmap around local install, offline demo, bounded collection, SQLite, privacy boundaries, and the existing Persian quickstart.
- Added deterministic Node checks for site identity, installation instructions, links, local assets, CSP, and responsive/focus styles. No runtime dependencies were added.
- Updated only the Myket landing-page metadata and shared presentation logic in the separately scoped private portfolio change. Other portfolio routes and product repositories remain out of scope.

### Verification limits

CI is the source of truth for the merge-time Python platform matrix and Pages build/deploy. Browser QA is run against the static local site at the required widths. No Myket request, live crawl, real user dataset, developer contact, credential, or external integration is used by site tests.

The static site does not prove that the live crawler still matches Myket's current DOM or terms. That requires separate verification in an authorized environment and is not part of an offline website release.
