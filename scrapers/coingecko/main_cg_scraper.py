# scrapers/coingecko/main_cg_scraper.py
"""
CoinGecko scraper entrypoint placeholder.

This module defines the public scrape_coingecko_data(query) API expected by the router.
Per docs/plan.md, CoinGecko is not yet implemented; we raise a clear NotImplementedError
so callers can handle it gracefully.
"""
import time
import os
from pathlib import Path

from pynput.keyboard import Key
from pynput.mouse import Button
import pynput
import time
import pyautogui
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from MasterProjectManager import MasterProjectManager
from config.private import get_mongodb_uri
from messengers.pages.tele_pages import SEARCH_BOX
from messengers.telegram.admin_extractor import _reset_to_telegram_main
from scrapers.coingecko.cg_data_extractor import enrich_project_with_details
from scrapers.pages.coingecko_pages import *

from utils.project_enrichment import enrich_telegram_data, enrich_data_from_website
from utils.text_utils import replace_string_at_index
from utils.web_driver import get_dedicated_local_web_driver, get_local_web_driver, get_local_headless_web_driver


# def keyboard_1press(keyboard, key1):
#     keyboard.press(key1)
#     keyboard.release(key1)
#     time.sleep(1)
#
# def keyboard_2press(keyboard, key1, key2):
#     keyboard.press(key1)
#     if key2 is str:
#         keyboard.type(key2)
#     else:
#         keyboard.press(key2)
#         keyboard.release(key2)
#     keyboard.release(key1)
#     time.sleep(1)
#
# def keyboard_3press(keyboard, key1, key2, key3):
#     keyboard.press(key1)
#     keyboard.press(key2)
#     if key3 is str:
#         keyboard.type(key3)
#     else:
#         keyboard.press(key3)
#         keyboard.release(key3)
#     keyboard.release(key2)
#     keyboard.release(key1)
#     time.sleep(1)
#
#
# def click_image(mouse, image_path):
#     """
#     Search for an image and click if found.
#
#     :param mouse: pynput mouse controller
#     :param image_path: Path to the image to search on the screen.
#     """
#     try:
#         location = pyautogui.locateOnScreen(image_path)
#         if location:
#             print(f"Image found at {location}!")
#
#             # Move the mouse to the center of the found image
#             center_x = location.left/2 + location.width/4
#             center_y = location.top/2 + location.height/4
#             mouse.position = (center_x, center_y)
#             time.sleep(1)
#
#             mouse.click(Button.left, 1)
#             print(f"Clicked at ({center_x}, {center_y})")
#             time.sleep(1)
#             return True
#     except pyautogui.ImageNotFoundException as e:
#         return False
#
#
# def get_coingecko_table(page='new'):
#     keyboard = pynput.keyboard.Controller()
#
#     # Open Mac spotlight search
#     keyboard_2press(keyboard, Key.cmd, Key.space)
#     # go to chrome
#     keyboard.type("chrome")
#     time.sleep(2)
#     keyboard_1press(keyboard, Key.enter)
#     # open new tab
#     keyboard_2press(keyboard, Key.cmd, "t")
#     # go to https://www.coingecko.com/en/new-cryptocurrencies
#     if page != 'new':
#         link = "https://www.coingecko.com/?page=" + str(page)
#     else:
#         link = "coingecko.com/en/new-cryptocurrencies"
#     keyboard.type(link)
#     time.sleep(1)
#     keyboard_1press(keyboard, Key.enter)
#     time.sleep(5)
#     # open inspect tool
#     keyboard_1press(keyboard, Key.f12)
#     time.sleep(1)
#     # Click elements text
#     mouse = pynput.mouse.Controller()
#     elements_text = str(Path(os.path.join(os.getcwd(), "data/image_captures/elements_text.png")))
#     click_image(mouse, elements_text)
#     # ctrl + f to find in inspect
#     keyboard_2press(keyboard, Key.cmd, "f")
#     # search for <table>
#     keyboard.type("<table")
#     time.sleep(1)
#     # Edit as HTML (f2)
#     keyboard_1press(keyboard, Key.f2)
#     # ctrl + a to select all
#     keyboard_2press(keyboard, Key.cmd, "a")
#     # ctrl + c to select all
#     keyboard_2press(keyboard, Key.cmd, "c")
#     keyboard_2press(keyboard, Key.cmd, "c")
#     # ctrl + w to close tab
#     keyboard_2press(keyboard, Key.cmd, "w")
#     # Open Mac spotlight search
#     keyboard_2press(keyboard, Key.cmd, Key.space)
#     # go to finder
#     keyboard.type("finder")
#     time.sleep(2)
#     keyboard_1press(keyboard, Key.enter)
#     # cmd shift G in finder to search by path
#     keyboard_3press(keyboard, Key.cmd, Key.shift, "g")
#     # search for this path /Users/joshualeow/Desktop/
#     keyboard.type("/Users/joshualeow/Desktop/")
#     time.sleep(2)
#     keyboard_1press(keyboard, Key.enter)
#     # cmd shift G in finder to search by path
#     keyboard_3press(keyboard, Key.cmd, Key.shift, "g")
#     # search for this path /Users/joshualeow/Documents/Projects/scrape_CMC/data/
#     keyboard.type("/Users/joshualeow/Documents/Projects/scrape_CMC/data/cg_table/")
#     time.sleep(2)
#     keyboard_1press(keyboard, Key.enter)
#     # tab to select first item
#     keyboard_1press(keyboard, Key.tab)
#     # ctrl o to open in TextEdit
#     keyboard_2press(keyboard, Key.cmd, "o")
#     # ctrl a to select all
#     keyboard_2press(keyboard, Key.cmd, "a")
#     # ctrl v to paste
#     keyboard_2press(keyboard, Key.cmd, "v")
#     # ctrl s to save
#     keyboard_2press(keyboard, Key.cmd, "s")
#     # ctrl w to close TextEdit
#     keyboard_2press(keyboard, Key.cmd, "w")


