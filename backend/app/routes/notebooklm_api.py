from fastapi import APIRouter, HTTPException, status
from playwright.async_api import Page

from app.automation.tasks.notebooklm.create_notebook import NotebookLMError
from app.models import NotebookCreateResponse
from app.utils.browser_state import get_browser_page
from app.utils.notebooklm import trigger_notebook_creation

router = APIRouter(prefix="/notebooklm", tags=["NotebookLM"])


@router.post(
    "/notebooks",
    response_model=NotebookCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_notebook_endpoint() -> NotebookCreateResponse:
    """
    Create a new notebook in NotebookLM using the browser page from app state.
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
        result = await trigger_notebook_creation(page)
    except NotebookLMError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while creating a NotebookLM notebook.",
        ) from exc

    return NotebookCreateResponse(
        status=result["status"],
        message=result["message"],
        notebook_url=result.get("page_url"),
    )
