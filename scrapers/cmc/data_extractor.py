# core/scrapers/cmc/data_extractor.py
"""
CMC data extraction functions.
"""
import time
from typing import List, Tuple

import requests
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains

from scrapers.pages.cmc_pages import MARKET_CAP_TEXT, TAGS, TAGS_SECTION, TAGS_MODAL, TAGS_MODAL_2, \
    EXCHANGE_LINK_12, EXCHANGE_ROWS_OPTION, EXCHANGE_ROWS_100, NEXT_PAGE_BUTTON, FDV_TEXT, ABOUT_TEXT, \
    PROJECT_NAME_TEXT, PROJECT_TICKER_TEXT

from utils.text_utils import replace_string_at_index, parse_dollar_amount, _normalize_name, _get_ecosystem_regex, \
    _strip_ecosystem, _add_unique_ci, get_link_field_map


def extract_categories(driver) -> Tuple[List[str], List[str]]:
    """
    Extract tags, normalize, and split into (categories, networks).
    - Converts hyphens to spaces, title-cases, de-duplicates case-insensitively.
    - Any tag containing 'ecosystem' is moved to networks with 'ecosystem' removed.
    Returns:
        (categories: list[str], networks: list[str])
    """
    def _normalize_and_split(names: List[str]) -> Tuple[List[str], List[str]]:
        cats: List[str] = []
        nets: List[str] = []
        for n in names:
            n = _normalize_name(n)
            if not n:
                continue
            if _get_ecosystem_regex().search(n):
                m = _strip_ecosystem(n)
                if m:
                    _add_unique_ci(nets, m)
            else:
                _add_unique_ci(cats, n)
        # Final dedupe + sort
        cats = sorted({v.title() for v in cats})
        nets = sorted({v.title() for v in nets})
        return cats, nets

    time.sleep(0.5)
    tag_elements = driver.find_elements(By.XPATH, TAGS_SECTION)

    # If a "Show all" button exists, click and collect from modal
    for el in tag_elements:
        if el.text.strip().lower() == "show all":
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            driver.execute_script("arguments[0].click();", el)
            time.sleep(0.5)
            modal_tags = driver.find_elements(By.XPATH, TAGS_MODAL)
            modal_tags_2 = driver.find_elements(By.XPATH, TAGS_MODAL_2)
            all_modal_tags = modal_tags + modal_tags_2
            time.sleep(0.3)
            names = [e.text.strip() for e in all_modal_tags if e.text.strip()]
            return _normalize_and_split(names)

    # Else collect from visible section
    if tag_elements:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", tag_elements[0])
    time.sleep(0.3)
    names = [el.text.strip() for el in tag_elements if el.text.strip()]
    return _normalize_and_split(names)


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


def extract_market_cap(driver):
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
        raw = elem.text
        market_cap = parse_dollar_amount(raw)
        if market_cap > 0: return market_cap
        else: return None
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
        raw = elem.text
        return parse_dollar_amount(raw)
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
            if project.get("project_name") is None:
                project_name = extract_project_name(driver)
                if project_name: project["project_name"] = project_name
        except Exception as e:
            print(f"Missing project_name via Selenium for {project['sources']['coinmarketcap']}")

        try:
            if project.get("project_ticker") is None:
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
            market_cap = extract_market_cap(driver)
            if market_cap: project["market_cap"] = market_cap
        except Exception as e:
            print(f"Missing market cap via Selenium for {project.get('project_name', 'Unknown')}")

        try:
            # extract social links
            all_links = extract_all_social_links(driver)
            if all_links:
                link_field_map = get_link_field_map()

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
            cats, nets = extract_categories(driver)
            if nets:
                for v in nets: _add_unique_ci(project.setdefault("network", []), v)
                project["network"] = sorted({(v or "").title() for v in project.get("network", []) if isinstance(v, str)})
            if cats:
                for v in cats: _add_unique_ci(project.setdefault("category", []), v)
                project["category"] = sorted({(v or "").title() for v in project.get("category", []) if isinstance(v, str)})
        except Exception as e:
            # import logging, traceback, sys, pprint as pp
            # logging.basicConfig(level=logging.DEBUG, format="%(levelname)s:%(message)s")
            #
            # def _exc_dump(msg: str, **ctx):
            #     et, ev, tb = sys.exc_info()
            #     logging.error("%s: %s: %s", msg, et.__name__ if et else "Exception", ev)
            #     for k, v in ctx.items():
            #         logging.error("  %s=%s", k, v)
            #     traceback.print_exc()
            #
            # _exc_dump(
            #     "Missing categories via Selenium",
            #     project_name=project.get("project_name"),
            #     has_network=isinstance(project.get("network"), list),
            #     has_category=isinstance(project.get("category"), list),
            #     nets_len=("n/a" if "nets" not in locals() else len(nets)),
            #     cats_len=("n/a" if "cats" not in locals() else len(cats)),
            #     project_keys=sorted(project.keys()),
            #     sample_network=(project.get("network")[:5] if isinstance(project.get("network"), list) else None),
            #     sample_category=(project.get("category")[:5] if isinstance(project.get("category"), list) else None),
            # )
            print(f"Missing categories via Selenium for {project.get('project_name', 'Unknown')}\n{e}")

    except Exception as e:
        print(f"Error connecting Selenium driver for {project.get('project_name', 'Unknown')}: {e}")

    return project