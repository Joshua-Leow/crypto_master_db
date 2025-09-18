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
    INFO_TABLE_KEYS, WEBSITE_LINK, SOCIALS_LINKS, INFO_SECTION_LINKS
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
        WEBSITE_LINK_TARGET = replace_string_at_index(INFO_SECTION_LINKS, -12, str(website+1))
        website = driver.find_element(By.CSS_SELECTOR, WEBSITE_LINK_TARGET).get_attribute('href')
    except Exception as e: print(f"Failed to get website\n{e}")
    try:
        SOCIAL_LINKS_TARGET = replace_string_at_index(INFO_SECTION_LINKS, -12, str(community+1))
        all_socials = driver.find_elements(By.CSS_SELECTOR, SOCIAL_LINKS_TARGET).get_attribute('href')
        # TODO: all socials mapping to socials dict (follow cmc)
    except Exception as e: print(f"Failed to get all_socials\n{e}")
    try:
        CHAIN_LINKS_TARGET = replace_string_at_index(INFO_SECTION_LINKS, -12, str(chains+1))
        chains = driver.find_elements(By.CSS_SELECTOR, CHAIN_LINKS_TARGET).get_attribute('href')
        # TODO: click more info, then get CHAINS_INFO_LINKS
    except Exception as e: print(f"Failed to get all_socials\n{e}")
    try:
        CATEGORIES_LINKS_TARGET = replace_string_at_index(INFO_SECTION_LINKS, -12, str(categories+1))
        categories = driver.find_elements(By.CSS_SELECTOR, CATEGORIES_LINKS_TARGET).get_attribute('href')
        # TODO: click more info, then get CATEGORIES_INFO_LINKS
    except Exception as e: print(f"Failed to get all_socials\n{e}")

    # TODO: return project Dict
    return website

def get_website(driver):
    website = ""
    try:
        info_table_keys_elements = driver.find_elements(By.CSS_SELECTOR, INFO_TABLE_KEYS)
        info_table_keys = [elem.text for elem in info_table_keys_elements]
        for i, key in enumerate(info_table_keys):
            if 'Website' in key:
                row = i
        WEBSITE_LINK_TARGET = replace_string_at_index(WEBSITE_LINK, -12, str(row+1))
        website = driver.find_element(By.CSS_SELECTOR, WEBSITE_LINK_TARGET)
        website = website.get_attribute('href')
    except Exception as e: print(f"Failed to get website\n{e}")
    # print(f"website is: {website}")
    return website

def get_socials(driver):
    socials = ""
    try:
        info_table_keys_elements = driver.find_elements(By.CSS_SELECTOR, INFO_TABLE_KEYS)
        info_table_keys = [elem.text for elem in info_table_keys_elements]
        for i, key in enumerate(info_table_keys):
            if 'Community' in key:
                row = i
        SOCIALS_LINKS_TARGET = replace_string_at_index(SOCIALS_LINKS, -12, str(row+1))
        socials = driver.find_elements(By.CSS_SELECTOR, SOCIALS_LINKS_TARGET).get_attribute('href')
    except Exception as e: print(f"Failed to get website\n{e}")
    # print(f"socials is: {socials}")
    return socials

def enrich_project_with_details(driver, project):
    """
    Enrich project data with additional details from project page.

    Args:
        driver: Selenium WebDriver instance
        project (dict): Project data dictionary

    Returns:
        dict: Enriched project data
    """
    #         name = get_coin_name(driver)
    #         symbol = get_coin_symbol(driver)
    #         mcap = get_mcap(driver)
    #         website = get_website(driver)
    #         twitter_link = get_x_link(driver)
    #         discord_link = get_discord_link(driver)
    #         tele_link = get_tele_link(driver)
    #         if GET_TELE_OWNER:
    #             tele_handle = get_tele_owner(tele_link)
    #         else: tele_handle = ''
    #         socials = ''
    #         if X_link:
    #             socials += 'twitter, '
    #         if tele_link:
    #             socials += 'tele, '
    #         status = 'Pending for reply'
    #         stage = "1st Reach Out"
    #         notes = get_notes(driver)
    #         tags = get_tags(driver)
    #         exchange, cex_exchange = get_exchange(driver)
    #         est_value = 30000
    #         predicted_probability = get_predicted_probability()
    #         contact = get_email(website)
    #         if contact:
    #             socials += 'email, '
    #         impt = get_important(driver)

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
            website = get_website(driver)
            if not isinstance(project.get("socials"), dict):
                project["socials"] = {}
            project["socials"].update({"website": website})
        except Exception as e:
            print(f"Missing website via Selenium for {project.get('project_name', 'Unknown')}")

        # try:
        #     exchanges = extract_exchanges(driver)
        #     if exchanges: project["exchanges"] = exchanges
        # except Exception as e:
        #     print(f"Missing exchanges via Selenium for {project.get('project_name', 'Unknown')}")

        try:
            # extract social links
            all_links = get_socials(driver)
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

    except Exception as e:
        print(f"Error connecting Selenium driver for {project.get('project_name', 'Unknown')}: {e}")

    return project



