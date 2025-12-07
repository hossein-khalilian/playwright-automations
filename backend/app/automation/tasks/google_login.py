import asyncio
import os
import random
import re
import time
from pathlib import Path
from typing import Tuple

from dotenv import load_dotenv
from playwright.sync_api import Page as SyncPage

from app.utils.browser_utils import initialize_page_sync
from app.utils.google import check_google_login_status_sync

NAVIGATION_DELAY_RANGE = (2.0, 3.0)
PAGE_WARMUP_DELAY_RANGE = (1.0, 2.0)


def load_credentials_from_env() -> Tuple[str, str]:
    """Load Gmail credentials from environment variables / .env file."""
    load_dotenv()
    email = os.getenv("GMAIL_EMAIL")
    password = os.getenv("GMAIL_PASSWORD")

    if not email or not password:
        raise RuntimeError(
            "GMAIL_EMAIL and GMAIL_PASSWORD must be set in your environment or .env file."
        )

    return email, password


# ---- Sync variants ----
def _human_pause_sync(min_seconds: float = 0.5, max_seconds: float = 1.0) -> None:
    time.sleep(random.uniform(min_seconds, max_seconds))


def _type_with_human_delay_sync(field, value: str) -> None:
    field.click()
    _human_pause_sync()
    field.type(value, delay=random.randint(50, 150))
    _human_pause_sync()


def _click_next_button_sync(page: SyncPage) -> None:
    next_button = page.get_by_role("button", name=re.compile("^next$", re.IGNORECASE))
    next_button.click()
    _human_pause_sync(*NAVIGATION_DELAY_RANGE)


def check_or_login_google_sync(page: SyncPage) -> None:
    try:
        if check_google_login_status_sync(page):
            print("[+] Google is already logged in.")
            return

        print("[*] Not logged in to Google. Attempting to login...")
        email, password = load_credentials_from_env()
        success = login_to_google_sync(page, email, password)
        if success:
            print("[+] Google login completed successfully!")
        else:
            print(
                "[!] Warning: Google login failed. Some endpoints may not work correctly."
            )
    except Exception as exc:
        raise RuntimeError(f"Login failed: {exc}")


def login_to_google_sync(
    page: SyncPage,
    email: str,
    password: str,
    force_renew: bool = False,
) -> bool:
    """
    Sync Gmail login process using provided credentials.
    """
    try:
        print("\n[*] Opening Gmail login page...")
        page.goto(
            "https://accounts.google.com/signin/v2/identifier?service=mail&passive=true",
            wait_until="domcontentloaded",
            timeout=60_000,
        )

        print("[*] Entering email...")
        email_input = page.get_by_role(
            "textbox", name=re.compile("email|phone", re.IGNORECASE)
        )
        email_input.wait_for(timeout=15_000)
        _type_with_human_delay_sync(email_input, email)
        _click_next_button_sync(page)

        print("[*] Waiting for password field...")
        password_input = page.get_by_role(
            "textbox", name=re.compile("password", re.IGNORECASE)
        )
        password_input.wait_for(timeout=20_000)
        time.sleep(random.uniform(0.5, 1.0))

        print("[*] Entering password...")
        _type_with_human_delay_sync(password_input, password)
        _click_next_button_sync(page)

        print("[*] Waiting for Gmail to load after password submission...")
        page.wait_for_load_state("networkidle", timeout=60_000)

        if check_google_login_status_sync(page):
            print("\n[+] Successfully logged into Gmail!")
            return True

        print("\n[!] Login flow completed but could not verify inbox access.")
        return False
    except Exception as exc:
        print(f"\n[!] Error during Gmail login: {exc}")
        return False


def main(user_profile_name: str = "test_google_login", headless: bool = False):
    print("[*] Initializing browser...")
    page = None
    context = None
    playwright = None

    try:
        # Use a test profile to avoid conflicts with running FastAPI app
        print(f"[*] Using profile: {user_profile_name}")
        page, context, playwright = initialize_page_sync(
            headless=headless, user_profile_name=user_profile_name
        )

        # Check if already logged in
        print("[*] Checking if Google is already logged in...")
        if check_google_login_status_sync(page):
            print("[+] Google is already logged in. No need to login again.")
            print("[*] Browser will remain open for 5 seconds. Press Ctrl+C to close.")
            time.sleep(5)
        else:
            print("[*] Not logged in. Starting login process...")
            # Load credentials from environment
            email, password = load_credentials_from_env()

            # Perform login
            success = login_to_google_sync(page, email, password)

            if success:
                print("[+] Login process completed successfully!")
            else:
                print("[-] Login process failed.")

            print("[*] Browser will remain open for 5 seconds. Press Ctrl+C to close.")
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n[*] Interrupted by user. Closing browser...")
    except Exception as exc:
        error_msg = str(exc)
        if "Target page, context or browser has been closed" in error_msg:
            print(
                "\n[!] Error: Browser profile is locked or in use by another process."
            )
            print(
                "[!] Solution: Stop other processes using the profile, or use a different profile name."
            )
        elif "profile appears to be in use" in error_msg.lower():
            print("\n[!] Error: Browser profile is locked by another Chromium process.")
            print(
                "[!] Solution: Close other browser instances or stop the FastAPI app."
            )
        else:
            print(f"\n[-] Error: {exc}")
    finally:
        # Clean up resources
        if context:
            try:
                context.close()
            except Exception as exc:
                print(f"[!] Warning: Error closing context: {exc}")
        if playwright:
            try:
                playwright.stop()
            except Exception as exc:
                print(f"[!] Warning: Error stopping playwright: {exc}")
        print("[+] Browser closed.")


if __name__ == "__main__":
    main()
