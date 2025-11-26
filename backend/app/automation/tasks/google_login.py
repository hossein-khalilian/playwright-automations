import random
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import Page

# Add parent directory to path to import from app.utils
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.utils.browser_utils import initialize_page
from app.utils.google import check_google_login_status, load_credentials_from_env

NAVIGATION_DELAY_RANGE = (2.0, 3.0)
PAGE_WARMUP_DELAY_RANGE = (1.0, 2.0)


def _human_pause(min_seconds: float = 0.5, max_seconds: float = 1.0) -> None:
    """Pause for a random duration to better mimic human interaction."""
    time.sleep(random.uniform(min_seconds, max_seconds))


def _type_with_human_delay(field, value: str) -> None:
    """Type text into a field using small randomized delays."""
    field.click()
    _human_pause()
    field.type(value, delay=random.randint(50, 150))
    _human_pause()


def _click_next_button(page: Page) -> None:
    """Click the generic Next button and wait for Google to progress."""
    next_button = page.get_by_role("button", name=re.compile("^next$", re.IGNORECASE))
    next_button.click()
    _human_pause(*NAVIGATION_DELAY_RANGE)


def login_to_google(
    page: Page,
    email: str,
    password: str,
    force_renew=False,
) -> bool:
    """
    Perform the Gmail login process using provided credentials.

    NOTE:
        - If Google requires additional verification (2FA, phone, etc.),
          this function will stop after submitting the password and ask
          you to complete the flow manually.
    """
    try:
        print("\n[*] Opening Gmail login page...")
        page.goto(
            "https://accounts.google.com/signin/v2/identifier?service=mail&passive=true",
            wait_until="domcontentloaded",
            timeout=60_000,
        )

        # ---- Email step ----
        print("[*] Entering email...")
        email_input = page.get_by_role(
            "textbox", name=re.compile("email|phone", re.IGNORECASE)
        )
        email_input.wait_for(timeout=15_000)

        # Human-like typing with random delays
        _type_with_human_delay(email_input, email)
        _click_next_button(page)

        # Wait for password field to appear
        print("[*] Waiting for password field...")
        password_input = page.get_by_role(
            "textbox", name=re.compile("password", re.IGNORECASE)
        )
        password_input.wait_for(timeout=20_000)
        time.sleep(random.uniform(0.5, 1.0))

        # ---- Password step ----
        print("[*] Entering password...")
        _type_with_human_delay(password_input, password)
        _click_next_button(page)

        # Let Google redirect after password
        print("[*] Waiting for Gmail to load after password submission...")
        page.wait_for_load_state("networkidle", timeout=60_000)

        if check_google_login_status(page):
            print("\n[+] Successfully logged into Gmail!")
            return True

        # At this point Google most likely wants additional verification.
        print(
            "\n[!] Google is asking for additional verification (2FA, phone, etc.). "
            "Complete the steps manually in the opened browser."
        )
        input("    When you see your inbox, press Enter here to continue...")

        if check_google_login_status(page):
            print("\n[+] Gmail login completed manually and session is now active.")
            return True

        print("\n[-] Login did not reach the inbox even after manual steps.")
        return False

    except Exception as exc:
        print(f"\n[-] Error during Gmail login: {exc}")
        return False


if __name__ == "__main__":
    print("[*] Initializing browser...")
    page, context, playwright = initialize_page(headless=False)
    
    try:
        # Check if already logged in
        print("[*] Checking if Google is already logged in...")
        if check_google_login_status(page):
            print("[+] Google is already logged in. No need to login again.")
            print("[*] Browser will remain open. Press Ctrl+C to close.")
            try:
                input("\n[*] Press Enter to close the browser...")
            except KeyboardInterrupt:
                pass
        else:
            print("[*] Not logged in. Starting login process...")
            # Load credentials from environment
            email, password = load_credentials_from_env()
            
            # Perform login
            success = login_to_google(page, email, password)
            
            if success:
                print("[+] Login process completed successfully!")
            else:
                print("[-] Login process failed.")
            
            print("[*] Browser will remain open. Press Ctrl+C to close.")
            try:
                input("\n[*] Press Enter to close the browser...")
            except KeyboardInterrupt:
                pass
    except KeyboardInterrupt:
        print("\n[*] Interrupted by user. Closing browser...")
    except Exception as exc:
        print(f"\n[-] Error: {exc}")
    finally:
        context.close()
        playwright.stop()
        print("[+] Browser closed.")
