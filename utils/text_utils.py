# core/utils/text_utils.py
"""
Text processing utility functions.
"""

import re
from typing import List, Optional, Dict


def get_link_field_map():
    link_field_map: Dict[str, str] = {
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
        "www.x.com": "twitter_link",
        "/x.com": "twitter_link",
        "mailto:": "email_link",
        "github": "github_link",
    }
    return link_field_map

# category and network util
def _get_ecosystem_regex():
    return re.compile(r"\becosystem\b", re.IGNORECASE)

def _collapse_ws(s: str) -> str:
    return " ".join(s.split())

def _normalize_name(s: str) -> str:
    """
    Hyphen->space, collapse whitespace, strip, Title Case.
    """
    s = s.replace("-", " ")
    s = _collapse_ws(s).strip()
    return s.title()

def _strip_ecosystem(s: str) -> str:
    """
    Remove the word 'ecosystem' and re-normalize.
    """
    ECOS_RE = _get_ecosystem_regex()
    x = ECOS_RE.sub("", s)
    return _normalize_name(x)

def _add_unique_ci(arr: List[str], value: str) -> None:
    """
    Append value if not already present (case-insensitive) in arr.
    """
    if not value:
        return
    lv = value.lower()
    if all((v or "").lower() != lv for v in arr):
        arr.append(value)

def _slug_from_categories_url(url: str) -> Optional[str]:
    """
    Extract the <slug> part from .../categories/<slug>(/...) URLs.
    """
    if not url or "/categories/" not in url:
        return None
    part = url.split("/categories/")[-1]
    slug = part.split("/", 1)[0]
    return slug or None
# end of category and network util


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
