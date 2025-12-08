"""
Helpers related to Google authentication flows.
"""

import re
from typing import Final

from playwright.sync_api import Page


def check_google_login_status_by_cookies(page: Page) -> bool:
    """
    Check Google login status by examining cookies.
    This is faster and doesn't require navigation.
    Cookies are stored at the context level, so this works even if page is on about:blank.
    
    Note: This may fail with greenlet errors when called from async contexts.
    In that case, the navigation-based check will be used as fallback.
    """
    import logging

    logger = logging.getLogger(__name__)

    try:
        # Get cookies for Google domains (cookies are at context level)
        # This can fail with greenlet errors when called from async FastAPI endpoints
        cookies = page.context.cookies()
        
        logger.info(f"Total cookies in context: {len(cookies)}")
        
        # Look for authentication cookies (Google uses these for session)
        auth_cookies = [
            "SID",
            "HSID",
            "SSID",
            "APISID",
            "SAPISID",
            "__Secure-1PSID",
            "__Secure-3PSID",
            "LSID",  # Additional Google auth cookie
        ]
        
        # Filter cookies for Google domains
        google_cookies = []
        for cookie in cookies:
            domain = cookie.get("domain", "")
            # Check for google.com in domain (could be .google.com, .accounts.google.com, etc.)
            if "google.com" in domain.lower():
                google_cookies.append(cookie)
                logger.debug(f"Found Google cookie: {cookie.get('name')} from {domain}")
        
        logger.info(f"Found {len(google_cookies)} Google cookies")
        
        # Check if we have authentication cookies
        auth_cookie_names = [c.get("name") for c in google_cookies if c.get("name") in auth_cookies]
        has_auth = len(auth_cookie_names) > 0
        
        if has_auth:
            logger.info(f"Found auth cookies: {auth_cookie_names}")
        else:
            logger.info("No authentication cookies found")
            # Log all cookie names for debugging
            all_cookie_names = [c.get("name") for c in google_cookies]
            logger.debug(f"All Google cookie names: {all_cookie_names}")
        
        return has_auth
    except Exception as e:
        # Catch greenlet errors and other exceptions - fall back to navigation check
        error_msg = str(e)
        if "greenlet" in error_msg.lower() or "thread" in error_msg.lower():
            logger.debug(
                "Cookie check failed due to greenlet/thread issue (expected in async context), "
                "will use navigation-based check instead"
            )
        else:
            logger.warning(f"Error checking cookies: {e}")
        return False


def check_google_login_status_sync(page: Page) -> bool:
    """
    Sync variant of Google login status check.
    Checks if the page is logged into Google by navigating to Gmail and checking for login indicators.
    """
    import logging

    logger = logging.getLogger(__name__)

    # First try cookie-based check (faster, no navigation needed)
    cookie_check = check_google_login_status_by_cookies(page)
    if cookie_check:
        logger.info("Cookie check indicates user is logged in")
        return True

    # If cookie check fails, try navigation-based check
    try:
        check_url: Final[str] = "https://mail.google.com/mail/u/0/#inbox"
        current_url = page.url
        
        # If already on Gmail, don't navigate again
        if "mail.google.com/mail" in current_url:
            logger.info(f"Already on Gmail URL: {current_url}, checking login status...")
        else:
            logger.info(f"Navigating to {check_url} to check login status...")
            # Navigate to Gmail inbox
            page.goto(check_url, wait_until="domcontentloaded", timeout=60_000)
            current_url = page.url
            logger.info(f"Navigated to: {current_url}")

        # Use Python's time.sleep instead of page.wait_for_timeout to avoid greenlet issues
        # This is safe to use in any thread context
        import time
        time.sleep(2)  # Give page a moment to load
        
        # Check if we're still on Gmail (not redirected to login page)
        if "mail.google.com/mail" not in current_url:
            if "accounts.google.com" in current_url:
                logger.info(f"Redirected to login page: {current_url} - not logged in")
            else:
                logger.info(f"Not on Gmail URL: {current_url} - checking if logged in...")
            return False

        # If we're on accounts.google.com, definitely not logged in
        if "accounts.google.com" in current_url:
            logger.info("On accounts.google.com - not logged in")
            return False

        logger.info("On Gmail URL, checking for login indicators...")

        # Check for compose button (indicates logged in) - try multiple selectors
        login_indicators_found = False
        
        # Method 1: Compose button by role
        try:
            compose_button = page.get_by_role(
                "button", name=re.compile("compose", re.IGNORECASE)
            )
            compose_button.wait_for(timeout=10_000, state="visible")
            logger.info("Found compose button - user is logged in")
            return True
        except Exception as e:
            logger.debug(f"Compose button (role) not found: {e}")

        # Method 2: Compose button by text
        try:
            compose_by_text = page.get_by_text(re.compile("compose", re.IGNORECASE))
            if compose_by_text.count() > 0:
                logger.info("Found compose text - user is logged in")
                return True
        except Exception:
            pass

        # Method 3: Check for inbox or mail list
        try:
            inbox_locator = page.locator('[aria-label*="Inbox"], [aria-label*="inbox"], [data-tooltip*="Inbox"]')
            if inbox_locator.count() > 0:
                logger.info("Found inbox indicator - user is logged in")
                return True
        except Exception as e:
            logger.debug(f"Inbox indicator not found: {e}")

        # Method 4: Check for Gmail-specific elements (mail list, search box, etc.)
        try:
            # Look for search box or mail list
            gmail_elements = page.locator(
                'input[placeholder*="Search"], '
                '[role="main"], '
                '[data-view-type="1"]'  # Gmail inbox view
            )
            if gmail_elements.count() > 0:
                logger.info("Found Gmail UI elements - user is logged in")
                return True
        except Exception as e:
            logger.debug(f"Gmail UI elements not found: {e}")

        # Method 5: Check page title
        try:
            title = page.title()
            if "gmail" in title.lower() and "sign in" not in title.lower():
                logger.info(f"Page title suggests logged in: {title}")
                return True
        except Exception:
            pass

        # If we're on Gmail URL and not on accounts.google.com, 
        # and we can't find clear indicators, check if there's any content
        try:
            body_text = page.locator("body").inner_text(timeout=2_000)
            if body_text and len(body_text.strip()) > 100:  # Has substantial content
                # If we have content and we're on Gmail, likely logged in
                logger.info("On Gmail with content - assuming logged in")
                return True
        except Exception:
            pass

        logger.warning("On Gmail URL but no clear login indicators found - returning False")
        return False
    except Exception as e:
        logger.warning(f"Exception during login check: {e}", exc_info=True)
        return False
