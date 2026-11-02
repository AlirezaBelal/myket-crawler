import time
import traceback
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Set
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

import config
from html_parser import create_app_details_from_html


MYKET_HOSTS = {"myket.ir", "www.myket.ir"}
MAX_CONSECUTIVE_FAILURES = 3
DEFAULT_NAVIGATION_BUDGET = 100


class NavigationBudgetExceeded(RuntimeError):
    """An extra browser navigation was blocked before it was issued."""



def _path(url: str) -> str:
    try:
        return urlparse(url).path.rstrip("/") or "/"
    except (TypeError, ValueError):
        return ""


def is_myket_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.scheme == "https" and parsed.netloc.lower() in MYKET_HOSTS
    except (TypeError, ValueError):
        return False


def is_app_url(url: str) -> bool:
    path = _path(url)
    return is_myket_url(url) and re.fullmatch(r"/app/[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)+", path) is not None


def is_collection_url(url: str) -> bool:
    path = _path(url)
    return is_myket_url(url) and path.startswith("/list/") and len(path) > len("/list/")


def is_category_url(url: str, section: str) -> bool:
    path = _path(url)
    prefix = f"/{section}/"
    return is_myket_url(url) and path.startswith(prefix) and len(path) > len(prefix)


@dataclass
class CrawlStats:
    discovered: int = 0
    saved: int = 0
    failed: int = 0
    skipped_duplicates: int = 0


