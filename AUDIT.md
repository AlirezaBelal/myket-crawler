# Independent production-readiness audit — 2026-11-02

Audited master `941a42534653b1c9f9176c6f8b74e7ae7011983a`, all tracked source,
assets, tests, launch script, requirements, README, ROADMAP, and workflows.
Reviewed recent history through the initial implementation, especially merged
PR #6 (its diff, metadata, tests and circuit-breaker semantics), and #3–#5.
No Myket requests, browser-driven live crawl, access-control bypass, or actual
dataset changes were performed. All database tests use temporary synthetic data.

## Confirmed findings and focused changes

| Severity | Reproduction on audited master | Impact and fix |
| --- | --- | --- |
| P1 | Export HTML or CSV to `<input.db>-wal`, `-shm`, or `-journal`. The atomic-output guard only compares the main SQLite path. | SQLite recovery paths can be replaced on filesystems permitting rename of open files; committed WAL data/recovery can be lost. Reject reserved recovery names and aliases before creating output. Windows denied replacement of an active WAL in the base reproduction, so actual committed-row loss was not demonstrated on this host. The missing guard is reproducible for unused recovery names; a temporary active WAL regression checks bytes and committed rows remain intact. |
| P2 | Mock a section/category/collection navigation redirect to an external login page containing Myket links. Discovery still extracts/follows links, and a section crawl proceeds to later sections. | Continues discovery after leaving the trusted origin, allowing unintended requests. Validate requested and final hosts centrally in `_open`; raise before extracting links. Selenium itself follows the initial redirect before this check. |
| P2 | Parse `https://myket.ir/app/ir.example.app?ref=/campaign/other` or a fragment URL. Also classify `/app/ir.example.app/reviews`. | Parser returns `other` or a fragment-bearing identity; valid app links fail package validation, and nested routes pass discovery as app identities. Parse the URL path structurally and accept only a package detail path, with optional trailing slash/query/fragment. |
| P2 | Complete a crawl with `saved=2, failed=1`, without opening PR #6's consecutive-failure circuit. | Exit status is 0 despite missing records. Return nonzero for any recorded detail failure, preserving the printed counts and saved rows. |

No P0 issue was confirmed. The dedicated regression module is
`tests/test_production_audit.py`. Against the original source, discovery subtests,
package parsing, and partial CLI status fail; the active WAL test encounters an OS
permission error rather than an application guard. With the fixes, all tests pass.

## Other audit results

- Lifecycle: PR #6 cleans up timeout-configuration failure and CLI uses `finally`
  for normal crawl/interruption cleanup. Its three-consecutive-detail-failure
  stop and success-reset behavior remain covered. Quit errors can still mask an
  earlier exception; no extra lifecycle refactor was introduced.
- Navigation/discovery: HTTPS exact-host checks, detail redirect package checks,
  deduplication, category/collection limits and six-iteration scroll bound remain.
  `--max-apps` limits saved records, not requests; `--full` explicitly allows large
  collection. No application retry loop exists, so there is no retry storm to fix.
  Backoff, a global navigation budget and resume remain future work. Browser
  resources and automatic redirects are outside the application navigation count.
- Parsing/persistence: required-detail validation, parameterized SQLite writes,
  rollback on write failure and package/source replacement remain. Optional
  selectors/star extraction can yield missing/zero values; live DOM correctness
  and full metadata completeness are not established by fake-driver tests.
- Offline reporting: read-only input, atomic exports, HTML escaping, CSP,
  formula-safe CSV and omission of developer contact columns remain covered.
  Persian RTL assets, synthetic labels, safe default CLI and SQLite schema are
  unchanged. Raw databases still contain optional contacts. Arbitrary exception
  messages are printed by the existing crawler; operator logs should stay local.
- CI: PR tests are offline. The manual live workflow was not dispatched.
  ROADMAP's weekly-or-manual checkbox describes history; the current workflow
  permits live smoke only through deliberate manual dispatch.

## Validation evidence

On Windows with Python 3.12.14 in an isolated virtual environment:

- `python -m compileall -q src tests` — passed.
- `python -m unittest discover -s tests -v` — **36 tests passed**.
- Python 3.9 AST grammar parsing — all 17 Python source/test files passed.
- `git diff --check` — passed.
- New offline regressions cover all three discovery entry paths, malformed and
  decorated package URLs, partial CLI status, both export formats and all three
  reserved recovery paths, plus committed rows in a temporary active WAL.
- Existing offline demo/HTML/CSV/UI acceptance tests ran in the complete suite.

Not executed successfully: Playwright visual assertions/screenshots. The first
sandboxed launch stalled and was stopped; an unsandboxed attempt reported the
missing Chromium executable. Installing Chromium failed with provider HTTP 403
(location restriction); no bypass was attempted. UI assets were not changed.
Not executed: Python 3.9/3.14 runtime suites (only 3.12 is available here), Linux
runtime/rename behavior, real Chrome/Selenium lifecycle integration, and
`tests/live_smoke.py --yes-live` or any Myket network test. The existing PR CI
matrix can supply additional OS/version evidence; this audit does not claim it
has passed before results are available.

Remaining limitations: final-host checks cannot prevent the browser's initial
redirect request; same-host access barriers require live/fixture contract work;
large successful or intermittently failing crawls have no global request cap;
no retry/backoff is added to avoid increasing traffic without a defined policy.
Concurrent filesystem alias changes during export are not fully race-proof.
Python 3.9 grammar validation is not a substitute for its runtime CI.
