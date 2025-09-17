# core/messengers/telegram/tele_sender_helper.py
"""
Telegram web interface message sending functions.
"""

def _reset_to_telegram_main(driver):
    """Return to Telegram main page."""
    driver.get("https://web.telegram.org/k/")