class MyketCrawler:
    BASE_URLS = {
        "apps": "https://myket.ir/apps",
        "games": "https://myket.ir/games",
    }

    def __init__(
        self,
        db_path: Path,
        *,
        headless: bool = True,
        max_apps: Optional[int] = None,
        category_limit: Optional[int] = None,
        subcategory_limit: Optional[int] = None,
        max_navigations: Optional[int] = DEFAULT_NAVIGATION_BUDGET,
    ):
        if max_navigations is not None and max_navigations <= 0:
            raise ValueError("max_navigations must be greater than zero")
        self.max_navigations = max_navigations
        self.navigations = 0
        self.budget_exhausted = False
        self.db_path = Path(db_path)
        self.max_apps = max_apps
        self.category_limit = category_limit
        self.subcategory_limit = subcategory_limit
        self.stats = CrawlStats()
        self.seen_packages: Set[str] = set()
        self.consecutive_failures = 0
        self.stopped_due_to_failures = False
        self.driver = self._build_driver(headless=headless)

    @staticmethod
    def _build_driver(*, headless: bool):
        options = Options()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1440,1200")
        options.add_argument("--lang=fa-IR")
        driver = webdriver.Chrome(options=options)
        try:
            driver.set_page_load_timeout(config.PAGE_LOAD_TIMEOUT)
        except BaseException:
            try:
                driver.quit()
            except Exception:
                pass
            raise
        return driver

    def close(self) -> None:
        if self.driver:
            self.driver.quit()

    def _sleep_ms(self, milliseconds: int) -> None:
        if milliseconds > 0:
            time.sleep(milliseconds / 1000)

    def _open(self, url: str) -> None:
        if not is_myket_url(url):
            raise ValueError("Navigation requires an allowed HTTPS Myket URL")
        if self.max_navigations is not None and self.navigations >= self.max_navigations:
            self.budget_exhausted = True
            raise NavigationBudgetExceeded(
                f"Navigation budget reached ({self.max_navigations}); no further pages opened"
            )
        # Count attempted driver.get() calls, including navigation failures.
        # Selenium subresources and HTTP redirects are not counted here.
        self.navigations += 1
        self.driver.get(url)
        self._sleep_ms(config.PAGE_DELAY_MS)
        if not is_myket_url(self.driver.current_url):
            raise ValueError("Navigation left an allowed Myket URL")

    def _scroll_to_bottom(self) -> None:
        previous_height = 0
        for _ in range(6):
            height = self.driver.execute_script("return document.body.scrollHeight")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
            self._sleep_ms(250)
            if height == previous_height:
                break
            previous_height = height

    @staticmethod
    def _limited_count(total: int, limit: Optional[int]) -> int:
        return min(total, limit) if limit is not None else total

    def _reached_limit(self) -> bool:
        return self.max_apps is not None and self.stats.saved >= self.max_apps

    def _should_stop(self) -> bool:
        return self.stopped_due_to_failures or self._reached_limit()

    def _extract_links(self, predicate: Callable[[str], bool]) -> List[str]:
        self._scroll_to_bottom()
        links: List[str] = []
        for element in self.driver.find_elements(By.CSS_SELECTOR, "a[href]"):
            href = (element.get_attribute("href") or "").strip()
            if href and predicate(href):
                links.append(href.split("#", 1)[0])
        return list(dict.fromkeys(links))

    def _extract_app_links(self) -> List[str]:
        return self._extract_links(is_app_url)

    def _extract_collection_links(self) -> List[str]:
        return self._extract_links(is_collection_url)

    def _extract_category_links(self, section: str) -> List[str]:
        return self._extract_links(lambda url: is_category_url(url, section))

    @staticmethod
    def _validate_app(app) -> None:
        if not app.package_name:
            raise ValueError("Myket detail page did not expose a package name")
        if not app.name:
            raise ValueError(f"Myket detail page for {app.package_name} did not expose a name")
        if not any(
            [
                app.version,
                app.category,
                app.installation_count,
                app.comment_count,
                app.last_update,
            ]
        ):
            raise ValueError(
                f"Myket detail metadata was empty for {app.package_name}; DOM may have changed"
            )

    def _crawl_links(self, links: Iterable[str]) -> None:
        for url in links:
            if self._should_stop():
                return

            package_name = _path(url).split("/")[-1]
            if not package_name or package_name in self.seen_packages:
                self.stats.skipped_duplicates += 1
                continue

            self.seen_packages.add(package_name)
            self.stats.discovered += 1

            try:
                self._open(url)
                # Redirects and unexpected page contents must not be recorded as
                # the package originally discovered on the trusted Myket page.
                final_url = self.driver.current_url
                if not is_app_url(final_url):
                    raise ValueError("App navigation left an allowed Myket app URL")
                final_package = _path(final_url).split("/")[-1]
                if final_package != package_name:
                    raise ValueError("App navigation redirected to a different package")
                app = create_app_details_from_html(self.driver, final_url)
                self._validate_app(app)
                if app.package_name != package_name:
                    raise ValueError("Parsed package does not match the requested app")
                app.save_to_db(str(self.db_path))
                self.stats.saved += 1
                self.consecutive_failures = 0
                print(f"[saved] {app.package_name} — {app.name}")
            except NavigationBudgetExceeded:
                raise
            except Exception as exc:
                self.stats.failed += 1
                self.consecutive_failures += 1
                if self.consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    self.stopped_due_to_failures = True
                print(f"[failed] {package_name}: {exc}")
                print(traceback.format_exc())
                if self.stopped_due_to_failures:
                    print(
                        f"[stopped] {MAX_CONSECUTIVE_FAILURES} consecutive app failures; "
                        "stopping further requests."
                    )
            finally:
                self._sleep_ms(config.APP_DELAY_MS)

    def crawl_app_url(self, url: str) -> CrawlStats:
        if not is_app_url(url):
            raise ValueError(f"Not a Myket app URL: {url}")
        try:
            self._crawl_links([url])
        except NavigationBudgetExceeded:
            pass
        return self.stats

    def _crawl_category_page(self, category_url: str, *, already_open: bool = False) -> None:
        if not already_open:
            self._open(category_url)
        app_links = self._extract_app_links()
        collection_links = self._extract_collection_links()

        self._crawl_links(app_links)
        if self._should_stop():
            return

        collection_count = self._limited_count(
            len(collection_links), self.subcategory_limit
        )
        for collection_url in collection_links[:collection_count]:
            if self._should_stop():
                return
            self._open(collection_url)
            self._crawl_links(self._extract_app_links())

    def crawl_section(self, section: str) -> None:
        base_url = self.BASE_URLS[section]
        print(f"== Crawling Myket {section} ==")
        self._open(base_url)
        categories = self._extract_category_links(section)

        if not categories:
            self._crawl_category_page(base_url, already_open=True)
            return

        category_count = self._limited_count(len(categories), self.category_limit)
        for category_url in categories[:category_count]:
            if self._should_stop():
                return
            self._crawl_category_page(category_url)

    def crawl(self, sections: Iterable[str]) -> CrawlStats:
        try:
            for section in sections:
                if self._should_stop():
                    break
                self.crawl_section(section)
        except NavigationBudgetExceeded:
            print(f"[stopped] Browser navigation budget exhausted after {self.navigations} pages.")
        return self.stats
