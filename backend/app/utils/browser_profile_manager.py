"""
Browser profile management utilities.
Handles copying browser profiles and initializing them with Google credentials.
Uses a single profile with multiple Google accounts added via AddSession.
"""

import logging
import shutil
from pathlib import Path
from typing import List, Optional

from app.automation.tasks.google_login import add_google_account_via_addsession_sync
from app.utils.browser_utils import setup_stealth_mode_sync
from app.utils.config import config
from app.utils.db import get_all_working_google_credentials_sync
from app.utils.google import (
    check_google_login_status_sync,
    check_profile_has_account_sync,
)
from app.utils.system_resolution import get_system_resolution
from playwright.sync_api import BrowserContext, Page, Playwright

logger = logging.getLogger(__name__)


def copy_browser_profile(source_profile_path: Path, target_profile_path: Path) -> bool:
    """
    Copy a browser profile directory to a new location.
    Returns True if successful, False otherwise.
    """
    try:
        if not source_profile_path.exists():
            logger.warning(f"Source profile does not exist: {source_profile_path}")
            return False

        # Remove target if it exists
        if target_profile_path.exists():
            logger.info(f"Removing existing target profile: {target_profile_path}")
            shutil.rmtree(target_profile_path)

        # Copy the profile
        logger.info(
            f"Copying profile from {source_profile_path} to {target_profile_path}"
        )
        shutil.copytree(source_profile_path, target_profile_path)
        logger.info(f"Successfully copied profile to {target_profile_path}")
        return True
    except Exception as e:
        logger.error(
            f"Error copying profile from {source_profile_path} to {target_profile_path}: {e}",
            exc_info=True,
        )
        return False


def ensure_profile_has_account(
    playwright: Playwright,
    profile_path: Path,
    email: str,
    password: str,
    headless: bool = True,
) -> bool:
    """
    Ensure a browser profile has a specific Google account added.
    Uses AddSession flow to add the account if it's not already present.
    Returns True if account is present (or successfully added), False otherwise.
    """
    context = None
    page = None

    try:
        # Launch browser with the profile
        user_agent = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        )
        viewport = get_system_resolution()

        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(profile_path),
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

        page = context.pages[0] if context.pages else context.new_page()
        setup_stealth_mode_sync(context, page)

        # Check if account is already added
        logger.info(f"Checking if profile {profile_path.name} has account {email}...")
        if check_profile_has_account_sync(page, email):
            logger.info(f"Profile {profile_path.name} already has account {email}")
            return True

        # Add account using AddSession flow
        logger.info(
            f"Adding account {email} to profile {profile_path.name} using AddSession..."
        )
        success = add_google_account_via_addsession_sync(page, email, password)
        if success:
            logger.info(
                f"Successfully added account {email} to profile {profile_path.name}"
            )
            return True
        else:
            logger.error(
                f"Failed to add account {email} to profile {profile_path.name}"
            )
            return False

    except Exception as e:
        logger.error(
            f"Error ensuring profile {profile_path.name} has account {email}: {e}",
            exc_info=True,
        )
        return False
    finally:
        if context:
            try:
                context.close()
            except Exception:
                pass


