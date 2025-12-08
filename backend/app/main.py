import asyncio
import logging
import os
import sys

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.automation.tasks.google_login import check_or_login_google_sync
from app.routes.auth_api import router as auth_router
from app.routes.google_api import router as google_router
from app.routes.notebooklm_api import router as notebooklm_router
from app.utils.browser_state import clear_browser_resources, set_browser_resources
from app.utils.browser_utils import initialize_page_sync
from app.utils.config import config

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
api_router.include_router(google_router)
api_router.include_router(notebooklm_router)


app = FastAPI(
    title="Playwright Automations API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


def _initialize_browser_sync():
    """Synchronous function to initialize browser pool and login to Google."""
    try:
        # Get configuration from environment variables
        user_profile_name = os.getenv("GOOGLE_PROFILE_NAME", "default")
        headless = os.getenv("BROWSER_HEADLESS", "true").lower() == "true"

        # Get pool size from config, default to 1 if not set
        pool_size = config.get("browser_pool_size", 1)
        if pool_size < 1:
            pool_size = 1

        logger.info(
            f"Initializing browser pool with {pool_size} pages "
            f"(profile: {user_profile_name}, headless: {headless})"
        )

        # Initialize first browser page (this creates the context)
        first_page, context, playwright = initialize_page_sync(
            headless=headless, user_profile_name=user_profile_name
        )

        # Check if already logged in, or login if needed
        # Since all pages share the same persistent context, they'll all share the login session
        logger.info("Checking Google login status on first page...")
        check_or_login_google_sync(first_page)

        # Create list of pages: first page + additional pages
        pages = [first_page]

        # Create additional pages from the same context
        if pool_size > 1:
            logger.info(f"Creating {pool_size - 1} additional pages...")
            for i in range(pool_size - 1):
                try:
                    new_page = context.new_page()
                    pages.append(new_page)
                    logger.info(f"Created page {i + 2}/{pool_size}")
                except Exception as e:
                    logger.warning(f"Failed to create page {i + 2}: {e}")
                    # Continue with whatever pages we managed to create

        # Navigate all pages to Gmail to ensure they have active session
        # This is important because new pages start on about:blank
        logger.info("Navigating all pages to Gmail to activate login session...")
        gmail_url = "https://mail.google.com/mail/u/0/#inbox"
        for index, page in enumerate(pages):
            try:
                if not page.is_closed():
                    logger.info(f"Navigating page {index} to Gmail...")
                    page.goto(gmail_url, wait_until="domcontentloaded", timeout=60_000)
                    page.wait_for_timeout(2_000)  # Wait for page to fully load
                    logger.info(f"Page {index} successfully navigated to Gmail")
                else:
                    logger.warning(f"Page {index} is closed, skipping navigation")
            except Exception as e:
                logger.warning(f"Failed to navigate page {index} to Gmail: {e}")

        # Store browser resources in global state
        set_browser_resources(pages, context, playwright)

        logger.info(
            f"Browser pool initialized successfully with {len(pages)} pages "
            f"(all logged into Google)!"
        )
        return True
    except Exception as e:
        logger.error(f"Failed to initialize browser pool: {e}", exc_info=True)
        return False


@app.on_event("startup")
async def startup_event():
    """Initialize browser and login to Google on FastAPI startup."""
    logger.info("Starting browser initialization...")
    # Run sync code in thread executor since FastAPI handlers are async
    success = await asyncio.to_thread(_initialize_browser_sync)
    if not success:
        logger.warning(
            "Browser initialization failed. Some endpoints may not work correctly."
        )


def _cleanup_browser_sync():
    """Synchronous function to clean up browser resources."""
    try:
        from app.utils.browser_state import get_browser_context, get_playwright

        context = get_browser_context()
        playwright = get_playwright()

        if context:
            try:
                context.close()
                logger.info("Browser context closed.")
            except Exception as e:
                logger.warning(f"Error closing browser context: {e}")

        if playwright:
            try:
                playwright.stop()
                logger.info("Playwright stopped.")
            except Exception as e:
                logger.warning(f"Error stopping playwright: {e}")

        clear_browser_resources()
        logger.info("Browser resources cleaned up.")
    except Exception as e:
        logger.error(f"Error during browser cleanup: {e}", exc_info=True)


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up browser resources on FastAPI shutdown."""
    logger.info("Cleaning up browser resources...")
    await asyncio.to_thread(_cleanup_browser_sync)


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok"}
