# core/scrapers/dextools/scroll_handler.py
"""
DexTools scrolling and page loading functions.
"""
import time
from typing import List
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from scrapers.pages.dextools_pages import PAIRS_DASHBOARD_SELECTOR, SOCIAL_CARD_SELECTOR
from utils.logger import app_logger


def scroll_to_load_all_projects(driver: WebDriver, max_scrolls: int = 100) -> List[WebElement]:
    """
    Scroll to the bottom of the page to load all project social-cards.

    Args:
        driver: Selenium WebDriver instance
        max_scrolls (int): Maximum number of scroll attempts

    Returns:
        List of WebElements for the final social cards loaded.
    """
    print("DexTools: scrolling to load all projects...")

    try:
        first_card = driver.find_element(By.CSS_SELECTOR, PAIRS_DASHBOARD_SELECTOR)
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", first_card)
        time.sleep(0.5)

        previous_card_count = 0
        scroll_count = 0
        no_change_count = 0

        while scroll_count < max_scrolls:
            # Get current count of social cards
            current_cards = driver.find_elements(By.CSS_SELECTOR, SOCIAL_CARD_SELECTOR)
            current_card_count = len(current_cards)

            print("DexTools: current social cards count=%d", current_card_count)

            if current_card_count == previous_card_count:
                no_change_count += 1
                if no_change_count >= 8:  # Stop if no new cards appear for 8 consecutive scrolls
                    print("DexTools: no more new social cards appearing. Stopping scroll.")
                    break
            else:
                no_change_count = 0  # Reset counter if new cards appeared

            # Scroll to the last social card
            if current_cards:
                last_card = current_cards[-1]
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", last_card)
                time.sleep(0.1)  # Wait for new content to load

            previous_card_count = current_card_count
            scroll_count += 1
            print("DexTools: scroll %d/%d completed", scroll_count, max_scrolls)

        final_cards = driver.find_elements(By.CSS_SELECTOR, SOCIAL_CARD_SELECTOR)
        print("DexTools: finished scrolling after %d attempts. Total cards loaded: %d", scroll_count, len(final_cards))
        return final_cards

    except Exception as e:
        print("DexTools: error during scrolling: %s", e)
        return []

