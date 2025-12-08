import asyncio
import logging

from fastapi import APIRouter, HTTPException, status

from app.auth import CurrentUser
from app.models import GooglePagesStatusResponse, PageLoginStatus
from app.utils.browser_state import get_all_pages
from app.utils.google import check_google_login_status_sync

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/google", tags=["Google"])


def _check_page_login_status_sync(index: int, page) -> PageLoginStatus:
    """
    Synchronous function to check login status for a single page.
    This runs in a thread executor to avoid greenlet errors.
    """
    page_status = PageLoginStatus(
        page_index=index,
        is_logged_in=False,
        is_closed=False,
        error=None,
    )

    try:
        # Check if page is closed
        if page.is_closed():
            page_status.is_closed = True
            page_status.error = "Page is closed"
        else:
            # Check Google login status
            try:
                logger.info(f"Checking login status for page {index}...")
                is_logged_in = check_google_login_status_sync(page)
                page_status.is_logged_in = is_logged_in
                logger.info(
                    f"Page {index} login status: {is_logged_in}, current URL: {page.url}"
                )
                if not is_logged_in:
                    # Try to get more info about why it failed
                    try:
                        current_url = page.url
                        page_status.error = (
                            f"Login check returned False. Current URL: {current_url}"
                        )
                        logger.warning(
                            f"Page {index} is not logged in. Current URL: {current_url}"
                        )
                    except Exception:
                        pass
            except Exception as exc:
                logger.warning(
                    f"Error checking login status for page {index}: {exc}",
                    exc_info=True,
                )
                page_status.error = str(exc)
    except Exception as exc:
        logger.error(f"Error accessing page {index}: {exc}", exc_info=True)
        page_status.error = str(exc)

    return page_status


@router.get(
    "/pages-status",
    response_model=GooglePagesStatusResponse,
    status_code=status.HTTP_200_OK,
)
async def get_pages_login_status(current_user: CurrentUser) -> GooglePagesStatusResponse:
    """
    Get the login status of all pages in the browser pool.
    Returns the status of each page indicating whether it's logged into Google.
    """
    all_pages = get_all_pages()

    if not all_pages:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Browser pages not initialized. Please check server logs.",
        )

    # Run sync Playwright code in thread executor to avoid greenlet errors
    # Check all pages concurrently
    tasks = [
        asyncio.to_thread(_check_page_login_status_sync, index, page)
        for index, page in enumerate(all_pages)
    ]
    
    pages_status = await asyncio.gather(*tasks)
    
    # Check if all pages are logged in
    all_logged_in = all(page.is_logged_in for page in pages_status)

    return GooglePagesStatusResponse(
        total_pages=len(all_pages),
        pages_status=list(pages_status),
        all_logged_in=all_logged_in,
    )
