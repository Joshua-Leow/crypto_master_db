# core/scrapers/cmc/data_extractor.py
"""
CMC data extraction functions.
"""
import time
from typing import Dict

import requests
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains

from scrapers.pages.coingecko_pages import COIN_NAME_TEXT, COIN_SYMBOL_TEXT, MARKET_CAP_TEXT, IMPORTANT_TEXT, \
    INFO_TABLE_KEYS, WEBSITE_LINK, SOCIALS_LINKS, INFO_SECTION_LINKS, CHAINS_INFO_LINKS, MORE_INFO_BUTTON, \
    CATEGORY_INFO_LINKS, ABOUT_MORE_BUTTON, ABOUT_TEXT, EXCHANGE_ROWS_OPTION, EXCHANGE_ROWS_100, \
    NEXT_PAGE_BUTTON, NAVIGATION_NUMBERS, EXCHANGE_LINK__14
from utils.text_utils import replace_string_at_index


def get_coin_symbol(driver):
    coin_symbol = ""
    try:
        coin_symbol = driver.find_element(By.CSS_SELECTOR, COIN_SYMBOL_TEXT).text
        if coin_symbol[-6:] == ' Price':
            coin_symbol = coin_symbol[:-6]
    except Exception as e:
        print(f"Failed at get_coin_symbol function. COIN_SYMBOL_TEXT not found.")
    # print(f"coin_symbol is: {coin_symbol}")
    return coin_symbol


