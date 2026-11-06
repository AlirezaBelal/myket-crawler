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
                    ("desktop-1920", 1920, 1080),
                    ("desktop-1440", 1440, 900),
                    ("tablet-1024", 1024, 768),
                    ("tablet-768", 768, 1024),
                    ("mobile-390", 390, 844),
                    ("mobile-375", 375, 812),
                    ("mobile-320", 320, 740),
                ):
                    page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
                    external = []
                    errors = []
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    page.on("request", lambda request: external.append(request.url) if request.url.startswith(("http:", "https:")) else None)
                    page.goto(report.resolve().as_uri(), wait_until="load")
                    page.locator("#inventory").scroll_into_view_if_needed()
                    assert page.locator("#apps tbody tr").count() == 12
                    assert page.locator("#apps tbody tr:visible").count() == 12
                    overflow = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
                    assert overflow <= 1, "horizontal overflow {}px on {}".format(overflow, label)
                    assert not external, "Report attempted external network access: {}".format(external)
                    assert not errors, "Unexpected browser JavaScript errors: {}".format(errors)
                    assert page.locator(".report-mode").is_visible(), "Demo label hidden on {}".format(label)
                    assert "ساختگی" in page.locator(".report-mode").inner_text()
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

                        import_file = Path(tmp) / "browser-import.csv"
                        import_file.write_text(
                            "package_name,name,category,sub_category,installation_count,average_score,comment_count,version,last_update,source,developer_email\n"
                            'ir.example.imported,"Imported, ""quoted""",QA,Sample,42,4.8,3,1.0,2026-10-01,MYKET,ignored@example.test\n'
                            'ir.example.unsafe,"<img src=x onerror=alert(1)>",QA,Sample,7,0,0,1.0,2026-10-02,MYKET,private@example.test\n',
                            encoding="utf-8-sig",
                        )
                        page.locator("#local-data-file").set_input_files(str(import_file))
                        page.wait_for_function("document.querySelector('#local-data-status').textContent.includes('فقط در این زبانه پردازش شد.')")
                        assert page.locator("#apps tbody tr").count() == 2
                        assert 'Imported, "quoted"' in page.locator(".app-title").all_text_contents()
                        assert page.locator("img").count() == 0, "Imported text must not become executable markup"
                        assert "private@example.test" not in page.locator("body").inner_text()
                        assert "بدون بارگذاری" in page.locator(".report-mode").inner_text()
                        page.locator("#search").fill("quoted")
                        assert page.locator("#apps tbody tr:visible").count() == 1
                        page.locator("#reset-filters").click()
                        assert page.locator("#apps tbody tr:visible").count() == 2
                        page.locator("#reset-local-data").click()
                        assert page.locator("#apps tbody tr:visible").count() == 12
                        assert "ساختگی" in page.locator(".report-mode").inner_text()
                    page.close()
            finally:
                browser.close()
    print("Visual QA PASS: seven viewports, visible demo badge, no JS errors/network/overflow, interactive filters/sort/dark mode")


if __name__ == "__main__":
    main()
