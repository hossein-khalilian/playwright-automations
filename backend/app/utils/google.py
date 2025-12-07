"""
Helpers related to Google authentication flows.
"""

import re
from typing import Final

from playwright.sync_api import Page


def check_google_login_status_sync(page: Page) -> bool:
    """
    Sync variant of Google login status check.
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
            return True
    except Exception:
        return False
