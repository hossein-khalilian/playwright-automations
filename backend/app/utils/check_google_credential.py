"""
Function to check if Google credentials are working.
"""
import logging
import time
from typing import Tuple

from playwright.sync_api import Page

logger = logging.getLogger(__name__)


def check_google_credential_flow(page: Page, email: str, password: str) -> Tuple[bool, str]:
    """
    Check if Google credentials are working by attempting to log in.
    This is a flow function that takes a page as the first argument.
    
    Args:
        page: Playwright page instance (from pool or newly created)
        email: Google account email
        password: Google account password
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        logger.info(f"Starting credential check for {email}")
        
        # Navigate to Google sign-in page (using the exact URL from user's example)
        logger.info("Navigating to Google sign-in page")
        page.goto(
            "https://accounts.google.com/v3/signin/identifier?flowName=GlifWebSignIn&flowEntry=AddSession&dsh=S-838376335%3A1767087387204569",
            wait_until="domcontentloaded",
            timeout=30000
        )
        
        # Enter email
        logger.info("Entering email")
        email_input = page.get_by_role("textbox", name="Email or phone")
        email_input.wait_for(timeout=10000, state="visible")
        email_input.click()
        email_input.fill(email)
        
        # Click Next button
        logger.info("Clicking Next button")
        next_button = page.get_by_role("button", name="Next")
        next_button.click()
        
        # Wait for password field
        logger.info("Waiting for password field")
        time.sleep(2)  # Give page time to load
        
        # Enter password
        logger.info("Entering password")
        password_input = page.get_by_role("textbox", name="Enter your password")
        password_input.wait_for(timeout=10000, state="visible")
        password_input.click()
        password_input.fill(password)
        
        # Press Enter to submit (as in user's example)
        logger.info("Submitting password")
        password_input.press("Enter")
        
        # Wait for navigation/response
        logger.info("Waiting for login response")
        time.sleep(3)
        
        # Check if login was successful by looking for account button (as in user's example)
        try:
            # Try to find the account button (indicates successful login)
            # The user's example shows: page.get_by_role("button", name="Google Account: Hossein (")
            account_button = page.get_by_role("button", name=lambda name: name and "Google Account" in name)
            account_button.wait_for(timeout=10000, state="visible")
            logger.info("Login successful - found account button")
            return True, "Credentials are working"
        except Exception as e:
            logger.debug(f"Account button not found: {e}")
            # Check for error messages
            try:
                error_text = page.locator("text=/wrong password|incorrect|error|try again|invalid/i").first
                if error_text.count() > 0:
                    error_msg = error_text.inner_text(timeout=2000)
                    logger.warning(f"Login failed: {error_msg}")
                    return False, f"Login failed: {error_msg}"
            except Exception:
                pass
            
            # Check if we're still on the login page
            current_url = page.url
            if "accounts.google.com" in current_url and "signin" in current_url:
                logger.warning("Still on login page - credentials may be invalid")
                return False, "Login failed: Unable to authenticate"
            
            # If we got here, we might have logged in but couldn't find the account button
            # Check the page title or URL
            if "myaccount.google.com" in current_url or "accounts.google.com" not in current_url:
                logger.info("Login appears successful based on URL")
                return True, "Credentials are working"
            
            logger.warning("Unable to determine login status")
            return False, "Unable to verify login status"
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error checking credentials: {error_msg}", exc_info=True)
        return False, f"Error checking credentials: {error_msg}"


def check_google_credential_sync(email: str, password: str) -> Tuple[bool, str]:
    """
    Check if Google credentials are working by attempting to log in.
    This is a convenience wrapper that creates its own browser.
    For Celery tasks, use check_google_credential_flow with _run_with_browser instead.
    
    Args:
        email: Google account email
        password: Google account password
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    import os
    from app.utils.browser_utils import initialize_page_sync
    
    page = None
    context = None
    playwright = None
    
    try:
        logger.info(f"Starting credential check for {email} (standalone)")
        
        # Use initialize_page_sync which handles sync API correctly for Celery workers
        # Use a unique profile name for credential checking to avoid conflicts
        profile_name = os.getenv("USER_PROFILE_NAME", "default")
        page, context, playwright = initialize_page_sync(
            headless=True, user_profile_name=f"{profile_name}_credential_check"
        )
        
        return check_google_credential_flow(page, email, password)
        
    finally:
        # Clean up
        try:
            if context:
                context.close()
            if playwright:
                playwright.stop()
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")

