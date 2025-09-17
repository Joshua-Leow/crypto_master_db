from pymongo import MongoClient, ASCENDING
from datetime import datetime
import uuid
from typing import Dict, List, Any, Optional

from config.private import get_mongodb_uri


class MasterProjectManager:
    def __init__(self, connection_string: str, database_name: str = "master_projects"):
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
            "coinmarketcap",
            "coingecko",
            "dextools",
            "dexscreener",
            "birdeye"
        ]

        self._setup_indexes()

    def _setup_indexes(self):
        """Setup MongoDB indexes for optimal performance"""
        # Compound index for duplicate detection
        self.collection.create_index([
            ("project_name", ASCENDING),
            ("project_ticker", ASCENDING)
        ], name="duplicate_detection_idx")

        # Unique index on project_uid
        self.collection.create_index("project_uid", unique=True, name="project_uid_idx")

        # Index on categories for filtering
        self.collection.create_index("category", name="category_idx")

        # Sparse index on market_cap for projects with market data
        self.collection.create_index("market_cap", sparse=True, name="market_cap_idx")

        # Index on sources keys for source-based queries
        self.collection.create_index("sources", name="sources_idx")

        print("MongoDB indexes created successfully")

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
        Merge new data with existing data based on source priority

        Args:
            existing_data: Current project data in database
            new_data: New project data to merge
            new_source: Source of the new data

        Returns:
            Merged data dictionary
        """
        if not existing_data.get('sources'):
            # First time data, just add the new source
            merged_data = new_data.copy()
            merged_data['sources'] = {
                new_source: {
                    'url': new_data.get('sources', {}).get(new_source, ''),
                    'last_updated': datetime.now().strftime('%Y-%m-%d')
                }
            }
            return merged_data

        # Get current highest priority source
        current_highest_source = self._get_highest_priority_source(existing_data['sources'])
        current_highest_priority = self._get_source_priority_index(current_highest_source)
        new_source_priority = self._get_source_priority_index(new_source)

        merged_data = existing_data.copy()

        # Update sources with new source info
        if 'sources' not in merged_data:
            merged_data['sources'] = {}

        merged_data['sources'][new_source] = {
            'url': new_data.get('sources', {}).get(new_source, ''),
            'last_updated': datetime.now().strftime('%Y-%m-%d')
        }

        if new_source_priority <= current_highest_priority:
            # New source has higher/equal priority - update all fields
            for key, value in new_data.items():
                if key != 'sources' and value is not None:
                    merged_data[key] = value
        else:
            # New source has lower priority - only add missing fields
            for key, value in new_data.items():
                if key != 'sources' and value is not None:
                    if key not in merged_data or merged_data[key] is None or merged_data[key] == "":
                        merged_data[key] = value

        return merged_data

    def find_existing_project(self, project_name: str, project_ticker: str) -> Optional[Dict]:
        """
        Find existing project by name and ticker

        Args:
            project_name: Name of the project
            project_ticker: Ticker symbol (should be uppercase)

        Returns:
            Existing project document or None
        """
        return self.collection.find_one({
            "project_name": project_name,
            "project_ticker": project_ticker.upper()
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

    def get_projects_by_source(self, source: str) -> List[Dict]:
        """Get all projects that have data from a specific source"""
        return list(self.collection.find({f"sources.{source}": {"$exists": True}}))

    def get_projects_by_category(self, category: str) -> List[Dict]:
        """Get all projects in a specific category"""
        return list(self.collection.find({"category": category}))

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
    project_uid = manager.upsert_project(example_project, "coinmarketcap")
    print(f"Project UID: {project_uid}")

    # stats = manager.get_project_stats()
    # print(f"Database stats: {stats}")