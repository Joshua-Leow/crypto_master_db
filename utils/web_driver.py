# core/utils/web_driver.py
"""
WebDriver utility functions.
"""
import time

from selenium.webdriver import Remote
import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def get_local_web_driver():
    """
    Creates and returns a Chrome WebDriver instance using a specific Chrome profile.

    Returns:
        webdriver.Chrome: Configured Chrome WebDriver
    """
    try:
        options = Options()
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-features=CalculateNativeWinOcclusion")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1200,1080")
        # options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                             "(KHTML, like Gecko) Chrome/125.0.6422.141 Safari/537.36") #required for X (Twitter)

        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(10)
        driver.implicitly_wait(int(10))

        return driver

    except Exception as e:
        print(f"Error creating WebDriver: {e}")
        raise

def get_local_headless_web_driver():
    """
    Creates and returns a headless Chrome WebDriver instance using a specific Chrome profile.

    Returns:
        webdriver.Chrome: Configured Chrome WebDriver
    """
    try:
        options = Options()
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-features=CalculateNativeWinOcclusion")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1200,1080")
        options.add_argument("--headless=new")
        # options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                             "(KHTML, like Gecko) Chrome/125.0.6422.141 Safari/537.36") #required for X (Twitter)

        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(20)
        driver.implicitly_wait(int(10))

        return driver

    except Exception as e:
        print(f"Error creating WebDriver: {e}")
        raise



def get_dedicated_local_web_driver(chrome_profile: str, retries: int = 2, delay: int = 5):
    """
    Create a Local Chrome WebDriver bound to a server-side Chrome profile directory.
    Creates and returns a Chrome WebDriver instance using a specific Chrome profile with retries.

    Args:
        chrome_profile (str): Chrome profile name (e.g., 'telegram_1')
        retries (int): Number of retry attempts
        delay (int): Delay between retries in seconds

    NOTE:
    - Do NOT create/mutate server-side paths from the client. The remote node
      (EC2) will use the provided --user-data-dir path.
    - options.binary_location is ignored for Remote; the node's Chrome is used.

    Returns:
        webdriver.Remote: Configured Chrome WebDriver

    Raises:
        Exception: If WebDriver creation fails after all retries
    """
    if not chrome_profile or "/" in chrome_profile:
        raise ValueError(f"Invalid chrome_profile: {chrome_profile}")

    for attempt in range(1, retries + 1):
        try:
            options = Options()
            options.add_argument("--disable-background-timer-throttling")
            options.add_argument("--disable-backgrounding-occluded-windows")
            options.add_argument("--disable-renderer-backgrounding")
            options.add_argument("--disable-features=CalculateNativeWinOcclusion")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--headless=new")  # Must Enable headless runs for remote EC2
            options.add_argument(
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/125.0.6422.141 Safari/537.36"
            )

            chrome_profile_path = f"/Users/chainreachai/selenium_chrome_profiles/{chrome_profile}"
            os.makedirs(chrome_profile_path, exist_ok=True)
            options.add_argument(f"--user-data-dir={chrome_profile_path}")

            GRID_HUB_URL = "http://localhost:4444/wd/hub"
            driver = Remote(command_executor=GRID_HUB_URL, options=options, keep_alive=True)
            driver.set_page_load_timeout(10)
            driver.implicitly_wait(int(10))
            print(f"[WebDriver] Created local driver for profile '{chrome_profile}'")
            return driver
        except Exception as e:
            print(f"[WebDriver] Attempt {attempt}/{retries} failed for profile '{chrome_profile}': {e}")
            if attempt < retries:
                time.sleep(delay)
            else:
                raise

