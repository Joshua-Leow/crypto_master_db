# from typing import Dict
#
# from telebot import TeleBot
# from messengers.telegram.admin_extractor import get_telegram_channel_admins_chat_type_router
# from utils.text_utils import get_telegram_group_from_link, get_link_field_map
#
#
# def enrich_telegram_data(driver, project: Dict, chrome_profile) -> Dict:
#     """
#     Enrich project with Telegram admin data.
#
#     Args:
#         driver: Web driver for telegram automation
#         project: Project data dictionary
#
#     Returns:
#         Dict: Enriched project data
#     """
#     try:
#         telegram_link = project.get('socials', {}).get('telegram_link')
#         if not telegram_link:
#             return project
#
#         tele_group = get_telegram_group_from_link(telegram_link)
#
#         print(f"Getting Telegram admins for: {tele_group}")
#
#         # Use a random bot instance per project
#         from config.private import get_tele_bot_tokens
#         bot_tokens = get_tele_bot_tokens()
#         bot_info = None
#         random_bot = None
#         max_retries = len(bot_tokens)
#         retry_count = 0
#
#         while not bot_info and retry_count < max_retries:
#             random_token = ""
#             try:
#                 random_token = random.choice(bot_tokens)
#                 random_bot = TeleBot(random_token)
#                 bot_info = random_bot.get_me()  # Raises exception if invalid
#                 print(f"Using Telegram bot {bot_info.username}")
#             except Exception as e:
#                 print(f"Bot token failed: {random_token[:10]}... – {e}")
#                 retry_count += 1
#                 continue
#
#         if not bot_info:
#             print(f"✗ All Telegram bots failed for {project.get('project_name', 'Unknown')}")
#             return project
#
#         # Get admin list using validated bot
#         admin_list = get_telegram_channel_admins_chat_type_router(chrome_profile, driver, tele_group, random_bot)
#
#         if admin_list:
#             # Add admin data to project
#             project['telegram_admins'] = admin_list
#             print(f"✓ Added {len(admin_list)} Telegram admins for {project.get('project_name', 'Unknown')}")
#         else:
#             print(f"✗ No Telegram admins found for {project.get('project_name', 'Unknown')}")
#
#     except Exception as e:
#         print(f"Failed to get Telegram data for {project.get('project_name', 'Unknown')}: {e}")
#
#     return project

# def enrich_data_from_website(project: Dict) -> Dict:
#     """
#     Enrich project with email data by scraping website for email addresses.
#
#     Args:
#         project: Project data dictionary
#
#     Returns:
#         Dict: Enriched project data
#     """
#     try:
#         # Check if we already have email data
#         existing_email = project.get('socials', {}).get('email_link')
#         if existing_email:
#             print(f"✓ Email already exists for {project.get('project_name', 'Unknown')}: {existing_email}")
#             return project
#
#         # Get website URL to scrape for emails
#         website = project.get('socials', {}).get('website')
#         if not website:
#             print(f"✗ No website found for {project.get('project_name', 'Unknown')} - cannot scrape emails")
#             return project
#     except Exception as e:
#         print(f"Failed to navigate to {project.get('project_name', 'Unknown')} website: {project.get('socials', {}).get('website')}: {e}")
#
#     try:
#         print(f"🔍 Scraping emails from website for {project.get('project_name', 'Unknown')}")
#
#         # Extract emails using the provided logic
#         emails = get_email_from_website(website)
#
#         if emails:
#             if ', ' in emails:
#                 project['socials']['email_links'] = emails
#             else:
#                 project['socials']['email_link'] = emails
#             print(f"✓ Found email(s) for {project.get('project_name', 'Unknown')}: {emails}")
#         else:
#             print(f"✗ No emails found for {project.get('project_name', 'Unknown')}")
#
#     except Exception as e:
#         print(f"Failed to enrich email data for {project.get('project_name', 'Unknown')}: {e}")
#
#     return project
#
# def get_email_from_website(website):
#     """Extract emails including mailto links."""
#     try:
#         if not website:
#             return None
#         url = website if website.startswith("http") else "https://" + website
#         headers = {'User-Agent': 'Mozilla/5.0'}
#
#         try:
#             response = requests.get(url, headers=headers, timeout=8, verify=True)
#             response.raise_for_status()
#         except (requests.exceptions.SSLError, requests.exceptions.ConnectionError):
#             response = requests.get(url, headers=headers, timeout=8, verify=False)
#             response.raise_for_status()
#
#         soup = BeautifulSoup(response.text, "html.parser")
#         email_pattern = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
#
#         matching_emails = set()
#
#         # Scan only a subset of tags
#         tags_to_check = soup.find_all(["a", "p", "span", "div"], limit=1000)
#
#         for tag in tags_to_check:
#             # Check mailto links
#             if tag.name == "a" and tag.has_attr("href") and tag["href"].startswith("mailto:"):
#                 email = tag["href"][7:]
#                 matching_emails.add(email)
#
#             # Check visible text
#             if tag.string:
#                 for email in email_pattern.findall(tag.string):
#                     matching_emails.add(email)
#
#             if len(matching_emails) >= 10:
#                 break
#
#         return ", ".join(matching_emails) if matching_emails else None
#
#     except Exception as e:
#         print(f"Failed to scrape emails from {website}: {e}")
#         return None


