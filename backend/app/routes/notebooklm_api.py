import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from playwright.async_api import Page

from app.auth import CurrentUser
from app.automation.tasks.notebooklm.create_notebook import NotebookLMError
from app.models import (
    Notebook,
    NotebookCreateResponse,
    NotebookListResponse,
    Source,
    SourceListResponse,
    SourceUploadResponse,
)
from app.utils.browser_state import get_browser_page
from app.utils.db import delete_notebook_from_db, get_notebooks_by_user, save_notebook
from app.utils.notebooklm import (
    trigger_notebook_creation,
    trigger_notebook_deletion,
    trigger_source_deletion,
    trigger_source_listing,
    trigger_source_upload,
)

router = APIRouter(prefix="/notebooklm", tags=["NotebookLM"])


@router.post(
    "/notebooks",
    response_model=NotebookCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_notebook_endpoint(current_user: CurrentUser) -> NotebookCreateResponse:
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

    # Save notebook to MongoDB if we have a notebook_id and URL
    notebook_id = result.get("notebook_id")
    notebook_url = result.get("page_url")
    if notebook_id and notebook_url:
        await save_notebook(
            username=current_user.username,
            notebook_id=notebook_id,
            notebook_url=notebook_url,
        )

    return NotebookCreateResponse(
        status=result["status"],
        message=result["message"],
        notebook_url=notebook_url,
    )


@router.get(
    "/notebooks",
    response_model=NotebookListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_notebooks_endpoint(current_user: CurrentUser) -> NotebookListResponse:
    """
    List all notebooks for the current user.
    """
    notebooks_data = await get_notebooks_by_user(current_user.username)
    
    notebooks = [
        Notebook(
            notebook_id=notebook["notebook_id"],
            notebook_url=notebook["notebook_url"],
            created_at=notebook["created_at"],
        )
        for notebook in notebooks_data
    ]
    
    return NotebookListResponse(notebooks=notebooks)


@router.delete(
    "/notebooks/{notebook_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_notebook_endpoint(
    notebook_id: str,
    current_user: CurrentUser,
) -> dict:
    """
    Delete a notebook in NotebookLM by its ID.
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

    # Verify the notebook belongs to the current user
    notebooks_data = await get_notebooks_by_user(current_user.username)
    notebook_exists = any(
        notebook["notebook_id"] == notebook_id for notebook in notebooks_data
    )

    if not notebook_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notebook {notebook_id} not found for the current user.",
        )

    try:
        result = await trigger_notebook_deletion(page, notebook_id)
    except NotebookLMError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while deleting a NotebookLM notebook.",
        ) from exc

    # Delete notebook from MongoDB
    await delete_notebook_from_db(
        username=current_user.username,
        notebook_id=notebook_id,
    )

    return {
        "status": result["status"],
        "message": result["message"],
    }


@router.post(
    "/notebooks/{notebook_id}/sources",
    response_model=SourceUploadResponse,
    status_code=status.HTTP_200_OK,
)
async def add_source_to_notebook_endpoint(
    notebook_id: str,
    current_user: CurrentUser,
    file: UploadFile = File(...),
) -> SourceUploadResponse:
    """
    Add a source file to a notebook in NotebookLM.
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

    # Verify the notebook belongs to the current user
    notebooks_data = await get_notebooks_by_user(current_user.username)
    notebook_exists = any(
        notebook["notebook_id"] == notebook_id for notebook in notebooks_data
    )

    if not notebook_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notebook {notebook_id} not found for the current user.",
        )

    # Save uploaded file to a temporary location
    temp_file_path = None
    try:
        # Create a temporary file with the same extension as the uploaded file
        file_extension = Path(file.filename).suffix if file.filename else ""
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=file_extension
        ) as temp_file:
            # Read the uploaded file content and write to temp file
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            result = await trigger_source_upload(page, notebook_id, temp_file_path)
        except NotebookLMError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unexpected error while adding source to NotebookLM notebook.",
            ) from exc

        return SourceUploadResponse(
            status=result["status"],
            message=result["message"],
        )
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception:
                # Ignore errors during cleanup
                pass


@router.get(
    "/notebooks/{notebook_id}/sources",
    response_model=SourceListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_sources_endpoint(
    notebook_id: str,
    current_user: CurrentUser,
) -> SourceListResponse:
    """
    List all sources in a notebook.
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

    # Verify the notebook belongs to the current user
    notebooks_data = await get_notebooks_by_user(current_user.username)
    notebook_exists = any(
        notebook["notebook_id"] == notebook_id for notebook in notebooks_data
    )

    if not notebook_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notebook {notebook_id} not found for the current user.",
        )

    try:
        result = await trigger_source_listing(page, notebook_id)
    except NotebookLMError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while listing sources from NotebookLM notebook.",
        ) from exc

    # Convert source names to Source objects
    sources = [Source(name=name) for name in result.get("sources", [])]

    return SourceListResponse(
        status=result["status"],
        message=result["message"],
        sources=sources,
    )


@router.delete(
    "/notebooks/{notebook_id}/sources/{source_name:path}",
    status_code=status.HTTP_200_OK,
)
async def delete_source_endpoint(
    notebook_id: str,
    source_name: str,
    current_user: CurrentUser,
) -> dict:
    """
    Delete a source from a notebook.
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

    # Verify the notebook belongs to the current user
    notebooks_data = await get_notebooks_by_user(current_user.username)
    notebook_exists = any(
        notebook["notebook_id"] == notebook_id for notebook in notebooks_data
    )

    if not notebook_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notebook {notebook_id} not found for the current user.",
        )

    try:
        result = await trigger_source_deletion(page, notebook_id, source_name)
    except NotebookLMError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while deleting source from NotebookLM notebook.",
        ) from exc

    return {
        "status": result["status"],
        "message": result["message"],
    }
