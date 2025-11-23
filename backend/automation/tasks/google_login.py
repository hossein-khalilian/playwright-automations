import argparse
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Base directory for automation backend
BASE_DIR = Path(__file__).resolve().parent.parent

# Path to store browser context (persistent profile)
CONTEXT_PATH = BASE_DIR / "browser_profiles" / "default"


def load_credentials_from_env() -> tuple[str, str]:
    """Load Gmail credentials from .env / environment variables."""
    # Load variables from a .env file if present (does nothing if missing)
    load_dotenv()

    email = os.getenv("GMAIL_EMAIL")
    password = os.getenv("GMAIL_PASSWORD")

    if not email or not password:
        raise RuntimeError(
            "GMAIL_EMAIL and GMAIL_PASSWORD must be set in your environment or .env file."
        )

    return email, password


def setup_stealth_context(context) -> None:
    """Add stealth scripts to avoid basic automation detection."""
    context.add_init_script(
        """
        // Override the navigator.webdriver property
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });

        // Override permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
            Promise.resolve({ state: Notification.permission }) :
            originalQuery(parameters)
        );

        // Override plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });

        // Override languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });
    """
    )


def login_to_gmail(page, email: str, password: str) -> bool:
    """Perform the Gmail login process using provided credentials."""
    try:
        print("\n[*] Navigating to Gmail...")
        page.goto("https://mail.google.com/", wait_until="networkidle", timeout=60000)
        time.sleep(2)

        # Enter email
        print("[*] Entering email...")
        email_field = page.wait_for_selector('input[type="email"]', timeout=10000)
        email_field.click()
        email_field.type(email, delay=100)
        time.sleep(1)

        # Click Next button
        print("[*] Clicking Next...")
        page.click('button:has-text("Next"), #identifierNext')
        time.sleep(3)

        # Enter password
        print("[*] Entering password...")
        password_field = page.wait_for_selector('input[type="password"]', timeout=10000)
        password_field.click()
        password_field.type(password, delay=100)
        time.sleep(1)

        # Click Next/Sign in button
        print("[*] Signing in...")
        page.click('button:has-text("Next"), #passwordNext')

        # Wait for login to complete
        print("[*] Waiting for login to complete...")
        page.wait_for_load_state("networkidle", timeout=30000)

        print("\n[+] Successfully logged in to Gmail!")
        return True

    except Exception as e:
        print(f"\n[-] Error during login: {str(e)}")
        return False


def check_if_logged_in(page) -> bool:
    """Check if already logged into Gmail."""
    try:
        page.goto("https://mail.google.com/", wait_until="networkidle", timeout=30000)
        time.sleep(2)

        # Check if we see the inbox (look for compose button or inbox elements)
        current_url = page.url
        if (
            "mail.google.com/mail" in current_url
            or page.locator("text=Compose").count() > 0
        ):
            print("\n[+] Already logged in! Using saved session.")
            return True
        return False
    except Exception:
        return False


def clear_saved_session() -> None:
    """Clear the saved browser context directory."""
    import shutil

    context_path_str = str(CONTEXT_PATH)
    if os.path.exists(context_path_str):
        shutil.rmtree(context_path_str)
        print(f"[+] Cleared saved session from {context_path_str}")
    else:
        print("[!] No saved session found.")


def run_gmail_session(force_renew: bool = False) -> None:
    """
    Main function to run Gmail with persistent context.

    - If force_renew is False (default):
        * If already logged in, reuse session and do NOT re-login.
        * Otherwise, perform login with credentials from .env.
    - If force_renew is True:
        * Clear saved session before launching and always perform login.
    """
    if force_renew:
        print("[*] force_renew enabled. Clearing any saved session...")
        clear_saved_session()

    with sync_playwright() as p:
        # Launch browser with stealth options and persistent profile
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(CONTEXT_PATH),
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
            ],
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            timezone_id="America/New_York",
        )

        # Setup stealth on the context
        setup_stealth_context(browser)

        # Get or create a page
        page = browser.pages[0] if browser.pages else browser.new_page()

        try:
            should_login = True

            if not force_renew:
                # Only reuse existing login when not forcing renewal
                if check_if_logged_in(page):
                    should_login = False

            if should_login:
                print("\n[*] Not logged in. Starting login process...")
                email, password = load_credentials_from_env()
                if not login_to_gmail(page, email, password):
                    print("\n[!] Login failed. You can complete it manually in the browser.")

            print("\n[*] Gmail is ready!")
            print(
                "[*] Browser session is saved. Next time you run this, you'll stay logged in "
                "unless you use --force-renew."
            )
            print("[*] Do not close the browser from this script; close the window manually when done.")
            input("\nPress Enter to finish the script (browser will remain open until you close it)...")

        except Exception as e:
            print(f"\n[-] Error occurred: {str(e)}")
            input("\nPress Enter to finish the script...")

        # IMPORTANT: Do not call browser.close() here.


def main() -> None:
    parser = argparse.ArgumentParser(description="Gmail login with persistent session.")
    parser.add_argument(
        "--force-renew",
        dest="force_renew",
        action="store_true",
        help="Force renew the Gmail session by clearing saved data and re-logging in.",
    )
    args = parser.parse_args()

    run_gmail_session(force_renew=args.force_renew)


if __name__ == "__main__":
    main()


