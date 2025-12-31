import logging
import sys

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.admin_api import router as admin_router
from app.routes.auth_api import router as auth_router
from app.routes.notebooklm_api import router as notebooklm_router
from app.utils.db import initialize_default_roles_and_permissions

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
    force=True,  # Override any existing logging configuration
)

logger = logging.getLogger(__name__)

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(notebooklm_router)
api_router.include_router(admin_router)


app = FastAPI(
    title="Playwright Automations API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.on_event("startup")
async def startup_event():
    """Initialize default roles and permissions on application startup."""
    import os

    # Ensure PLAYWRIGHT_BROWSERS_PATH is set to system-wide location
    if not os.environ.get("PLAYWRIGHT_BROWSERS_PATH"):
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/ms-playwright"
        logger.info(f"Set PLAYWRIGHT_BROWSERS_PATH to /ms-playwright")

    logger.info("Initializing default roles and permissions...")
    success = await initialize_default_roles_and_permissions()
    if success:
        logger.info("Default roles and permissions initialized successfully")
    else:
        logger.warning("Failed to initialize default roles and permissions")

    # Note: Browser profile initialization is handled by the Celery worker,
    # not by the FastAPI backend. This ensures Playwright operations are
    # only performed in the worker process.


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok"}