###################################################################################################################
# file: enrichers/website_enricher.py

from typing import Dict, Optional, Tuple, Any
from telebot import TeleBot
import random

from messengers.telegram.admin_extractor import get_telegram_channel_admins_chat_type_router
from utils.text_utils import get_telegram_group_from_link, get_link_field_map
from typing import Iterable

def _as_list_str(v: Any) -> list[str]:
    """Coerce any value into list[str], stripped, drop empties."""
    if isinstance(v, list):
        return [s.strip() for s in v if isinstance(s, str) and s.strip()]
    if isinstance(v, str):
        s = v.strip()
        return [s] if s else []
    return []

def _merge_unique_ci(*lists: Iterable[str]) -> list[str]:
    """Merge lists, case-insensitive unique, keep first casing."""
    out, seen = [], set()
    for seq in lists:
        for x in seq:
            if not isinstance(x, str):
                continue
            k = x.strip().lower()
            if k and k not in seen:
                seen.add(k)
                out.append(x.strip())
    return out

def _ensure_social_list(project: dict, key: str) -> list[str]:
    """Ensure project['socials'][key] exists as list[str] and return it."""
    socials = project.setdefault("socials", {})
    lst = _as_list_str(socials.get(key))
    socials[key] = lst
    return lst


def _choose_working_bot() -> Optional[TeleBot]:
    """Return a validated TeleBot or None after trying all tokens."""
    from config.private import get_tele_bot_tokens
    tokens = get_tele_bot_tokens()
    random.shuffle(tokens)
    for tok in tokens:
        try:
            bot = TeleBot(tok)
            bot.get_me()  # validates token
            print(f"Using Telegram bot token ****{tok[-6:]}")
            return bot
        except Exception as e:
            print(f"Bot token failed ****{tok[-6:]} – {e}")
    return None


def _admin_key(admin: Dict) -> Tuple:
    """
    Stable dedupe key for admin dicts supporting both schemas:
    - {'username', 'first_name', 'role_title', ...}
    - or legacy {'telegram_username', 'telegram_name', 'telegram_role_title', ...}
    """
    uname = (admin.get("username") or admin.get("telegram_username") or "").strip().lstrip("@").lower()
    if uname:
        return ("u", uname)
    fname = (admin.get("first_name") or admin.get("telegram_name") or "").strip().lower()
    role = (admin.get("role_title") or admin.get("telegram_role_title") or "").strip().lower()
    return ("n", fname, role)


