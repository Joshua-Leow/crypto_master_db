#!/usr/bin/env python3
"""
Migration: move top-level email_link/email_links into socials.email_link
and remove the old fields.
"""

from __future__ import annotations
from pymongo import MongoClient, UpdateOne
from pymongo.errors import BulkWriteError
from typing import List, Dict, Any, Optional
from bson import ObjectId

from config.private import get_mongodb_uri

DB_NAME = "chainreachai"
COLL_NAME = "projects"
BATCH = 1000

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
        update: Dict[str, Any] = {}
        socials = d.get("socials") if isinstance(d.get("socials"), dict) else {}
        modified = False

        # Collect a candidate email
        email = d.get("email_link")
        if not email and isinstance(d.get("email_links"), list) and d["email_links"]:
            email = d["email_links"][0]  # pick first if list exists

        if email and not socials.get("email_link"):
            socials["email_link"] = email
            update["$set"] = {"socials": socials}
            modified = True

        # Always remove old keys if present
        unset_fields = {}
        if "email_link" in d:
            unset_fields["email_link"] = ""
        if "email_links" in d:
            unset_fields["email_links"] = ""
        if unset_fields:
            update.setdefault("$unset", {}).update(unset_fields)
            modified = True

        if modified:
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
