# core/scrapers/cmc/data_extractor.py
"""
CMC data extraction functions.
"""
import time

import requests
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains

from scrapers.pages.cmc_pages import MARKET_CAP_TEXT, TAGS, TAGS_SECTION, TAGS_MODAL, TAGS_MODAL_2, \
    EXCHANGE_LINK_12, EXCHANGE_ROWS_OPTION, EXCHANGE_ROWS_100, NEXT_PAGE_BUTTON, FDV_TEXT, ABOUT_TEXT, \
    PROJECT_NAME_TEXT, PROJECT_TICKER_TEXT

from utils.text_utils import replace_string_at_index

def extract_categories(driver):
    """
    Extract category tags from a crypto project page.
    If more than 3 tags are shown, click 'Show all' and collect from modal.
    Otherwise, collect tags directly from the visible section.

    Args:
        driver: Selenium WebDriver instance.

    Returns:
        list[str]: List of category tags.
    """
    time.sleep(0.5)
    tag_elements = driver.find_elements(By.XPATH, TAGS_SECTION)

    for el in tag_elements:
        if el.text.strip().lower() == "show all":
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            driver.execute_script("arguments[0].click();", el)
            time.sleep(0.5)
            # Wait for modal and extract tags
            modal_tags = driver.find_elements(By.XPATH, TAGS_MODAL)
            modal_tags_2 = driver.find_elements(By.XPATH, TAGS_MODAL_2)
            all_modal_tags = modal_tags + modal_tags_2
            time.sleep(0.3)
            categories = [el.text.strip() for el in all_modal_tags if el.text.strip()]
            return categories

    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", tag_elements[0])
    time.sleep(0.3)
    categories = [el.text.strip() for el in tag_elements if el.text.strip()]
    return categories


def extract_project_name(driver):
    """
    Extract project_name text from the project page.

    Args:
        driver: Selenium WebDriver instance

    Returns:
        list[str]: List of href links found
    """
    try:
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, PROJECT_NAME_TEXT))
        )
        elem = driver.find_element(By.XPATH, PROJECT_NAME_TEXT)
        return elem.text
    except Exception as e:
        print(f"Error extracting project name: {e}")
    return None


def extract_project_ticker(driver):
    """
    Extract project_ticker text from the project page.

    Args:
        driver: Selenium WebDriver instance

    Returns:
        list[str]: List of href links found
    """
    try:
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, PROJECT_TICKER_TEXT))
        )
        elem = driver.find_element(By.XPATH, PROJECT_TICKER_TEXT)
        return elem.text.upper()
    except Exception as e:
        print(f"Error extracting project ticker: {e}")
    return None


def extract_exchanges(driver, timeout=5, pause=1):
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
        for row_index in range(1, 101):
            EXCHANGE_LINK = replace_string_at_index(EXCHANGE_LINK_12, -12, row_index)
            try:
                el = wait.until(EC.presence_of_element_located((By.XPATH, EXCHANGE_LINK)))
                driver.execute_script("arguments[0].scrollIntoView();", el)
                href = el.get_attribute("href")
                if 'exchanges' in href:
                    # Extract slug part from href
                    slug = href.replace('https://coinmarketcap.com/exchanges/', '').replace('/', '')
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


def extract_website_from_soup(soup):
    """
    Extract website URL from project page soup.

    Args:
        soup: BeautifulSoup object

    Returns:
        str: Website URL or None
    """
    try:
        site = soup.select_one("div.CoinInfoLinks_info-items-wrapper__dHVKe > div:nth-child(1) a")
        if site and site["href"]:
            return "https:" + site["href"]
    except Exception as e:
        print(f"Error extracting website: {e}")
    return None


def extract_important_notice_from_soup(soup):
    """
    Extract important notice from project page soup.

    Args:
        soup: BeautifulSoup object

    Returns:
        str: Important notice text or None
    """
    try:
        el = soup.select_one("div.notice-container > section > div > div > span")
        return el.get_text() if el else None
    except Exception as e:
        print(f"Error extracting important notice: {e}")
    return None


def extract_about_from_soup(soup):
    try:
        about_notes_target = soup.select_one(ABOUT_TEXT)
        about_notes = about_notes_target.get_text() if about_notes_target else None
    except Exception as e:
        print(e)
        return None
    if about_notes is not None:
        about_notes = about_notes[:4500]
    return about_notes


def extract_market_cap_text(driver):
    """
    Extract market cap text from the project page.

    Args:
        driver: Selenium WebDriver instance

    Returns:
        list[str]: List of href links found
    """
    try:
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, MARKET_CAP_TEXT))
        )
        elem = driver.find_element(By.XPATH, MARKET_CAP_TEXT)
        return elem.text
    except Exception as e:
        print(f"Error extracting market cap: {e}")
    return None

