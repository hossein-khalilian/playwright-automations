from datetime import datetime, timezone
from typing import List, Optional

from pymongo import AsyncMongoClient, MongoClient
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


async def get_notebooks_collection():
    """Get the notebooks collection from MongoDB."""
    client = await get_db_client()
    if client is None:
        return None
    db_name = config.get("mongo_db_name", "playwright_automations")
    db = client[db_name]
    return db["notebooks"]


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


def save_notebook_sync(username: str, notebook_id: str, notebook_url: str, email: str = None) -> bool:
    """
    Save a notebook to the database for a user (sync version for Celery tasks).
    Returns True if successful, False if database error.
    """
    mongo_uri = config.get("mongo_uri")
    if not mongo_uri:
        return False
    
    db_name = config.get("mongo_db_name", "playwright_automations")
    client = None
    
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        db = client[db_name]
        collection = db["notebooks"]
        
        # Create index on username and notebook_id if they don't exist
        collection.create_index("username")
        collection.create_index([("username", 1), ("notebook_id", 1)], unique=True)
        
        notebook_doc = {
            "username": username,
            "notebook_id": notebook_id,
            "notebook_url": notebook_url,
            "created_at": datetime.now(timezone.utc),
        }
        if email:
            notebook_doc["email"] = email
        collection.insert_one(notebook_doc)
        return True
    except DuplicateKeyError:
        # Notebook already exists for this user, which is fine
        return True
    except ConnectionFailure:
        return False
    except Exception:
        return False
    finally:
        if client is not None:
            client.close()


def delete_notebook_sync(username: str, notebook_id: str) -> bool:
    """
    Delete a notebook from the database for a user (sync version for Celery tasks).
    Returns True if successful (including if notebook didn't exist), False on database error.
    """
    mongo_uri = config.get("mongo_uri")
    if not mongo_uri:
        return False

    db_name = config.get("mongo_db_name", "playwright_automations")
    client = None

    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        db = client[db_name]
        collection = db["notebooks"]

        collection.delete_one({"username": username, "notebook_id": notebook_id})
        return True
    except ConnectionFailure:
        return False
    except Exception:
        return False
    finally:
        if client is not None:
            client.close()

async def get_notebooks_by_user(username: str) -> List[dict]:
    """
    Get all notebooks for a user.
    Returns a list of notebook documents, or empty list if error.
    """
    collection = await get_notebooks_collection()
    if collection is None:
        return []

    try:
        cursor = collection.find({"username": username}).sort("created_at", -1)
        notebooks = await cursor.to_list(length=None)
        return notebooks
    except Exception:
        return []


async def delete_notebook_from_db(username: str, notebook_id: str) -> bool:
    """
    Delete a notebook from the database for a user.
    Returns True if successful (including if notebook didn't exist), False if database error.
    """
    collection = await get_notebooks_collection()
    if collection is None:
        return False

    try:
        result = await collection.delete_one(
            {"username": username, "notebook_id": notebook_id}
        )
        # Return True even if no document was deleted (notebook didn't exist)
        return True
    except Exception:
        return False


async def update_notebook_title(username: str, notebook_id: str, title: Optional[str]) -> bool:
    """
    Update the title of a notebook in the database.
    Returns True if successful, False if database error.
    """
    collection = await get_notebooks_collection()
    if collection is None:
        return False

    try:
        result = await collection.update_one(
            {"username": username, "notebook_id": notebook_id},
            {"$set": {"title": title}}
        )
        return True
    except Exception:
        return False


async def update_notebook_titles(username: str, titles: dict) -> bool:
    """
    Update titles for multiple notebooks.
    
    Args:
        username: The username
        titles: Dictionary mapping notebook_id to title (or None)
    
    Returns:
        True if successful, False if database error
    """
    collection = await get_notebooks_collection()
    if collection is None:
        return False

    try:
        for notebook_id, title in titles.items():
            await collection.update_one(
                {"username": username, "notebook_id": notebook_id},
                {"$set": {"title": title}}
            )
        return True
    except Exception:
        return False


def update_notebook_title_sync(username: str, notebook_id: str, title: Optional[str]) -> bool:
    """
    Update the title of a notebook in the database (sync version for Celery tasks).
    Returns True if successful, False if database error.
    """
    mongo_uri = config.get("mongo_uri")
    if not mongo_uri:
        return False
    
    db_name = config.get("mongo_db_name", "playwright_automations")
    client = None
    
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        db = client[db_name]
        collection = db["notebooks"]
        
        collection.update_one(
            {"username": username, "notebook_id": notebook_id},
            {"$set": {"title": title}}
        )
        return True
    except Exception:
        return False
    finally:
        if client is not None:
            client.close()


def update_notebook_titles_sync(username: str, titles: dict) -> bool:
    """
    Update titles for multiple notebooks (sync version for Celery tasks).
    
    Args:
        username: The username
        titles: Dictionary mapping notebook_id to title (or None)
    
    Returns:
        True if successful, False if database error
    """
    mongo_uri = config.get("mongo_uri")
    if not mongo_uri:
        return False
    
    db_name = config.get("mongo_db_name", "playwright_automations")
    client = None
    
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        db = client[db_name]
        collection = db["notebooks"]
        
        for notebook_id, title in titles.items():
            collection.update_one(
                {"username": username, "notebook_id": notebook_id},
                {"$set": {"title": title}}
            )
        return True
    except Exception:
        return False
    finally:
        if client is not None:
            client.close()


async def close_db_client():
    """Close the MongoDB client connection. Call this on app shutdown."""
    global _db_client
    if _db_client is not None:
        await _db_client.close()
        _db_client = None
