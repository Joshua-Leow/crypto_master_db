#!/usr/bin/env python3
"""
Normalize socials.* values to lists (even if single item).

Examples:
  "https://x.com/foo"        -> ["https://x.com/foo"]
  ["a", "A", " ", None]      -> ["a"]        # case-insensitive dedupe + strip + drop empties
  123 / {} / True            -> []           # non-string/list become empty list

Writes back only when a change occurs.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from bson import ObjectId
from pymongo import MongoClient, UpdateOne
from pymongo.errors import BulkWriteError

from config.private import get_mongodb_uri

DB_NAME = "chainreachai"
COLL_NAME = "projects"
BATCH = 1000

# Optional: restrict to known socials keys. If you want ALL keys under socials, set to None.
SOCIAL_KEYS_WHITELIST = None
# Example whitelist:
# SOCIAL_KEYS_WHITELIST = {
#   "website","twitter_link","reddit_link","telegram_link","email_link",
#   "linkedin_link","facebook_link","instagram_link","tiktok_link",
#   "youtube_link","discord_link","medium_link","github_link"
# }

def _to_list_norm(v: Any) -> List[str]:
    """Coerce to list[str]: strip, drop empties, case-insensitive dedupe preserving first casing."""
    items: List[str]
    if isinstance(v, list):
        items = [str(x).strip() for x in v if isinstance(x, (str, bytes)) and str(x).strip()]
    elif isinstance(v, (str, bytes)):
        s = str(v).strip()
        items = [s] if s else []
    else:
        items = []

    seen = set()
    out: List[str] = []
    for s in items:
        k = s.lower()
        if k not in seen:
            seen.add(k)
            out.append(s)
    return out

def _normalize_socials(socials: Any) -> Optional[Dict[str, List[str]]]:
    """
    Return a NEW normalized socials dict if changes are needed, else None.
    Only processes keys in whitelist if provided.
    Leaves unknown keys unchanged but coerces their value to list if whitelist is None.
    """
    if not isinstance(socials, dict):
        # No socials or wrong type -> create empty dict (but only if you want to force-create)
        return {"website": []} if False else None  # keep as None to avoid creating new field
    changed = False
    new_socials: Dict[str, Any] = dict(socials)  # shallow copy

    keys = list(socials.keys())
    if SOCIAL_KEYS_WHITELIST is not None:
        keys = [k for k in keys if k in SOCIAL_KEYS_WHITELIST]

    for k in keys:
        norm_list = _to_list_norm(socials.get(k))
        if norm_list != socials.get(k):
            new_socials[k] = norm_list
            changed = True

    return new_socials if changed else None

def _fetch_batch(coll, last_id: Optional[ObjectId]) -> List[Dict[str, Any]]:
    q = {"_id": {"$gt": last_id}} if last_id else {}
    return list(
        coll.find(q, {"_id": 1, "socials": 1})
            .sort("_id", 1).limit(BATCH)
    )

def run() -> None:
    client = MongoClient(get_mongodb_uri())
    coll = client[DB_NAME][COLL_NAME]

    scanned = updated = 0
    last_id: Optional[ObjectId] = None

    while True:
        batch = _fetch_batch(coll, last_id)
        if not batch:
            break
        last_id = batch[-1]["_id"]

        ops: List[UpdateOne] = []
        for d in batch:
            scanned += 1
            normalized = _normalize_socials(d.get("socials"))
            if normalized is not None:
                ops.append(UpdateOne({"_id": d["_id"]}, {"$set": {"socials": normalized}}))

        if ops:
            try:
                res = coll.bulk_write(ops, ordered=False)
                updated += res.modified_count
            except BulkWriteError as e:
                print("Bulk write error:", e.details)

    print(f"Scanned={scanned} Updated={updated}")

if __name__ == "__main__":
    run()
