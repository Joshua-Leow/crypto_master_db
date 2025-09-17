# core/scrapers/dextools/project_scraper.py
"""
DexTools project scraping functions.
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from scrapers.dextools.link_extractor import extract_social_link_from_element, categorize_social_link
from scrapers.pages.dextools_pages import *

from utils.text_utils import replace_string_at_index


def enrich_project_data(driver, project_dict):
    """
    Scrape social links for a specific project.

    Args:
        driver: Selenium WebDriver instance
        project_index (int): Index of the project (1-based)
        project_dict (dict): Dict of the project

    Returns:
        dict: Project data with social links
    """
    if project_dict.get('source_link', None):
        driver.get(project_dict['source_link'])
        # Extract project name, liquidity, market_cap if available
        try:
            project_dict["project_name"] = driver.find_element(By.XPATH, PROJECT_PAGE_PROJECT_NAME_TEXT).text
            project_dict["liquidity"] = driver.find_element(By.XPATH, PROJECT_PAGE_LIQUIDITY_TEXT).text
            project_dict["market_cap"] = driver.find_element(By.XPATH, PROJECT_PAGE_MARKET_CAP_TEXT).text
        except:
            pass


def scrape_project_data(driver, project_index):
    """
    Scrape social links for a specific project.

    Args:
        driver: Selenium WebDriver instance
        project_index (int): Index of the project (1-based)

    Returns:
        dict: Project data with social links
    """
    project_data = {
        "project_name": f"DexTools_Project_{project_index}",
    }

    try:
        # Find the project container using the correct selector
        PROJECT_SELECTOR = replace_string_at_index(PROJECT_SELECTOR__2, -2, str(project_index))
        project_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, PROJECT_SELECTOR))
        )

        # Find all social elements within this project
        try:
            driver.implicitly_wait(0)
            WebDriverWait(project_element, 0.1).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, PROJECT_CHILD_SOCIAL))
            )
            social_elements = project_element.find_elements(By.CSS_SELECTOR, PROJECT_CHILD_SOCIAL)
        except Exception as e:
            social_elements = []
        finally:
            driver.implicitly_wait(10)

        print(f"Found {len(social_elements)} social elements for project {project_index}")

        # Extract project source link
        try:
            project_source_link = project_element.find_element(By.CSS_SELECTOR, PROJECT_CHILD_SOURCE_LINK)
            source_link = project_source_link.get_attribute("href")
            project_data["sources"] = {"dextools": source_link,}
        except:
            pass

        # Extract project name and ticker if available
        try:
            project_ticker_name_element = project_element.find_element(By.CSS_SELECTOR, PROJECT_CHILD_TICKER_NAME)
            project_data["project_name"] = project_ticker_name_element.text.strip().split('\n')[-1]
            project_data["project_ticker"] = project_ticker_name_element.text.strip().split('\n')[0].upper()
        except:
            pass

        # Process each social element only once
        for social_index, social_element in enumerate(social_elements, 1):
            try:
                # Extract link from this social element
                link = extract_social_link_from_element(driver, social_element)
                if link:
                    link_field_map = {
                        'telegram': 'telegram_link',
                        'twitter': 'twitter_link',
                        'discord': 'discord_link',
                        'linkedin': 'linkedin_link',
                        'facebook': 'facebook_link',
                        'instagram': 'instagram_link',
                        'tiktok': 'tiktok_link',
                        'youtube': 'youtube_link',
                        'medium': 'medium_link',
                        'reddit': 'reddit_link',
                        'email': 'email_link',
                        'website': 'website',
                        'github': 'github_link',
                    }

                    # Categorize and store the link
                    category = categorize_social_link(link)
                    if category in link_field_map:
                        if link[:8] == 'mailto: ': link = link[8:]
                        # project_data[link_field_map[category]] = link
                        if not isinstance(project_data.get("socials"), dict):
                            project_data["socials"] = {}
                        project_data["socials"].update({link_field_map[category]: link})
            except Exception as e:
                print(f"Error processing social element {social_index} for project {project_index}: {str(e)}")
                continue

    except Exception as e:
        print(f"Error scraping project {project_index}: {str(e)}")

    return project_data