# core/scrapers/dexscreener/main_dexscreener_scraper.py

from utils.webdriver.web_driver import get_local_headless_web_driver
from utils.text_utils import replace_string_at_index

from scrapers.pages.dexscreener_pages import *

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time

def scrape_dexscreener_data(driver, query):
    """
    Scrape DexScreener project data based on query.

    Args:
        driver (WebDriver): Selenium WebDriver instance
        query (dict): Must include 'type' and 'page'

    Returns:
        list: List of dictionaries with project data
    """
    qtype = query.get("type")
    qpage = query.get("page", 1)
    projects = []

    if qtype != "new coins":
        app_logger.warning("DexScreener only supports 'new coins' type for now.")
        return []

    url = f"https://dexscreener.com/page-{qpage}?maxAge=24&minLiq=10000&order=asc&profile=1&rankBy=pairAge"
    print(f"Scraping DexScreener page: {url}")

    driver.get(url)
    time.sleep(3)

    for i in range(2, 102):
        try:
            name_sel = replace_string_at_index(PROJECT_NAME__12, index=12, replacement=str(i))
            ticker_sel = replace_string_at_index(PROJECT_TICKERS__12, index=12, replacement=str(i))
            liq_sel = replace_string_at_index(PROJECT_LIQUIDITY__12, index=12, replacement=str(i))
            mcap_sel = replace_string_at_index(PROJECT_MARKET_CAP__12, index=12, replacement=str(i))

            driver.implicitly_wait(1)
            name_elem = driver.find_element(By.CSS_SELECTOR, name_sel)
            ticker_elem = driver.find_element(By.CSS_SELECTOR, ticker_sel)
            liquidity_elem = driver.find_element(By.CSS_SELECTOR, liq_sel)
            mcap_elem = driver.find_element(By.CSS_SELECTOR, mcap_sel)

            name_elem.click()
            time.sleep(1.5)  # allow modal to open

            project = {
                "project_name": name_elem.text.strip(),
                "project_ticker": ticker_elem.text.strip(),
                "liquidity": liquidity_elem.text.strip(),
                "market_cap": mcap_elem.text.strip(),
            }

            all_links = extract_all_social_links(driver, i)
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
                    "github": "github_link",
                }
                assigned_fields = set()
                for link in all_links:
                    matched = False
                    for keyword, field in link_field_map.items():
                        if keyword in link and field not in assigned_fields:
                            if link.startswith('mailto:'):
                                link = link[8:]
                            if not isinstance(project.get("socials"), dict):
                                project["socials"] = {}
                            project["socials"].update({field: link})
                            assigned_fields.add(field)
                            matched = True
                            break  # stop once matched
                    if not matched and "website" not in assigned_fields:
                        if not isinstance(project.get("socials"), dict):
                            project["socials"] = {}
                        project["socials"].update({"website": link})
                        assigned_fields.add("website")

            print(f"Extracted project {i-1} data: {project}")
            projects.append(project)

            close_btn = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, PROJECT_PAGE_CLOSE_BUTTON))
            )
            close_btn.click()
            time.sleep(0.8)

        except (TimeoutException, NoSuchElementException) as e:
            print(f"DexScreener skipped row {i}: {e}")
            continue
        except Exception as e:
            print(f"DexScreener error at row {i}: {e}")
            continue

    driver.quit()
    return projects

def extract_all_social_links(driver, index):
    """
    Extract all social links from modal popup (excluding last button).

    Args:
        driver (WebDriver): Selenium driver
        index (int): Current row index (used to build selector)

    Returns:
        list: All extracted href links
    """
    all_links = []
    try:
        # Find all social buttons
        buttons = driver.find_elements(By.XPATH, PROJECT_PAGE_LINKS__2.replace("[x]", ""))  # find generic buttons
        num_buttons = len(buttons)

        # Loop through all buttons except the last
        for j in range(1, num_buttons):  # exclude last button
            xpath = replace_string_at_index(PROJECT_PAGE_LINKS__2, index=-2, replacement=str(j))
            try:
                social_button = driver.find_element(By.XPATH, xpath)
                href = social_button.get_attribute("href")
                if href:
                    all_links.append(href)
            except Exception as e:
                print(f"Failed to get social link at index {j}: {e}")
    except Exception as e:
        print(f"Error extracting social links: {e}")
    return all_links
