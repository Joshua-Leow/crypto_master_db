#!/usr/bin/env python3
"""
Migration: Normalize emails into socials.email_link (always a list).
- Accepts top-level email_link (str|list) and email_links (str|list).
- Merges with existing socials.email_link (if any).
- Deduplicates case-insensitively, preserves original casing of first occurrence.
- Removes top-level email_link and email_links.
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional
from pymongo import MongoClient, UpdateOne
from pymongo.errors import BulkWriteError
from bson import ObjectId

from config.private import get_mongodb_uri

DB_NAME = "chainreachai"
COLL_NAME = "projects"
BATCH = 1000

def _to_list(v: Any) -> List[str]:
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x).strip() for x in v if isinstance(x, (str, bytes)) and str(x).strip()]
    if isinstance(v, (str, bytes)):
        s = str(v).strip()
        return [s] if s else []
    return []

def _merge_unique_ci(existing: List[str], incoming: List[str]) -> List[str]:
    seen = {}
    # keep first-seen original casing
    for x in existing + incoming:
        if not isinstance(x, str):
            continue
        k = x.strip().lower()
        if not k:
            continue
        if k not in seen:
            seen[k] = x.strip()
    return list(seen.values())

def fetch_batch(coll, last_id: Optional[ObjectId]) -> List[Dict[str, Any]]:
    q = {"_id": {"$gt": last_id}} if last_id else {}
    return list(
        coll.find(q, {"_id": 1, "email_link": 1, "email_links": 1, "socials": 1})
            .sort("_id", 1)
            .limit(BATCH)
    )

def build_updates(docs: List[Dict[str, Any]]) -> List[UpdateOne]:
    ops: List[UpdateOne] = []
    for d in docs:
        socials = d.get("socials") if isinstance(d.get("socials"), dict) else {}
        existing_list = _to_list(socials.get("email_link"))
        top_email_link  = _to_list(d.get("email_link"))
        top_email_links = _to_list(d.get("email_links"))
        merged = _merge_unique_ci(existing_list, _merge_unique_ci(top_email_link, top_email_links))

        update: Dict[str, Any] = {}
        changed = False

        # set socials.email_link only if changed or if socials missing it
        if merged != existing_list:
            new_socials = dict(socials)
            new_socials["email_link"] = merged
            update["$set"] = {"socials": new_socials}
            changed = True

        # always remove old fields if present
        unset_fields = {}
        if "email_link" in d:
            unset_fields["email_link"] = ""
        if "email_links" in d:
            unset_fields["email_links"] = ""
        if unset_fields:
            update.setdefault("$unset", {}).update(unset_fields)
            changed = True

        if changed:
            ops.append(UpdateOne({"_id": d["_id"]}, update))
    return ops

def run() -> None:
    client = MongoClient(get_mongodb_uri())
    coll = client[DB_NAME][COLL_NAME]

    total_scanned = total_updated = 0
    last_id: Optional[ObjectId] = None

    while True:
        batch = fetch_batch(coll, last_id)
        if not batch:
            break
        last_id = batch[-1]["_id"]
        total_scanned += len(batch)

        ops = build_updates(batch)
        if ops:
            try:
                res = coll.bulk_write(ops, ordered=False)
                total_updated += res.modified_count
            except BulkWriteError as e:
                print("Bulk write error:", e.details)

    print(f"Scanned={total_scanned} Updated={total_updated}")

if __name__ == "__main__":
    run()
