import os

from dotenv import load_dotenv

load_dotenv()

config = {
    # MongoDB
    "MONGO_URI": os.environ.get("MONGO_URI"),
    "MONGO_DB_NAME": os.environ.get("MONGO_DB_NAME"),
    # JWT
    "JWT_SECRET_KEY": os.environ.get("JWT_SECRET_KEY"),
    "JWT_ACCESS_TOKEN_EXPIRE_MINUTES": os.environ.get(
        "JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    ),
    "JWT_ALGORITHM": os.environ.get("JWT_ALGORITHM"),
}

# Normalize keys to lowercase for easier access (existing behavior)
config = {key.lower(): value for key, value in config.items()}
