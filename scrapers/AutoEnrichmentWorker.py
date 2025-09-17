# core/scrapers/AutoEnrichmentWorker.py
"""
Automatic data enrichment system that runs after scraping.
"""
import random
from typing import List, Dict
from PySide6.QtCore import QThread, Signal
from telebot import TeleBot
import re
import requests
from bs4 import BeautifulSoup
import urllib3
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from messengers.pages.tele_pages import SEARCH_BOX

from utils.selenium_grid_manager import set_profile_state, get_available_profiles, allocate_account
from utils.webdriver.web_driver import get_dedicated_remote_web_driver, get_dedicated_local_web_driver

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from config.private import get_tele_bot_tokens
from messengers.telegram.admin_extractor import get_telegram_channel_admins_chat_type_router
from utils.text_utils import get_telegram_group_from_link


class AutoEnrichmentWorker(QThread):
    """Worker thread for automatic data enrichment after scraping."""

    progress_updated = Signal(str)  # Progress message
    project_processed = Signal(int, int, str)  # current, total, project_name
    enrichment_completed = Signal(list)  # Enriched data
    error_occurred = Signal(str)  # Error message

    def __init__(self, projects_data: List[Dict], chrome_profile: str, parent=None):
        super().__init__(parent)
        self.projects_data = projects_data
        self.chrome_profile = chrome_profile
        self.bot_tokens = get_tele_bot_tokens()
        self.driver = None
        self._stop_requested = False

    def stop(self):
        """Gracefully stop the thread and clean up resources."""
        self._stop_requested = True
        if self.driver:
            try:
                self.driver.quit()
                self.print(f"WebDriver for profile {self.chrome_profile} closed")
            except Exception as e:
                self.print(f"Error closing WebDriver: {e}")
            finally:
                self.driver = None
        try:
            # set_profile_state(self.chrome_profile, False)
            self.print(f"Released Chrome profile {self.chrome_profile}")
        except Exception as e:
            self.print(f"Error releasing profile {self.chrome_profile}: {e}")

    def run(self):
        """Run all extraction processes automatically."""
        try:
            # set_profile_state(self.chrome_profile, True)
            self.progress_updated.emit("Starting automatic data extraction...")
            self.print(f"Starting {self.chrome_profile} chrome profile")

            account_name = allocate_account(self.chrome_profile)  # e.g. account_1
            account_num = account_name[-1]
            # self.driver = get_dedicated_remote_web_driver(self.chrome_profile)
            self.driver = get_dedicated_local_web_driver(self.chrome_profile)
            self.driver.get(f"https://web.telegram.org/k/?account={account_num}#@ChainReachAI")

            WebDriverWait(self.driver, 60).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, SEARCH_BOX))
            )
            self.print(f"Telegram Web login detected ({self.chrome_profile}, {account_name})")
            time.sleep(2)

            enriched_data = []
            for i, project in enumerate(self.projects_data):
                if self._stop_requested:
                    self.print("Stop requested, exiting enrichment loop")
                    break

                enriched_project = project.copy()
                enriched_project.update(self.enrich_telegram_data(self.driver, enriched_project))
                enriched_project.update(self.enrich_linkedin_data(enriched_project))
                enriched_project.update(self.enrich_twitter_data(enriched_project))
                enriched_project.update(self.enrich_email_data(enriched_project))
                enriched_data.append(enriched_project)

            if not self._stop_requested:
                self.enrichment_completed.emit(enriched_data)

        except Exception as e:
            self.print(f"Auto extraction failed: {e}")
            self.error_occurred.emit(f"Auto extraction failed: {str(e)}")
        finally:
            self.stop()  # Always release profile


    def enrich_telegram_data(self, driver, project: Dict) -> Dict:
        """
        Enrich project with Telegram admin data.

        Args:
            driver: Web driver for telegram automation
            project: Project data dictionary

        Returns:
            Dict: Enriched project data
        """
        try:
            telegram_link = project.get('telegram_link')
            if not telegram_link:
                return project

            tele_group = get_telegram_group_from_link(telegram_link)

            self.print(f"Getting Telegram admins for: {tele_group}")

            # Use a random bot instance per project
            bot_info = None
            random_bot = None
            max_retries = len(self.bot_tokens)
            retry_count = 0

            while not bot_info and retry_count < max_retries:
                random_token = ""
                try:
                    random_token = random.choice(self.bot_tokens)
                    random_bot = TeleBot(random_token)
                    bot_info = random_bot.get_me()  # Raises exception if invalid
                    print(f"Using Telegram bot {bot_info.username}")
                    self.print(f"Using Telegram bot {bot_info.username}")
                except Exception as e:
                    print(f"Bot token failed: {random_token[:10]}... – {e}")
                    self.print(f"Bot token failed: {random_token[:10]}... – {e}")
                    retry_count += 1
                    continue

            if not bot_info:
                print(f"✗ All Telegram bots failed for {project.get('project_name', 'Unknown')}")
                self.print(f"✗ All Telegram bots failed for {project.get('project_name', 'Unknown')}")
                return project

            # Get admin list using validated bot
            admin_list = get_telegram_channel_admins_chat_type_router(self.chrome_profile, driver, tele_group, random_bot)

            if admin_list:
                # Add admin data to project
                project['telegram_admins'] = admin_list
                self.print(f"✓ Added {len(admin_list)} Telegram admins for {project.get('project_name', 'Unknown')}")
            else:
                self.print(f"✗ No Telegram admins found for {project.get('project_name', 'Unknown')}")

        except Exception as e:
            print(f"Failed to get Telegram data for {project.get('project_name', 'Unknown')}: {e}")
            self.print(f"Failed to get Telegram data for {project.get('project_name', 'Unknown')}: {e}")

        return project

    def enrich_linkedin_data(self, project: Dict) -> Dict:
        """
        Enrich project with LinkedIn data (company pages, c-suite profiles).

        Args:
            project: Project data dictionary

        Returns:
            Dict: Enriched project data
        """
        try:
            linkedin_link = project.get('linkedin_link')
            # if not linkedin_link:
            #     # Try to search for LinkedIn based on project_name
            #     project_name = project.get('project_name', '').replace(' ', '-').lower()
            #     if project_name:
            #         # This is a placeholder - in real implementation, you'd use LinkedIn API or scraping
            #         potential_linkedin = f"https://linkedin.com/company/{project_name}"
            #         project['linkedin_potential_company'] = potential_linkedin
            #         print(f"✓ Generated potential LinkedIn URL for {project.get('project_name', 'Unknown')}")
            #     return project

            # If LinkedIn link exists, extract additional info
            # This is a placeholder for future LinkedIn enrichment
            # project['linkedin_enriched'] = True
            # project['linkedin_type'] = 'company' if '/company/' in linkedin_link else 'personal'

            # Placeholder for future implementation:
            # - Extract company size
            # - Get executive profiles
            # - Analyze company posts and engagement

            print(f"✓ LinkedIn data placeholder added for {project.get('project_name', 'Unknown')}")

        except Exception as e:
            print(f"Failed to enrich LinkedIn data for {project.get('project_name', 'Unknown')}: {e}")
            print(f"Failed to enrich LinkedIn data for {project.get('project_name', 'Unknown')}: {e}")

        return project

    def enrich_twitter_data(self, project: Dict) -> Dict:
        """
        Enrich project with Twitter data (organization page, founder profiles).

        Args:
            project: Project data dictionary

        Returns:
            Dict: Enriched project data
        """
        try:
            twitter_link = project.get('twitter_link')
            # if not twitter_link:
            #     # Try to search for Twitter based on project_name
            #     project_name = project.get('project_name', '').replace(' ', '').lower()
            #     if project_name:
            #         # This is a placeholder - in real implementation, you'd search Twitter API
            #         potential_twitter = f"https://twitter.com/{project_name}"
            #         project['twitter_potential_company'] = potential_twitter
            #         print(f"✓ Generated potential Twitter URL for {project.get('project_name', 'Unknown')}")
            #     return project

                # If Twitter link exists, extract additional info
                # Extract handle from URL
            # if '/status/' not in twitter_link:  # Not a tweet link
            #     handle = twitter_link.split('/')[-1] if '/' in twitter_link else twitter_link
            #     project['twitter_handle'] = handle.replace('@', '')

                # Placeholder for future implementation:
            # - Get follower count
            # - Analyze recent tweets
            # - Find founder/team member profiles
            # - Get engagement metrics

            print(f"✓ Twitter data placeholder added for {project.get('project_name', 'Unknown')}")

        except Exception as e:
            print(f"Failed to enrich Twitter data for {project.get('project_name', 'Unknown')}: {e}")
            print(f"Failed to enrich Twitter data for {project.get('project_name', 'Unknown')}: {e}")

        return project

    def enrich_email_data(self, project: Dict) -> Dict:
        """
        Enrich project with email data by scraping website for email addresses.

        Args:
            project: Project data dictionary

        Returns:
            Dict: Enriched project data
        """
        try:
            # Check if we already have email data
            existing_email = project.get('email_link')
            if existing_email:
                print(f"✓ Email already exists for {project.get('project_name', 'Unknown')}: {existing_email}")
                return project

            # Get website URL to scrape for emails
            website = project.get('website')
            if not website:
                print(f"✗ No website found for {project.get('project_name', 'Unknown')} - cannot scrape emails")
                return project

            print(f"🔍 Scraping emails from website for {project.get('project_name', 'Unknown')}")

            # Extract emails using the provided logic
            emails = self.get_email_from_website(website)

            if emails:
                if ', ' in emails:
                    project['email_links'] = emails
                else:
                    project['email_link'] = emails
                print(f"✓ Found email(s) for {project.get('project_name', 'Unknown')}: {emails}")
                print(f"✓ Found email(s) for {project.get('project_name', 'Unknown')}: {emails}")
            else:
                print(f"✗ No emails found for {project.get('project_name', 'Unknown')}")
                print(f"✗ No emails found for {project.get('project_name', 'Unknown')}")

        except Exception as e:
            print(f"Failed to enrich email data for {project.get('project_name', 'Unknown')}: {e}")
            print(f"Failed to enrich email data for {project.get('project_name', 'Unknown')}: {e}")

        return project

    def get_email_from_website(self, website):
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