def enrich_telegram_data(driver, project: Dict, chrome_profile) -> Dict:
    """
    Enrich project with Telegram admin data from ALL Telegram links.
    Aggregates into project['telegram_admins'] with de-duplication.
    Requires socials.telegram_link to be a list[str] (this function enforces it).
    """
    try:
        # normalize to list schema
        telegram_links = _ensure_social_list(project, "telegram_link")
        if not telegram_links:
            return project

        bot = _choose_working_bot()
        if not bot:
            print(f"✗ All Telegram bots failed for {project.get('project_name', 'Unknown')}")
            return project

        aggregated: list[dict] = []
        seen_keys: set[Tuple] = set()

        # keep existing admins idempotently
        for adm in _as_list_str(None) or []:  # no-op placeholder; list kept below
            pass
        existing_admins = project.get("telegram_admins")
        if isinstance(existing_admins, list):
            for adm in existing_admins:
                if isinstance(adm, dict):
                    k = _admin_key(adm)
                    if k not in seen_keys:
                        seen_keys.add(k)
                        aggregated.append(adm)

        # collect from each tg link
        for tg_link in telegram_links:
            try:
                tele_group = get_telegram_group_from_link(tg_link)
                if not tele_group:
                    print(f"Skipped invalid Telegram link: {tg_link}")
                    continue

                print(f"Getting Telegram admins for: {tele_group}")
                admins = get_telegram_channel_admins_chat_type_router(
                    chrome_profile, driver, tele_group, bot
                )
                if not admins:
                    print(f"✗ No Telegram admins found for {tele_group}")
                    continue

                added = 0
                for admin in admins:
                    if not isinstance(admin, dict):
                        continue
                    key = _admin_key(admin)
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)
                    aggregated.append(admin)
                    added += 1

                print(f"✓ Added {added} new admins from {tele_group}")

            except Exception as e:
                print(f"Error while processing {tg_link}: {e}")

        if aggregated:
            project["telegram_admins"] = aggregated
            print(
                f"✓ Total {len(aggregated)} unique Telegram admins aggregated from {len(telegram_links)} link(s) "
                f"for {project.get('project_name', 'Unknown')}"
            )
        else:
            print(f"✗ No Telegram admins found for any Telegram links for {project.get('project_name', 'Unknown')}")

    except Exception as e:
        print(f"Failed to get Telegram data for {project.get('project_name', 'Unknown')}: {e}")

    return project


import json
import random
import re
import time
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

# -----------------------
# Config
# -----------------------

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)

REQUEST_TIMEOUT = 8.0
MAX_TOTAL_PAGES = 6
MAX_BYTES_PER_PAGE = 1_200_000
TOTAL_BUDGET_SECONDS = 18.0
PER_HOST_DELAY = (0.2, 0.6)

PRIORITY_PATHS = ["/contact", "/about", "/team", "/support", "/help", "/legal", "/privacy"]

EMAIL_REGEX = re.compile(r"\b[a-zA-Z0-9._%+\-]+@(?:[A-Za-z0-9\-]+\.)+[A-Za-z]{2,24}\b")

OBFUSCATION_RULES: Tuple[Tuple[re.Pattern, str], ...] = (
    (re.compile(r"\s*\[\s*at\s*\]\s*", re.I), "@"),
    (re.compile(r"\s*\(\s*at\s*\)\s*", re.I), "@"),
    (re.compile(r"\s+at\s+", re.I), "@"),
    (re.compile(r"\s*\[\s*dot\s*\]\s*", re.I), "."),
    (re.compile(r"\s*\(\s*dot\s*\)\s*", re.I), "."),
    (re.compile(r"\s+dot\s+", re.I), "."),
    (re.compile(r"\s*mailto:\s*", re.I), ""),
    (re.compile(r"\s*{at}\s*", re.I), "@"),
    (re.compile(r"\s*{dot}\s*", re.I), "."),
    (re.compile(r"\s*\[at\]\s*", re.I), "@"),
    (re.compile(r"\s*\[dot\]\s*", re.I), "."),
)

SKIP_HOSTS = {
    "facebook.com", "l.facebook.com", "m.facebook.com", "web.facebook.com", "twitter.com", "t.co",
    "linkedin.com", "www.linkedin.com", "outlook.live.com", "google.com", "www.google.com",
    "mailto",
}

# -----------------------
# HTTP helpers
# -----------------------

def _session() -> httpx.Client:
    return httpx.Client(
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
        follow_redirects=True,
        http2=True,
        timeout=httpx.Timeout(REQUEST_TIMEOUT),
        verify=True,
    )

def _get(client: httpx.Client, url: str, allow_insecure_retry: bool = True) -> Optional[httpx.Response]:
    try:
        r = client.get(url)
        r.raise_for_status()
        return r
    except httpx.HTTPError:
        if allow_insecure_retry:
            try:
                with httpx.Client(
                    headers=client.headers,
                    follow_redirects=True,
                    http2=True,
                    timeout=client.timeout,
                    verify=False,
                ) as insecure:
                    r = insecure.get(url)
                    r.raise_for_status()
                    return r
            except httpx.HTTPError:
                return None
        return None

def _looks_html(resp: httpx.Response) -> bool:
    ctype = resp.headers.get("Content-Type", "")
    if "text/html" in ctype or "application/xhtml+xml" in ctype:
        return True
    try:
        return "<html" in resp.text[:400].lower()
    except Exception:
        return False

def _sleep_jitter():
    time.sleep(random.uniform(*PER_HOST_DELAY))

