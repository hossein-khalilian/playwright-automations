import os
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from playwright.async_api import Page

from app.auth import CurrentUser
from app.automation.tasks.notebooklm.exceptions import NotebookLMError
from app.models import (
    ArtifactDeleteResponse,
    ArtifactDownloadResponse,
    ArtifactInfo,
    ArtifactListResponse,
    AudioOverviewCreateResponse,
    AudioOverviewDeleteResponse,
    AudioOverviewDownloadResponse,
    AudioOverviewRenameRequest,
    AudioOverviewRenameResponse,
    AudioOverviewStatusResponse,
    ChatHistoryResponse,
    ChatMessage,
    Notebook,
    NotebookCreateResponse,
    NotebookListResponse,
    NotebookQueryRequest,
    NotebookQueryResponse,
    Source,
    SourceListResponse,
    SourceUploadResponse,
    VideoInfo,
    VideoOverviewCreateResponse,
    VideoOverviewDeleteRequest,
    VideoOverviewDeleteResponse,
    VideoOverviewDownloadRequest,
    VideoOverviewDownloadResponse,
    VideoOverviewRenameRequest,
    VideoOverviewRenameResponse,
    VideoOverviewStatusResponse,
)
from app.utils.browser_state import get_browser_page
from app.utils.db import delete_notebook_from_db, get_notebooks_by_user, save_notebook
from app.utils.notebooklm import (
    trigger_artifact_deletion,
    trigger_artifact_download,
    trigger_artifact_listing,
    trigger_audio_overview_creation,
    trigger_audio_overview_deletion,
    trigger_audio_overview_rename,
    trigger_audio_overview_status,
    trigger_chat_history,
    trigger_chat_history_deletion,
    trigger_notebook_creation,
    trigger_notebook_deletion,
    trigger_notebook_query,
    trigger_source_deletion,
    trigger_source_listing,
    trigger_source_upload,
    trigger_video_overview_creation,
    trigger_video_overview_deletion,
    trigger_video_overview_rename,
    trigger_video_overview_status,
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


@router.post(
    "/notebooks/{notebook_id}/query",
    response_model=NotebookQueryResponse,
    status_code=status.HTTP_200_OK,
)
async def query_notebook_endpoint(
    notebook_id: str,
    request: NotebookQueryRequest,
    current_user: CurrentUser,
) -> NotebookQueryResponse:
    """
    Query a notebook in NotebookLM.
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
        result = await trigger_notebook_query(page, notebook_id, request.query)
    except NotebookLMError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while querying NotebookLM notebook.",
        ) from exc

    return NotebookQueryResponse(
        status=result["status"],
        message=result["message"],
        query=result["query"],
    )


@router.get(
    "/notebooks/{notebook_id}/chat",
    response_model=ChatHistoryResponse,
    status_code=status.HTTP_200_OK,
)
async def get_chat_history_endpoint(
    notebook_id: str,
    current_user: CurrentUser,
) -> ChatHistoryResponse:
    """
    Get the complete chat history from a notebook.
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
        result = await trigger_chat_history(page, notebook_id)
    except NotebookLMError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while retrieving chat history from NotebookLM notebook.",
        ) from exc

    # Convert messages to ChatMessage objects
    chat_messages = [
        ChatMessage(role=msg["role"], content=msg["content"])
        for msg in result.get("messages", [])
    ]

    return ChatHistoryResponse(
        status=result["status"],
        message=result["message"],
        messages=chat_messages,
    )


@router.delete(
    "/notebooks/{notebook_id}/chat",
    status_code=status.HTTP_200_OK,
)
async def delete_chat_history_endpoint(
    notebook_id: str,
    current_user: CurrentUser,
) -> dict:
    """
    Delete the chat history from a notebook.
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
        result = await trigger_chat_history_deletion(page, notebook_id)
    except NotebookLMError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while deleting chat history from NotebookLM notebook.",
        ) from exc

    return {
        "status": result["status"],
        "message": result["message"],
    }


@router.post(
    "/notebooks/{notebook_id}/audio-overview",
    response_model=AudioOverviewCreateResponse,
    status_code=status.HTTP_200_OK,
)
async def create_audio_overview_endpoint(
    notebook_id: str,
    current_user: CurrentUser,
) -> AudioOverviewCreateResponse:
    """
    Create an audio overview for a notebook.
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
        result = await trigger_audio_overview_creation(page, notebook_id)
    except NotebookLMError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while creating audio overview.",
        ) from exc

    return AudioOverviewCreateResponse(
        status=result["status"],
        message=result["message"],
    )