# import re
# import os
# import time
# from typing import List, Tuple, Optional
# from datetime import datetime, timedelta
# from bs4 import BeautifulSoup
# import requests
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options
# from webdriver_manager.chrome import ChromeDriverManager
#
# from config import MAX_ROWS, GET_TELE_OWNER
# from desktop_automation import get_tele_owner
# from scraper.pages_cg import *
#
# def replace_str_index(text,index=0,replacement=''):
#     return f'{text[:index]}{replacement}{text[index+1:]}'
#
# def read_last_hyperlink_cg():
#     script_dir = os.path.dirname(__file__)
#     rel_path = "../data/last_hyperlink_cg.txt"
#     abs_file_path = os.path.join(script_dir, rel_path)
#
#     # Read the last hyperlink if the file exists
#     last_hyperlink = None
#     try:
#         with open(abs_file_path, "r") as file:
#             last_hyperlink = file.read().strip()
#             print(f"Current link in last_hyperlink.txt is: {last_hyperlink}")
#     except Exception as e:
#         print(f"Failed to locate last_hyperlink.txt file in path: [{abs_file_path}]")
#         print(e)
#     return last_hyperlink
#
# def read_CG_table():
#     script_dir = os.path.dirname(__file__)
#     rel_path = "../data/cg_table/CG_table.txt"
#     abs_file_path = os.path.join(script_dir, rel_path)
#
#     # Read the last hyperlink if the file exists
#     cg_table = None
#     try:
#         with open(abs_file_path, "r") as file:
#             cg_table = file.read().strip()
#             # print(f"cg_table in cg_table.txt is: {cg_table[:100]}")
#     except Exception as e:
#         print(f"Failed to locate cg_table.txt file in path: [{abs_file_path}]")
#         print(e)
#     return cg_table
#
# def get_time(table, i):
#     time_selector = f"tr:nth-child({i}) > td:nth-child(11)"
#     time_text = table.select_one(time_selector).text
#     ini_time_for_now = datetime.now() - timedelta(minutes=i)
#     time, num = None, None
#     time_text_list = time_text.split()
#     for time_text in time_text_list:
#         try:
#             num = int(time_text)
#             break
#         except:
#             pass
#     try:
#         if time_text_list[-1] == 'minutes' or time_text_list[-1] == 'minute':
#             time = ini_time_for_now - timedelta(minutes=num)
#         elif time_text_list[-1] == 'hours' or time_text_list[-1] == 'hour':
#             time = ini_time_for_now - timedelta(hours=num)
#         elif time_text_list[-1] == 'days' or time_text_list[-1] == 'day':
#             time = ini_time_for_now - timedelta(days=num)
#         time = time.strftime("%Y-%m-%d %H:%M")
#     except Exception as e:
#         print(f"Failed to get time. time_text is: {time_text}")
#         print(e)
#     return time
#
# def get_link(table, i, last_hyperlink):
#     link_selector = f"tr:nth-child({i}) > td:nth-child(3) > a"
#     link_tag = table.select_one(link_selector)
#     hyperlink = None
#     try:
#         hyperlink = link_tag["href"]
#     except Exception as e:
#         print(f"Failed to get link tag href hyperlink. link_tag is: {link_tag}")
#         print(e)
#     if hyperlink == last_hyperlink:
#         return hyperlink  # Stop if the hyperlink matches last_hyperlink_cmc.txt
#
#     return hyperlink
#
# def get_hyperlinks_time_cg() -> Tuple[List[Tuple[str, str]], Optional[str]]:
#     """
#     Retrieves new cryptocurrency listing URLs and their timestamps.
#
#     Returns:
#         Tuple containing:
#         - List of tuples (hyperlink, timestamp)
#         - First hyperlink found (for progress tracking)
#
#     Raises:
#         requests.exceptions.RequestException: For network-related errors
#         ValueError: If required elements aren't found
#     """
#
#     hyperlinks_time, first_hyperlink = [], None
#     CG_table = read_CG_table()
#     last_hyperlink = read_last_hyperlink_cg()
#     max_rows = MAX_ROWS if last_hyperlink else 1  # Limit rows based on the file existence
#     if max_rows > 50: max_rows = 50
#
#     # Fetch the webpage
#     soup = BeautifulSoup(CG_table, "html.parser")
#     # Locate the table
#     table_selector = "table > tbody"
#     table = soup.select_one(table_selector)
#     if not table: raise ValueError("Table not found on the webpage")
#
#     for i in range(1, max_rows + 1):
#         hyperlink = get_link(table, i, last_hyperlink)
#         time = get_time(table, i)
#         if i == 1:
#             first_hyperlink = hyperlink
#         if hyperlink == last_hyperlink:
#             break
#         hyperlinks_time.append((hyperlink,time))
#         print(f"Row {i} hyperlink is: {hyperlink}")
#         print(f"      time is: {time}")
#
#     return hyperlinks_time, first_hyperlink
#
# def get_coin_name(driver):
#     coin_name = ""
#     try:
#         coin_name = driver.find_element(By.CSS_SELECTOR, COIN_NAME_TEXT).text
#     except Exception as e:
#         print(f"Failed at get_coin_name function. COIN_NAME_TEXT not found.")
#     # print(f"coin_name is: {coin_name}")
#     return coin_name
#
# def get_coin_symbol(driver):
#     coin_symbol = ""
#     try:
#         coin_symbol = driver.find_element(By.CSS_SELECTOR, COIN_SYMBOL_TEXT).text
#         if coin_symbol[-6:] == ' Price':
#             coin_symbol = coin_symbol[:-6]
#     except Exception as e:
#         print(f"Failed at get_coin_symbol function. COIN_SYMBOL_TEXT not found.")
#     # print(f"coin_symbol is: {coin_symbol}")
#     return coin_symbol
#
# def get_mcap(driver):
#     mcap = ""
#     try:
#         mcap = driver.find_element(By.CSS_SELECTOR, MARKET_CAP_TEXT).text
#     except Exception as e:
#         print(f"Failed at get_mcap function. MARKET_CAP_TEXT not found.")
#     # print(f"mcap is: {mcap}")
#     return mcap
#
# def get_tags(driver):
#     tags_str = ""
#     try:
#         info_table_keys_elements = driver.find_elements(By.CSS_SELECTOR, INFO_TABLE_KEYS)
#         info_table_keys = [elem.text for elem in info_table_keys_elements]
#         for i, key in enumerate(info_table_keys):
#             if 'Categories' in key:
#                 row = i
#         TAGS_TARGET = replace_str_index(TAGS, 54, str(row+1))
#         tags_elements = driver.find_elements(By.CSS_SELECTOR, TAGS_TARGET)
#         tags = [elem.text for elem in tags_elements]
#         for i, tag in enumerate(tags):
#             if 'Suggest a Category' in tag:
#                 tags.pop(i)
#         tags_str = ", ".join(tags)
#     except Exception as e: print(f"Failed at get_tags function.\n{e}")
#     # print(f'tags_str is: {tags_str}')
#     return tags_str
#
# def extract_percentage(item):
#     match = re.search(r"\[(\d+\.?\d*)%]", item)  # Regex to extract percentage
#     return float(match.group(1)) if match else -1  # Return -1 for items without percentage
#
# def deduplicate_and_sort(exchange_data):
#     highest_percentages = {}
#     for item in exchange_data:
#         match = re.search(r"(.+?) \[(\d+\.?\d*)%]", item)  # Extract exchange name and percentage
#         if match:
#             exchange_name = match.group(1).strip()
#             percentage = float(match.group(2))
#             # Keep the highest percentage for each exchange
#             if exchange_name not in highest_percentages or percentage > highest_percentages[exchange_name]:
#                 highest_percentages[exchange_name] = percentage
#     # Reconstruct the list and sort it
#     sorted_exchanges = sorted(
#         [f"{name} [{percentage:.2f}%]" for name, percentage in highest_percentages.items()],
#         key=extract_percentage,
#         reverse=True
#     )
#     return sorted_exchanges
#
# def get_exchange(driver):
#     exchanges_str, cex_exchanges_str=None,None
#     try:
#         time.sleep(3)
#         market_rows_elements = driver.find_elements(By.CSS_SELECTOR, MARKETS_TABLE)
#         exchange_data, cex_exchange_data=[],[]
#         for row in market_rows_elements:
#             exchange = row.find_element(By.CSS_SELECTOR, EXCHANGE_TEXT).text
#             dex_cex = row.find_element(By.CSS_SELECTOR, DEX_CEX_TEXT).text
#             vol_perc = row.find_element(By.CSS_SELECTOR, VOL_PERC_TEXT).text
#             # print(f"exchange is {exchange}, dex_cex is {dex_cex}, vol_perc is {vol_perc}")
#             exchange_data.append(exchange+' ['+vol_perc+']')
#             if dex_cex == 'CEX':
#                 cex_exchange_data.append(exchange+' ['+vol_perc+']')
#         sorted_exchanges = deduplicate_and_sort(sorted(list(set(exchange_data)), key=extract_percentage, reverse=True))
#         sorted_cex_exchanges = deduplicate_and_sort(sorted(list(set(cex_exchange_data)), key=extract_percentage, reverse=True))
#         exchanges_str = ", ".join(sorted_exchanges)
#         cex_exchanges_str = ", ".join(sorted_cex_exchanges)
#     except Exception as e: print(f"Failed at get_exchange function.\n{e}")
#     # print(f'exchanges_str is: {exchanges_str}\ncex_exchanges_str is: {cex_exchanges_str}')
#     return exchanges_str, cex_exchanges_str
#
# def get_notes(driver):
#     about_text = ''
#     try:
#         about_more_button = driver.find_element(By.CSS_SELECTOR, ABOUT_MORE_BUTTON)
#         driver.execute_script("arguments[0].scrollIntoView();", about_more_button)
#         driver.execute_script("arguments[0].click();", about_more_button)
#         about_text = driver.find_element(By.CSS_SELECTOR, ABOUT_TEXT).text.strip()
#     except Exception as e:
#         print(e)
#
#     # print(f"about_text is: {about_text}")
#     return about_text[:4500]
#
# def get_website(driver):
#     website = ""
#     try:
#         info_table_keys_elements = driver.find_elements(By.CSS_SELECTOR, INFO_TABLE_KEYS)
#         info_table_keys = [elem.text for elem in info_table_keys_elements]
#         for i, key in enumerate(info_table_keys):
#             if 'Website' in key:
#                 row = i
#         WEBSITE_LINK_TARGET = replace_str_index(WEBSITE_LINK, -12, str(row+1))
#         website = driver.find_element(By.CSS_SELECTOR, WEBSITE_LINK_TARGET)
#         website = website.get_attribute('href')
#     except Exception as e: print(f"Failed to get website\n{e}")
#     # print(f"website is: {website}")
#     return website
#
# def get_x_link(driver):
#     twitter_link = ""
#     try:
#         social_elements = driver.find_elements(By.CSS_SELECTOR, SOCIALS_LINKS)
#         social_links = [elem.get_attribute('href') for elem in social_elements]
#         for link in social_links:
#             if 'twitter.com' in link:
#                 print(f"Twitter link: {link}")
#                 twitter_link = link
#         if not twitter_link: return None
#     except Exception as e:
#         print(f"Failed at X link function.\n{e}")
#     # print(f'twitter_link is: {twitter_link}')
#     return twitter_link
#
# def get_tele_link(driver):
#     tele_link = ""
#     try:
#         social_elements = driver.find_elements(By.CSS_SELECTOR, SOCIALS_LINKS)
#         social_links = [elem.get_attribute('href') for elem in social_elements]
#         for link in social_links:
#             print(link)
#             if 't.me' in link:
#                 tele_link = link
#         if len(social_links) > 0 and tele_link is None:
#             tele_link = social_links[0]
#     except Exception as e:
#         print(f"Failed at get_tele_link function.\n{e}")
#     # print(f'tele_link is: {tele_link}')
#     return tele_link
#
# def get_discord_link(driver):
#     discord_link = ""
#     try:
#         social_elements = driver.find_elements(By.CSS_SELECTOR, SOCIALS_LINKS)
#         social_links = [elem.get_attribute('href') for elem in social_elements]
#         for link in social_links:
#             print(link)
#             if 'discord' in link:
#                 discord_link = link
#         if len(social_links) > 0 and discord_link is None:
#             discord_link = social_links[0]
#     except Exception as e:
#         print(f"Failed at get_discord_link function.\n{e}")
#     # print(f'discord_link is: {discord_link}')
#     return discord_link
#
# def get_email(website):
#     """
#         Extracts all email addresses from BeautifulSoup.
#
#         :param website: URL of website to scrape
#         :return: List of unique email addresses
#     """
#     emails_str = ''
#     try:
#         if not website:
#             print("website empty")
#             return None
#         # driver.get(url)
#         url = website
#         if "http" not in url:
#             url = "https://" + url
#         print(f"  Navigating to: {url} to get email")
#         response = requests.get(url, verify=False)
#         response.raise_for_status()
#         soup = BeautifulSoup(response.text, "html.parser")
#
#         # Regular expression pattern to match email addresses
#         # email_pattern = "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
#         # emails = re.findall(email_pattern, text)
#         # unique_emails = list(set(emails))
#         # emails_str = ", ".join(unique_emails)
#
#         # Regular expression pattern to match email addresses
#         email_pattern = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
#
#         # Find all tags that contain text
#         matching_tags = []
#         for tag in soup.find_all(limit=500):  # Get all HTML tags
#             if tag.string and email_pattern.search(tag.string) and len(str(tag)) < 50:  # Check if the tag contains an email
#                 matching_tags.append(tag.string.strip())
#                 if len(matching_tags) > 10:
#                     break
#         if not matching_tags:
#             return None
#         emails_str = ", ".join(matching_tags)
#         print(f"Email is: {emails_str}")
#     except Exception as e:
#         print(f"Failed at email function.\n{e}")
#     # print(emails_str)
#     return emails_str
#
# def get_predicted_probability():
#     return 0.50
#
# def get_important(driver):
#     impt = ""
#     try:
#         impt = driver.find_element(By.CSS_SELECTOR, IMPORTANT_TEXT).text
#     except: pass
#     # print(f"impt is: {impt}")
#     return impt
#
# def get_data_from_hyperlink_cg(base_url: str, hyperlink: str) -> List[str]:
#     """
#     Extracts detailed information about a cryptocurrency from its listing page.
#
#     Args:
#         base_url (str): Base URL of the cryptocurrency platform
#         hyperlink (str): Specific URL path for the cryptocurrency
#
#     Returns:
#         List containing extracted data in the following order:
#         [name, market_cap, tags, exchanges, cex_exchanges, stage, value,
#          contact, probability, website, social_link, description, source]
#
#     Raises:
#         selenium.common.exceptions.WebDriverException: For browser automation errors
#         ValueError: If required data cannot be extracted
#     """
#     # Use the Service and ChromeDriverManager class to use correct chromedriver version
#     service = Service(ChromeDriverManager().install())
#     options = Options()
#     options.add_argument('--disable-blink-features=AutomationControlled')
#     driver = webdriver.Chrome(service=service, options=options)
#     name ,mcap, tags, exchange, cex_exchange, website, X_link, notes, source = "", "", "", "", "", "", "", "", ""
#     try:
#         url = base_url + hyperlink
#         driver.get(url)
#         source = url
#         print(f"  Navigated to: {url}")
#     except Exception as e:
#         print(f"Failed to navigate to {base_url+hyperlink}\n{e}")
#     try:
#         name = get_coin_name(driver)
#         symbol = get_coin_symbol(driver)
#         mcap = get_mcap(driver)
#         website = get_website(driver)
#         twitter_link = get_x_link(driver)
#         discord_link = get_discord_link(driver)
#         tele_link = get_tele_link(driver)
#         if GET_TELE_OWNER:
#             tele_handle = get_tele_owner(tele_link)
#         else: tele_handle = ''
#         socials = ''
#         if X_link:
#             socials += 'twitter, '
#         if tele_link:
#             socials += 'tele, '
#         status = 'Pending for reply'
#         stage = "1st Reach Out"
#         notes = get_notes(driver)
#         tags = get_tags(driver)
#         exchange, cex_exchange = get_exchange(driver)
#         est_value = 30000
#         predicted_probability = get_predicted_probability()
#         contact = get_email(website)
#         if contact:
#             socials += 'email, '
#         impt = get_important(driver)
#
#         result = [
#             name,
#             symbol,
#             # date goes here
#             '', # "Morning/Afternoon"
#             'cg',
#             socials,
#             status,
#             stage,
#             website,
#             contact,
#             tele_link,
#             twitter_link,
#             discord_link,
#             tags,
#             exchange,
#             cex_exchange,
#             mcap,
#             notes,
#             source,
#             impt
#         ]
#
#         daily_tracker_result = [
#             name,
#             # date goes here
#             '', #Time
#             'cg', #Source/Website
#             # contacts, # Telegram/Email
#             status,
#             stage,
#             # Project Replied date
#             # Appointment
#             # Appointment Date
#             # Appoinment with Who
#             # Project's comment
#             # BD's Comment
#             # Support needed
#         ]
#     finally:
#         driver.quit()
#
#     return result