def _truncate_bytes(b: bytes, cap: int) -> bytes:
    return b if len(b) <= cap else b[:cap]

# -----------------------
# URL and parsing helpers
# -----------------------

def _normalize_url(website: str) -> Optional[str]:
    if not website:
        return None
    website = website.strip()
    if not website:
        return None
    if not website.startswith(("http://", "https://")):
        website = "https://" + website
    parsed = urlparse(website)
    if not parsed.netloc:
        return None
    return parsed.geturl().split("#", 1)[0]

def _candidate_urls(base_url: str) -> List[str]:
    urls = [base_url]
    urls.extend(urljoin(base_url, p) for p in PRIORITY_PATHS)
    return urls

def _same_host_only(base: str, href: str) -> bool:
    try:
        return urlparse(base).netloc == urlparse(href).netloc
    except Exception:
        return False

def _clean_text_for_emails(text: str) -> str:
    s = text
    for pat, rep in OBFUSCATION_RULES:
        s = pat.sub(rep, s)
    return s

def _last_segment_key(url: str) -> Optional[str]:
    """
    Generic dedupe key: last non-empty path segment, lowercased, without trailing slash or query.
    """
    try:
        p = urlparse(url)
        if p.scheme == "mailto":
            return p.path.lower()
        parts = [seg for seg in p.path.split("/") if seg]
        if not parts:
            return None
        return parts[-1].lower()
    except Exception:
        return None

# -----------------------
# Email extraction
# -----------------------

def _extract_emails_from_text(text: str) -> Set[str]:
    text = _clean_text_for_emails(text)
    return set(EMAIL_REGEX.findall(text))

def _extract_emails_from_mailto(href: str) -> Set[str]:
    if not href.lower().startswith("mailto:"):
        return set()
    addr = href[7:].split("?", 1)[0]
    outs = set()
    for raw in addr.split(","):
        cand = _clean_text_for_emails(raw.strip())
        if EMAIL_REGEX.fullmatch(cand):
            outs.add(cand)
    return outs

def _extract_emails_from_jsonld(soup: BeautifulSoup) -> Set[str]:
    emails = set()
    for tag in soup.find_all("script", type=("application/ld+json", "application/json")):
        try:
            data = json.loads(tag.string or "")
        except Exception:
            continue
        stack = data if isinstance(data, list) else [data]
        for obj in stack:
            if isinstance(obj, dict):
                v = obj.get("email")
                if isinstance(v, str):
                    v = _clean_text_for_emails(v.strip())
                    if EMAIL_REGEX.fullmatch(v):
                        emails.add(v)
    return emails

# -----------------------
# Social extraction primitives
# -----------------------

def _map_social_field(href: str) -> Optional[str]:
    h = href.lower()
    for key, field in get_link_field_map().items():
        if key == "mailto:":
            continue
        if key in h:
            return field
    if h.startswith("mailto:"):
        return get_link_field_map()["mailto:"]
    return None

def _extract_socials_from_jsonld(soup: BeautifulSoup) -> Dict[str, Set[str]]:
    out: Dict[str, Set[str]] = {}
    for tag in soup.find_all("script", type=("application/ld+json", "application/json")):
        try:
            data = json.loads(tag.string or "")
        except Exception:
            continue
        stack = data if isinstance(data, list) else [data]
        for obj in stack:
            if not isinstance(obj, dict):
                continue
            same_as = obj.get("sameAs")
            if isinstance(same_as, str):
                same_as = [same_as]
            if isinstance(same_as, list):
                for href in same_as:
                    if not isinstance(href, str):
                        continue
                    field = _map_social_field(href)
                    if field:
                        out.setdefault(field, set()).add(href)
    return out

def _extract_socials_from_anchors(soup: BeautifulSoup) -> Dict[str, Set[str]]:
    out: Dict[str, Set[str]] = {}
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href:
            continue
        field = _map_social_field(href)
        if field:
            host = urlparse(href).netloc.lower()
            if host in SKIP_HOSTS and "intent" in href:
                continue
            out.setdefault(field, set()).add(href)
    return out

# -----------------------
# Canonicalization + de-duplication
# -----------------------

def _canon_twitter(url: str) -> Optional[Tuple[str, str]]:
    """
    Return (canonical_url, dedupe_key). Canonical is https://x.com/<handle>
    """
    try:
        p = urlparse(url)
        host = p.netloc.lower()
        if "twitter.com" not in host and "x.com" not in host and "mobile.twitter.com" not in host:
            return None
        parts = [seg for seg in p.path.split("/") if seg]
        if not parts:
            return None
        handle = parts[0].lstrip("@")
        # filter share/intent
        if handle in {"i", "intent", "share"}:
            return None
        return (f"https://x.com/{handle}", handle.lower())
    except Exception:
        return None