@router.get(
    "/notebooks/{notebook_id}/audio-overview",
    response_model=AudioOverviewStatusResponse,
    status_code=status.HTTP_200_OK,
)
async def get_audio_overview_status_endpoint(
    notebook_id: str,
    current_user: CurrentUser,
) -> AudioOverviewStatusResponse:
    """
    Get the status of the audio overview for a notebook.
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
        result = await trigger_audio_overview_status(page, notebook_id)
    except NotebookLMError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while getting audio overview status.",
        ) from exc

    return AudioOverviewStatusResponse(
        status=result["status"],
        message=result["message"],
        is_generating=result.get("is_generating", False),
        audio_name=result.get("audio_name"),
    )


@router.put(
    "/notebooks/{notebook_id}/audio-overview/rename",
    response_model=AudioOverviewRenameResponse,
    status_code=status.HTTP_200_OK,
)
async def rename_audio_overview_endpoint(
    notebook_id: str,
    request: AudioOverviewRenameRequest,
    current_user: CurrentUser,
) -> AudioOverviewRenameResponse:
    """
    Rename an audio overview.
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
        result = await trigger_audio_overview_rename(
            page, notebook_id, request.new_name
        )
    except NotebookLMError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while renaming audio overview.",
        ) from exc

    return AudioOverviewRenameResponse(
        status=result["status"],
        message=result["message"],
    )


@router.delete(
    "/notebooks/{notebook_id}/audio-overview",
    response_model=AudioOverviewDeleteResponse,
    status_code=status.HTTP_200_OK,
)
async def delete_audio_overview_endpoint(
    notebook_id: str,
    current_user: CurrentUser,
) -> AudioOverviewDeleteResponse:
    """
    Delete an audio overview from a notebook.
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
        result = await trigger_audio_overview_deletion(page, notebook_id)
    except NotebookLMError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while deleting audio overview.",
        ) from exc

    return AudioOverviewDeleteResponse(
        status=result["status"],
        message=result["message"],
    )


@router.post(
    "/notebooks/{notebook_id}/video-overview",
    response_model=VideoOverviewCreateResponse,
    status_code=status.HTTP_200_OK,
)
async def create_video_overview_endpoint(
    notebook_id: str,
    current_user: CurrentUser,
) -> VideoOverviewCreateResponse:
    """
    Create a video overview for a notebook.
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
        result = await trigger_video_overview_creation(page, notebook_id)
    except NotebookLMError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while creating video overview.",
        ) from exc

    return VideoOverviewCreateResponse(
        status=result["status"],
        message=result["message"],
    )


@router.get(
    "/notebooks/{notebook_id}/video-overview",
    response_model=VideoOverviewStatusResponse,
    status_code=status.HTTP_200_OK,
)
async def get_video_overview_status_endpoint(
    notebook_id: str,
    current_user: CurrentUser,
) -> VideoOverviewStatusResponse:
    """
    Get the status of the video overview for a notebook.
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
        result = await trigger_video_overview_status(page, notebook_id)
    except NotebookLMError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while getting video overview status.",
        ) from exc

    # Convert video dicts to VideoInfo objects
    videos = [VideoInfo(name=video["name"]) for video in result.get("videos", [])]

    return VideoOverviewStatusResponse(
        status=result["status"],
        message=result["message"],
        is_generating=result.get("is_generating", False),
        videos=videos,
    )


@router.put(
    "/notebooks/{notebook_id}/video-overview/rename",
    response_model=VideoOverviewRenameResponse,
    status_code=status.HTTP_200_OK,
)
async def rename_video_overview_endpoint(
    notebook_id: str,
    request: VideoOverviewRenameRequest,
    current_user: CurrentUser,
) -> VideoOverviewRenameResponse:
    """
    Rename a video overview.
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
        result = await trigger_video_overview_rename(
            page, notebook_id, request.video_name, request.new_name
        )
    except NotebookLMError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while renaming video overview.",
        ) from exc

    return VideoOverviewRenameResponse(
        status=result["status"],
        message=result["message"],
    )


