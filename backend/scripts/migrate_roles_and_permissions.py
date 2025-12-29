#!/usr/bin/env python3
"""
Migration script to migrate from single role to multiple roles system.

This script:
1. Connects to MongoDB
2. Initializes default roles and permissions (admin, user)
3. Migrates users from old 'role' field to new 'roles' array
4. Removes the old 'role' field from user documents
5. Reports migration statistics

Usage:
    python backend/scripts/migrate_roles_and_permissions.py
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

# Add the backend directory to the path so we can import app modules
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError

# Load environment variables
load_dotenv()

# Import config to use the same configuration system as the app
from app.utils.config import config

# Get configuration from config (which already loads from .env)
MONGO_URI = config.get("mongo_uri")
MONGO_DB_NAME = config.get("mongo_db_name", "playwright_automations")


def migrate_users():
    """Migrate users from single role to roles array."""
    if not MONGO_URI:
        print("ERROR: MONGO_URI not set in environment variables")
        sys.exit(1)
    
    client = None
    try:
        print(f"Connecting to MongoDB at {MONGO_URI}...")
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        
        # Test connection
        client.admin.command("ping")
        print("✓ Successfully connected to MongoDB")
        
        db = client[MONGO_DB_NAME]
        users_collection = db["users"]
        roles_collection = db["roles"]
        
        # Step 1: Initialize default roles and permissions
        print("\n" + "=" * 60)
        print("Step 1: Initializing default roles and permissions")
        print("=" * 60)
        
        # Ensure unique index on role_name
        try:
            roles_collection.create_index("role_name", unique=True)
        except Exception:
            pass  # Index might already exist
        
        # Define admin permissions
        admin_permissions = [
            "manage_google_credentials",
            "manage_users",
            "access_admin_panel",
            "view_all_notebooks",
            "manage_roles",
            "manage_permissions",
        ]
        
        # Check if roles already exist
        existing_roles = list(roles_collection.find({}, {"role_name": 1}))
        existing_role_names = [r["role_name"] for r in existing_roles]
        
        roles_created = 0
        
        # Create admin role if it doesn't exist
        if "admin" not in existing_role_names:
            try:
                roles_collection.insert_one({
                    "role_name": "admin",
                    "description": "Administrator with full system access",
                    "permissions": admin_permissions,
                    "created_at": datetime.now(timezone.utc),
                })
                print("✓ Created 'admin' role")
                roles_created += 1
            except DuplicateKeyError:
                print("✓ 'admin' role already exists")
        else:
            print("✓ 'admin' role already exists")
        
        # Create user role if it doesn't exist
        if "user" not in existing_role_names:
            try:
                roles_collection.insert_one({
                    "role_name": "user",
                    "description": "Standard user with basic access",
                    "permissions": ["access_notebooks", "create_notebooks"],
                    "created_at": datetime.now(timezone.utc),
                })
                print("✓ Created 'user' role")
                roles_created += 1
            except DuplicateKeyError:
                print("✓ 'user' role already exists")
        else:
            print("✓ 'user' role already exists")
        
        if roles_created == 0:
            print("\n✓ All default roles already exist")
        else:
            print(f"\n✓ Created {roles_created} new role(s)")
        
        # Step 2: Migrate users from 'role' to 'roles'
        print("\n" + "=" * 60)
        print("Step 2: Migrating users from 'role' to 'roles'")
        print("=" * 60)
        
        # Find all users that have 'role' field but not 'roles' field
        query = {
            "role": {"$exists": True},
            "roles": {"$exists": False}
        }
        
        # Count documents to update
        count = users_collection.count_documents(query)
        print(f"\nFound {count} user(s) with old 'role' field")
        
        if count == 0:
            print("✓ No users need migration. All users already have 'roles' field")
        else:
            # Show preview of users to be migrated
            print("\nUsers to be migrated:")
            users_to_migrate = list(users_collection.find(query, {"username": 1, "role": 1}).limit(10))
            for user in users_to_migrate:
                print(f"  - {user.get('username', 'unknown')}: '{user.get('role', 'unknown')}' -> ['{user.get('role', 'user')}']")
            if count > 10:
                print(f"  ... and {count - 10} more")
            
            # Ask for confirmation
            print(f"\nThis will migrate {count} user(s) from 'role' to 'roles' array")
            response = input("Do you want to proceed? (yes/no): ").strip().lower()
            
            if response not in ["yes", "y"]:
                print("Migration cancelled.")
                return
            
            # Migrate users
            print("\nMigrating users...")
            migrated_count = 0
            errors = []
            
            for user in users_collection.find(query):
                try:
                    old_role = user.get("role", "user")
                    username = user.get("username", "unknown")
                    
                    # Convert single role to roles array
                    new_roles = [old_role] if old_role else ["user"]
                    
                    # Update user document
                    result = users_collection.update_one(
                        {"_id": user["_id"]},
                        {
                            "$set": {"roles": new_roles},
                            "$unset": {"role": ""}
                        }
                    )
                    
                    if result.modified_count > 0:
                        migrated_count += 1
                        print(f"  ✓ Migrated {username}: '{old_role}' -> {new_roles}")
                    else:
                        errors.append(f"Failed to migrate {username}")
                        
                except Exception as e:
                    errors.append(f"Error migrating {user.get('username', 'unknown')}: {str(e)}")
            
            print(f"\n✓ User migration complete!")
            print(f"  - Users migrated: {migrated_count}")
            if errors:
                print(f"  - Errors: {len(errors)}")
                for error in errors:
                    print(f"    - {error}")
        
        # Step 3: Clean up any users that have both 'role' and 'roles' (shouldn't happen, but just in case)
        print("\n" + "=" * 60)
        print("Step 3: Cleaning up users with both 'role' and 'roles'")
        print("=" * 60)
        
        query_both = {
            "role": {"$exists": True},
            "roles": {"$exists": True}
        }
        
        count_both = users_collection.count_documents(query_both)
        if count_both > 0:
            print(f"Found {count_both} user(s) with both 'role' and 'roles' fields")
            response = input("Remove old 'role' field from these users? (yes/no): ").strip().lower()
            
            if response in ["yes", "y"]:
                result = users_collection.update_many(
                    query_both,
                    {"$unset": {"role": ""}}
                )
                print(f"✓ Removed 'role' field from {result.modified_count} user(s)")
        else:
            print("✓ No users have both fields")
        
        # Step 4: Ensure all users have 'roles' field
        print("\n" + "=" * 60)
        print("Step 4: Ensuring all users have 'roles' field")
        print("=" * 60)
        
        query_no_roles = {
            "roles": {"$exists": False}
        }
        
        count_no_roles = users_collection.count_documents(query_no_roles)
        if count_no_roles > 0:
            print(f"Found {count_no_roles} user(s) without 'roles' field")
            response = input("Add default 'roles' field (['user']) to these users? (yes/no): ").strip().lower()
            
            if response in ["yes", "y"]:
                result = users_collection.update_many(
                    query_no_roles,
                    {"$set": {"roles": ["user"]}}
                )
                print(f"✓ Added default 'roles' field to {result.modified_count} user(s)")
        else:
            print("✓ All users have 'roles' field")
        
        # Final summary
        print("\n" + "=" * 60)
        print("Migration Summary")
        print("=" * 60)
        
        total_users = users_collection.count_documents({})
        users_with_roles = users_collection.count_documents({"roles": {"$exists": True}})
        users_with_old_role = users_collection.count_documents({"role": {"$exists": True}})
        
        print(f"Total users: {total_users}")
        print(f"Users with 'roles' field: {users_with_roles}")
        print(f"Users with old 'role' field: {users_with_old_role}")
        
        if users_with_roles == total_users and users_with_old_role == 0:
            print("\n✓ Migration completed successfully!")
            print("  All users have been migrated to the new roles system.")
        else:
            print("\n⚠ Migration completed with warnings:")
            if users_with_roles < total_users:
                print(f"  - {total_users - users_with_roles} user(s) still missing 'roles' field")
            if users_with_old_role > 0:
                print(f"  - {users_with_old_role} user(s) still have old 'role' field")
        
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
    print("MongoDB Migration: Migrate to Multiple Roles System")
    print("=" * 60)
    migrate_users()