def get_project_info_section(driver, project:Dict):
    """
    get project info section from project page and enrich project data
    with website, socials, chains, categories

    :param driver:
    :param project:
    :return: project dictionary
    """
    website = community = chains = categories = None
    try:
        info_table_keys_elements = driver.find_elements(By.CSS_SELECTOR, INFO_TABLE_KEYS)
        info_table_keys = [elem.text for elem in info_table_keys_elements]
        for i, key in enumerate(info_table_keys):
            if 'Website' in key: website = i
            if 'Community' in key: community = i
            if 'Chains' in key: chains = i
            if 'Categories' in key: categories = i
    except Exception as e: print(f"Failed to get info_table_keys\n{e}")
    try:
        if website:
            WEBSITE_LINK_TARGET = replace_string_at_index(INFO_SECTION_LINKS, -12, str(website+1))
            website = driver.find_element(By.CSS_SELECTOR, WEBSITE_LINK_TARGET).get_attribute('href')
            if not isinstance(project.get("socials"), dict):
                project["socials"] = {}
            project["socials"].update({"website": website})
    except Exception as e: print(f"Failed to get website\n{e}")
    try:
        if community:
            SOCIAL_LINKS_TARGET = replace_string_at_index(INFO_SECTION_LINKS, -12, str(community+1))
            all_socials = driver.find_elements(By.CSS_SELECTOR, SOCIAL_LINKS_TARGET)
            all_socials = [element.get_attribute('href') for element in all_socials]
            all_socials = [href for href in all_socials if href]
            if all_socials:
                link_field_map = {
                    "t.me": "telegram_link",
                    "linkedin": "linkedin_link",
                    "facebook": "facebook_link",
                    "instagram": "instagram_link",
                    "tiktok": "tiktok_link",
                    "youtube": "youtube_link",
                    "discord": "discord_link",
                    "reddit": "reddit_link",
                    "medium": "medium_link",
                    "twitter": "twitter_link",
                    "x.com": "twitter_link",
                    "mailto:": "email_link",
                    'github': 'github_link',
                }

                # Categorize and store the link
                assigned_fields = set()
                for link in all_socials:
                    for keyword, field in link_field_map.items():
                        if keyword in link and field not in assigned_fields:
                            if link[:8] == 'mailto: ': link = link[8:]
                            if not isinstance(project.get("socials"), dict):
                                project["socials"] = {}
                            project["socials"].update({field: link})
                            assigned_fields.add(field)
                            break  # Stop checking more keywords for this link
    except Exception as e: print(f"Failed to get all_socials\n{e}")
    try:
        if chains:
            CHAIN_LINKS_TARGET = replace_string_at_index(INFO_SECTION_LINKS, -12, str(chains+1))
            unfiltered_chains = driver.find_elements(By.CSS_SELECTOR, CHAIN_LINKS_TARGET)
            unfiltered_chains = [element.get_attribute('href') for element in unfiltered_chains]
            unfiltered_chains = [href for href in unfiltered_chains if href]

            try:
                MORE_INFO_BUTTON_TARGET = replace_string_at_index(MORE_INFO_BUTTON, -20, str(chains+1))
                more_info_button = WebDriverWait(driver, 2).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, MORE_INFO_BUTTON_TARGET)))
                more_info_button.click()
                CHAIN_INFO_LINKS_TARGET = replace_string_at_index(CHAINS_INFO_LINKS, -36, str(chains+1))
                more_unfiltered_chains = driver.find_elements(By.CSS_SELECTOR, CHAIN_INFO_LINKS_TARGET)
                more_unfiltered_chains = [element.get_attribute('href') for element in more_unfiltered_chains]
                more_unfiltered_chains = [href for href in more_unfiltered_chains if href]

                unfiltered_chains.extend(more_unfiltered_chains)
                more_info_button.click()
            except Exception as e: print(f"more chain info button missing")

            if not isinstance(project.get("category"), dict):
                project["category"] = []
            for chain in unfiltered_chains:
                if '/categories/' in chain:
                    project["category"].append(chain.split('/categories/')[-1])
    except Exception as e: print(f"Failed to get more chains\n{e}")
    try:
        if categories:
            CATEGORIES_LINKS_TARGET = replace_string_at_index(INFO_SECTION_LINKS, -12, str(categories+1))
            unfiltered_categories = driver.find_elements(By.CSS_SELECTOR, CATEGORIES_LINKS_TARGET)
            unfiltered_categories = [element.get_attribute('href') for element in unfiltered_categories]
            unfiltered_categories = [href for href in unfiltered_categories if href]

            try:
                MORE_INFO_BUTTON_TARGET = replace_string_at_index(MORE_INFO_BUTTON, -20, str(categories + 1))
                more_info_button = WebDriverWait(driver, 2).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, MORE_INFO_BUTTON_TARGET)))
                more_info_button.click()
                CATEGORY_INFO_LINKS_TARGET = replace_string_at_index(CATEGORY_INFO_LINKS, -42, str(categories + 1))
                more_unfiltered_categories = driver.find_elements(By.CSS_SELECTOR, CATEGORY_INFO_LINKS_TARGET)
                more_unfiltered_categories = [element.get_attribute('href') for element in more_unfiltered_categories]
                more_unfiltered_categories = [href for href in more_unfiltered_categories if href]

                unfiltered_categories.extend(more_unfiltered_categories)
                more_info_button.click()
            except Exception as e: print(f"more category info button missing\n{e}")

            if not isinstance(project.get("category"), dict):
                project["category"] = []
            for category in unfiltered_categories:
                if '/categories/' in category:
                    project["category"].append(category.split('/categories/')[-1])
    except Exception as e: print(f"Failed to get more categories\n{e}")

    return project

def get_about_text(driver):
    about_text = ''
    try:
        about_more_button = driver.find_element(By.CSS_SELECTOR, ABOUT_MORE_BUTTON)
        driver.execute_script("arguments[0].scrollIntoView();", about_more_button)
        driver.execute_script("arguments[0].click();", about_more_button)
        about_text = driver.find_element(By.CSS_SELECTOR, ABOUT_TEXT).text.strip()
    except Exception as e:
        print(e)

    # print(f"about_text is: {about_text}")
    return about_text[:4500]


