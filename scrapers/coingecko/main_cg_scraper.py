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
from scrapers.pages.coingecko_pages import *

from utils.project_enrichment import enrich_telegram_data, enrich_email_data
from utils.web_driver import get_dedicated_local_web_driver, get_local_web_driver


def keyboard_1press(keyboard, key1):
    keyboard.press(key1)
    keyboard.release(key1)
    time.sleep(1)

def keyboard_2press(keyboard, key1, key2):
    keyboard.press(key1)
    if key2 is str:
        keyboard.type(key2)
    else:
        keyboard.press(key2)
        keyboard.release(key2)
    keyboard.release(key1)
    time.sleep(1)

def keyboard_3press(keyboard, key1, key2, key3):
    keyboard.press(key1)
    keyboard.press(key2)
    if key3 is str:
        keyboard.type(key3)
    else:
        keyboard.press(key3)
        keyboard.release(key3)
    keyboard.release(key2)
    keyboard.release(key1)
    time.sleep(1)


def click_image(mouse, image_path):
    """
    Search for an image and click if found.

    :param mouse: pynput mouse controller
    :param image_path: Path to the image to search on the screen.
    """
    try:
        location = pyautogui.locateOnScreen(image_path)
        if location:
            print(f"Image found at {location}!")

            # Move the mouse to the center of the found image
            center_x = location.left/2 + location.width/4
            center_y = location.top/2 + location.height/4
            mouse.position = (center_x, center_y)
            time.sleep(1)

            mouse.click(Button.left, 1)
            print(f"Clicked at ({center_x}, {center_y})")
            time.sleep(1)
            return True
    except pyautogui.ImageNotFoundException as e:
        return False


def get_coingecko_table(page='new'):
    keyboard = pynput.keyboard.Controller()

    # Open Mac spotlight search
    keyboard_2press(keyboard, Key.cmd, Key.space)
    # go to chrome
    keyboard.type("chrome")
    time.sleep(2)
    keyboard_1press(keyboard, Key.enter)
    # open new tab
    keyboard_2press(keyboard, Key.cmd, "t")
    # go to https://www.coingecko.com/en/new-cryptocurrencies
    if page != 'new':
        link = "https://www.coingecko.com/?page=" + str(page)
    else:
        link = "coingecko.com/en/new-cryptocurrencies"
    keyboard.type(link)
    time.sleep(1)
    keyboard_1press(keyboard, Key.enter)
    time.sleep(5)
    # open inspect tool
    keyboard_1press(keyboard, Key.f12)
    time.sleep(1)
    # Click elements text
    mouse = pynput.mouse.Controller()
    elements_text = str(Path(os.path.join(os.getcwd(), "data/image_captures/elements_text.png")))
    click_image(mouse, elements_text)
    # ctrl + f to find in inspect
    keyboard_2press(keyboard, Key.cmd, "f")
    # search for <table>
    keyboard.type("<table")
    time.sleep(1)
    # Edit as HTML (f2)
    keyboard_1press(keyboard, Key.f2)
    # ctrl + a to select all
    keyboard_2press(keyboard, Key.cmd, "a")
    # ctrl + c to select all
    keyboard_2press(keyboard, Key.cmd, "c")
    keyboard_2press(keyboard, Key.cmd, "c")
    # ctrl + w to close tab
    keyboard_2press(keyboard, Key.cmd, "w")
    # Open Mac spotlight search
    keyboard_2press(keyboard, Key.cmd, Key.space)
    # go to finder
    keyboard.type("finder")
    time.sleep(2)
    keyboard_1press(keyboard, Key.enter)
    # cmd shift G in finder to search by path
    keyboard_3press(keyboard, Key.cmd, Key.shift, "g")
    # search for this path /Users/joshualeow/Desktop/
    keyboard.type("/Users/joshualeow/Desktop/")
    time.sleep(2)
    keyboard_1press(keyboard, Key.enter)
    # cmd shift G in finder to search by path
    keyboard_3press(keyboard, Key.cmd, Key.shift, "g")
    # search for this path /Users/joshualeow/Documents/Projects/scrape_CMC/data/
    keyboard.type("/Users/joshualeow/Documents/Projects/scrape_CMC/data/cg_table/")
    time.sleep(2)
    keyboard_1press(keyboard, Key.enter)
    # tab to select first item
    keyboard_1press(keyboard, Key.tab)
    # ctrl o to open in TextEdit
    keyboard_2press(keyboard, Key.cmd, "o")
    # ctrl a to select all
    keyboard_2press(keyboard, Key.cmd, "a")
    # ctrl v to paste
    keyboard_2press(keyboard, Key.cmd, "v")
    # ctrl s to save
    keyboard_2press(keyboard, Key.cmd, "s")
    # ctrl w to close TextEdit
    keyboard_2press(keyboard, Key.cmd, "w")



def scrape_cg_page(page_num: int):
    """Placeholder for CoinGecko scraping."""
    driver = get_local_web_driver()
    driver.get(f"https://coingecko.com/?page={page_num}")
    time.sleep(10)

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//table/tbody//tr[1]/td/a")))
    # TODO: replace PROJECT_LINK__7 text and get all hyperlinks
    # driver.execute_script("arguments[0].click();", new_button)
    # time.sleep(0.5)

    # if page_num > 1:
    #     go_cg_to_page(driver, page_num)
    #
    # time.sleep(2.5)
    # projects = handle_standard_cmc_table(driver, chrome_profile)
    # driver.quit()
    # time.sleep(1)
    # print(projects)