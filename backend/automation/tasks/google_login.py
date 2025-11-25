import argparse
import os
import random
import re
import time
from pathlib import Path
from typing import Tuple

from dotenv import load_dotenv
from playwright.sync_api import BrowserContext, Page, sync_playwright

from automation.utils.system_resolution import get_system_resolution

# Base directory for automation backend
BASE_DIR = Path(__file__).resolve().parent.parent

# Path to store browser context (persistent profile)
CONTEXT_PATH = BASE_DIR / "browser_profiles" / "default"

GMAIL_INBOX_URL = "https://mail.google.com/mail/u/0/#inbox"
GMAIL_LOGIN_URL = (
    "https://accounts.google.com/signin/v2/identifier?service=mail&passive=true"
)


def load_credentials_from_env() -> Tuple[str, str]:
    """Load Gmail credentials from .env / environment variables."""
    load_dotenv()

    email = os.getenv("GMAIL_EMAIL")
    password = os.getenv("GMAIL_PASSWORD")

    if not email or not password:
        raise RuntimeError(
            "GMAIL_EMAIL and GMAIL_PASSWORD must be set in your environment or .env file."
        )

    return email, password


def clear_saved_session() -> None:
    """Delete the saved persistent browser profile directory."""
    import shutil

    context_path_str = str(CONTEXT_PATH)
    if os.path.exists(context_path_str):
        shutil.rmtree(context_path_str)
        print(f"[+] Cleared saved session from {context_path_str}")
    else:
        print("[*] No saved Gmail session found.")