def extract_fdv_text(driver):
    """
    Extract market cap text from the project page.

    Args:
        driver: Selenium WebDriver instance

    Returns:
        list[str]: List of href links found
    """
    try:
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, FDV_TEXT))
        )
        elem = driver.find_element(By.XPATH, FDV_TEXT)
        return elem.text
    except Exception as e:
        print(f"Error extracting market cap: {e}")
    return None

def extract_all_social_links(driver):
    """
    Extract all social media links from the project page.

    Args:
        driver: Selenium WebDriver instance

    Returns:
        list[str]: List of href links found
    """
    links = []

    try:
        more_links = WebDriverWait(driver, 1).until(
            EC.visibility_of_element_located((By.XPATH, "//div[@data-test='chip-more-social-links']"))
        )
        ActionChains(driver).move_to_element(more_links).perform()

        # Wait for tooltip to appear
        WebDriverWait(driver, 3).until(EC.visibility_of_element_located((
            By.XPATH, "//div[@role='tooltip']/div/div/a")))

        tooltip = driver.find_elements(By.XPATH, "//div[@role='tooltip']/div/div/a")

        for elem in tooltip:
            href = elem.get_attribute("href")
            if href:
                links.append(href)
        return links
    except:
        pass

    try:
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "div.CoinInfoLinks_info-items-wrapper__dHVKe a"))
        )
        elems = driver.find_elements(By.CSS_SELECTOR, "div.CoinInfoLinks_info-items-wrapper__dHVKe a")
        for elem in elems:
            href = elem.get_attribute("href")
            if href:
                links.append(href)
    except Exception as e:
        print(f"Error extracting social links: {e}")
    return links


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
        response = requests.get(project["sources"]["coinmarketcap"], timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        try:
            website = extract_website_from_soup(soup)
            if not isinstance(project.get("socials"), dict):
                project["socials"] = {}
            project["socials"].update({"website": website})
        except Exception as e:
            print(f"Missing website via BeatifulSoup for {project.get('project_name', 'Unknown')}")

        try:
            impt = extract_important_notice_from_soup(soup)
            if impt: project["important_note"] = impt
        except Exception as e:
            print(f"Missing impt note via BeatifulSoup for {project.get('project_name', 'Unknown')}")

        try:
            about = extract_about_from_soup(soup)
            if about: project["about"] = about
        except Exception as e:
            print(f"Missing about text via BeatifulSoup for {project.get('project_name', 'Unknown')}")

    except Exception as e:
        print(f"Error connecting to BeatifulSoup for {project.get('project_name', 'Unknown')}: {e}")

    try:
        driver.get(project["sources"]["coinmarketcap"])

        try:
            project_name = extract_project_name(driver)
            if project_name: project["project_name"] = project_name
        except Exception as e:
            print(f"Missing project_name via Selenium for {project['sources']['coinmarketcap']}")

        try:
            project_ticker = extract_project_ticker(driver)
            if project_ticker: project["project_ticker"] = project_ticker
        except Exception as e:
            print(f"Missing project_ticker via Selenium for {project.get('project_name', 'Unknown')}")

        try:
            exchanges = extract_exchanges(driver)
            if exchanges: project["exchanges"] = exchanges
        except Exception as e:
            print(f"Missing exchanges via Selenium for {project.get('project_name', 'Unknown')}")

        try:
            # get market cap
            market_cap = extract_market_cap_text(driver)
            if market_cap: project["market_cap"] = market_cap
        except Exception as e:
            print(f"Missing market cap via Selenium for {project.get('project_name', 'Unknown')}")

        try:
            # extract social links
            all_links = extract_all_social_links(driver)
            if all_links:
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
                for link in all_links:
                    for keyword, field in link_field_map.items():
                        if keyword in link and field not in assigned_fields:
                            if link[:8] == 'mailto: ': link = link[8:]
                            if not isinstance(project.get("socials"), dict):
                                project["socials"] = {}
                            project["socials"].update({field: link})
                            assigned_fields.add(field)
                            break  # Stop checking more keywords for this link
        except Exception as e:
            print(f"Missing socials via Selenium for {project.get('project_name', 'Unknown')}")

        try:
            categories = extract_categories(driver)
            if categories: project["category"] = categories
        except Exception as e:
            print(f"Missing categories via Selenium for {project.get('project_name', 'Unknown')}")

    except Exception as e:
        print(f"Error connecting Selenium driver for {project.get('project_name', 'Unknown')}: {e}")

    return project