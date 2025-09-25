#!/usr/bin/env python3
"""
Normalize and migrate:
- Replace '-' with ' ' in category items.
- Title-case and de-duplicate both 'category' and 'network'.
- Move any category item containing 'ecosystem' (case-insensitive) into 'network',
  stripping the word 'ecosystem' from the moved value.
- Print debug info and final unique networks (sorted).
"""

from __future__ import annotations
from pymongo import MongoClient, UpdateOne
from pymongo.errors import BulkWriteError
from bson import ObjectId
from typing import List, Dict, Any, Optional, Tuple
import re

from config.private import get_mongodb_uri

BATCH_DOCS = 2000
DB_NAME = "chainreachai"
COLL_NAME = "projects"

ECOS_RE = re.compile(r"\becosystem\b", re.IGNORECASE)
SPACE_RE = re.compile(r"\s+")

def _titlecase(s: str) -> str:
    return s.strip().title()

def _clean_item(s: str) -> str:
    """Hyphen->space, collapse spaces."""
    s2 = s.replace("-", " ")
    s2 = SPACE_RE.sub(" ", s2).strip()
    return s2

def _easy_strip_ecosystem(s: str) -> str:
    """Remove the word 'ecosystem' and clean leftover spacing."""
    x = ECOS_RE.sub("", s)
    x = SPACE_RE.sub(" ", x).strip()
    return x

def normalize_list(values: Any) -> List[str]:
    """Title Case + unique (case-insensitive)."""
    if not isinstance(values, list):
        return []
    seen = set()
    out: List[str] = []
    for v in values:
        if not isinstance(v, str):
            continue
        v = _clean_item(v)      # apply '-' -> ' ' before titlecasing
        norm = _titlecase(v)
        key = norm.lower()
        if key not in seen:
            seen.add(key)
            out.append(norm)
    return out

def split_category_into_keep_and_network(categories: Any) -> Tuple[List[str], List[str]]:
    """
    Return (keep_category, moved_network).
    Detect 'ecosystem' in category entries after cleaning; strip the word when moving.
    """
    if not isinstance(categories, list):
        return [], []

    keep: List[str] = []
    moved: List[str] = []

    for v in categories:
        if not isinstance(v, str):
            continue
        cleaned = _clean_item(v)
        if ECOS_RE.search(cleaned):
            net = _easy_strip_ecosystem(cleaned)
            if net:
                moved.append(net)
        else:
            keep.append(cleaned)

    # Normalize both lists now (title-case + dedupe)
    keep = normalize_list(keep)
    moved = normalize_list(moved)
    return keep, moved

def fetch_batch(coll, last_id: Optional[ObjectId], limit: int) -> List[Dict[str, Any]]:
    q: Dict[str, Any] = {}
    if last_id is not None:
        q["_id"] = {"$gt": last_id}
    return list(
        coll.find(q, {"_id": 1, "network": 1, "category": 1, "project_name": 1})
            .sort("_id", 1)
            .limit(limit)
    )

def build_updates(docs: List[Dict[str, Any]]) -> Tuple[List[UpdateOne], Dict[str, int]]:
    ops: List[UpdateOne] = []
    stats = {"scanned": 0, "updated": 0, "moved_items": 0, "no_category": 0, "no_moves": 0}

    for d in docs:
        stats["scanned"] += 1
        cat = d.get("category")
        if not isinstance(cat, list):
            stats["no_category"] += 1
            continue

        keep_cat, moved_net = split_category_into_keep_and_network(cat)
        existing_net = normalize_list(d.get("network"))

        # Merge networks (case-insensitive unique)
        merged_net = normalize_list((existing_net or []) + (moved_net or []))

        # Debug: show docs where a move happens
        if moved_net:
            print(f"[MOVE] _id={d['_id']} name={d.get('project_name')!r} "
                  f"moved={moved_net} | kept_category={keep_cat} | prev_net={existing_net}")

        update_set: Dict[str, Any] = {}
        changed = False

        # If category changed after normalization/moves, set it
        if keep_cat != normalize_list(cat):
            update_set["category"] = keep_cat
            changed = True

        # If network changed after merge/normalize, set it
        if merged_net != (existing_net or []):
            update_set["network"] = merged_net
            changed = True

        if changed:
            ops.append(UpdateOne({"_id": d["_id"]}, {"$set": update_set}))
            stats["updated"] += 1
            stats["moved_items"] += len(moved_net)
        else:
            stats["no_moves"] += 1

    # Batch-level debug
    print(f"[BATCH] scanned={stats['scanned']} updated={stats['updated']} "
          f"moved_items={stats['moved_items']} no_category={stats['no_category']} "
          f"no_moves={stats['no_moves']}")
    return ops, stats

def run() -> None:
    client = MongoClient(get_mongodb_uri())
    coll = client[DB_NAME][COLL_NAME]

    totals = {"scanned": 0, "updated": 0, "moved_items": 0, "no_category": 0, "no_moves": 0}
    last_id: Optional[ObjectId] = None

    while True:
        batch = fetch_batch(coll, last_id, BATCH_DOCS)
        if not batch:
            break
        last_id = batch[-1]["_id"]

        ops, stats = build_updates(batch)
        for k, v in stats.items():
            totals[k] += v

        if ops:
            try:
                res = coll.bulk_write(ops, ordered=False)
                print(f"[WRITE] modified={res.modified_count}")
            except BulkWriteError as e:
                print("[ERROR] Bulk write error:", e.details)

    print(f"[TOTAL] scanned={totals['scanned']} updated={totals['updated']} "
          f"moved_items={totals['moved_items']} no_category={totals['no_category']} "
          f"no_moves={totals['no_moves']}")

    # Post-migration checks
    left_ecosystem = coll.count_documents({"category": {"$elemMatch": {"$regex": r"ecosystem", "$options": "i"}}})
    print(f"[CHECK] documents still having 'ecosystem' in category: {left_ecosystem}")

    # Show all unique networks sorted for manual review
    nets = coll.aggregate([
        {"$unwind": "$network"},
        {"$group": {"_id": "$network", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ], allowDiskUse=True)
    print("[NETWORKS] unique values (sorted):")
    for d in nets:
        print(d["_id"])
    # If you want counts too, print(f"{d['_id']} ({d['count']})")

if __name__ == "__main__":
    run()
