# core/scrapers/dextools/link_extractor.py
"""
DexTools social link extraction functions.
"""
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException


def extract_social_link_from_element(driver, social_element):
    """
    Extract social link from a single social element by hovering once.

    Args:
        driver: Selenium WebDriver instance
        social_element: Web element to hover over

    Returns:
        str: Extracted link if found, None otherwise
    """
    try:
        wait = WebDriverWait(driver, 3)

        # Hover over the element
        ActionChains(driver).move_to_element(social_element).perform()

        # Wait for tooltip to appear
        tooltip = wait.until(EC.visibility_of_element_located((
            By.CSS_SELECTOR,
            "div.tippy-box[data-state='hidden'] > div.tippy-content[data-state='hidden'] > div"
        )))

        # Extract full text
        lines = tooltip.text.strip().splitlines()

        if lines:
            link = lines[-1].strip()
            return link

    except (TimeoutException, NoSuchElementException):
        # Tooltip didn't appear or element not found
        pass
    except Exception as e:
        print(f"Unexpected error extracting link: {str(e)}")

    return None


def categorize_social_link(link):
    """
    Categorize a social link based on its URL.

    Args:
        link (str): Social media link

    Returns:
        str: Category of the link ('telegram', 'twitter', 'discord', 'website', 'email', 'unknown')
    """
    if not link:
        return 'unknown'

    link_lower = link.lower()

    if 't.me' in link_lower or 'telegram' in link_lower:
        return 'telegram'
    elif 'twitter.com' in link_lower or 'x.com' in link_lower:
        return 'twitter'
    elif 'discord' in link_lower:
        return 'discord'
    elif 'mailto:' in link_lower:
        return 'email'
    elif 'facebook' in link_lower:
        return 'facebook'
    elif 'linkedin' in link_lower:
        return 'linkedin'
    elif 'tiktok' in link_lower:
        return 'tiktok'
    elif 'instagram' in link_lower:
        return 'instagram'
    elif 'youtube' in link_lower:
        return 'youtube'
    elif 'medium' in link_lower:
        return 'medium'
    elif 'reddit' in link_lower:
        return 'reddit'
    # TODO: improve method to get website by using "Web" text in popup
    elif link_lower.startswith(('http://', 'https://')):
        return 'website'
    else:
        return 'unknown'