import logging
import os

from celery import Celery
from celery.signals import worker_ready, worker_shutting_down

from app.automation.tasks.google_login import check_or_login_google_sync
from app.utils.browser_state import set_browser_resources
from app.utils.browser_utils import initialize_page_sync
from app.utils.config import config

logger = logging.getLogger(__name__)

celery_app = Celery(
    "worker",
    broker=config.get("celery_broker_url"),
    backend=config.get("celery_result_backend"),
    include=["app.celery_tasks.notebooklm"],
)

celery_app.conf.update(
    task_track_started=True,
    worker_pool="solo",  # Use solo pool for sync Playwright - no asyncio event loop
)


@worker_ready.connect
def initialize_browser_pool_on_worker_start(sender, **kwargs):
    """
    Initialize browser pool when Celery worker starts.
    This ensures each worker has its own browser pool ready for tasks.
    """
    try:
        # Get configuration from environment variables
        user_profile_name = os.getenv("GOOGLE_PROFILE_NAME", "default")
        headless = os.getenv("BROWSER_HEADLESS", "true").lower() == "true"

        # Get pool size from config, default to 1 if not set
        pool_size = config.get("browser_pool_size", 1)
        if pool_size < 1:
            pool_size = 1

        logger.info(
            f"[Celery Worker] Initializing browser pool with {pool_size} pages "
            f"(profile: {user_profile_name}, headless: {headless})"
        )

        # Initialize first browser page (this creates the context)
        first_page, context, playwright = initialize_page_sync(
            headless=headless, user_profile_name=user_profile_name
        )

        # Check if already logged in, or login if needed
        logger.info("[Celery Worker] Checking Google login status on first page...")
        check_or_login_google_sync(first_page)

        # Create list of pages: first page + additional pages
        pages = [first_page]

        # Create additional pages from the same context
        if pool_size > 1:
            logger.info(f"[Celery Worker] Creating {pool_size - 1} additional pages...")
            for i in range(pool_size - 1):
                try:
                    new_page = context.new_page()
                    pages.append(new_page)
                    logger.info(f"[Celery Worker] Created page {i + 2}/{pool_size}")
                except Exception as e:
                    logger.warning(f"[Celery Worker] Failed to create page {i + 2}: {e}")

        # Navigate all pages to Gmail to ensure they have active session
        logger.info("[Celery Worker] Navigating all pages to Gmail to activate login session...")
        gmail_url = "https://mail.google.com/mail/u/0/#inbox"
        for index, page in enumerate(pages):
            try:
                if not page.is_closed():
                    logger.info(f"[Celery Worker] Navigating page {index} to Gmail...")
                    page.goto(gmail_url, wait_until="domcontentloaded", timeout=60_000)
                    page.wait_for_timeout(2_000)  # Wait for page to fully load
                    logger.info(f"[Celery Worker] Page {index} successfully navigated to Gmail")
                else:
                    logger.warning(f"[Celery Worker] Page {index} is closed, skipping navigation")
            except Exception as e:
                logger.warning(f"[Celery Worker] Failed to navigate page {index} to Gmail: {e}")

        # Store browser resources in global state
        set_browser_resources(pages, context, playwright)

        logger.info(
            f"[Celery Worker] Browser pool initialized successfully with {len(pages)} pages "
            f"(all logged into Google)!"
        )
    except Exception as e:
        logger.error(
            f"[Celery Worker] Failed to initialize browser pool: {e}",
            exc_info=True,
        )
        logger.warning(
            "[Celery Worker] Tasks will fall back to creating new browser instances."
        )


@worker_shutting_down.connect
def cleanup_browser_pool_on_worker_shutdown(sender, **kwargs):
    """
    Clean up browser pool when Celery worker shuts down.
    """
    try:
        from app.utils.browser_state import (
            clear_browser_resources,
            get_browser_context,
            get_playwright,
        )

        logger.info("[Celery Worker] Cleaning up browser resources...")

        context = get_browser_context()
        playwright = get_playwright()

        if context:
            try:
                context.close()
                logger.info("[Celery Worker] Browser context closed.")
            except Exception as e:
                logger.warning(f"[Celery Worker] Error closing browser context: {e}")

        if playwright:
            try:
                playwright.stop()
                logger.info("[Celery Worker] Playwright stopped.")
            except Exception as e:
                logger.warning(f"[Celery Worker] Error stopping playwright: {e}")

        clear_browser_resources()
        logger.info("[Celery Worker] Browser resources cleaned up.")
    except Exception as e:
        logger.error(
            f"[Celery Worker] Error during browser cleanup: {e}", exc_info=True
        )
