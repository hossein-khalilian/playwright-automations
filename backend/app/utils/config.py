import os

from dotenv import load_dotenv

load_dotenv()

config = {
    # MongoDB
    "MONGO_URI": os.environ.get("MONGO_URI"),
    "MONGO_DB_NAME": os.environ.get("MONGO_DB_NAME"),
    # JWT
    "JWT_SECRET_KEY": os.environ.get("JWT_SECRET_KEY"),
    "JWT_ACCESS_TOKEN_EXPIRE_MINUTES": int(
        os.environ.get("JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    ),
    "JWT_ALGORITHM": os.environ.get("JWT_ALGORITHM"),
    # CELERY
    "CELERY_RESULT_BACKEND": os.environ.get("CELERY_RESULT_BACKEND"),
    "CELERY_BROKER_URL": os.environ.get("CELERY_BROKER_URL"),
    # minio
    "MINIO_ENDPOINT": os.environ.get("MINIO_ENDPOINT"),
    "MINIO_ROOT_USER": os.environ.get("MINIO_ROOT_USER"),
    "MINIO_ROOT_PASSWORD": os.environ.get("MINIO_ROOT_PASSWORD"),
    "MINIO_AUDIO_BUCKET": os.environ.get("MINIO_AUDIO_BUCKET"),
    # configs
    "BROWSER_POOL_SIZE": os.environ.get("BROWSER_POOL_SIZE"),
    "GMAIL_EMAIL": os.environ.get("GMAIL_EMAIL"),
    "GMAIL_PASSWORD": os.environ.get("GMAIL_PASSWORD"),
    # Encryption key for email passwords
    "ENCRYPTION_KEY": os.environ.get("ENCRYPTION_KEY"),
}


# Normalize keys to lowercase for easier access (existing behavior)
config = {key.lower(): value for key, value in config.items()}
# Convert browser_pool_size to int, default to 1 if not set
config.update({"browser_pool_size": int(config.get("browser_pool_size", 1))})
