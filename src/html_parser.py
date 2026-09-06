import re
from datetime import datetime, timedelta, timezone
from typing import Tuple

import jdatetime
from selenium.webdriver.common.by import By

from models import AppDetails, Source


_PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
_TEHRAN_TZ = timezone(timedelta(hours=3, minutes=30))


def normalize_digits(value: str) -> str:
    return (value or "").translate(_PERSIAN_DIGITS)


def parse_integer(value: str) -> int:
    digits = re.sub(r"[^0-9]", "", normalize_digits(value))
    return int(digits) if digits else 0


def parse_installation_count(value: str) -> int:
    text = normalize_digits(value).replace(",", "").strip()
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    if not match:
        return 0

    number = float(match.group(1))
    multiplier = 1
    if "میلیارد" in text:
        multiplier = 1_000_000_000
    elif "میلیون" in text:
        multiplier = 1_000_000
    elif "هزار" in text:
        multiplier = 1_000

    return int(number * multiplier)


def parse_price(value: str) -> int:
    text = normalize_digits(value).strip()
    if not text or "رایگان" in text:
        return 0
    return parse_integer(text)


def parse_last_update_to_epoch(value: str) -> int:
    text = normalize_digits(value).strip()
    match = re.search(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})", text)
    if not match:
        return 0

    try:
        year, month, day = map(int, match.groups())
        gregorian = jdatetime.date(year, month, day).togregorian()
        dt = datetime(gregorian.year, gregorian.month, gregorian.day, tzinfo=_TEHRAN_TZ)
        return int(dt.timestamp())
    except (TypeError, ValueError):
        return 0


def parse_star_ratings(driver, total_comments: int) -> Tuple[int, int, int, int, int]:
    counts = [0, 0, 0, 0, 0]
    try:
        elements = driver.find_elements(
            By.XPATH,
            "//div[contains(@class,'ratingSec')]//div[contains(@class,'rateItem')]",
        )
        for element in elements:
            label = element.find_element(
                By.XPATH, ".//div[contains(@class,'ratesLabel')]//div"
            ).text
            star_value = parse_integer(label)
            style = element.find_element(
                By.XPATH, ".//div[contains(@class,'ratesProgress')]/div"
            ).get_attribute("style") or ""
            percentage_match = re.search(r"(\d+(?:\.\d+)?)\s*%", style)
            percentage = float(percentage_match.group(1)) if percentage_match else 0.0
            if 1 <= star_value <= 5:
                counts[star_value - 1] = int(round(total_comments * percentage / 100))
    except Exception:
        return 0, 0, 0, 0, 0

    return tuple(counts)


def _optional_text(driver, by: str, selector: str, default: str = "") -> str:
    elements = driver.find_elements(by, selector)
    return elements[0].text.strip() if elements else default


def _detail_text(driver, label: str, default: str = "") -> str:
    xpath = (
        f"//td[contains(normalize-space(.), '{label}')]/following-sibling::td[1]"
    )
    return _optional_text(driver, By.XPATH, xpath, default)


def _detail_link(driver, label: str, default: str = "") -> str:
    xpath = (
        f"//td[contains(normalize-space(.), '{label}')]/following-sibling::td[1]//a"
    )
    elements = driver.find_elements(By.XPATH, xpath)
    if not elements:
        return default
    return (elements[0].get_attribute("href") or elements[0].text or "").strip()


def create_app_details_from_html(driver, url: str) -> AppDetails:
    name = _optional_text(driver, By.XPATH, "//h1")
    package_name = url.rstrip("/").split("/")[-1].split("?")[0]

    author_name = _detail_text(driver, "سازنده")
    author_phone_number = _optional_text(
        driver, By.CSS_SELECTOR, ".developer-phone", "N/A"
    )
    email_elements = driver.find_elements(By.CSS_SELECTOR, "a[href^='mailto:']")
    author_email = (
        (email_elements[0].get_attribute("href") or "").replace("mailto:", "").strip()
        if email_elements
        else "N/A"
    )

    installation_count = parse_installation_count(_detail_text(driver, "تعداد دانلود"))
    score_text = normalize_digits(_detail_text(driver, "امتیاز", "0")).replace(",", ".")
    score_match = re.search(r"\d+(?:\.\d+)?", score_text)
    average_score = float(score_match.group(0)) if score_match else 0.0
    comment_count = parse_integer(_detail_text(driver, "تعداد نظرات"))
    version = _detail_text(driver, "نسخه")
    star_counts = parse_star_ratings(driver, comment_count)

    category = _detail_text(driver, "دسته‌بندی")
    last_update = parse_last_update_to_epoch(_detail_text(driver, "آخرین بروزرسانی"))
    tags = [
        item.text.strip()
        for item in driver.find_elements(By.CSS_SELECTOR, ".tags a")
        if item.text.strip()
    ]
    if driver.find_elements(
        By.XPATH,
        "//div[contains(@class,'topApp-title') and contains(.,'منتخب سردبیر')]",
    ):
        tags.append("منتخب سردبیر")

    price = parse_price(_optional_text(driver, By.CSS_SELECTOR, ".price", "0"))
    meta_description = driver.find_elements(By.CSS_SELECTOR, "meta[name='description']")
    short_description = (
        (meta_description[0].get_attribute("content") or "").strip()
        if meta_description
        else ""
    )
    long_elements = driver.find_elements(By.CLASS_NAME, "app-text")
    long_description = (
        (long_elements[0].get_attribute("innerHTML") or "").strip()
        if long_elements
        else ""
    )
    homepage_url = _detail_link(driver, "وب‌سایت")

    return AppDetails(
        name=name,
        package_name=package_name,
        author_name=author_name,
        author_phone_number=author_phone_number,
        author_email=author_email,
        installation_count=installation_count,
        average_score=average_score,
        comment_count=comment_count,
        star_1_count=star_counts[0],
        star_2_count=star_counts[1],
        star_3_count=star_counts[2],
        star_4_count=star_counts[3],
        star_5_count=star_counts[4],
        category=category,
        sub_category="",
        last_update=last_update,
        tags=tags,
        price=price,
        source=Source.MYKET,
        short_description=short_description,
        long_description=long_description,
        homepage_url=homepage_url,
        version=version,
    )