def is_already_logged_in(page: Page) -> bool:
    """Return True if the current persistent context is already logged into Gmail."""
    try:
        print("[*] Checking existing Gmail session...")
        page.goto(GMAIL_INBOX_URL, wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(2_000)

        # Heuristic: inbox URL + presence of Compose button (English UI).
        if "mail.google.com/mail" not in page.url:
            return False

        compose_button = page.get_by_role(
            "button", name=re.compile("compose", re.IGNORECASE)
        )
        try:
            compose_button.wait_for(timeout=5_000)
            print("[+] Existing Gmail session detected (already logged in).")
            return True
        except Exception:
            # URL looks like inbox but we didn't find the Compose button –
            # could be a different screen or different locale.
            return True
    except Exception:
        return False


def login_to_gmail(page: Page, email: str, password: str) -> bool:
    """
    Perform the Gmail login process using provided credentials.

    NOTE:
        - If Google requires additional verification (2FA, phone, etc.),
          this function will stop after submitting the password and ask
          you to complete the flow manually.
    """
    try:
        print("\n[*] Opening Gmail login page...")
        page.goto(GMAIL_LOGIN_URL, wait_until="domcontentloaded", timeout=60_000)

        # ---- Email step ----
        print("[*] Entering email...")
        email_input = page.get_by_role(
            "textbox", name=re.compile("email|phone", re.IGNORECASE)
        )
        email_input.wait_for(timeout=15_000)

        # Human-like typing with random delays
        email_input.click()
        time.sleep(random.uniform(0.5, 1.0))
        email_input.type(email, delay=random.randint(50, 150))
        time.sleep(random.uniform(0.5, 1.0))

        next_button = page.get_by_role(
            "button", name=re.compile("^next$", re.IGNORECASE)
        )
        next_button.click()
        time.sleep(random.uniform(2.0, 3.0))

        # Wait for password field to appear
        print("[*] Waiting for password field...")
        password_input = page.get_by_role(
            "textbox", name=re.compile("password", re.IGNORECASE)
        )
        password_input.wait_for(timeout=20_000)
        time.sleep(random.uniform(0.5, 1.0))

        # ---- Password step ----
        print("[*] Entering password...")
        password_input.click()
        time.sleep(random.uniform(0.5, 1.0))
        password_input.type(password, delay=random.randint(50, 150))
        time.sleep(random.uniform(0.5, 1.0))

        password_next_button = page.get_by_role(
            "button", name=re.compile("^next$", re.IGNORECASE)
        )
        password_next_button.click()
        time.sleep(random.uniform(2.0, 3.0))

        # Let Google redirect after password
        print("[*] Waiting for Gmail to load after password submission...")
        page.wait_for_load_state("networkidle", timeout=60_000)

        if is_already_logged_in(page):
            print("\n[+] Successfully logged into Gmail!")
            return True

        # At this point Google most likely wants additional verification.
        print(
            "\n[!] Google is asking for additional verification (2FA, phone, etc.). "
            "Complete the steps manually in the opened browser."
        )
        input("    When you see your inbox, press Enter here to continue...")

        if is_already_logged_in(page):
            print("\n[+] Gmail login completed manually and session is now active.")
            return True

        print("\n[-] Login did not reach the inbox even after manual steps.")
        return False

    except Exception as exc:
        print(f"\n[-] Error during Gmail login: {exc}")
        return False


def setup_stealth_mode(context: BrowserContext, page: Page) -> None:
    """
    Inject comprehensive stealth scripts using CDP to make the browser appear as a real user browser.
    This helps bypass Google's automation detection.
    """
    # Comprehensive stealth script that runs before any page script
    stealth_script = """
    (function() {
        'use strict';
        
        // Remove webdriver property completely - this is the most important
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        
        // Delete webdriver from prototype chain
        try {
            delete navigator.__proto__.webdriver;
        } catch(e) {}

        // Override plugins to look real
        Object.defineProperty(navigator, 'plugins', {
            get: () => {
                const plugins = [
                    { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
                    { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
                    { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' }
                ];
                plugins.item = function(index) { return this[index] || null; };
                plugins.namedItem = function(name) { 
                    for (let i = 0; i < this.length; i++) {
                        if (this[i].name === name) return this[i];
                    }
                    return null;
                };
                return plugins;
            }
        });

        // Override languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });

        // Override permissions API
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => {
            if (parameters.name === 'notifications') {
                return Promise.resolve({ state: Notification.permission });
            }
            return originalQuery(parameters);
        };

        // Full Chrome object - Google checks for this
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {
                isInstalled: false,
                InstallState: {
                    DISABLED: "disabled",
                    INSTALLED: "installed",
                    NOT_INSTALLED: "not_installed"
                },
                RunningState: {
                    CANNOT_RUN: "cannot_run",
                    READY_TO_RUN: "ready_to_run",
                    RUNNING: "running"
                }
            }
        };

        // Override WebGL vendor/renderer
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) {
                return 'Intel Inc.';
            }
            if (parameter === 37446) {
                return 'Intel Iris OpenGL Engine';
            }
            return getParameter.call(this, parameter);
        };
    })();
    """

    # Inject via CDP which runs before page scripts - this is critical
    try:
        cdp_session = context.new_cdp_session(page)
        cdp_session.send(
            "Page.addScriptToEvaluateOnNewDocument", {"source": stealth_script}
        )
    except Exception as e:
        print(f"[!] Warning: Could not set up CDP stealth: {e}")

    # Also add via context init script for additional coverage
    context.add_init_script(stealth_script)


def run_gmail_session(force_renew: bool = False, headless: bool = False) -> None:
    """
    Open a persistent Chromium profile and ensure Gmail is logged in.

    - If force_renew is False (default):
        * If already logged in, reuse the existing session (no re-login).
        * Otherwise, perform login with credentials from .env.
    - If force_renew is True:
        * Clear saved session before launching and always perform login.
    """
    if force_renew:
        print("[*] --force-renew enabled. Clearing any saved Gmail session...")
        clear_saved_session()

    print(f"[*] Using persistent profile at: {CONTEXT_PATH}")

    with sync_playwright() as p:
        # Use a realistic Chrome user agent
        user_agent = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        )

        # Get system resolution for viewport
        viewport = get_system_resolution()

        context = p.chromium.launch_persistent_context(
            user_data_dir=str(CONTEXT_PATH),
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

        # Navigate to a neutral page first to establish normal browsing pattern
        print("[*] Establishing browser session...")
        page.goto(
            "https://www.google.com", wait_until="domcontentloaded", timeout=10000
        )
        time.sleep(random.uniform(1.0, 2.0))

        # Apply comprehensive stealth mode using CDP
        setup_stealth_mode(context, page)

        # Small delay to let stealth scripts initialize
        time.sleep(0.5)

        try:
            if not force_renew and is_already_logged_in(page):
                print("\n[*] Gmail session is already authenticated. Nothing to do.")
            else:
                print("\n[*] Gmail is not logged in. Starting login flow...")
                email, password = load_credentials_from_env()
                success = login_to_gmail(page, email, password)
                if not success:
                    print(
                        "\n[!] Gmail login did not succeed. "
                        "Check your credentials, 2FA settings, or try again with --force-renew."
                    )

            print(
                "\n[*] Gmail session is ready. The login state is stored in the persistent profile."
            )
            print(
                f"[*] Profile directory: {CONTEXT_PATH}\n"
                "    You can reuse this profile from other Playwright scripts."
            )

        finally:
            # Closing the context writes all cookies and session data to disk.
            print("[*] Closing browser context...")
            context.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Open a persistent Chromium profile and log into Gmail."
    )
    parser.add_argument(
        "--force-renew",
        dest="force_renew",
        action="store_true",
        help="Clear any saved Gmail session and force a fresh login.",
    )
    parser.add_argument(
        "--headless",
        dest="headless",
        action="store_true",
        help="Run the browser in headless mode (not recommended for 2FA).",
    )

    args = parser.parse_args()
    run_gmail_session(force_renew=args.force_renew, headless=args.headless)


if __name__ == "__main__":
    main()
