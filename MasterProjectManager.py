import re

from pymongo import MongoClient, ASCENDING
from datetime import datetime
import uuid
from typing import Dict, List, Any, Optional, Tuple, Set
import json
from copy import deepcopy

from config.private import get_mongodb_uri


class MasterProjectManager:
    def __init__(self, connection_string: str, database_name: str = "chainreachai"):
        """
        Initialize the MasterProjectManager with MongoDB connection

        Args:
            connection_string: MongoDB connection string
            database_name: Name of the database to use
        """
        self.client = MongoClient(connection_string)
        self.db = self.client[database_name]
        self.collection = self.db.projects

        # Source priority list (index 0 = highest priority)
        self.source_priority = [
            "coingecko",
            "coinmarketcap",
            "dextools",
            "dexscreener",
            "birdeye"
        ]

        # self._setup_indexes()

    def _setup_indexes(self):
        """Setup MongoDB indexes for optimal performance"""
        # Compound index for duplicate detection
        self.collection.create_index([
            ("project_name", ASCENDING),
            ("project_ticker", ASCENDING)
        ], name="duplicate_detection_idx")

        # Unique index on project_uid
        self.collection.create_index("project_uid", unique=True, name="project_uid_idx")

        # Unique index on project_ticker
        self.collection.create_index("project_ticker", name="project_ticker_idx")

        # Index on categories for filtering
        self.collection.create_index("category", name="category_idx")

        # Sparse index on market_cap for projects with market data
        self.collection.create_index("market_cap", sparse=True, name="market_cap_idx")

        # Index on sources keys for source-based queries
        self.collection.create_index("sources", name="sources_idx")

        print("MongoDB indexes created successfully")

    # ---------- tiny utilities ----------
    @staticmethod
    def _is_empty(value: Any) -> bool:
        if value is None:
            return True
        if isinstance(value, str):
            return value.strip() == ""
        if isinstance(value, (list, tuple, set, dict)):
            return len(value) == 0
        return False

    @staticmethod
    def _signature(item: Any) -> str:
        """Stable signature for list de-duplication of unstructured items."""
        try:
            return json.dumps(item, sort_keys=True, separators=(",", ":"))
        except Exception:
            return f"{type(item).__name__}:{repr(item)}"

    @staticmethod
    def _ensure_list(v: Any) -> List[Any]:
        if v is None:
            return []
        return v if isinstance(v, list) else [v]

    @staticmethod
    def _norm_link(s: str) -> str:
        s = str(s or "").strip()
        return s.rstrip("/").lower()

    def _prefer_scalar(self, a: Any, b: Any, prefer_b: bool) -> Any:
        if self._is_empty(a) and not self._is_empty(b):
            return deepcopy(b)
        if self._is_empty(b):
            return deepcopy(a)
        return deepcopy(b) if prefer_b else deepcopy(a)

    # ---------- field-specific helpers ----------
    def _merge_simple_list(self, la: List[Any], lb: List[Any], prefer_b: bool) -> List[Any]:
        base = (lb + la) if prefer_b else (la + lb)
        out, seen = [], set()
        for itm in base:
            sig = self._signature(itm)
            if sig not in seen:
                seen.add(sig)
                out.append(itm)
        return out

    def _merge_socials(self, va: Dict[str, Any], vb: Dict[str, Any], prefer_b: bool) -> Dict[str, List[str]]:
        va = va or {}
        vb = vb or {}
        keys = set(va) | set(vb)
        res: Dict[str, List[str]] = {}
        for field in keys:
            la = self._ensure_list(va.get(field))
            lb = self._ensure_list(vb.get(field))
            ordered = (lb + la) if prefer_b else (la + lb)
            out, seen = [], set()
            for link in ordered:
                key = self._norm_link(link)
                if key and key not in seen:
                    seen.add(key)
                    out.append(link)
            res[field] = out
        return res

    def _merge_admin_entry(self, a: Dict[str, Any], b: Dict[str, Any], prefer_b: bool) -> Dict[str, Any]:
        """Flat merge of two admin dicts. Prefer non-empty from preferred side per key."""
        keys = set(a) | set(b)
        out: Dict[str, Any] = {}
        for k in keys:
            out[k] = self._prefer_scalar(a.get(k), b.get(k), prefer_b)
        return out

    def _merge_admins(self, la: List[Dict[str, Any]], lb: List[Dict[str, Any]], prefer_b: bool) -> List[Dict[str, Any]]:
        la = la or []
        lb = lb or []

        def uname(d: Dict[str, Any]) -> str:
            return str(d.get("username", "")).strip().lower()

        # order: preferred side first
        base = (lb + la) if prefer_b else (la + lb)
        out: List[Dict[str, Any]] = []
        idx: Dict[str, int] = {}
        sig_seen: Set[str] = set()

        for adm in base:
            u = uname(adm)
            if u:
                if u not in idx:
                    idx[u] = len(out)
                    out.append(deepcopy(adm))
                else:
                    i = idx[u]
                    out[i] = self._merge_admin_entry(out[i], adm, prefer_b)
            else:
                # no username -> dedupe by structural signature
                sig = self._signature(adm)
                if sig not in sig_seen:
                    sig_seen.add(sig)
                    out.append(deepcopy(adm))
        return out

    # ---------- deep merge (payload is always dict) ----------
    def _deep_merge(
            self,
            a: Dict[str, Any],
            b: Dict[str, Any],
            prefer_b: bool,
            protected_keys: Set[str],
    ) -> Dict[str, Any]:
        """
        Non-destructive deep merge with clear per-field strategies.
        Known keys:
          - sources: ignored here (caller handles)
          - socials: dict of lists -> union by normalized link, order by prefer_b
          - market_cap/about: scalar preference
          - category/exchanges/network: list union, order by prefer_b
          - telegram_admins: list of dicts -> dedupe by username, merge entries
          - other keys: scalar preference (same as market_cap/about)
        Top-level protected_keys are never changed unless empty in 'a'.
        """
        result = deepcopy(a) if isinstance(a, dict) else {}
        b = b or {}

        for k, v_b in b.items():
            if k == "sources":
                continue  # handled by caller

            v_a = result.get(k)

            # top-level protection
            if k in protected_keys:
                if self._is_empty(v_a) and not self._is_empty(v_b):
                    result[k] = deepcopy(v_b)
                continue

            # socials
            if k == "socials":
                result[k] = self._merge_socials(v_a or {}, v_b or {}, prefer_b)
                continue

            # list-union fields
            if k in {"category", "exchanges", "network"}:
                la = self._ensure_list(v_a)
                lb = self._ensure_list(v_b)
                result[k] = self._merge_simple_list(la, lb, prefer_b)
                continue

            # admins
            if k == "telegram_admins":
                la = v_a if isinstance(v_a, list) else []
                lb = v_b if isinstance(v_b, list) else []
                result[k] = self._merge_admins(la, lb, prefer_b)
                continue

            # scalar-preference fields (explicit)
            if k in {"market_cap", "about"}:
                result[k] = self._prefer_scalar(v_a, v_b, prefer_b)
                continue

            # default: same as scalar preference for unknown keys
            result[k] = self._prefer_scalar(v_a, v_b, prefer_b)

        return result

    def _get_source_priority_index(self, source: str) -> int:
        """Get priority index of a source (lower number = higher priority)"""
        try:
            return self.source_priority.index(source)
        except ValueError:
            # If source not in priority list, give it lowest priority
            return len(self.source_priority)

    def _get_highest_priority_source(self, sources: Dict) -> str:
        """Get the highest priority source from a sources dict"""
        if not sources:
            return None

        highest_priority_source = None
        highest_priority_index = float('inf')

        for source in sources.keys():
            priority_index = self._get_source_priority_index(source)
            if priority_index < highest_priority_index:
                highest_priority_index = priority_index
                highest_priority_source = source

        return highest_priority_source

    def _merge_data_by_priority(self, existing_data: Dict, new_data: Dict, new_source: str) -> Dict:
        """
        Deep, non-destructive merge with source priority.
        Higher priority updates missing or conflicting fields but never deletes existing data.
        Lists are unioned with de-duplication. Dicts merge recursively.
        """
        merged_data = deepcopy(existing_data) if existing_data else {}
        merged_data.setdefault("sources", {})

        # Update sources: add/refresh new_source and carry over any other provided sources
        now_str = datetime.now().strftime('%Y-%m-%d')
        new_sources_raw = new_data.get("sources", {}) or {}

        # Always record the incoming new_source explicitly
        new_src_url = new_sources_raw.get(new_source, "")
        merged_data["sources"][new_source] = {
            "url": new_src_url,
            "last_updated": now_str,
        }

        # Optionally ingest any other sources present in the payload too
        for src, url in new_sources_raw.items():
            if src == new_source:
                continue
            merged_data["sources"][src] = {
                "url": url,
                "last_updated": now_str,
            }

        # Nothing else to merge
        if not existing_data:
            # First write wins, nothing to compare against
            tmp = deepcopy(new_data)
            tmp.pop("sources", None)
            protected = {"project_uid", "project_name", "project_ticker", "created_at"}
            merged_payload = self._deep_merge({}, tmp, True, protected)
            merged_data.update(merged_payload)
            return merged_data

        # Determine priority
        current_highest_source = self._get_highest_priority_source(merged_data.get("sources", {}))
        current_highest_priority = self._get_source_priority_index(current_highest_source)
        new_source_priority = self._get_source_priority_index(new_source)
        prefer_new = new_source_priority <= current_highest_priority

        # Merge payloads excluding 'sources'
        existing_payload = deepcopy(existing_data)
        existing_payload.pop("sources", None)
        incoming_payload = deepcopy(new_data)
        incoming_payload.pop("sources", None)

        protected = {"project_uid", "project_name", "project_ticker", "created_at"}
        merged_payload = self._deep_merge(existing_payload, incoming_payload, prefer_new, protected)
        # Reattach merged payload
        for k, v in merged_payload.items():
            merged_data[k] = v

        return merged_data

    def find_existing_project(self, project_name: str, project_ticker: str) -> Optional[Dict]:
        """Case-insensitive name + uppercase ticker match."""
        name = (project_name or "").strip()
        ticker = (project_ticker or "").upper().strip()
        if not name or not ticker:
            return None

        pattern = f"^{re.escape(name)}$"  # exact match, ignore case
        return self.collection.find_one({
            "project_name": {"$regex": pattern, "$options": "i"},
            "project_ticker": ticker,
        })

    def upsert_project(self, project_data: Dict, source: str) -> str:
        """
        Insert or update a crypto project

        Args:
            project_data: Project data dictionary
            source: Source of the data (e.g., 'coinmarketcap', 'coingecko')

        Returns:
            project_uid of the inserted/updated project
        """
        project_name = project_data.get('project_name')
        project_ticker = project_data.get('project_ticker', '').upper()

        if not project_name or not project_ticker:
            raise ValueError("project_name and project_ticker are required")

        # Check for existing project
        existing_project = self.find_existing_project(project_name, project_ticker)

        if existing_project:
            # Project exists - merge data based on priority
            merged_data = self._merge_data_by_priority(existing_project, project_data, source)
            project_uid = existing_project['project_uid']

            # Update existing project
            self.collection.update_one(
                {"project_uid": project_uid},
                {"$set": merged_data}
            )

            print(f"Updated project {project_name} ({project_ticker}) from source {source}")

        else:
            # New project - create with new UID
            project_uid = str(uuid.uuid4())

            # Prepare data for insertion
            insert_data = project_data.copy()
            insert_data['project_uid'] = project_uid
            insert_data['project_ticker'] = project_ticker  # Ensure uppercase
            insert_data['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Format sources with timestamp
            if 'sources' in insert_data:
                formatted_sources = {}
                for src, url in insert_data['sources'].items():
                    formatted_sources[src] = {
                        'url': url,
                        'last_updated': datetime.now().strftime('%Y-%m-%d')
                    }
                insert_data['sources'] = formatted_sources

            # Insert new project
            self.collection.insert_one(insert_data)

            print(f"Inserted new project {project_name} ({project_ticker}) from source {source}")

        return project_uid

    def bulk_upsert_projects(self, projects_data: List[Dict], source: str) -> List[str]:
        """
        Bulk upsert multiple projects

        Args:
            projects_data: List of project data dictionaries
            source: Source of the data

        Returns:
            List of project_uids
        """
        project_uids = []

        for project_data in projects_data:
            try:
                project_uid = self.upsert_project(project_data, source)
                project_uids.append(project_uid)
            except Exception as e:
                project_name = project_data.get('project_name', 'Unknown')
                print(f"Failed to upsert project {project_name}: {str(e)}")
                continue

        return project_uids

    def get_project_by_uid(self, project_uid: str) -> Optional[Dict]:
        """Get project by its unique ID"""
        return self.collection.find_one({"project_uid": project_uid})

    def get_project_by_project_name(self, project_name: str) -> Optional[Dict]:
        """Get project by its unique ID"""
        pattern = f"^{re.escape(project_name.strip())}$"
        return self.collection.find_one({"project_name": {"$regex": pattern, "$options": "i"}})

    def get_projects_by_source(self, source: str) -> List[Dict]:
        """Get all projects that have data from a specific source"""
        return list(self.collection.find({f"sources.{source}": {"$exists": True}}))

    def get_projects_by_category(self, category: str) -> List[Dict]:
        """Get all projects in a specific category"""
        return list(self.collection.find({"category": category}))

    from typing import Any, Dict, List, Optional

    def get_projects_grouped_by_duplicate_ticker(
            self, exclude_fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Return full project docs grouped by duplicate ticker, excluding large fields.
        Example: {"project_ticker": "GOLD", "count": 3, "projects": [ {...}, ... ]}
        """
        exclude_fields = exclude_fields or ["about", "exchanges", "category", "telegram_admins"]
        pipeline: List[Dict[str, Any]] = [
            {"$match": {"project_ticker": {"$ne": None, "$ne": ""}}},
        ]

        # Exclude fields from each document before grouping
        if exclude_fields:
            pipeline.append({"$project": {f: 0 for f in exclude_fields}})

        pipeline += [
            {
                "$group": {
                    "_id": "$project_ticker",
                    "count": {"$sum": 1},
                    "projects": {"$push": "$$ROOT"},
                }
            },
            {"$match": {"count": {"$gt": 1}}},
            {"$sort": {"count": -1, "_id": 1}},
            {"$project": {"_id": 0, "project_ticker": "$_id", "count": 1, "projects": 1}},
        ]
        return list(self.collection.aggregate(pipeline, allowDiskUse=True))

    # def get_projects_grouped_by_duplicate_ticker(self) -> List[Dict[str, Any]]:
    #     """
    #     Return full project docs grouped by duplicate ticker.
    #     Example item: {"project_ticker": "GOLD", "count": 3, "projects": [ {...}, {...}, {...} ]}
    #     """
    #     pipeline = [
    #         {"$match": {"project_ticker": {"$ne": None, "$ne": ""}}},
    #         {
    #             "$group": {
    #                 "_id": "$project_ticker",
    #                 "count": {"$sum": 1},
    #                 "projects": {"$push": "$$ROOT"},
    #             }
    #         },
    #         {"$match": {"count": {"$gt": 1}}},
    #         {"$sort": {"count": -1, "_id": 1}},
    #         {"$project": {"_id": 0, "project_ticker": "$_id", "count": 1, "projects": 1}},
    #     ]
    #     return list(self.collection.aggregate(pipeline, allowDiskUse=True))

    def get_project_stats(self) -> Dict:
        """Get database statistics"""
        total_projects = self.collection.count_documents({})

        # Count projects per source
        source_stats = {}
        for source in self.source_priority:
            count = self.collection.count_documents({f"sources.{source}": {"$exists": True}})
            source_stats[source] = count

        return {
            "total_projects": total_projects,
            "projects_per_source": source_stats
        }


# Example usage and testing
if __name__ == "__main__":
    # Example project data
    example_project = {
        "category": [
            "Memes",
            "Ethereum Ecosystem"
        ],
        "exchanges": [
            "stellar-decentralized-exchange",
            "uniswap-v2",
            "zedcex-exchange",
            "dodo",
            "xt"
        ],
        "sources": {
            "coinmarketcap": "https://coinmarketcap.com/currencies/digital-gold-ethereum/",
        },
        "socials": {
            "website": "https://goldgold.club/",
            "telegram_link": "https://t.me/digitalgoldtg",
            "twitter_link": "https://twitter.com/goldgold_coin",
            "email_link": "DigitalGOLD-@outlook.com",
        },
        "market_cap": "$249.67K",
        "project_name": "digital gold",
        "project_ticker": "GOLD",
        "telegram_admins": [
            {
                "first_name": "pe",
                "status": "admin",
                "username": "ppponmoon"
            }
        ]
    }

    # Initialize the manager
    manager = MasterProjectManager(get_mongodb_uri())

    # Usage example:
    # project_uid = manager.upsert_project(example_project, "coinmarketcap")
    # print(f"Project UID: {project_uid}")

    stats = manager.get_project_stats()
    print(f"Database stats: {stats}\n")

    BTC = manager.get_project_by_project_name("Ethereum")
    print(f"BTC stats: {BTC}\n")

    # duplicates = manager.get_projects_grouped_by_duplicate_ticker()
    # print(f"duplicates: {duplicates}\n")


    # "38c75acb-399f-4f03-907b-2d81ce53108b"
    # "df22aa71-e3fe-4243-a2b2-d84feb2e79e8"