def initialize_browser_profiles_for_credentials(
    base_profile_name: str = "default",
    pool_size: Optional[int] = None,
    headless: bool = True,
    browser_profiles_dir: Optional[Path] = None,
) -> List[Path]:
    """
    Initialize browser profiles for all working Google credentials.
    Uses a single base profile and adds all accounts to it using AddSession flow.
    Then copies the profile to create pool_size copies.

    Args:
        base_profile_name: Base name for the profile (e.g., "default")
        pool_size: Number of profile copies to create. If None, uses config value.
        headless: Whether to run browsers in headless mode
        browser_profiles_dir: Directory containing browser profiles. If None, uses default.

    Returns:
        List of profile paths that were created/initialized
    """
    from playwright.sync_api import sync_playwright

    if pool_size is None:
        pool_size = config.get("browser_pool_size", 1)
    if pool_size < 1:
        pool_size = 1

    if browser_profiles_dir is None:
        # Calculate BASE_DIR: this file is at backend/app/utils/, so parents[2] is backend/
        BASE_DIR = Path(__file__).resolve().parents[2]
        browser_profiles_dir = BASE_DIR / "browser_profiles"
    else:
        browser_profiles_dir = Path(browser_profiles_dir)

    browser_profiles_dir.mkdir(parents=True, exist_ok=True)

    # Get all working credentials
    logger.info("Fetching all working Google credentials...")
    credentials = get_all_working_google_credentials_sync()
    if not credentials:
        logger.warning("No working Google credentials found")
        return []

    logger.info(f"Found {len(credentials)} working Google credentials")

    # Use a single base profile for all accounts
    base_profile_path = browser_profiles_dir / base_profile_name
    playwright = sync_playwright().start()
    initialized_profiles = []

    try:
        # Add all accounts to the base profile
        logger.info(
            f"Adding all {len(credentials)} accounts to base profile {base_profile_name}..."
        )
        for cred_index, cred in enumerate(credentials):
            email = cred["email"]
            password = cred["password"]
            logger.info(
                f"Processing account {cred_index + 1}/{len(credentials)}: {email}"
            )

            # Ensure account is added to the base profile
            success = ensure_profile_has_account(
                playwright=playwright,
                profile_path=base_profile_path,
                email=email,
                password=password,
                headless=headless,
            )

            if not success:
                logger.error(
                    f"Failed to add account {email} to base profile. Continuing with other accounts..."
                )
                # Continue with other accounts even if one fails

        # Verify base profile has at least some accounts
        try:
            context = playwright.chromium.launch_persistent_context(
                user_data_dir=str(base_profile_path),
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                ],
            )
            page = context.pages[0] if context.pages else context.new_page()
            if check_google_login_status_sync(page):
                logger.info("Base profile has at least one account logged in")
            context.close()
        except Exception as e:
            logger.warning(f"Error verifying base profile: {e}")

        initialized_profiles.append(base_profile_path)

        # Copy the base profile to create pool_size copies
        logger.info(
            f"Copying base profile {base_profile_name} to create {pool_size} copies..."
        )
        for i in range(pool_size):
            copy_profile_name = f"{base_profile_name}_{i}"
            copy_profile_path = browser_profiles_dir / copy_profile_name

            # Only copy if the copy doesn't exist
            should_copy = True
            if copy_profile_path.exists():
                # Check if copy already has accounts (verify it's a valid profile)
                try:
                    context = playwright.chromium.launch_persistent_context(
                        user_data_dir=str(copy_profile_path),
                        headless=True,
                        args=[
                            "--disable-blink-features=AutomationControlled",
                            "--disable-dev-shm-usage",
                            "--no-sandbox",
                            "--disable-setuid-sandbox",
                        ],
                    )
                    page = context.pages[0] if context.pages else context.new_page()
                    if check_google_login_status_sync(page):
                        logger.info(
                            f"Profile {copy_profile_name} already exists and has accounts, skipping copy"
                        )
                        should_copy = False
                    context.close()
                except Exception as e:
                    logger.warning(
                        f"Error checking existing profile {copy_profile_name}: {e}. Will copy anyway."
                    )

            if should_copy:
                logger.info(
                    f"Copying profile to {copy_profile_name} ({i + 1}/{pool_size})..."
                )
                if copy_browser_profile(base_profile_path, copy_profile_path):
                    initialized_profiles.append(copy_profile_path)
                    logger.info(
                        f"Successfully created profile copy: {copy_profile_name}"
                    )
                else:
                    logger.error(f"Failed to create profile copy: {copy_profile_name}")

        logger.info(
            f"Initialized {len(initialized_profiles)} browser profiles "
            f"(1 base profile with {len(credentials)} accounts, {pool_size} copies)"
        )
        return initialized_profiles

    finally:
        playwright.stop()
