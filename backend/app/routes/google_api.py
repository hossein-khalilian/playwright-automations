import os

from fastapi import APIRouter, HTTPException, status
from playwright.async_api import Page

from app.models import GoogleLoginStatusResponse
from app.utils.browser_state import get_browser_page
from app.utils.google import check_google_login_status

router = APIRouter(prefix="/google", tags=["Google"])


@router.get(
    "/login-status",
    response_model=GoogleLoginStatusResponse,
    status_code=status.HTTP_200_OK,
)
async def check_login_status() -> GoogleLoginStatusResponse:
    """
    Check if Google is currently logged in by examining the persistent browser profile.
    Uses the browser page initialized at app startup.
    """
    page = get_browser_page()
    if page is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Browser page not initialized. Please check server logs.",
        )

    # Ensure we have an async page (should always be the case with async initialization)
    if not isinstance(page, Page):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Browser page type mismatch. Expected async page.",
        )

    try:
        result = await check_google_login_status(page)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking Google login status: {str(exc)}",
        ) from exc

    return GoogleLoginStatusResponse(is_logged_in=result)
