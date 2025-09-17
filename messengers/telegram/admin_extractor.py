# core/messengers/telegram/admin_extractor.py
"""
Telegram admin extraction functions.
"""
import time
from telebot.apihelper import ApiTelegramException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException

from messengers.pages.tele_pages import *
from messengers.telegram.tele_sender import _reset_to_telegram_main
from utils.local_state_manager import set_local_account_last_join, allocation_account


def handle_telegram_channel(driver, channel, chrome_profile):
    """
    Handle Telegram channel verification and extract group admin details.

    Args:
        driver: Selenium WebDriver instance
        channel (str): Channel username (e.g., '@channelname')
        chrome_profile (str): Chrome profile in use (e.g., 'telegram_1')

    Returns:
        list: Extracted admin data
    """
    def scroll_to_bottom(max_attempts=20):
        """Scrolls to bottom of group info until all content is loaded."""
        last_count = -1
        for attempt in range(max_attempts):
            items = driver.find_elements(By.XPATH, GROUP_INFO_SCROLL_SECTION)
            if len(items) == last_count:
                print("All Telegram users in group info loaded successfully")
                break
            driver.execute_script("arguments[0].scrollIntoView();", items[-1])
            last_count = len(items)
            print(f"[{attempt + 1}] Loaded {last_count} items")
            time.sleep(0.3)

    def extract_name(a):
        for xpath in [TARGET_A_TAG_NAME_TEXT_1, TARGET_A_TAG_NAME_TEXT_2]:
            try: return a.find_element(By.XPATH, xpath).text.strip()
            except: pass
        return "Unknown Name"

    def extract_role(a):
        for xpath in [TARGET_A_TAG_ROLE_TEXT_1, TARGET_A_TAG_ROLE_TEXT_2]:
            try: return a.find_element(By.XPATH, xpath).text.strip()
            except: pass
        return "Unknown Role"

    def extract_group_members():
        """Extract name, role, username of group members."""
        scroll_to_bottom()
        admin_list = []
        a_tags = driver.find_elements(By.XPATH, TARGET_ADMIN_A_TAG)
        print(f"Found {len(a_tags)} admins in group. Extracting info...\n")

        for i, a in enumerate(a_tags):
            try:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", a)
                time.sleep(0.3)

                driver.implicitly_wait(0)
                name, role = extract_name(a), extract_role(a)
                print(f"→ {i + 1}. Name: {name}, Role: {role}")
                driver.implicitly_wait(10)

                admin = {"first_name": name}

                role_l = role.lower().strip()
                if "owner" in role_l:
                    admin["status"] = "owner"
                elif "admin" in role_l:
                    admin["status"] = "admin"
                else:
                    admin["status"] = "admin"
                    admin["role_title"] = role.strip()

                try:
                    ActionChains(driver).move_to_element(a).click().perform()
                    time.sleep(0.5)

                    username = driver.current_url[39:]
                    if username and username.isdigit():
                        time.sleep(0.5)
                        username = driver.current_url[39:]
                    if username and not username.isdigit():
                        admin['username'] = username
                        print(f"     Username: {username}")
                    else:
                        print(f"{name} has invalid username: {username}")
                except Exception as err:
                    print(f"Username fetch failed: {err}")

                admin_list.append(admin)

            except Exception as err:
                print(f"Error processing user {i}: {err}")
            finally:
                ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                time.sleep(1)

        return admin_list

    # Begin handling
    account_name = allocation_account(chrome_profile) # (e.g., 'account_1')
    account_num = account_name[-1]
    print(f"Opening Telegram channel: {channel} with account {account_num}")
    driver.get(f"https://web.telegram.org/k/?account={account_num}#{channel}")
    time.sleep(5)

    try:
        group_info_section = WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.XPATH, OPEN_GROUP_INFO_SECTION))
        )
        ActionChains(driver).move_to_element(group_info_section).click().perform()
        print("Clicked on group info section, opening members list...")
        time.sleep(2)
    except: pass

    try:
        # 1. Tap on "Tap to verify" button in project channel
        tap_to_verify_button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, TAP_TO_VERIFY_BUTTON))
        )
        ActionChains(driver).move_to_element(tap_to_verify_button).pause(0.5).click().perform()
        print(f'clicked "Tap to verify" button in project channel {channel}. Navigating to SafeGuard...')
        time.sleep(2)

        try:
            # Tap on "LAUNCH" button to navigate to SafeGuard page
            launch_safeguard_popup = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, LAUNCH_SAFEGUARD_POPUP))
            )
            ActionChains(driver).move_to_element(launch_safeguard_popup).click().perform()
            print(f'clicked "LAUNCH" button in {channel}. Navigating to SafeGuard page...')
            time.sleep(4)
        except:
            pass

        # 2. Tap on "VERIFY" button in SafeGuard page, to open portal
        safeguard_verify_portal_link = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, SAFEGUARD_VERIFY_PORTAL_LINK))
        )
        ActionChains(driver).move_to_element(safeguard_verify_portal_link).pause(0.5).click().perform()
        print(f'clicked "VERIFY" button in SafeGuard for {channel}, Opening portal...')
        time.sleep(1)

        try:
            # Tap on "LAUNCH" button to open portal
            launch_safeguard_browser = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, LAUNCH_SAFEGUARD_BROWSER))
            )
            ActionChains(driver).move_to_element(launch_safeguard_browser).pause(0.5).click().perform()
            print(f'clicked "LAUNCH" button for {channel}. Opening portal...')
            time.sleep(2)
        except:
            pass

        # 3. Switch to the iframe
        iframe = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, SAFEGUARD_BROWSER_IFRAME))
        )
        driver.switch_to.frame(iframe)
        print('→ Switched to iframe')

        # 4. Tap on "Click Here" Verify button
        safeguard_browser_click_here_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, SAFEGUARD_BROWSER_CLICK_HERE_BUTTON))
        )
        ActionChains(driver).move_to_element(safeguard_browser_click_here_button).click().perform()
        print(f'clicked "CLICK HERE" button in portal to verify human for {channel}. Generating one-time group link...')
        time.sleep(3)

        # 5. Switch back to main frame
        driver.switch_to.default_content()
        print('→ Switched back to mainframe')

        # 6. Tap on one-time private group link
        safeguard_one_time_group_link = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, SAFEGUARD_ONE_TIME_GROUP_LINK))
        )
        ActionChains(driver).move_to_element(safeguard_one_time_group_link).click().perform()
        print(f'clicked on one-time group link for {channel}. Entering private group...')
        time.sleep(1)

        try:
            # 7. Tap on JOIN GROUP button
            join_group_button = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, JOIN_GROUP_BUTTON))
            )
            ActionChains(driver).move_to_element(join_group_button).pause(0.3).click().perform()
            print(f'clicked on "JOIN GROUP" button for {channel}. Entering private group...')
            time.sleep(2)
        except:
            pass

        try:
            joined_group = driver.find_elements(By.XPATH, GROUP_INFO_SCROLL_SECTION)
        except Exception as e:
            print(f"❌ Failed to join {channel}. Banned:\n{e}")
            return []

        print('setting account last join time')
        set_local_account_last_join(chrome_profile, account_name) # set last_join time to now

        admins_list = extract_group_members()
        print(f"========== Admins of channel: {channel} ==========")
        for admin in admins_list:
            print(f"Name: {admin.get('first_name')}, Role: {admin.get('role_title')}, Username: {admin.get('username', '-')}")

        _reset_to_telegram_main(driver)
        time.sleep(1)
        return admins_list

    except Exception as e:
        print(f"Failed to process {channel}:\n{e}")
        _reset_to_telegram_main(driver)
        return []


