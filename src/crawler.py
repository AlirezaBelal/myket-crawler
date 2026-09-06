import time
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Set

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

import config
from html_parser import create_app_details_from_html


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
    ):
        self.db_path = Path(db_path)
        self.max_apps = max_apps
        self.category_limit = category_limit
        self.subcategory_limit = subcategory_limit
        self.stats = CrawlStats()
        self.seen_packages: Set[str] = set()
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
        driver.set_page_load_timeout(config.PAGE_LOAD_TIMEOUT)
        return driver

    def close(self) -> None:
        if self.driver:
            self.driver.quit()

    def _sleep_ms(self, milliseconds: int) -> None:
        if milliseconds > 0:
            time.sleep(milliseconds / 1000)

    def _open(self, url: str) -> None:
        self.driver.get(url)
        self._sleep_ms(config.PAGE_DELAY_MS)

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

    def _extract_app_links(self) -> List[str]:
        self._scroll_to_bottom()
        links = []
        for element in self.driver.find_elements(By.CLASS_NAME, "app-detail-link"):
            href = element.get_attribute("href")
            if href and href.startswith("http"):
                links.append(href)
        return list(dict.fromkeys(links))

    def _crawl_links(self, links: Iterable[str]) -> None:
        for url in links:
            if self._reached_limit():
                return

            package_name = url.rstrip("/").split("/")[-1].split("?")[0]
            if not package_name or package_name in self.seen_packages:
                self.stats.skipped_duplicates += 1
                continue

            self.seen_packages.add(package_name)
            self.stats.discovered += 1

            try:
                self._open(url)
                app = create_app_details_from_html(self.driver, self.driver.current_url)
                app.save_to_db(str(self.db_path))
                self.stats.saved += 1
                print(f"[saved] {app.package_name} — {app.name}")
            except Exception as exc:
                self.stats.failed += 1
                print(f"[failed] {package_name}: {exc}")
                print(traceback.format_exc())
            finally:
                self._sleep_ms(config.APP_DELAY_MS)

    def _crawl_category_page(self, category_url: str) -> None:
        self._open(category_url)
        buttons = self.driver.find_elements(By.CLASS_NAME, "btn-all-apps")

        if not buttons:
            self._crawl_links(self._extract_app_links())
            return

        button_count = self._limited_count(len(buttons), self.subcategory_limit)
        for index in range(button_count):
            if self._reached_limit():
                return

            self._open(category_url)
            buttons = self.driver.find_elements(By.CLASS_NAME, "btn-all-apps")
            if index >= len(buttons):
                continue

            try:
                self.driver.execute_script("arguments[0].click();", buttons[index])
                self._sleep_ms(config.PAGE_DELAY_MS)
                self._crawl_links(self._extract_app_links())
            except WebDriverException as exc:
                self.stats.failed += 1
                print(f"[failed] subcategory index {index}: {exc}")

    def crawl_section(self, section: str) -> None:
        base_url = self.BASE_URLS[section]
        print(f"== Crawling Myket {section} ==")
        self._open(base_url)
        categories = self.driver.find_elements(By.CLASS_NAME, "category-item")

        if not categories:
            self._crawl_category_page(base_url)
            return

        category_count = self._limited_count(len(categories), self.category_limit)
        for index in range(category_count):
            if self._reached_limit():
                return

            self._open(base_url)
            categories = self.driver.find_elements(By.CLASS_NAME, "category-item")
            if index >= len(categories):
                continue

            try:
                self.driver.execute_script("arguments[0].click();", categories[index])
                self._sleep_ms(config.PAGE_DELAY_MS)
                category_url = self.driver.current_url
                self._crawl_category_page(category_url)
            except WebDriverException as exc:
                self.stats.failed += 1
                print(f"[failed] category index {index}: {exc}")

    def crawl(self, sections: Iterable[str]) -> CrawlStats:
        for section in sections:
            if self._reached_limit():
                break
            self.crawl_section(section)
        return self.stats
