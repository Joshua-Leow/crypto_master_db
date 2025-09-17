# core/scrapers/gmgn/main_gmgn_scraper.py
"""
Scraper for gmgn.ai projects.
Applies filters, scrolls through projects, and extracts project details.
Results are returned as a list of dictionaries.
"""

import time
from typing import List, Dict, Any, Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    ElementClickInterceptedException,
    ElementNotInteractableException,
)

from scrapers.pages.gmgn_pages import *   # XPaths stored here

from utils.webdriver.web_driver import get_remote_web_driver, get_local_web_driver

BASE_URL = "https://gmgn.ai/?chain="


def safe_get_text(driver, xpath: str, timeout: int = 5) -> Optional[str]:
    """Safely get text from element. Returns None if not found."""
    try:
        el = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        return el.text.strip()
    except Exception as e:
        print(f"safe_get_text failed for {xpath}: {e}")
        return None


def safe_get_attribute(driver, xpath: str, attr: str, timeout: int = 5) -> Optional[str]:
    """Safely get attribute from element. Returns None if not found."""
    try:
        el = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        return el.get_attribute(attr)
    except Exception as e:
        print(f"safe_get_attribute failed for {xpath}: {e}")
        return None


def apply_filters(driver):
    """Apply gmgn.ai filters before scraping."""
    wait = WebDriverWait(driver, 15)

    try:
        time.sleep(10)
        print("Clicking filter button")
        wait.until(EC.element_to_be_clickable((By.XPATH, FILTER_BUTTON))).click()
        time.sleep(1)

        print("Clicking completed button")
        wait.until(EC.element_to_be_clickable((By.XPATH, COMPLETED_BUTTON))).click()
        time.sleep(1)

        print("Setting max age input to 1440")
        time.sleep(2)
        age_input = wait.until(EC.presence_of_element_located((By.XPATH, MAX_AGE_INPUT)))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", age_input)
        driver.execute_script("arguments[0].value = '';", age_input)
        age_input.clear()
        age_input.send_keys("1440")
        time.sleep(1)

        print("Setting min liquidity input to 10")
        liq_input = wait.until(EC.presence_of_element_located((By.XPATH, MIN_LIQUIDITY_INPUT)))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", liq_input)
        driver.execute_script("arguments[0].value = '';", liq_input)
        liq_input.clear()
        liq_input.send_keys("10")
        time.sleep(1)

        print("Clicking socials button")
        wait.until(EC.element_to_be_clickable((By.XPATH, SOCIALS_BUTTON))).click()
        time.sleep(1)

        print("Clicking telegram checkbox")
        checkbox = wait.until(EC.element_to_be_clickable((By.XPATH, TELEGRAM_CHECKBOX)))
        if not checkbox.is_selected():
            driver.execute_script("arguments[0].click();", checkbox)
        time.sleep(1)

        print("Clicking apply button")
        wait.until(EC.element_to_be_clickable((By.XPATH, APPLY_BUTTON))).click()

        time.sleep(2)  # wait for filter results to load
        print("Filters applied successfully")

    except (TimeoutException, ElementClickInterceptedException, ElementNotInteractableException) as e:
        print(f"Error applying filters: {e}")
        raise


def get_project_links(driver) -> List[str]:
    """
    Scroll and collect project links until no more are loaded.
    Returns list of hrefs.
    """
    links = []
    i = 1
    print("Collecting project links")

    while True:
        xpath = PROJECT_LINKS.replace("x", str(i))
        try:
            el = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            href = el.get_attribute("href")
            if href:
                links.append(href)
                print(f"Project {i} link collected: {href}")
            i += 1
        except TimeoutException:
            print("No more projects found")
            break
    return links


def scrape_project(driver, url: str) -> Dict[str, Any]:
    """Scrape details for a single project."""
    print(f"Scraping project: {url}")
    driver.get(url)
    time.sleep(1)

    data = {
        "source_link": url,
        "project_name": safe_get_text(driver, PROJECT_NAME),
        "ticker": safe_get_text(driver, TICKER),
        "market_cap": safe_get_text(driver, MARKET_CAP),
        "liquidity": safe_get_text(driver, LIQUIDITY),
        "website": safe_get_attribute(driver, WEBSITE, "href"),
        "twitter_link": safe_get_attribute(driver, TWITTER, "href"),
        "telegram_link": safe_get_attribute(driver, TELEGRAM, "href"),
        # "solscan": safe_get_attribute(driver, SOLSCAN, "href"),
    }
    return data


def scrape_gmgn(query: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Main function to scrape gmgn.ai.
    Args:
        query: dict with optional 'chain' key.
    Returns:
        List of project data dicts.
    """
    chain = query.get("chain", "sol")
    url = BASE_URL + chain

    print(f"Launching driver for chain: {chain}")
    driver = get_local_web_driver()
    driver.get(url)

    try:
        apply_filters(driver)
        project_links = get_project_links(driver)
        results = [scrape_project(driver, link) for link in project_links]
        print(f"Scraping completed. Total projects: {len(results)}")
        return results
    except Exception as e:
        print(f"Scraping failed: {e}")
        return []
    finally:
        time.sleep(30)
        driver.quit()
        print("Driver closed")


def test_scraper():
    """Run gmgn scraper with default chain and print results."""
    query = {"chain": "sol"}  # you can change chain here
    results = scrape_gmgn(query)

    for i, project in enumerate(results, start=1):
        print(f"\nProject {i}:")
        for key, value in project.items():
            print(f"  {key}: {value}")


if __name__ == "__main__":
    test_scraper()