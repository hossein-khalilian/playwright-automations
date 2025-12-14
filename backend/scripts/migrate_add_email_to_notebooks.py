#!/usr/bin/env python3
"""
Migration script to add 'email' field to existing notebook documents in MongoDB.

This script:
1. Connects to MongoDB
2. Finds all notebooks that don't have the 'email' field
3. Updates them with the email from GMAIL_EMAIL environment variable
4. Reports how many documents were updated

Usage:
    python backend/scripts/migrate_add_email_to_notebooks.py
"""

import os
import sys
from pathlib import Path

# Add the backend directory to the path so we can import app modules
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# Load environment variables
load_dotenv()

# Import config to use the same configuration system as the app
from app.utils.config import config

# Get configuration from config (which already loads from .env)
MONGO_URI = config.get("mongo_uri")
MONGO_DB_NAME = config.get("mongo_db_name", "playwright_automations")
GMAIL_EMAIL = config.get("gmail_email")


def migrate_notebooks():
    """Add email field to notebooks that don't have it."""
    if not MONGO_URI:
        print("ERROR: MONGO_URI not set in environment variables")
        sys.exit(1)
    
    if not GMAIL_EMAIL:
        print("ERROR: GMAIL_EMAIL not set in environment variables")
        print("Please set GMAIL_EMAIL in your .env file")
        sys.exit(1)
    
    client = None
    try:
        print(f"Connecting to MongoDB at {MONGO_URI}...")
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        
        # Test connection
        client.admin.command("ping")
        print("✓ Successfully connected to MongoDB")
        
        db = client[MONGO_DB_NAME]
        collection = db["notebooks"]
        
        # Find all notebooks that don't have the 'email' field
        # or have it set to None/null
        query = {
            "$or": [
                {"email": {"$exists": False}},
                {"email": None},
                {"email": ""}
            ]
        }
        
        # Count documents to update
        count = collection.count_documents(query)
        print(f"\nFound {count} notebook(s) without email field")
        
        if count == 0:
            print("No notebooks need updating. Migration complete!")
            return
        
        # Ask for confirmation
        print(f"\nThis will update {count} notebook(s) with email: {GMAIL_EMAIL}")
        response = input("Do you want to proceed? (yes/no): ").strip().lower()
        
        if response not in ["yes", "y"]:
            print("Migration cancelled.")
            return
        
        # Update all matching documents
        print("\nUpdating notebooks...")
        result = collection.update_many(
            query,
            {
                "$set": {
                    "email": GMAIL_EMAIL
                }
            }
        )
        
        print(f"\n✓ Migration complete!")
        print(f"  - Documents matched: {result.matched_count}")
        print(f"  - Documents modified: {result.modified_count}")
        
        # Verify the update
        remaining = collection.count_documents(query)
        if remaining == 0:
            print(f"  - All notebooks now have the email field")
        else:
            print(f"  - Warning: {remaining} notebook(s) still missing email field")
        
    except ConnectionFailure:
        print("ERROR: Could not connect to MongoDB")
        print(f"Please check your MONGO_URI: {MONGO_URI}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if client:
            client.close()
            print("\nConnection closed.")


if __name__ == "__main__":
    print("=" * 60)
    print("MongoDB Migration: Add email field to notebooks")
    print("=" * 60)
    migrate_notebooks()
