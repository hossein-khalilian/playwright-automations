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
from bson import ObjectId

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
        
        # Step 2: Migrate users from role names to role_ids
        print("\n" + "=" * 60)
        print("Step 2: Migrating users from role names to role_ids")
        print("=" * 60)
        
        # Find all users that need migration:
        # - Users with 'role' field (old single role)
        # - Users with 'roles' field but not 'role_ids' (role names array)
        query = {
            "$or": [
                {"role": {"$exists": True}},
                {"roles": {"$exists": True}, "role_ids": {"$exists": False}}
            ]
        }
        
        # Count documents to update
        count = users_collection.count_documents(query)
        print(f"\nFound {count} user(s) that need migration to role_ids")
        
        if count == 0:
            print("✓ No users need migration. All users already have 'role_ids' field")
        else:
            # Build a mapping of role names to role_ids
            role_name_to_id = {}
            all_roles = list(roles_collection.find({}, {"_id": 1, "role_name": 1}))
            for role in all_roles:
                role_name_to_id[role["role_name"]] = role["_id"]
            
            # Show preview of users to be migrated
            print("\nUsers to be migrated:")
            users_to_migrate = list(users_collection.find(query, {"username": 1, "role": 1, "roles": 1}).limit(10))
            for user in users_to_migrate:
                username = user.get("username", "unknown")
                if "role" in user:
                    old_role = user.get("role", "user")
                    role_id = role_name_to_id.get(old_role)
                    print(f"  - {username}: '{old_role}' -> role_id: {role_id}")
                elif "roles" in user:
                    old_roles = user.get("roles", [])
                    role_ids = [role_name_to_id.get(r) for r in old_roles if r in role_name_to_id]
                    print(f"  - {username}: {old_roles} -> role_ids: {role_ids}")
            if count > 10:
                print(f"  ... and {count - 10} more")
            
            # Ask for confirmation
            print(f"\nThis will migrate {count} user(s) from role names to role_ids")
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
                    username = user.get("username", "unknown")
                    role_ids = []
                    
                    # Handle old single 'role' field
                    if "role" in user:
                        old_role = user.get("role", "user")
                        role_id = role_name_to_id.get(old_role)
                        if role_id:
                            role_ids = [role_id]
                        else:
                            # Default to user role if role not found
                            user_role_id = role_name_to_id.get("user")
                            if user_role_id:
                                role_ids = [user_role_id]
                            errors.append(f"Role '{old_role}' not found for {username}, defaulted to 'user'")
                    
                    # Handle 'roles' array (role names)
                    elif "roles" in user:
                        old_roles = user.get("roles", [])
                        for role_name in old_roles:
                            role_id = role_name_to_id.get(role_name)
                            if role_id:
                                role_ids.append(role_id)
                            else:
                                errors.append(f"Role '{role_name}' not found for {username}")
                        
                        # If no valid role_ids found, default to user role
                        if not role_ids:
                            user_role_id = role_name_to_id.get("user")
                            if user_role_id:
                                role_ids = [user_role_id]
                    
                    # If still no role_ids, skip this user
                    if not role_ids:
                        errors.append(f"No valid role_ids found for {username}")
                        continue
                    
                    # Update user document
                    update_op = {
                        "$set": {"role_ids": role_ids}
                    }
                    # Remove old fields
                    unset_op = {}
                    if "role" in user:
                        unset_op["role"] = ""
                    if "roles" in user and "role_ids" not in user:
                        unset_op["roles"] = ""
                    
                    if unset_op:
                        update_op["$unset"] = unset_op
                    
                    result = users_collection.update_one(
                        {"_id": user["_id"]},
                        update_op
                    )
                    
                    if result.modified_count > 0:
                        migrated_count += 1
                        role_names = [r["role_name"] for r in all_roles if r["_id"] in role_ids]
                        print(f"  ✓ Migrated {username}: {role_names} -> {len(role_ids)} role_id(s)")
                    else:
                        errors.append(f"Failed to migrate {username}")
                        
                except Exception as e:
                    errors.append(f"Error migrating {user.get('username', 'unknown')}: {str(e)}")
            
            print(f"\n✓ User migration complete!")
            print(f"  - Users migrated: {migrated_count}")
            if errors:
                print(f"  - Errors/Warnings: {len(errors)}")
                for error in errors[:10]:  # Show first 10 errors
                    print(f"    - {error}")
                if len(errors) > 10:
                    print(f"    ... and {len(errors) - 10} more errors")
        
        # Step 3: Clean up old role name fields
        print("\n" + "=" * 60)
        print("Step 3: Cleaning up old role name fields")
        print("=" * 60)
        
        # Remove 'role' field from users that have role_ids
        query_old_role = {
            "role": {"$exists": True},
            "role_ids": {"$exists": True}
        }
        
        count_old_role = users_collection.count_documents(query_old_role)
        if count_old_role > 0:
            print(f"Found {count_old_role} user(s) with both 'role' and 'role_ids' fields")
            response = input("Remove old 'role' field from these users? (yes/no): ").strip().lower()
            
            if response in ["yes", "y"]:
                result = users_collection.update_many(
                    query_old_role,
                    {"$unset": {"role": ""}}
                )
                print(f"✓ Removed 'role' field from {result.modified_count} user(s)")
        else:
            print("✓ No users have both 'role' and 'role_ids' fields")
        
        # Remove 'roles' field from users that have role_ids
        query_old_roles = {
            "roles": {"$exists": True},
            "role_ids": {"$exists": True}
        }
        
        count_old_roles = users_collection.count_documents(query_old_roles)
        if count_old_roles > 0:
            print(f"Found {count_old_roles} user(s) with both 'roles' and 'role_ids' fields")
            response = input("Remove old 'roles' field from these users? (yes/no): ").strip().lower()
            
            if response in ["yes", "y"]:
                result = users_collection.update_many(
                    query_old_roles,
                    {"$unset": {"roles": ""}}
                )
                print(f"✓ Removed 'roles' field from {result.modified_count} user(s)")
        else:
            print("✓ No users have both 'roles' and 'role_ids' fields")
        
        # Step 4: Ensure all users have 'role_ids' field
        print("\n" + "=" * 60)
        print("Step 4: Ensuring all users have 'role_ids' field")
        print("=" * 60)
        
        query_no_role_ids = {
            "role_ids": {"$exists": False}
        }
        
        count_no_role_ids = users_collection.count_documents(query_no_role_ids)
        if count_no_role_ids > 0:
            # Get user role_id
            user_role = roles_collection.find_one({"role_name": "user"})
            if user_role:
                user_role_id = user_role["_id"]
                print(f"Found {count_no_role_ids} user(s) without 'role_ids' field")
                response = input(f"Add default 'role_ids' field ([{user_role_id}]) to these users? (yes/no): ").strip().lower()
                
                if response in ["yes", "y"]:
                    result = users_collection.update_many(
                        query_no_role_ids,
                        {"$set": {"role_ids": [user_role_id]}}
                    )
                    print(f"✓ Added default 'role_ids' field to {result.modified_count} user(s)")
            else:
                print("⚠ Warning: 'user' role not found. Cannot set default role_ids.")
        else:
            print("✓ All users have 'role_ids' field")
        
        # Final summary
        print("\n" + "=" * 60)
        print("Migration Summary")
        print("=" * 60)
        
        total_users = users_collection.count_documents({})
        users_with_role_ids = users_collection.count_documents({"role_ids": {"$exists": True}})
        users_with_old_role = users_collection.count_documents({"role": {"$exists": True}})
        users_with_old_roles = users_collection.count_documents({"roles": {"$exists": True}, "role_ids": {"$exists": False}})
        
        print(f"Total users: {total_users}")
        print(f"Users with 'role_ids' field: {users_with_role_ids}")
        print(f"Users with old 'role' field: {users_with_old_role}")
        print(f"Users with old 'roles' field (without role_ids): {users_with_old_roles}")
        
        if users_with_role_ids == total_users and users_with_old_role == 0 and users_with_old_roles == 0:
            print("\n✓ Migration completed successfully!")
            print("  All users have been migrated to the new role_ids system.")
        else:
            print("\n⚠ Migration completed with warnings:")
            if users_with_role_ids < total_users:
                print(f"  - {total_users - users_with_role_ids} user(s) still missing 'role_ids' field")
            if users_with_old_role > 0:
                print(f"  - {users_with_old_role} user(s) still have old 'role' field")
            if users_with_old_roles > 0:
                print(f"  - {users_with_old_roles} user(s) still have old 'roles' field without 'role_ids'")
        
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
    print("MongoDB Migration: Migrate to Role IDs System")
    print("=" * 60)
    print("This migration will:")
    print("  1. Initialize default roles (admin, user)")
    print("  2. Convert user role names to role_ids (ObjectIds)")
    print("  3. Remove old role name fields")
    print("  4. Ensure all users have role_ids")
    print("=" * 60)
    migrate_users()

