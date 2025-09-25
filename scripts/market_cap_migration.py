from __future__ import annotations
from pymongo import MongoClient, UpdateOne
from pymongo.errors import BulkWriteError
from bson import ObjectId
from typing import Iterable, Optional, List, Dict, Any, Tuple

from config.private import get_mongodb_uri
from utils.text_utils import parse_dollar_amount

# connect
client = MongoClient(get_mongodb_uri())
db = client["chainreachai"]
projects = db["projects"]

def fetch_batch(coll, last_id: Optional[ObjectId], limit: int = 1000) -> List[Dict[str, Any]]:
    q: Dict[str, Any] = {}
    if last_id is not None:
        q["_id"] = {"$gt": last_id}
    return list(
        coll.find(q, {"_id": 1, "market_cap": 1})
            .sort("_id", 1)
            .limit(limit)
    )

def build_updates(docs: Iterable[Dict[str, Any]]) -> Tuple[List[UpdateOne], int, int, int]:
    ops: List[UpdateOne] = []
    parsed = skipped = unset = 0
    for d in docs:
        new_val = parse_dollar_amount(d.get("market_cap"))
        if new_val is None:
            skipped += 1
            continue
        if new_val == 0.0:
            ops.append(UpdateOne({"_id": d["_id"]}, {"$unset": {"market_cap": ""}}))
            unset += 1
        else:
            ops.append(UpdateOne({"_id": d["_id"]}, {"$set": {"market_cap": new_val}}))
            parsed += 1
    return ops, parsed, skipped, unset

def run(batch_size_docs: int = 2000) -> None:
    client = MongoClient(get_mongodb_uri())
    coll = client["chainreachai"]["projects"]

    total_scanned = total_modified = total_parsed = total_skipped = total_unset = 0
    last_id: Optional[ObjectId] = None

    while True:
        batch = fetch_batch(coll, last_id, limit=batch_size_docs)
        if not batch:
            break
        last_id = batch[-1]["_id"]
        ops, parsed, skipped, unset = build_updates(batch)
        total_scanned += len(batch)
        total_parsed += parsed
        total_skipped += skipped
        total_unset += unset

        if ops:
            try:
                res = coll.bulk_write(ops, ordered=False)
                total_modified += res.modified_count
            except BulkWriteError as e:
                print("Bulk write error:", e.details)

    print(
        f"Scanned={total_scanned} Parsed(set)={total_parsed} Unset(=0)={total_unset} "
        f"Skipped(unparsable)={total_skipped} Modified={total_modified}"
    )

if __name__ == "__main__":
    run()