def start_data_extraction(self, data: List[Dict]):
    self.update_progress("Starting automatic data extraction...")
    while True:
        available_chrome_profiles = get_available_profiles()
        data_length = len(data)
        num_profiles = len(available_chrome_profiles)
        if num_profiles >= 4: break
        else: time.sleep(5)

    # Clear previous workers
    self.enrichment_workers.clear()

    # Restrict to 1 chrome profile for testing
    # available_chrome_profiles = ["telegram_4"]
    # num_profiles = len(available_chrome_profiles)

    for index, chrome_profile in enumerate(available_chrome_profiles):
        start_index = index * (data_length // num_profiles) + min(index, data_length % num_profiles)
        end_index = start_index + (data_length // num_profiles) + (1 if index < data_length % num_profiles else 0)

        # Create and configure the enrichment worker with parent
        worker = AutoEnrichmentWorker(data[start_index:end_index], chrome_profile, parent=self)
        worker.progress_updated.connect(self.update_progress)
        worker.project_processed.connect(self.on_enrichment_project_processed)
        worker.enrichment_completed.connect(self.on_enrichment_completed)
        worker.error_occurred.connect(self.on_enrichment_error)
        # Use a direct slot with worker-specific method to avoid closure issues
        worker.finished.connect(self.create_worker_finished_slot(worker))
        self.enrichment_workers.append(worker)
        worker.start()
        self.print(f"Started enrichment worker {index + 1} for profile {chrome_profile}")
        time.sleep(2)
