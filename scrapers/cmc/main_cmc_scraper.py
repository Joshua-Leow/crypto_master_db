# core/scrapers/cmc/main_cmc_scraper.py
"""
Main CMC scraping functions.
"""
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from scrapers.pages.cmc_pages import *

from scrapers.cmc.data_extractor import enrich_project_with_details


def map_social_links(social_links):
    """Map social links to their respective fields."""
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

    mapped = {}
    assigned_fields = set()

    for link in social_links:
        clean_link = link[8:] if link.startswith('mailto: ') else link
        for keyword, field in link_field_map.items():
            if keyword in link and field not in assigned_fields:
                mapped[field] = clean_link
                assigned_fields.add(field)
                break

    return mapped

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


def scrape_dexscan_project_rows_from_table(driver):
    """
    Scrape project rows from CMC table.

    Args:
        driver: Selenium WebDriver instance

    Returns:
        list: List of project dictionaries
    """
    results = []

    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table > tbody > tr > td > span"))
        )
        trs = driver.find_elements(By.CSS_SELECTOR, "table > tbody > tr")

        print(f"CoinMarketCap scraper: Found {len(trs)} table rows")

        for i, tr in enumerate(trs):
            try:
                driver.execute_script("arguments[0].scrollIntoView();", tr)

                source_link = tr.find_element(By.XPATH, DEXSCAN_PROJECT_SOURCE_LINK)
                ticker = tr.find_element(By.XPATH, DEXSCAN_PROJECT_NAME)
                market_cap = tr.find_element(By.XPATH, DEXSCAN_PROJECT_MCAP_TEXT)
                liquidity = tr.find_element(By.XPATH, DEXSCAN_PROJECT_LIQUIDITY_TEXT)

                project_dict = {
                    "project_name": ticker.text,
                    "project_ticker": ticker.text.upper(),
                    "market_cap": market_cap.text,
                    "liquidity": liquidity.text,
                    "sources": {"coinmarketcap": source_link.get_attribute("href")},
                }

                try:
                    social_elements = tr.find_elements(By.XPATH, DEXSCAN_PROJECT_SOCIALS_LINKS)
                    social_links = [elem.get_attribute("href") for elem in social_elements if elem.get_attribute("href")]

                    if social_links:
                        social_data = map_social_links(social_links)
                        print(social_data)
                        project_dict["socials"] = social_data

                except Exception as se:
                    print(f"Error parsing social links for row {i}: {se}")

                results.append(project_dict)

            except Exception as e:
                print(f"Error extracting data for row {i}: {e}")

    except Exception as e:
        print(f"Error scraping table rows: {e}")

    return results


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


def handle_standard_cmc_table(driver):
    projects = scrape_standard_project_rows_from_table(driver)
    if not projects:
        print("No projects found in table")
        return []

    print(f"Scraped {len(projects)} projects, enriching data...")

    enriched_projects = []
    for i, project in enumerate(projects[:10]):   # for testing purposes
    # for i, project in enumerate(projects):
        print(f"Enriching project {i + 1}/{len(projects)}: {project.get('project_name', 'Unknown')}")
        enriched_project = enrich_project_with_details(driver, project)
        enriched_projects.append(enriched_project)

    print(f"Successfully scraped {len(enriched_projects)} projects")
    return enriched_projects


def scrape_cmc_data(driver, query):
    """
    Main function to scrape CMC data based on query.

    Args:
        query (dict): Query parameters

    Returns:
        list: List of enriched project data
    """
    try:
        qtype = query.get('type')
        qpage = query.get('page')

        # By Category
        if qtype == "by category":
            category = query.get('category')
            driver.get(f"https://coinmarketcap.com/view/{category}/")
            if qpage != 1:
                go_cmc_to_page(driver, qpage)
            time.sleep(2.5)
            return handle_standard_cmc_table(driver)

        # New Coins
        elif qtype == "new coins":
            print(qpage)
            if qpage == 0:
                driver.get("https://coinmarketcap.com")

                new_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, NEW_BUTTON)))
                driver.execute_script("arguments[0].click();", new_button)
                time.sleep(0.5)

                filters_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, FILTERS_BUTTON)))
                driver.execute_script("arguments[0].click();", filters_button)
                time.sleep(0.5)

                dexscan_filters_max_age_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, DEXSCAN_FILTERS_MAX_AGE_INPUT)))
                dexscan_filters_max_age_input.send_keys('24')
                time.sleep(0.5)

                dexscan_filters_apply_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, DEXSCAN_FILTERS_APPLY_BUTTON)))
                driver.execute_script("arguments[0].click();", dexscan_filters_apply_button)
            elif qpage == 1:
                driver.get("https://coinmarketcap.com")

                new_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, NEW_BUTTON)))
                driver.execute_script("arguments[0].click();", new_button)
                time.sleep(0.5)
            else:
                driver.get("https://coinmarketcap.com")

                new_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, NEW_BUTTON)))
                driver.execute_script("arguments[0].click();", new_button)
                time.sleep(0.5)

                go_cmc_to_page(driver, qpage)
            time.sleep(2.5)
            return handle_standard_cmc_table(driver)

        # New DexScan
        elif qtype == "new dexscan":
            driver.get("https://coinmarketcap.com")
            new_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, NEW_BUTTON)))
            driver.execute_script("arguments[0].click();", new_button)
            time.sleep(0.5)

            dexscan_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, DEXSCAN_BUTTON)))
            driver.execute_script("arguments[0].click();", dexscan_button)
            time.sleep(0.5)

            filters_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, FILTERS_BUTTON)))
            driver.execute_script("arguments[0].click();", filters_button)

            dexscan_filters_min_1_social_account_checkbox = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, DEXSCAN_FILTERS_MIN_1_SOCIAL_ACCOUNT_CHECKBOX)))
            driver.execute_script("arguments[0].click();", dexscan_filters_min_1_social_account_checkbox)

            dexscan_filters_min_liquidity_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, DEXSCAN_FILTERS_MIN_LIQUIDITY_INPUT)))
            dexscan_filters_min_liquidity_input.send_keys('10000')

            dexscan_filters_apply_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, DEXSCAN_FILTERS_APPLY_BUTTON)))
            driver.execute_script("arguments[0].click();", dexscan_filters_apply_button)
            time.sleep(2.5)
            projects = scrape_dexscan_project_rows_from_table(driver)

            return projects


    except Exception as e:
        print(f"Error in scrape_cmc_data: {e}")
        return []
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass