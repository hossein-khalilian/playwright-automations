from datetime import datetime, timezone
from typing import Optional

from pymongo import AsyncMongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError

from app.utils.config import config

# Global async MongoDB client (reused across requests)
_db_client: Optional[AsyncMongoClient] = None


async def get_db_client() -> Optional[AsyncMongoClient]:
    """Get or create async MongoDB client connection."""
    global _db_client
    
    if _db_client is not None:
        return _db_client
    
    mongo_uri = config.get("mongo_uri")
    if not mongo_uri:
        return None
    
    try:
        client = AsyncMongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        # Test connection
        await client.admin.command("ping")
        _db_client = client
        return client
    except ConnectionFailure:
        return None
    except Exception:
        return None


async def get_users_collection():
    """Get the users collection from MongoDB."""
    client = await get_db_client()
    if client is None:
        return None
    db_name = config.get("mongo_db_name", "playwright_automations")
    db = client[db_name]
    return db["users"]


async def create_user(username: str, hashed_password: str) -> bool:
    """
    Create a new user in the database.
    Returns True if successful, False if user already exists or database error.
    """
    collection = await get_users_collection()
    if collection is None:
        return False

    try:
        # Create unique index on username if it doesn't exist
        await collection.create_index("username", unique=True)

        user_doc = {
            "username": username,
            "hashed_password": hashed_password,
            "created_at": datetime.now(timezone.utc),
            "is_active": True,
        }
        await collection.insert_one(user_doc)
        return True
    except DuplicateKeyError:
        return False
    except Exception:
        return False


async def get_user_by_username(username: str) -> Optional[dict]:
    """Get user document by username."""
    collection = await get_users_collection()
    if collection is None:
        return None

    try:
        user = await collection.find_one({"username": username})
        return user
    except Exception:
        return None


async def user_exists(username: str) -> bool:
    """Check if a user exists in the database."""
    user = await get_user_by_username(username)
    return user is not None


async def close_db_client():
    """Close the MongoDB client connection. Call this on app shutdown."""
    global _db_client
    if _db_client is not None:
        await _db_client.close()
        _db_client = None