def go_cg_to_page(driver, qpage, timeout=10):
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
            EC.presence_of_all_elements_located((By.XPATH, NAVIGATION_NUMBERS))
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


def get_project_links(driver):
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//table/tbody//tr[1]/td/a")))
    projects = []
    for i in range(1, 101):
        PROJECT_LINK = replace_string_at_index(PROJECT_LINK__7, -7, str(i))
        project_link = driver.find_element(By.XPATH, PROJECT_LINK).get_attribute("href")
        project = {"sources": {"coingecko": project_link}}
        projects.append(project)
    return projects


def handle_standard_cg_table(driver, chrome_profile, projects):
    if not projects:
        print("No projects found in table")

    print(f"Scraped {len(projects)} projects, enriching data...")
    driver2 = get_dedicated_local_web_driver(chrome_profile)
    _reset_to_telegram_main(driver2)
    # manager = MasterProjectManager(get_mongodb_uri())
    #
    try:
        enriched_projects = []
        # for i, project in enumerate(projects[70:]):   # for testing purposes
        for i, project in enumerate(projects):
            print(f"Enriching project {i + 1}/{len(projects)}: {project.get('sources', 'coingecko')}")
            enriched_project = enrich_project_with_details(driver, project)
            enriched_project.update(enrich_data_from_website(enriched_project))
            enriched_project.update(enrich_telegram_data(driver2, enriched_project, chrome_profile))
            print(enriched_project)

            if not enriched_project.get("project_name") or not enriched_project.get("project_ticker"):
                print(f"[ERROR] Project {project['sources']['coingecko']} not enriched...")
                continue
            enriched_projects.append(enriched_project)
            # project_uid = manager.upsert_project(enriched_project, "coingecko")
    finally:
        # driver2.quit()
        pass

    print(f"Successfully scraped {len(enriched_projects)} projects")
    return enriched_projects




def scrape_cg_page(page_num: int, chrome_profile: str, links=None):
    """Placeholder for CoinGecko scraping."""
    driver = get_local_headless_web_driver()
    # driver.get("https://coingecko.com")

    if links:
        projects = []
        for link in links:
            project = {"sources": {"coingecko": link}}
            projects.append(project)
    else:
        if page_num > 1:
            driver.get("https://coingecko.com/?page=" + str(page_num) + "")
            # go_cg_to_page(driver, page_num)
        else:
            driver.get("https://coingecko.com")
        time.sleep(1)
        projects = get_project_links(driver)

    handle_standard_cg_table(driver, chrome_profile, projects)
    driver.quit()
    time.sleep(1)