# def get_remote_web_driver():
#     """
#     Creates and returns a Chrome WebDriver instance using a specific Chrome profile.
#
#     Returns:
#         webdriver.Chrome: Configured Chrome WebDriver
#     """
#     try:
#         options = Options()
#         options.add_argument("--disable-background-timer-throttling")
#         options.add_argument("--disable-backgrounding-occluded-windows")
#         options.add_argument("--disable-renderer-backgrounding")
#         options.add_argument("--disable-features=CalculateNativeWinOcclusion")
#         options.add_argument("--no-sandbox")
#         options.add_argument("--disable-dev-shm-usage")
#         options.add_argument("--disable-gpu")
#         options.add_argument("--window-size=1200,1080")
#         options.add_argument("--headless=new")  # Must Enable headless runs for remote EC2
#         # options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
#         options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
#                              "(KHTML, like Gecko) Chrome/125.0.6422.141 Safari/537.36") #required for X (Twitter)
#
#         server_ip = get_server_ip()
#         GRID_HUB_URL = f"{server_ip}/wd/hub"
#         driver = Remote(command_executor=GRID_HUB_URL, options=options, keep_alive=True)
#         driver.set_page_load_timeout(10)
#         driver.implicitly_wait(int(10))
#
#         return driver
#
#     except Exception as e:
#         print(f"Error creating WebDriver: {e}")
#         raise
#
#
# def get_dedicated_remote_web_driver(chrome_profile: str, retries: int = 2, delay: int = 5):
#     """
#     Create a Remote Chrome WebDriver bound to a server-side Chrome profile directory.
#     Creates and returns a Chrome WebDriver instance using a specific Chrome profile with retries.
#
#     Args:
#         chrome_profile (str): Chrome profile name (e.g., 'telegram_1')
#         retries (int): Number of retry attempts
#         delay (int): Delay between retries in seconds
#
#     NOTE:
#     - Do NOT create/mutate server-side paths from the client. The remote node
#       (EC2) will use the provided --user-data-dir path.
#     - options.binary_location is ignored for Remote; the node's Chrome is used.
#
#     Returns:
#         webdriver.Remote: Configured Chrome WebDriver
#
#     Raises:
#         Exception: If WebDriver creation fails after all retries
#     """
#     if not chrome_profile or "/" in chrome_profile:
#         raise ValueError(f"Invalid chrome_profile: {chrome_profile}")
#
#     for attempt in range(1, retries + 1):
#         try:
#             options = Options()
#             options.binary_location = "/usr/bin/google-chrome-stable"
#             # Stability flags
#             options.add_argument("--disable-background-timer-throttling")
#             options.add_argument("--disable-backgrounding-occluded-windows")
#             options.add_argument("--disable-renderer-backgrounding")
#             options.add_argument("--disable-features=CalculateNativeWinOcclusion")
#             options.add_argument("--no-sandbox")
#             options.add_argument("--disable-dev-shm-usage")
#             options.add_argument("--disable-gpu")
#             options.add_argument("--window-size=1920,1080")
#             options.add_argument("--password-store=basic")
#             options.add_argument("--use-mock-keychain")  # harmless on Linux; avoids surprises
#             options.add_argument("--disable-features=TrustTokens")
#             options.add_argument("--headless=new")  # Must Enable headless runs for remote EC2
#             options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
#                                  "(KHTML, like Gecko) Chrome/125.0.6422.141 Safari/537.36")  # required for X (Twitter)
#
#             REMOTE_PROFILE_ROOT = "/home/ubuntu/selenium_chrome_profiles"  # exists on EC2
#             remote_profile_path = f"{REMOTE_PROFILE_ROOT}/{chrome_profile}"
#             options.add_argument(f"--user-data-dir={remote_profile_path}")
#
#             server_ip = get_server_ip()
#             GRID_HUB_URL = f"{server_ip}/wd/hub"
#             driver = Remote(command_executor=GRID_HUB_URL, options=options, keep_alive=True)
#             driver.set_page_load_timeout(10)
#             driver.implicitly_wait(int(10))
#             print(f"[WebDriver] Created remote driver for profile '{chrome_profile}'")
#             return driver
#         except Exception as e:
#             print(f"[WebDriver] Attempt {attempt}/{retries} failed for profile '{chrome_profile}': {e}")
#             if attempt < retries:
#                 time.sleep(delay)
#             else:
#                 raise
