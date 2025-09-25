# core/utils/text_utils.py
"""
Text processing utility functions.
"""

import re
from typing import List


def parse_dollar_amount(value: str) -> float | None:
    """
    Convert market cap string into float.
    Examples:
        "$249.67K" -> 249670.0
        "$142,116,149" -> 142116149.0
    """
    SUFFIX_MULTIPLIERS = {
        "K": 1e3,
        "M": 1e6,
        "B": 1e9,
        "T": 1e12,
    }

    if not value: return None

    v = value.strip().replace("$", "").replace(",", "")
    m = re.match(r"^([\d\.]+)([KMBT]?)$", v, re.IGNORECASE)
    if not m:
        return None

    num = float(m.group(1))
    suffix = m.group(2).upper()
    if suffix in SUFFIX_MULTIPLIERS:
        num *= SUFFIX_MULTIPLIERS[suffix]
    return num

def replace_string_at_index(text, index=0, replacement=''):
    """
    Replace character at specific index in string.

    Args:
        text (str): Original text
        index (int): Index to replace
        replacement (str): Replacement character

    Returns:
        str: Modified text
    """
    return f'{text[:index]}{replacement}{text[index+1:]}'

def extract_percentage_from_text(item):
    """
    Extract percentage value from text containing percentage.

    Args:
        item (str): Text containing percentage

    Returns:
        float: Extracted percentage or -1 if not found
    """
    match = re.search(r"\[(\d+\.?\d*)%]", item)
    return float(match.group(1)) if match else -1

def get_telegram_group_from_link(telegram_link:str):
    # Extract telegram group name
    if telegram_link.startswith('https://t.me/'):
        tele_group = '@' + telegram_link[13:]
    elif not telegram_link.startswith('@'):
        tele_group = '@' + telegram_link
    else:
        tele_group = telegram_link

    return tele_group


def split_message_if_needed(message: str, max_length: int = 4000) -> List[str]:
    """Split Telegram message into chunks by project blocks if total exceeds max_length.

    Projects are separated by '–––––––––––––––––––––––––'.
    Each chunk will contain full project blocks and never break mid-project.
    """
    if len(message) <= max_length:
        return [message]

    chunks = []
    current_chunk = ""
    project_blocks = message.split("–––––––––––––––––––––––––")

    for project in project_blocks:
        project = project.strip()
        if not project:
            continue
        project_text = project + "\n–––––––––––––––––––––––––\n\n"
        if len(current_chunk) + len(project_text) <= max_length:
            current_chunk += project_text
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = project_text

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks
