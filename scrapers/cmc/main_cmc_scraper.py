# scrapers/cmc/main_cmc_scraper.py
"""
Main CMC scraping functions.
"""
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from MasterProjectManager import MasterProjectManager
from config.private import get_mongodb_uri
from messengers.pages.tele_pages import SEARCH_BOX
from messengers.telegram.admin_extractor import _reset_to_telegram_main
from scrapers.pages.cmc_pages import *

from scrapers.cmc.data_extractor import enrich_project_with_details
from scrapers.pages.cmc_pages import NEW_BUTTON
from utils.project_enrichment import enrich_telegram_data, enrich_email_data
from utils.web_driver import get_dedicated_local_web_driver, get_local_web_driver


def go_cmc_to_page(driver, qpage, timeout=10):
    """
    Navigate to the requested page number using pagination controls.

    Args:
        driver: Selenium WebDriver instance.
        qpage (int): Target page number.
        timeout (int): Wait timeout in seconds.
    """
    while True:
        # Wait for pagination links
        page_elements = WebDriverWait(driver, timeout).until(
            EC.presence_of_all_elements_located((By.XPATH, PAGE_NUMBERS))
        )

        # Extract page numbers as integers where possible
        page_map = {}
        for el in page_elements:
            text = el.text.strip()
            if text.isdigit():
                page_map[int(text)] = el

        if not page_map:
            raise ValueError("No numeric pagination links found")

        # Find closest page to qpage
        available_pages = sorted(page_map.keys())
        if qpage in available_pages:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", page_map[qpage])
            page_map[qpage].click()
            break
        else:
            # Closest match
            closest_page = min(available_pages, key=lambda x: abs(x - qpage))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", page_map[closest_page])
            page_map[closest_page].click()


def scrape_standard_project_rows_from_table(driver):
    """
    Scrape project rows from CoinMarketCap table.

    Args:
        driver: Selenium WebDriver instance

    Returns:
        list: List of project dictionaries
    """
    results = []
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table > tbody > tr"))
        )
        trs = driver.find_elements(By.CSS_SELECTOR, "table > tbody > tr")
        print(f"CoinMarketCap scraper: Found {len(trs)} table rows")

        for i in range(len(trs)):
            tr = driver.find_elements(By.CSS_SELECTOR, "table > tbody > tr")[i]
            driver.execute_script("arguments[0].scrollIntoView();", tr)
            try:
                # TODO: make it dynamic to find the data from different links
                source_link = tr.find_element(By.CSS_SELECTOR, "td:nth-child(3) > div > a")
                ticker = tr.find_element(By.CSS_SELECTOR, "td:nth-child(3) > div > a > span > div > div > div > p")
                project_name = tr.find_element(By.CSS_SELECTOR, "td:nth-child(3) > div > a > span > div > div > p")

                results.append({
                    "project_name": project_name.text,
                    "project_ticker": ticker.text.upper(),
                    "sources": {"coinmarketcap": source_link.get_attribute("href")},
                })
            except Exception as e:
                print(f"Skipping row {i}: {e}")
                continue
    except Exception as e:
        print(f"Error scraping table rows: {e}")

    return results


def handle_standard_cmc_table(driver, chrome_profile):
    projects = scrape_standard_project_rows_from_table(driver)
    if not projects:
        print("No projects found in table")
        return []

    print(f"Scraped {len(projects)} projects, enriching data...")
    driver2 = get_dedicated_local_web_driver(chrome_profile)
    _reset_to_telegram_main(driver2)
    manager = MasterProjectManager(get_mongodb_uri())

    enriched_projects = []
    for i, project in enumerate(projects[:10]):   # for testing purposes
    # for i, project in enumerate(projects):
        print(f"Enriching project {i + 1}/{len(projects)}: {project.get('project_name', 'Unknown')}")
        enriched_project = enrich_project_with_details(driver, project)
        enriched_project.update(enrich_telegram_data(driver2, enriched_project, chrome_profile))
        enriched_project.update(enrich_email_data(enriched_project))
        enriched_projects.append(enriched_project)

        project_uid = manager.upsert_project(enriched_project, "coinmarketcap")

    driver2.quit()

    print(f"Successfully scraped {len(enriched_projects)} projects")
    return enriched_projects


def scrape_new_cmc_page(page_num:int, chrome_profile):
    driver = get_local_web_driver()
    driver.get("https://coinmarketcap.com")

    new_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, NEW_BUTTON)))
    driver.execute_script("arguments[0].click();", new_button)
    time.sleep(0.5)

    if page_num > 1:
        go_cmc_to_page(driver, page_num)
    time.sleep(2.5)

    projects = handle_standard_cmc_table(driver, chrome_profile)
    driver.quit()
    time.sleep(1)
    print(projects)