def handle_telegram_supergroup(channel, bot, max_retries):
    """
    Placeholder function to handle Telegram Supergroups.
    Replace with your actual function for processing channels.

    Args:
        channel (str): Supergroup username (e.g., '@channelname')
        bot: Telegram bot instance
        max_retries (int): Max number of retries

    Returns:
        Any: Replace with the appropriate return type for your use case
    """
    print(f"Handling Telegram supergroup: {channel}")
    print(f"Handling Telegram supergroup: {channel}")
    # Proceed with admin extraction for public supergroups
    attempt = 0
    while attempt < max_retries:
        try:
            print(f"Attempt {attempt + 1}: Getting admins for {channel}")
            administrators = bot.get_chat_administrators(channel)
            print(f"Found {len(administrators)} administrators in {channel}")
            print(f"Found {len(administrators)} administrators in {channel}")

            admin_list = []
            for admin in administrators:
                admin_info = {}
                user = admin.user

                print(user.username, '→', admin.custom_title, '→', admin.status)
                print(f"{user.username} → {admin.custom_title} → {admin.status}")

                if user.username: admin_info['username'] = user.username
                if user.first_name: admin_info['first_name'] = user.first_name
                if user.last_name: admin_info['last_name'] = user.last_name
                if admin.custom_title: admin_info['role_title'] = admin.custom_title
                admin_info['status'] = 'owner' if admin.status == 'creator' else 'admin'

                admin_list.append(admin_info)

            return admin_list

        except ApiTelegramException as e:
            print(f"Telegram API Error (attempt {attempt + 1}): {e}")
            print(f"Telegram API Error (attempt {attempt + 1}): {e}")
            if 'Error code: 429. Description: Too Many Requests' in str(e):
                cooldown_timer = int(str(e)[-2:]) if str(e)[-2:].isdigit() else 5
                print(f"Waiting {cooldown_timer + 1} seconds before retrying...")
                print(f"Waiting {cooldown_timer + 1} seconds before retrying...")
                time.sleep(cooldown_timer + 1)
                max_retries += 1
            elif 'chat not found' in str(e).lower() or 'user not found' in str(e).lower():
                print(f"Chat {channel} not accessible")
                print(f"Chat {channel} not accessible")
                return None

            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5
                print(f"Waiting {wait_time} seconds before retry...")
                print(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                print(f"Failed to get admins for {channel} after {max_retries} attempts")
                print(f"Failed to get admins for {channel} after {max_retries} attempts")
                return None
        except Exception as e:
            print(f"General Error in admin extraction: {e}")
            print(f"General Error in admin extraction: {e}")
            return None

        attempt += 1

    return None


def get_telegram_channel_admins_chat_type_router(chrome_profile, driver, channel, bot, max_retries=1):
    """
    Get Telegram channel administrators or handle channels/users based on chat type.

    Args:
        self: Object Instance
        driver: Web driver for telegram automation
        channel (str): Channel or group username (e.g., '@channelname')
        bot: Telegram bot instance
        max_retries (int): Maximum retry attempts for API calls

    Returns:
        list: List of admin dictionaries for supergroups, None for users, groups, or errors
              For channels, returns the result of handle_telegram_channel
    """
    if not channel:
        return None

    if channel[0] != '@':
        channel = '@' + channel

    # Check chat type
    try:
        chat = bot.get_chat(channel)
        chat_type = chat.type
        print(f"Chat type for {channel}: {chat_type}")
        time.sleep(1)

        # Handle different chat types
        if chat_type == 'supergroup':
            admin_list = handle_telegram_supergroup(channel, bot, max_retries)

        elif chat_type == 'channel':
            # Handle Telegram channel
            admin_list = handle_telegram_channel(driver, channel, chrome_profile)

        elif chat_type in ['private', 'group']:
            print(f"Chat {channel} is a {chat_type}, admin extraction not applicable")
            return None

        else:
            print(f"Unknown chat type {chat_type} for {channel}")
            return None

        # Sort admins (creator first, admins sorted alphabetically)
        if admin_list:
            admin_list = sorted(
                admin_list,
                key=lambda u: (
                    0 if u.get("status") == "owner" else 1,
                    0 if u.get("role_title") else 1,
                    u.get("role_title", "").lower()
                )
            )

        print(admin_list)
        return admin_list

    except Exception as e:
        print(f"General Error while checking chat type: {e}")
        return None