@router.delete(
    "/notebooks/{notebook_id}/video-overview",
    response_model=VideoOverviewDeleteResponse,
    status_code=status.HTTP_200_OK,
)
async def delete_video_overview_endpoint(
    notebook_id: str,
    current_user: CurrentUser,
    video_name: Optional[str] = None,
) -> VideoOverviewDeleteResponse:
    """
    Delete a video overview from a notebook.
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
        result = await trigger_video_overview_deletion(
            page, notebook_id, video_name
        )
    except NotebookLMError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while deleting video overview.",
        ) from exc

    return VideoOverviewDeleteResponse(
        status=result["status"],
        message=result["message"],
    )


@router.get(
    "/notebooks/{notebook_id}/artifacts",
    response_model=ArtifactListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_artifacts_endpoint(
    notebook_id: str,
    current_user: CurrentUser,
) -> ArtifactListResponse:
    """
    List all artifacts (materials) in a notebook with their status.
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
        result = await trigger_artifact_listing(page, notebook_id)
    except NotebookLMError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while listing artifacts from NotebookLM notebook.",
        ) from exc

    # Convert artifact dicts to ArtifactInfo objects
    artifacts = [
        ArtifactInfo(
            type=artifact.get("type"),
            name=artifact.get("name"),
            details=artifact.get("details"),
            status=artifact.get("status", "unknown"),
            is_generating=artifact.get("is_generating", False),
            has_play=artifact.get("has_play", False),
            has_interactive=artifact.get("has_interactive", False),
        )
        for artifact in result.get("artifacts", [])
    ]

    return ArtifactListResponse(
        status=result["status"],
        message=result["message"],
        artifacts=artifacts,
    )


@router.delete(
    "/notebooks/{notebook_id}/artifacts/{artifact_name:path}",
    response_model=ArtifactDeleteResponse,
    status_code=status.HTTP_200_OK,
)
async def delete_artifact_endpoint(
    notebook_id: str,
    artifact_name: str,
    current_user: CurrentUser,
) -> ArtifactDeleteResponse:
    """
    Delete an artifact from a notebook.
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
        result = await trigger_artifact_deletion(page, notebook_id, artifact_name)
    except NotebookLMError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while deleting artifact from NotebookLM notebook.",
        ) from exc

    return ArtifactDeleteResponse(
        status=result["status"],
        message=result["message"],
    )


@router.get(
    "/notebooks/{notebook_id}/artifacts/{artifact_name:path}/download",
    status_code=status.HTTP_200_OK,
)
async def download_artifact_endpoint(
    notebook_id: str,
    artifact_name: str,
    current_user: CurrentUser,
):
    """
    Download an artifact (audio or video overview) from a notebook.
    Returns the file as a downloadable file response.
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
        result = await trigger_artifact_download(page, notebook_id, artifact_name)
    except NotebookLMError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while downloading artifact from NotebookLM notebook.",
        ) from exc

    download_path = result.get("download_path")
    suggested_filename = result.get("suggested_filename")
    artifact_type = result.get("artifact_type")

    if not download_path or not os.path.exists(download_path):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Downloaded file not found. The download may have failed.",
        )

    # Determine media type and default filename based on artifact type
    if artifact_type == "video_overview":
        default_filename = suggested_filename or "video_overview.mp4"
        media_type = "video/mp4"
    else:  # audio_overview
        default_filename = suggested_filename or "audio_overview.m4a"
        media_type = "audio/mp4"  # m4a files use audio/mp4 MIME type

    # Return the file as a downloadable response
    return FileResponse(
        path=download_path,
        filename=default_filename,
        media_type=media_type,
    )
