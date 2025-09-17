# core/scrapers/dextools/main_dextools_scraper.py
"""
Main DexTools scraping functions.
"""
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from scrapers.pages.dextools_pages import *

from utils.text_utils import replace_string_at_index
from scrapers.dextools.scroll_handler import scroll_to_load_all_projects
from scrapers.dextools.project_scraper import scrape_project_data, enrich_project_data


def scrape_new_socials(driver, chain):
    """
    Scrape new socials from DexTools.

    Returns:
        list: List of scraped project data
    """
    url = "https://www.dextools.io/app/en/new-socials"
    print(f"Scraping DexTools New Socials")

    try:
        driver.get(url)

        # Wait for the page to load
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.ID, "socials")))
        time.sleep(2)
        # scroll_to_load_all_projects(driver)

        # Choose selected chain
        if chain != "all chains":
            chain_selector = driver.find_element(By.XPATH, CHAIN_SELECTOR)
            driver.execute_script("arguments[0].click();", chain_selector)

            SELECTED_CHAIN = replace_string_at_index(CHAIN_SELECTOR__3, -3, chain)
            selected_chain = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, SELECTED_CHAIN))
            )
            driver.execute_script("arguments[0].click();", selected_chain)

        # Scroll to load all projects
        wait.until(EC.presence_of_element_located((By.ID, "socials")))
        time.sleep(1)
        scroll_to_load_all_projects(driver)

        # Find all project cards after scrolling
        project_cards = driver.find_elements(By.CSS_SELECTOR, PROJECT_CARDS)
        print(f"Dextools: Found {len(project_cards)} projects to scrape")

        scraped_projects = []
        max_projects = min(len(project_cards), 100)  # Limit as per your code
        # max_projects = min(len(project_cards[:19]), 100)  # for testing purposes

        for index in range(1, max_projects + 1):
            print(f"Scraping project {index}/{max_projects}")

            try:
                project_data = scrape_project_data(driver, index)
                if chain != 'all chains': project_data['category'] = chain + ' ecosystem'
                scraped_projects.append(project_data)

            except Exception as e:
                print(f"Failed to scrape project {index}: {str(e)}")
                continue

        for project in scraped_projects:
            enrich_project_data(driver, project)

        print(f"Successfully scraped {len(scraped_projects)} projects")
        return scraped_projects

    except Exception as e:
        print(f"Error scraping DexTools New Socials: {str(e)}")
        print(f"Error scraping DexTools New Socials: {str(e)}")
        return []
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass


def scrape_dextools_data(driver, query):
    """
    Main function to scrape DexTools data based on query.

    Args:
        driver (WebDriver): Selenium WebDriver instance
        query (dict): Query parameters

    Returns:
        list: List of scraped project data
    """
    qtype = query.get('type')

    try:
        if qtype == "new socials":
            chain = query.get('chain', 'all chains')
            return scrape_new_socials(driver, chain)
        else:
            print(f"DexTools scrape type '{qtype}' not implemented")
            return []
    except Exception as e:
        print(f"Error in scrape_dextools_data: {e}")
        return []