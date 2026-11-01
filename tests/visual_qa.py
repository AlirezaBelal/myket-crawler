"""Optional real-browser visual/interaction smoke for the offline HTML report.

Requires: pip install playwright && python -m playwright install chromium.
No CafeBazaar requests are made.
"""
from pathlib import Path
import subprocess
import sys
import tempfile

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "visual-qa"


def main():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="myket-visual-") as tmp:
        database = Path(tmp) / "example.db"
        subprocess.run(
            [sys.executable, str(ROOT / "src" / "main.py"),
             "--demo", "--db", str(database)],
            check=True, cwd=ROOT,
        )
        report = database.with_name("example-report.html")
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                for label, width, height in (
                    ("desktop-1440", 1440, 900),
                    ("tablet-768", 768, 1024),
                    ("mobile-390", 390, 844),
                    ("mobile-320", 320, 740),
                ):
                    page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
                    external = []
                    page.on("request", lambda request: external.append(request.url) if request.url.startswith(("http:", "https:")) else None)
                    page.goto(report.resolve().as_uri(), wait_until="load")
                    page.locator("#inventory").scroll_into_view_if_needed()
                    assert page.locator("#apps tbody tr").count() == 12
                    assert page.locator("#apps tbody tr:visible").count() == 12
                    overflow = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
                    assert overflow <= 1, "horizontal overflow {}px on {}".format(overflow, label)
                    assert not external, "Report attempted external network access: {}".format(external)
                    page.screenshot(path=str(ARTIFACTS / (label + ".png")), full_page=True)
                    if label == "desktop-1440":
                        page.locator("#search").fill("یادداشت")
                        assert page.locator("#apps tbody tr:visible").count() == 1
                        page.locator("#search").fill("nonexistent-app-zz")
                        assert page.locator("#empty").is_visible()
                        page.locator("#empty-reset").click()
                        assert page.locator("#apps tbody tr:visible").count() == 12
                        page.locator("#category-filter").select_option(label="آموزش")
                        assert page.locator("#apps tbody tr:visible").count() == 2
                        page.locator("#reset-filters").click()
                        assert page.locator("#apps tbody tr:visible").count() == 12
                        page.locator("#sort-order").select_option("installs")
                        assert page.locator("#apps tbody tr:visible").first.get_attribute("data-installs") == "335000"
                        page.locator("#theme-toggle").click()
                        assert page.locator("html").get_attribute("data-theme") == "dark"
                        assert page.locator("#theme-toggle").get_attribute("aria-pressed") == "true"
                        page.screenshot(path=str(ARTIFACTS / "desktop-dark.png"), full_page=True)
                    page.close()
            finally:
                browser.close()
    print("Visual QA PASS: four viewports, no overflow/network, interactive filters/sort/dark mode")


if __name__ == "__main__":
    main()
