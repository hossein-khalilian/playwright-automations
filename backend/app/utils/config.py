import os

from dotenv import load_dotenv

load_dotenv()

config = {
    # MongoDB
    "MONGO_URI": os.environ.get("MONGO_URI"),
    "MONGO_DB_NAME": os.environ.get("MONGO_DB_NAME"),
    "MONGO_ACCOUNT_COLLECTION": os.environ.get("MONGO_ACCOUNT_COLLECTION"),
}

# Normalize keys to lowercase for easier access (existing behavior)
config = {key.lower(): value for key, value in config.items()}
