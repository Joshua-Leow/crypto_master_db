from typing import Dict

from bs4 import BeautifulSoup
from telebot import TeleBot
import requests
import random
import re

from messengers.telegram.admin_extractor import get_telegram_channel_admins_chat_type_router
from utils.text_utils import get_telegram_group_from_link


def enrich_telegram_data(driver, project: Dict, chrome_profile) -> Dict:
    """
    Enrich project with Telegram admin data.

    Args:
        driver: Web driver for telegram automation
        project: Project data dictionary

    Returns:
        Dict: Enriched project data
    """
    try:
        telegram_link = project.get('socials', {}).get('telegram_link')
        if not telegram_link:
            return project

        tele_group = get_telegram_group_from_link(telegram_link)

        print(f"Getting Telegram admins for: {tele_group}")

        # Use a random bot instance per project
        from config.private import get_tele_bot_tokens
        bot_tokens = get_tele_bot_tokens()
        bot_info = None
        random_bot = None
        max_retries = len(bot_tokens)
        retry_count = 0

        while not bot_info and retry_count < max_retries:
            random_token = ""
            try:
                random_token = random.choice(bot_tokens)
                random_bot = TeleBot(random_token)
                bot_info = random_bot.get_me()  # Raises exception if invalid
                print(f"Using Telegram bot {bot_info.username}")
            except Exception as e:
                print(f"Bot token failed: {random_token[:10]}... – {e}")
                retry_count += 1
                continue

        if not bot_info:
            print(f"✗ All Telegram bots failed for {project.get('project_name', 'Unknown')}")
            return project

        # Get admin list using validated bot
        admin_list = get_telegram_channel_admins_chat_type_router(chrome_profile, driver, tele_group, random_bot)

        if admin_list:
            # Add admin data to project
            project['telegram_admins'] = admin_list
            print(f"✓ Added {len(admin_list)} Telegram admins for {project.get('project_name', 'Unknown')}")
        else:
            print(f"✗ No Telegram admins found for {project.get('project_name', 'Unknown')}")

    except Exception as e:
        print(f"Failed to get Telegram data for {project.get('project_name', 'Unknown')}: {e}")

    return project

def enrich_email_data(project: Dict) -> Dict:
    """
    Enrich project with email data by scraping website for email addresses.

    Args:
        project: Project data dictionary

    Returns:
        Dict: Enriched project data
    """
    try:
        # Check if we already have email data
        existing_email = project.get('socials', {}).get('email_link')
        if existing_email:
            print(f"✓ Email already exists for {project.get('project_name', 'Unknown')}: {existing_email}")
            return project

        # Get website URL to scrape for emails
        website = project.get('socials', {}).get('website')
        if not website:
            print(f"✗ No website found for {project.get('project_name', 'Unknown')} - cannot scrape emails")
            return project

        print(f"🔍 Scraping emails from website for {project.get('project_name', 'Unknown')}")

        # Extract emails using the provided logic
        emails = get_email_from_website(website)

        if emails:
            if ', ' in emails:
                project['socials']['email_links'] = emails
            else:
                project['socials']['email_link'] = emails
            print(f"✓ Found email(s) for {project.get('project_name', 'Unknown')}: {emails}")
        else:
            print(f"✗ No emails found for {project.get('project_name', 'Unknown')}")

    except Exception as e:
        print(f"Failed to enrich email data for {project.get('project_name', 'Unknown')}: {e}")

    return project

def get_email_from_website(website):
    """Extract emails including mailto links."""
    try:
        if not website:
            return None
        url = website if website.startswith("http") else "https://" + website
        headers = {'User-Agent': 'Mozilla/5.0'}

        try:
            response = requests.get(url, headers=headers, timeout=8, verify=True)
            response.raise_for_status()
        except (requests.exceptions.SSLError, requests.exceptions.ConnectionError):
            response = requests.get(url, headers=headers, timeout=8, verify=False)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        email_pattern = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

        matching_emails = set()

        # Scan only a subset of tags
        tags_to_check = soup.find_all(["a", "p", "span", "div"], limit=1000)

        for tag in tags_to_check:
            # Check mailto links
            if tag.name == "a" and tag.has_attr("href") and tag["href"].startswith("mailto:"):
                email = tag["href"][7:]
                matching_emails.add(email)

            # Check visible text
            if tag.string:
                for email in email_pattern.findall(tag.string):
                    matching_emails.add(email)

            if len(matching_emails) >= 10:
                break

        return ", ".join(matching_emails) if matching_emails else None

    except Exception as e:
        print(f"Failed to scrape emails from {website}: {e}")
        return None