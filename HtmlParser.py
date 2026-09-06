from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
from typing import List
import re
from datetime import datetime
import jdatetime


from models.AppDetails import AppDetails, Source


def create_app_details_from_html(driver, url):
    try:
        # Extracting app information using Selenium
        name = driver.find_element(By.XPATH, "//h1").text
        package_name = url.split("/")[-1]  # Extract package name from URL
        author_name = driver.find_element(By.XPATH, "//td[contains(text(), 'سازنده')]/following-sibling::td/a").text
        author_phone_number = driver.find_element(By.XPATH, "//span[contains(@class, 'developer-phone')]").text if driver.find_elements(By.XPATH, "//span[contains(@class, 'developer-phone')]") else 'N/A'
        author_email = driver.find_element(By.XPATH, "//a[contains(@href, 'mailto:')]").text if driver.find_elements(By.XPATH, "//a[contains(@href, 'mailto:')]") else 'N/A'
        installation_count_text = driver.find_element(By.XPATH, "//td[contains(text(), 'تعداد دانلود')]/following-sibling::td").text
        installation_count = parse_installation_count(installation_count_text)
        average_score = driver.find_element(By.XPATH, "//td[contains(text(), 'امتیاز')]/following-sibling::td").text
        comment_count_text = driver.find_element(By.XPATH, "//td[contains(text(), 'تعداد نظرات')]/following-sibling::td").text
        comment_count = int(comment_count_text.replace(',', '')) if comment_count_text else 0
        version = driver.find_element(By.XPATH, "//td[contains(text(), 'نسخه')]/following-sibling::td").text
        # Extract star ratings from ratingSec
        star_1_count, star_2_count, star_3_count, star_4_count, star_5_count = parse_star_ratings(driver, comment_count)

        category = driver.find_element(By.XPATH, "//td[contains(text(), 'دسته‌بندی')]/following-sibling::td/a").text
        sub_category = 'N/A'  # Adjust this if there's a way to extract sub-category from the page
        last_update_text = driver.find_element(By.XPATH, "//td[contains(text(), 'آخرین بروزرسانی')]/following-sibling::td").text if driver.find_elements(By.XPATH, "//td[contains(text(), 'آخرین بروزرسانی')]") else 'N/A'
        last_update = parse_last_update_to_epoch(last_update_text)
        tags_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'tags')]/a")
        tags = [tag.text for tag in tags_elements]
        price = driver.find_element(By.XPATH, "//span[contains(@class, 'price')]").text if driver.find_elements(By.XPATH, "//span[contains(@class, 'price')]") else '0'
        short_description = driver.find_element(By.XPATH, "//meta[@name='description']").get_attribute("content") if driver.find_elements(By.XPATH, "//meta[@name='description']") else 'N/A'
        long_description = driver.find_element(By.CLASS_NAME,"app-text").get_attribute("innerHTML")
        #app-detail-section
        if driver.find_elements(By.XPATH, "//div[contains(@class, 'topApp-title') and contains(., 'منتخب سردبیر')]"):
            tags.append('منتخب سردبیر')

        # Create an AppDetails instance with the extracted information
        app_details = AppDetails(name, package_name, author_name, author_phone_number, author_email,
                                 installation_count, float(average_score), comment_count,
                                 star_1_count, star_2_count, star_3_count, star_4_count, star_5_count,
                                 category, sub_category, last_update, tags, int(price), Source.MYKET, short_description,long_description=long_description,homepageUrl='',version=version)

        return app_details

    except Exception as e:
        print(f"Error occurred: {e}")
        return None

def parse_star_ratings(driver, total_comments):
    try:
        rating_elements = driver.find_elements(By.XPATH, "//div[@class='ratingSec']//div[contains(@class, 'rateItem')]")
        star_counts = [0] * 5

        for element in rating_elements:
            star_value = int(element.find_element(By.XPATH, ".//div[contains(@class, 'ratesLabel')]//div").text)
            star_percentage_text = element.find_element(By.XPATH, ".//div[contains(@class, 'ratesProgress')]/div").get_attribute("style")
            star_percentage = int(re.findall(r'\d+', star_percentage_text)[0]) if star_percentage_text else 0

            if star_value >= 1 and star_value <= 5:
                star_counts[5 - star_value] = int((star_percentage / 100) * total_comments)

        return star_counts[4], star_counts[3], star_counts[2], star_counts[1], star_counts[0]

    except Exception as e:
        print(f"Error occurred while parsing star ratings: {e}")
        return 0, 0, 0, 0, 0

def parse_installation_count(installation_count_text):
    # Convert Persian words for numbers to integers (e.g., "2 میلیون" to 2000000)
    count = 0
    if "میلیون" in installation_count_text:
        number = re.findall(r'\d+', installation_count_text)
        if number:
            count = int(number[0]) * 1000000
    elif "هزار" in installation_count_text:
        number = re.findall(r'\d+', installation_count_text)
        if number:
            count = int(number[0]) * 1000
    else:
        number = re.findall(r'\d+', installation_count_text)
        if number:
            count = int(number[0])
    return count

def parse_last_update_to_epoch(last_update_text):
    try:
        # Convert Jalali date to Gregorian and then to epoch
        jdate = jdatetime.datetime.strptime(last_update_text, "%Y/%m/%d")
        gdate = jdate.togregorian()
        epoch_time = int(datetime(gdate.year, gdate.month, gdate.day).timestamp())
        return epoch_time
    except Exception as e:
        print(f"Error occurred while parsing last update date: {e}")
        return 0