def _canon_discord(url: str) -> Optional[Tuple[str, str]]:
    """
    Prefer https://discord.gg/<code> regardless of discord.com/invite or discord.gg
    """
    try:
        p = urlparse(url)
        host = p.netloc.lower()
        parts = [seg for seg in p.path.split("/") if seg]
        code = None
        if "discord.gg" in host and parts:
            code = parts[0]
        elif "discord.com" in host and len(parts) >= 2 and parts[0] == "invite":
            code = parts[1]
        if not code:
            # fallback to last segment
            key = _last_segment_key(url)
            if not key:
                return None
            return (f"https://discord.gg/{key}", key)
        return (f"https://discord.gg/{code}", code.lower())
    except Exception:
        return None

def _canon_reddit(url: str) -> Optional[Tuple[str, str]]:
    """
    Canonicalize subreddit links to https://www.reddit.com/r/<subreddit>
    If not a subreddit URL, fall back to last segment.
    """
    try:
        p = urlparse(url)
        if "reddit.com" not in p.netloc.lower():
            return None
        parts = [seg for seg in p.path.split("/") if seg]
        sub = None
        for i in range(len(parts) - 1):
            if parts[i].lower() == "r" and i + 1 < len(parts):
                sub = parts[i + 1]
                break
        if sub:
            return (f"https://www.reddit.com/r/{sub}", sub.lower())
        key = _last_segment_key(url)
        if not key:
            return None
        return (url, key)
    except Exception:
        return None

def _canon_generic_by_last_segment(url: str) -> Optional[Tuple[str, str]]:
    key = _last_segment_key(url)
    if not key:
        return None
    # leave URL as-is except strip trailing slash for a stable form
    if url.endswith("/"):
        url = url[:-1]
    return (url, key)

def _normalize_and_dedupe(field: str, urls: List[str]) -> List[str]:
    """
    Apply network-specific canonicalization and dedupe by key.
    Always returns a list.
    """
    out: List[str] = []
    seen: Set[str] = set()

    for u in urls:
        if not isinstance(u, str) or not u.strip():
            continue
        u = u.strip()
        cand: Optional[Tuple[str, str]] = None

        if field == "twitter_link":
            cand = _canon_twitter(u)
        elif field == "discord_link":
            cand = _canon_discord(u)
        elif field == "reddit_link":
            cand = _canon_reddit(u)
        else:
            cand = _canon_generic_by_last_segment(u)

        if not cand:
            continue

        canon_url, key = cand
        if key not in seen:
            seen.add(key)
            out.append(canon_url)

    # stable order, shortest first can help reduce visual noise
    out = sorted(out, key=lambda x: (len(x), x))
    return out

# -----------------------
# Public APIs
# -----------------------

def get_emails_from_website(
    website: str,
    max_pages: int = MAX_TOTAL_PAGES,
    stop_after: int = 10,
) -> List[str]:
    """
    Fast, budgeted email extraction from homepage + priority pages + small sitemap sample.
    Returns a sorted unique list.
    """
    start = time.time()
    base = _normalize_url(website)
    if not base:
        return []

    seen: Set[str] = set()
    found: Set[str] = set()

    def budget_ok() -> bool:
        return (time.time() - start) < TOTAL_BUDGET_SECONDS

    def fetch_and_extract(url: str, client: httpx.Client):
        nonlocal found
        if url in seen or len(found) >= stop_after:
            return
        seen.add(url)
        resp = _get(client, url)
        if not resp or not _looks_html(resp):
            return
        content = _truncate_bytes(resp.content, MAX_BYTES_PER_PAGE)
        try:
            soup = BeautifulSoup(content, "lxml")
        except Exception:
            soup = BeautifulSoup(content, "html.parser")

        for a in soup.find_all("a", href=True):
            found |= _extract_emails_from_mailto(a["href"])
            if len(found) >= stop_after:
                return

        for i, tag in enumerate(soup.select("a, p, span, div, li")):
            if i >= 1500:
                break
            txt = tag.get_text(separator=" ", strip=True)
            if not txt:
                continue
            found |= _extract_emails_from_text(txt)
            if len(found) >= stop_after:
                return

        found |= _extract_emails_from_jsonld(soup)

    def try_sitemap(client: httpx.Client) -> List[str]:
        locs: List[str] = []
        for root in (urljoin(base, "/sitemap.xml"), urljoin(base, "/sitemap_index.xml")):
            if not budget_ok():
                break
            r = _get(client, root)
            if not r or r.status_code >= 400:
                continue
            text = r.text
            if "<loc>" not in text:
                continue
            for m in re.finditer(r"<loc>(.*?)</loc>", text, re.I | re.S):
                href = m.group(1).strip()
                if href and _same_host_only(base, href):
                    locs.append(href)
                if len(locs) >= 12:
                    return locs
        return locs

    with _session() as client:
        for url in _candidate_urls(base):
            if not budget_ok() or len(seen) >= max_pages or len(found) >= stop_after:
                break
            fetch_and_extract(url, client)
            _sleep_jitter()

        if budget_ok() and len(found) < stop_after and len(seen) < max_pages:
            for href in try_sitemap(client):
                if not budget_ok() or len(seen) >= max_pages or len(found) >= stop_after:
                    break
                fetch_and_extract(href, client)
                _sleep_jitter()

    def _valid(email: str) -> bool:
        bad = ("example.com", "test@", "invalid@", "noemail@", "nospam@")
        return not any(k in email.lower() for k in bad)

    return sorted(e for e in found if _valid(e))

