"""
Helpers related to Google authentication flows.
"""

import re
from typing import Final, Tuple

from dotenv import load_dotenv
from playwright.sync_api import Page


def check_google_login_status(page: Page) -> bool:
    """
    Return True when the current persistent context is already authenticated with Google.

    The helper relies on a lightweight navigation to Gmail's inbox and a quick scan for
    UI elements (Compose button) that are only available to signed-in users. Exceptions
    are treated as "not logged in" so callers can safely fall back to the login flow.
    """
    try:
        check_url: Final[str] = "https://mail.google.com/mail/u/0/#inbox"
        page.goto(check_url, wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(2_000)

        if "mail.google.com/mail" not in page.url:
            return False

        compose_button = page.get_by_role(
            "button", name=re.compile("compose", re.IGNORECASE)
        )
        try:
            compose_button.wait_for(timeout=5_000)
            return True
        except Exception:
            # URL looks like inbox but Compose button wasn't found – assume logged in.
            return True
    except Exception:
        return False


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
