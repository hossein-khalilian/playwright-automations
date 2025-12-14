import logging
import os

from celery import Celery
from celery.signals import worker_ready, worker_shutting_down

from app.automation.tasks.google_login import check_or_login_google_sync
from app.utils.browser_state import get_all_contexts, set_browser_resources
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
    Each browser in the pool will have its own separate browser profile.
    Profile names will be: {user_profile_name}_0, {user_profile_name}_1, etc.
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
            f"[Celery Worker] Initializing browser pool with {pool_size} browsers "
            f"(base profile: {user_profile_name}, headless: {headless})"
        )
        logger.info(
            f"[Celery Worker] Each browser will have its own profile: "
            f"{user_profile_name}_0, {user_profile_name}_1, ..."
        )

        pages = []
        contexts = []
        
        # Create a single playwright instance to be reused for all browsers
        from playwright.sync_api import sync_playwright
        from pathlib import Path
        
        # Calculate BASE_DIR: celery_app.py is at backend/app/, so parents[2] is project root
        # browser_utils.py uses parents[3] because it's in backend/app/utils/
        BASE_DIR = Path(__file__).resolve().parents[2]
        
        playwright = sync_playwright().start()
        
        user_agent = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        )
        from app.utils.system_resolution import get_system_resolution
        viewport = get_system_resolution()

        # Create separate browser instances, each with its own profile
        for i in range(pool_size):
            profile_name = f"{user_profile_name}_{i}"
            logger.info(f"[Celery Worker] Creating browser {i+1}/{pool_size} with profile: {profile_name}")
            
            try:
                # Create profile directory
                context_path = BASE_DIR / "browser_profiles" / profile_name
                context_path.mkdir(parents=True, exist_ok=True)
                
                # Launch persistent context with this profile
                context = playwright.chromium.launch_persistent_context(
                    user_data_dir=str(context_path),
                    headless=headless,
                    viewport=viewport,
                    user_agent=user_agent,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--disable-dev-shm-usage",
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-infobars",
                        "--exclude-switches=enable-automation",
                        "--start-maximized",
                    ],
                    locale="en-US",
                    timezone_id="America/New_York",
                    extra_http_headers={
                        "Accept-Language": "en-US,en;q=0.9",
                    },
                )
                
                # Get or create page from context
                page = context.pages[0] if context.pages else context.new_page()
                
                # Setup stealth mode
                from app.utils.browser_utils import setup_stealth_mode_sync
                setup_stealth_mode_sync(context, page)
                
                # Check if already logged in, or login if needed
                logger.info(f"[Celery Worker] Checking Google login status on browser {i+1}...")
                check_or_login_google_sync(page)
                
                pages.append(page)
                contexts.append(context)
                
                logger.info(f"[Celery Worker] Browser {i+1}/{pool_size} initialized successfully")
                
            except Exception as e:
                logger.error(
                    f"[Celery Worker] Failed to initialize browser {i+1} with profile {profile_name}: {e}",
                    exc_info=True,
                )
                # Continue with remaining browsers even if one fails

        if not pages:
            raise Exception("Failed to initialize any browsers in the pool")

        # Navigate all pages to Gmail to ensure they have active session
        logger.info("[Celery Worker] Navigating all browsers to Gmail to activate login session...")
        gmail_url = "https://mail.google.com/mail/u/0/#inbox"
        for index, page in enumerate(pages):
            try:
                if not page.is_closed():
                    logger.info(f"[Celery Worker] Navigating browser {index} to Gmail...")
                    page.goto(gmail_url, wait_until="domcontentloaded", timeout=60_000)
                    page.wait_for_timeout(2_000)  # Wait for page to fully load
                    logger.info(f"[Celery Worker] Browser {index} successfully navigated to Gmail")
                else:
                    logger.warning(f"[Celery Worker] Browser {index} is closed, skipping navigation")
            except Exception as e:
                logger.warning(f"[Celery Worker] Failed to navigate browser {index} to Gmail: {e}")

        # Store browser resources in global state
        set_browser_resources(pages, contexts, playwright)

        logger.info(
            f"[Celery Worker] Browser pool initialized successfully with {len(pages)} browsers "
            f"(each with its own profile, all logged into Google)!"
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
            get_all_contexts,
            get_playwright,
        )

        logger.info("[Celery Worker] Cleaning up browser resources...")

        all_contexts = get_all_contexts()
        playwright = get_playwright()

        if all_contexts:
            for idx, context in enumerate(all_contexts):
                try:
                    context.close()
                    logger.info(f"[Celery Worker] Browser context {idx} closed.")
                except Exception as e:
                    logger.warning(f"[Celery Worker] Error closing browser context {idx}: {e}")

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