def extract_exchanges(driver, timeout=2, pause=1):
    """
    Extract all exchange slugs from the coin markets section.
    Expands rows to 100, loops through all pagination pages, and collects exchange names.

    Args:
        driver: Selenium WebDriver instance.
        timeout (int): Wait timeout in seconds.
        pause (float): Seconds to wait after page interactions.

    Returns:
        list[str]: Unique list of exchange slugs (e.g., 'pancakeswap-v3').
    """
    wait = WebDriverWait(driver, timeout)
    exchanges = set()
    # Set rows per page to 100
    try:
        rows_option = wait.until(EC.presence_of_element_located((By.XPATH, EXCHANGE_ROWS_OPTION)))
        ActionChains(driver).move_to_element(rows_option).perform()
        rows_option.click()
        rows_100 = driver.find_element(By.XPATH, EXCHANGE_ROWS_100)
        rows_100.click()
        time.sleep(pause)
    except: pass

    while True:
        # Collect rows on the current page
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", driver.find_element(By.XPATH, NAVIGATION_NUMBERS))
        for row_index in range(1, 101):
            EXCHANGE_LINK = replace_string_at_index(EXCHANGE_LINK__14, -14, row_index)
            try:
                el = wait.until(EC.presence_of_element_located((By.XPATH, EXCHANGE_LINK)))
                driver.execute_script("arguments[0].scrollIntoView();", el)
                href = el.get_attribute("href")
                if 'exchanges' in href:
                    # Extract slug part from href
                    slug = href.replace('https://www.coingecko.com/en/exchanges/', '').replace('/', '')
                    if slug:
                        exchanges.add(slug)
            except Exception:
                break  # No more rows in this page

        # Try clicking the next page
        try:
            next_btn = WebDriverWait(driver, 1).until(EC.element_to_be_clickable((By.XPATH, NEXT_PAGE_BUTTON)))
            ActionChains(driver).move_to_element(next_btn).perform()
            next_btn.click()
            time.sleep(pause)
        except Exception:
            break  # No more next button → exit loop

    return list(exchanges)


def enrich_project_with_details(driver, project):
    """
    Enrich project data with additional details from project page.

    Args:
        driver: Selenium WebDriver instance
        project (dict): Project data dictionary

    Returns:
        dict: Enriched project data
    """
    try:
        driver.get(project["sources"]["coingecko"])

        try:
            project_name = driver.find_element(By.CSS_SELECTOR, COIN_NAME_TEXT).text
            if project_name: project["project_name"] = project_name
        except Exception as e:
            print(f"Missing project_name via Selenium for {project["sources"]["coingecko"]}")

        try:
            symbol = get_coin_symbol(driver)
            if symbol: project["project_ticker"] = symbol
        except Exception as e:
            print(f"Missing project_ticker via Selenium for {project.get('project_name', 'Unknown')}")

        try:
            project.update(get_project_info_section(driver, project))
        except Exception as e:
            print(f"Error getting project info section via Selenium for {project.get('project_name', 'Unknown')}: {e}")

        try:
            market_cap = driver.find_element(By.CSS_SELECTOR, MARKET_CAP_TEXT).text
            if market_cap: project["market_cap"] = market_cap
        except Exception as e:
            print(f"Missing mcap via Selenium for {project.get('project_name', 'Unknown')}")

        try:
            impt = driver.find_element(By.CSS_SELECTOR, IMPORTANT_TEXT).text
            if impt: project["important_note"] = impt
        except Exception as e:
            print(f"Missing impt note via Selenium for {project.get('project_name', 'Unknown')}")

        try:
            about = get_about_text(driver)
            if about: project["about"] = about
        except Exception as e:
            print(f"Missing about text via Selenium for {project.get('project_name', 'Unknown')}")

        try:
            exchanges = extract_exchanges(driver)
            if exchanges: project["exchanges"] = exchanges
        except Exception as e:
            print(f"Missing exchanges via Selenium for {project.get('project_name', 'Unknown')}")

    except Exception as e:
        print(f"Error connecting Selenium driver for {project.get('project_name', 'Unknown')}: {e}")

    print(f"{project}")
    return project
