"""
Helpers related to Google authentication flows.
"""

import re
from typing import Final, List, Optional

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


def get_logged_in_email_sync(page: Page) -> Optional[str]:
    """
    Get the email address of the currently logged-in Google account.
    Returns None if not logged in or email cannot be determined.
    """
    import logging
    import time

    logger = logging.getLogger(__name__)

    try:
        # First check if logged in at all
        if not check_google_login_status_sync(page):
            logger.info("Not logged in to Google")
            return None

        # Navigate to Gmail account settings or account info page
        # Try to get email from Gmail account menu
        gmail_url = "https://mail.google.com/mail/u/0/#inbox"
        if "mail.google.com" not in page.url:
            page.goto(gmail_url, wait_until="domcontentloaded", timeout=60_000)
            time.sleep(2)

        # Try to get email from account button/avatar
        try:
            # Look for account button/avatar which often shows email
            account_button = page.locator(
                'button[aria-label*="@"], '
                'a[aria-label*="@"], '
                '[data-ogab*="@"], '
                'img[alt*="@"]'
            ).first
            if account_button.count() > 0:
                aria_label = account_button.get_attribute("aria-label") or ""
                # Extract email from aria-label
                email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', aria_label)
                if email_match:
                    email = email_match.group(0)
                    logger.info(f"Found email from account button: {email}")
                    return email
        except Exception as e:
            logger.debug(f"Could not get email from account button: {e}")

        # Try navigating to account info page
        try:
            account_url = "https://myaccount.google.com/"
            page.goto(account_url, wait_until="domcontentloaded", timeout=60_000)
            time.sleep(2)

            # Look for email in the page
            email_elements = page.locator('text=/[\\w\\.-]+@[\\w\\.-]+\\.\\w+/')
            if email_elements.count() > 0:
                # Get the first email found (should be the account email)
                email_text = email_elements.first.inner_text(timeout=5_000)
                email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', email_text)
                if email_match:
                    email = email_match.group(0)
                    logger.info(f"Found email from account page: {email}")
                    return email
        except Exception as e:
            logger.debug(f"Could not get email from account page: {e}")

        # Try to get from cookies (some cookies contain email info)
        try:
            cookies = page.context.cookies()
            for cookie in cookies:
                if "google.com" in cookie.get("domain", ""):
                    value = cookie.get("value", "")
                    # Some Google cookies contain email-like strings
                    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', value)
                    if email_match:
                        email = email_match.group(0)
                        logger.info(f"Found email from cookie: {email}")
                        return email
        except Exception as e:
            logger.debug(f"Could not get email from cookies: {e}")

        logger.warning("Could not determine logged-in email")
        return None
    except Exception as e:
        logger.warning(f"Exception while getting logged-in email: {e}", exc_info=True)
        return None


def get_all_logged_in_accounts_sync(page: Page) -> List[str]:
    """
    Get all Google accounts that are logged in to the current browser profile.
    Returns a list of email addresses.
    """
    import logging
    import time

    logger = logging.getLogger(__name__)
    accounts = []

    try:
        # Navigate to account switcher or account management page
        # Try Gmail first as it shows account switcher
        gmail_url = "https://mail.google.com/mail/u/0/#inbox"
        if "mail.google.com" not in page.url:
            page.goto(gmail_url, wait_until="domcontentloaded", timeout=60_000)
            time.sleep(2)

        # Try to find account switcher button
        try:
            # Look for account switcher button/avatar
            account_switcher = page.locator(
                'button[aria-label*="Account"], '
                'button[aria-label*="account"], '
                '[data-ogab*="Account"], '
                'img[alt*="@"]'
            )
            
            # Try clicking to see account list
            if account_switcher.count() > 0:
                account_switcher.first.click()
                time.sleep(1)
                
                # Look for email addresses in the account switcher
                email_elements = page.locator('text=/[\\w\\.-]+@[\\w\\.-]+\\.\\w+/')
                for i in range(email_elements.count()):
                    try:
                        email_text = email_elements.nth(i).inner_text(timeout=2_000)
                        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', email_text)
                        if email_match:
                            email = email_match.group(0).lower().strip()
                            if email not in accounts:
                                accounts.append(email)
                    except Exception:
                        continue
        except Exception as e:
            logger.debug(f"Could not get accounts from account switcher: {e}")

        # Also try navigating to account management
        try:
            account_url = "https://myaccount.google.com/"
            page.goto(account_url, wait_until="domcontentloaded", timeout=60_000)
            time.sleep(2)
            
            # Look for all email addresses on the page
            email_elements = page.locator('text=/[\\w\\.-]+@[\\w\\.-]+\\.\\w+/')
            for i in range(email_elements.count()):
                try:
                    email_text = email_elements.nth(i).inner_text(timeout=2_000)
                    email_match = re.search(r'[\w\.-]+@[\w\\.-]+\.\w+', email_text)
                    if email_match:
                        email = email_match.group(0).lower().strip()
                        if email not in accounts:
                            accounts.append(email)
                except Exception:
                    continue
        except Exception as e:
            logger.debug(f"Could not get accounts from account page: {e}")

        # If we found at least one account, return them
        if accounts:
            logger.info(f"Found {len(accounts)} logged-in accounts: {accounts}")
            return accounts

        # Fallback: try to get at least the primary account
        primary_email = get_logged_in_email_sync(page)
        if primary_email:
            accounts.append(primary_email.lower().strip())
            logger.info(f"Found primary account: {primary_email}")

        return accounts
    except Exception as e:
        logger.warning(f"Exception while getting logged-in accounts: {e}", exc_info=True)
        return []


def check_profile_has_account_sync(page: Page, target_email: str) -> bool:
    """
    Check if the browser profile has a specific Google account added.
    Returns True if the account is present, False otherwise.
    """
    import logging

    logger = logging.getLogger(__name__)

    try:
        # Get all logged-in accounts
        accounts = get_all_logged_in_accounts_sync(page)
        
        # Normalize target email
        target_email_normalized = target_email.lower().strip()
        
        # Check if target email is in the list
        has_account = target_email_normalized in [acc.lower().strip() for acc in accounts]
        
        if has_account:
            logger.info(f"Profile has account {target_email}")
        else:
            logger.info(f"Profile does not have account {target_email}. Found accounts: {accounts}")
        
        return has_account
    except Exception as e:
        logger.warning(
            f"Exception while checking if profile has account {target_email}: {e}", exc_info=True
        )
        return False


def check_profile_logged_in_to_email_sync(
    page: Page, target_email: str
) -> bool:
    """
    Check if the browser profile is logged in to a specific email address.
    Returns True if logged in to the target email, False otherwise.
    Note: With multiple accounts, this checks if the account is present in the profile.
    """
    return check_profile_has_account_sync(page, target_email)
