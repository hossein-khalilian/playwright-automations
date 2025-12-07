# import os
#
# from fastapi import APIRouter, HTTPException, status
# from playwright.sync_api import Page  # ← sync Page type
#
# from app.auth import CurrentUser
# from app.models import GoogleLoginStatusResponse
# from app.utils.browser_state import get_browser_page
# from app.utils.google import check_google_login_status_sync
#
# router = APIRouter(prefix="/google", tags=["Google"])
#
#
# @router.get(
#     "/login-status-sync",
#     response_model=GoogleLoginStatusResponse,
#     status_code=status.HTTP_200_OK,
# )
# def check_login_status_sync(current_user: CurrentUser) -> GoogleLoginStatusResponse:
#     """
#     Check if Google is logged in (SYNC version).
#     Uses a synchronous Playwright page.
#     """
#     page = get_browser_page()
#     if page is None:
#         raise HTTPException(
#             status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#             detail="Browser page not initialized. Please check server logs.",
#         )
#
#     # Ensure we have a synchronous page
#     if not isinstance(page, Page):
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Browser page type mismatch. Expected sync page.",
#         )
#
#     try:
#         result = check_google_login_status_sync(page)
#     except Exception as exc:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Error checking Google login status: {str(exc)}",
#         ) from exc
#
#     return GoogleLoginStatusResponse(is_logged_in=result)