def get_socials_from_website(
    website: str,
    max_pages: int = MAX_TOTAL_PAGES,
) -> Dict[str, List[str]]:
    """
    Harvest social links using anchor tags and JSON-LD sameAs across
    homepage + priority pages. Returns dict keyed by your project fields.
    Always lists.
    """
    start = time.time()
    base = _normalize_url(website)
    if not base:
        return {}

    seen: Set[str] = set()
    agg: Dict[str, Set[str]] = {}

    def budget_ok() -> bool:
        return (time.time() - start) < TOTAL_BUDGET_SECONDS

    def fetch(url: str, client: httpx.Client):
        if url in seen:
            return
        seen.add(url)
        resp = _get(client, url)
        if not resp or not _looks_html(resp):
            return
        content = _truncate_bytes(resp.content, MAX_BYTES_PER_PAGE)
        try:
            soup = BeautifulSoup(content, "lxml")
        except Exception:
            soup = BeautifulSoup(content, "html.parser")

        anchors = _extract_socials_from_anchors(soup)
        for field, links in anchors.items():
            agg.setdefault(field, set()).update(links)

        same_as = _extract_socials_from_jsonld(soup)
        for field, links in same_as.items():
            agg.setdefault(field, set()).update(links)

    with _session() as client:
        for url in _candidate_urls(base):
            if not budget_ok() or len(seen) >= max_pages:
                break
            fetch(url, client)
            _sleep_jitter()

    return {field: sorted(vals) for field, vals in agg.items()}

def enrich_data_from_website(project: Dict) -> Dict:
    """
    Enriches project['socials'] with:
      - email_link (list[str])
      - social links per LINK_FIELD_MAP, canonicalized and de-duplicated
    Preserves existing values. All socials end as lists.
    """
    socials = project.setdefault("socials", {})

    # website itself should be a list now
    website_list = _ensure_social_list(project, "website")
    website = website_list[0] if website_list else None
    if not website:
        print(f"✗ No website found for {project.get('project_name', 'Unknown')}")
        return project

    print(f"🔍 Scraping website for {project.get('project_name', 'Unknown')}: {website}")

    # Emails -> always list
    existing_emails = _ensure_social_list(project, "email_link")
    if not existing_emails:
        emails = get_emails_from_website(website, max_pages=MAX_TOTAL_PAGES, stop_after=10)
        if emails:
            socials["email_link"] = _merge_unique_ci(existing_emails, emails)
            print(f"✓ Found email(s): {', '.join(socials['email_link'])}")
        else:
            print("✗ No emails found")

    # Social links
    found_socials = get_socials_from_website(website, max_pages=MAX_TOTAL_PAGES)
    for field, new_links in found_socials.items():
        if field == "email_link":
            # already handled
            continue
        current = _ensure_social_list(project, field)
        merged = _merge_unique_ci(current, new_links)
        socials[field] = _normalize_and_dedupe(field, merged)

    # Ensure every existing social subfield is a list
    for k, v in list(socials.items()):
        socials[k] = _as_list_str(v)

    project["socials"] = socials
    return project
