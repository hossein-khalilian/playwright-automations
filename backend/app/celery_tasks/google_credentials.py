"""
Celery tasks for Google credential management.
"""
import logging
import os
from datetime import datetime, timezone
from typing import Dict, Any

from app.celery_app import celery_app
from app.utils.browser_utils import initialize_page_sync
from app.utils.browser_state import get_page_from_pool, return_page_to_pool
from app.utils.check_google_credential import check_google_credential_flow
from app.utils.db import (
    get_decrypted_google_credential_sync,
    update_google_credential_sync,
)

logger = logging.getLogger(__name__)


@celery_app.task(name="google_credentials.check_credential")
def check_google_credential_task(email: str) -> Dict[str, Any]:
    """
    Check if Google credentials are working by attempting to log in.
    Updates the status in the database.
    
    Args:
        email: Google account email
        
    Returns:
        Dictionary with status and message
    """
    try:
        logger.info(f"Starting credential check task for {email}")
        
        # Update status to "checking"
        update_google_credential_sync(email, status="checking")
        
        # Get decrypted credentials
        decrypted_cred = get_decrypted_google_credential_sync(email)
        if not decrypted_cred:
            error_msg = "Failed to retrieve credentials"
            logger.error(f"{error_msg} for {email}")
            update_google_credential_sync(
                email,
                status="not_working",
                status_checked_at=datetime.now(timezone.utc),
            )
            return {
                "status": "error",
                "message": error_msg,
                "is_working": False,
            }
        
        # Check credentials using browser from pool
        page = None
        context = None
        playwright = None
        page_from_pool = False
        
        try:
            # Try to get a page from the pool first
            page = get_page_from_pool()
            
            if page is not None:
                logger.debug("Using page from pool for credential check")
                page_from_pool = True
            else:
                # Fallback: create a new browser if pool is not available
                logger.warning(
                    "No page available in pool, creating new browser instance for credential check. "
                    "Consider initializing browser pool in Celery worker."
                )
                profile_name = os.getenv("USER_PROFILE_NAME", "default")
                page, context, playwright = initialize_page_sync(
                    headless=True, user_profile_name=profile_name
                )
            
            # Run the credential check flow
            is_working, message = check_google_credential_flow(
                page,
                decrypted_cred["email"],
                decrypted_cred["password"],
            )
        finally:
            # Return page to pool if it came from pool, otherwise clean up
            if page_from_pool and page is not None:
                try:
                    return_page_to_pool(page)
                    logger.debug("Returned page to pool after credential check")
                except Exception as e:
                    logger.warning(f"Error returning page to pool: {e}")
            elif context and playwright:
                # Clean up browser resources for fallback browser
                try:
                    if context:
                        context.close()
                    if playwright:
                        playwright.stop()
                except Exception as e:
                    logger.warning(f"Error cleaning up browser: {e}")
        
        # Update status in database
        status_value = "working" if is_working else "not_working"
        update_google_credential_sync(
            email,
            status=status_value,
            status_checked_at=datetime.now(timezone.utc),
        )
        
        logger.info(f"Credential check completed for {email}: {status_value}")
        
        return {
            "status": "success",
            "message": message,
            "is_working": is_working,
        }
        
    except Exception as e:
        error_msg = f"Error checking credentials: {str(e)}"
        logger.error(f"{error_msg} for {email}", exc_info=True)
        
        # Update status to indicate error
        try:
            update_google_credential_sync(
                email,
                status="not_working",
                status_checked_at=datetime.now(timezone.utc),
            )
        except Exception as update_error:
            logger.error(f"Failed to update status in database: {update_error}")
        
        return {
            "status": "error",
            "message": error_msg,
            "is_working": False,
        }

