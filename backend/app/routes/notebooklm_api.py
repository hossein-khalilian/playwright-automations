import os
import tempfile
import time
from pathlib import Path
from typing import Optional
from urllib.parse import quote

from celery.result import AsyncResult
from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.auth import CurrentUser
from app.celery_app import celery_app
from app.celery_tasks.notebooklm import (
    add_source_task,
    add_url_source_task,
    create_audio_overview_task,
    create_flashcards_task,
    create_infographic_task,
    create_mindmap_task,
    create_notebook_task,
    create_quiz_task,
    create_report_task,
    create_slide_deck_task,
    create_video_overview_task,
    delete_artifact_task,
    delete_chat_history_task,
    delete_notebook_task,
    delete_source_task,
    download_artifact_task,
    get_chat_history_task,
    list_artifacts_task,
    list_sources_task,
    query_notebook_task,
    rename_artifact_task,
    rename_source_task,
    review_source_task,
    update_notebook_titles_task,
)
from app.models import (
    ArtifactRenameRequest,
    AudioOverviewCreateRequest,
    FlashcardCreateRequest,
    InfographicCreateRequest,
    MindmapCreateRequest,
    Notebook,
    NotebookListResponse,
    NotebookQueryRequest,
    QuizCreateRequest,
    ReportCreateRequest,
    SlideDeckCreateRequest,
    SourceRenameRequest,
    TaskStatusResponse,
    TaskSubmissionResponse,
    UrlSourceAddRequest,
    VideoOverviewCreateRequest,
)
from app.utils.db import get_notebooks_by_user

router = APIRouter(prefix="/notebooklm")


def _headless() -> bool:
    return os.getenv("HEADLESS", "true").lower() == "true"


def _profile() -> str:
    return os.getenv("USER_PROFILE_NAME", "default")


def _submit(task_fn, *args, **kwargs) -> TaskSubmissionResponse:
    task = task_fn.delay(*args, **kwargs)
    return TaskSubmissionResponse(task_id=task.id, status="submitted")


def _task_status(task_id: str) -> TaskStatusResponse:
    res = AsyncResult(task_id, app=celery_app)
    state = res.state
    status_txt = "pending"
    message = None
    result_payload = None

    if state == "SUCCESS":
        status_txt = "success"
        result_payload = res.result
        if isinstance(result_payload, dict) and "message" in result_payload:
            message = result_payload.get("message")
        else:
            message = str(result_payload)
    elif state in {"FAILURE", "REVOKED"}:
        status_txt = "failure"
        try:
            result_payload = res.result
            message = str(result_payload)
        except Exception:
            message = None

    return TaskStatusResponse(
        task_id=task_id,
        state=state,
        status=status_txt,
        message=message,
        result=result_payload if status_txt == "success" else None,
    )


# ============================================================================
# Notebooks
# ============================================================================


def _is_untitled_title(title: Optional[str]) -> bool:
    """
    Check if a title is considered "untitled" and should be refreshed.
    
    Args:
        title: The title to check
        
    Returns:
        True if the title is considered untitled
    """
    if not title:
        return True
    
    title_lower = title.strip().lower()
    # Common variations of "untitled notebook"
    untitled_patterns = [
        "untitled notebook",
        "untitled",
        "بدون عنوان",  # Persian: "without title"
        "دفترچه بدون عنوان",  # Persian: "notebook without title"
    ]
    
    return title_lower in [p.lower() for p in untitled_patterns]


@router.get(
    "/notebooks",
    response_model=NotebookListResponse,
    status_code=status.HTTP_200_OK,
    tags=["Notebooks"],
)
async def list_notebooks_endpoint(current_user: CurrentUser) -> NotebookListResponse:
    """
    List all notebooks for the current user.
    Returns notebooks directly from MongoDB without using Celery.
    If notebooks don't have titles or have "Untitled notebook", triggers a background task to fetch them.
    """
    notebooks_data = await get_notebooks_by_user(current_user.username)
    
    # Check which notebooks need titles (no title or "Untitled notebook")
    notebooks_without_titles = [
        doc["notebook_id"]
        for doc in notebooks_data
        if _is_untitled_title(doc.get("title"))
    ]
    
    # Trigger background task to fetch titles if needed
    if notebooks_without_titles:
        update_notebook_titles_task.delay(
            current_user.username,
            notebooks_without_titles,
            _headless(),
            _profile(),
        )
    
    notebooks = [
        Notebook(
            notebook_id=doc["notebook_id"],
            notebook_url=doc["notebook_url"],
            created_at=doc["created_at"],
            email=doc.get("email"),
            title=doc.get("title"),
        )
        for doc in notebooks_data
    ]
    return NotebookListResponse(notebooks=notebooks)


@router.post(
    "/notebooks",
    response_model=TaskSubmissionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Notebooks"],
)
def create_notebook_endpoint(current_user: CurrentUser) -> TaskSubmissionResponse:
    return _submit(create_notebook_task, current_user.username, _headless(), _profile())


@router.delete(
    "/notebooks/{notebook_id}",
    response_model=TaskSubmissionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Notebooks"],
)
def delete_notebook_endpoint(
    notebook_id: str, current_user: CurrentUser
) -> TaskSubmissionResponse:
    return _submit(
        delete_notebook_task,
        current_user.username,
        notebook_id,
        _headless(),
        _profile(),
    )


# ============================================================================
# Sources
# ============================================================================


@router.get(
    "/notebooks/{notebook_id}/sources",
    response_model=TaskSubmissionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Sources"],
)
def list_sources_endpoint(
    notebook_id: str, current_user: CurrentUser
) -> TaskSubmissionResponse:
    return _submit(list_sources_task, notebook_id, _headless(), _profile())


@router.post(
    "/notebooks/{notebook_id}/sources/upload",
    response_model=TaskSubmissionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Sources"],
)
def upload_source_endpoint(
    notebook_id: str, file: UploadFile = File(...), current_user: CurrentUser = None
) -> TaskSubmissionResponse:
    try:
        suffix = Path(file.filename).suffix if file.filename else ".bin"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = file.file.read()
            tmp.write(content)
            tmp_path = tmp.name
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store upload: {exc}",
        )
    username = current_user.username if current_user else None
    return _submit(add_source_task, notebook_id, tmp_path, _headless(), _profile(), username)


@router.post(
    "/notebooks/{notebook_id}/sources/urls",
    response_model=TaskSubmissionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Sources"],
)
def add_url_source_endpoint(
    notebook_id: str,
    payload: UrlSourceAddRequest,
    current_user: CurrentUser,
) -> TaskSubmissionResponse:
    """Add URL sources to a notebook."""
    return _submit(
        add_url_source_task, notebook_id, payload.urls, _headless(), _profile(), current_user.username
    )


@router.delete(
    "/notebooks/{notebook_id}/sources/{source_name}",
    response_model=TaskSubmissionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Sources"],
)
def delete_source_endpoint(
    notebook_id: str, source_name: str, current_user: CurrentUser
) -> TaskSubmissionResponse:
    return _submit(
        delete_source_task, notebook_id, source_name, _headless(), _profile()
    )


@router.post(
    "/notebooks/{notebook_id}/sources/{source_name}/rename",
    response_model=TaskSubmissionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Sources"],
)
def rename_source_endpoint(
    notebook_id: str,
    source_name: str,
    payload: SourceRenameRequest,
    current_user: CurrentUser,
) -> TaskSubmissionResponse:
    return _submit(
        rename_source_task,
        notebook_id,
        source_name,
        payload.new_name,
        _headless(),
        _profile(),
    )


@router.post(
    "/notebooks/{notebook_id}/sources/{source_name}/review",
    response_model=TaskSubmissionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Sources"],
)
def review_source_endpoint(
    notebook_id: str, source_name: str, current_user: CurrentUser
) -> TaskSubmissionResponse:
    return _submit(
        review_source_task, notebook_id, source_name, _headless(), _profile()
    )


# ============================================================================
# Chat
# ============================================================================
@router.get(
    "/notebooks/{notebook_id}/chat",
    response_model=TaskSubmissionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Chat"],
)
def chat_history_endpoint(
    notebook_id: str, current_user: CurrentUser
) -> TaskSubmissionResponse:
    return _submit(get_chat_history_task, notebook_id, _headless(), _profile())


@router.post(
    "/notebooks/{notebook_id}/query",
    response_model=TaskSubmissionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Chat"],
)
def query_notebook_endpoint(
    notebook_id: str, payload: NotebookQueryRequest, current_user: CurrentUser
) -> TaskSubmissionResponse:
    return _submit(
        query_notebook_task, notebook_id, payload.query, _headless(), _profile()
    )


@router.delete(
    "/notebooks/{notebook_id}/chat",
    response_model=TaskSubmissionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Chat"],
)
def delete_chat_history_endpoint(
    notebook_id: str, current_user: CurrentUser
) -> TaskSubmissionResponse:
    return _submit(delete_chat_history_task, notebook_id, _headless(), _profile())


# ============================================================================
# Artifacts - Management
# ============================================================================


@router.get(
    "/notebooks/{notebook_id}/artifacts",
    response_model=TaskSubmissionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Artifacts - Management"],
)
def list_artifacts_endpoint(
    notebook_id: str, current_user: CurrentUser
) -> TaskSubmissionResponse:
    return _submit(list_artifacts_task, notebook_id, _headless(), _profile())


@router.delete(
    "/notebooks/{notebook_id}/artifacts/{artifact_name}",
    response_model=TaskSubmissionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Artifacts - Management"],
)
def delete_artifact_endpoint(
    notebook_id: str, artifact_name: str, current_user: CurrentUser
) -> TaskSubmissionResponse:
    return _submit(
        delete_artifact_task, notebook_id, artifact_name, _headless(), _profile()
    )


@router.post(
    "/notebooks/{notebook_id}/artifacts/{artifact_name}/rename",
    response_model=TaskSubmissionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Artifacts - Management"],
)
def rename_artifact_endpoint(
    notebook_id: str,
    artifact_name: str,
    payload: ArtifactRenameRequest,
    current_user: CurrentUser,
) -> TaskSubmissionResponse:
    return _submit(
        rename_artifact_task,
        notebook_id,
        artifact_name,
        payload.new_name,
        _headless(),
        _profile(),
    )


@router.post(
    "/notebooks/{notebook_id}/artifacts/{artifact_name}/download",
    tags=["Artifacts - Management"],
)
def download_artifact_endpoint(
    notebook_id: str, artifact_name: str, current_user: CurrentUser
):
    """
    Download an artifact. Waits for download to complete and returns the file.
    """
    # Submit the download task and wait for it to complete
    task_result = _submit(
        download_artifact_task, notebook_id, artifact_name, _headless(), _profile()
    )
    
    # Wait for the task to complete
    status_result = _task_status(task_result.task_id)
    
    # Poll until task is complete (wait up to 2 minutes)
    max_attempts = 60
    poll_interval = 2
    for attempt in range(max_attempts):
        if status_result.status in ("success", "failure"):
            break
        time.sleep(poll_interval)
        status_result = _task_status(task_result.task_id)
    
    if status_result.status != "success":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=status_result.message or "Download failed",
        )
    
    # Get the download path from the result
    result = status_result.result
    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Download completed but no result returned",
        )
    
    if not isinstance(result, dict):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected result format: {type(result)}",
        )
    
    if "download_path" not in result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Download completed but file path not found in result",
        )
    
    download_path = result["download_path"]
    suggested_filename = result.get("filename", f"{artifact_name}.png")
    
    # Use the suggested filename from the download (it should already have the correct extension)
    filename = suggested_filename
    
    # Only add extension if missing, and try to detect from actual file first
    if not Path(filename).suffix:
        # If no extension, try to detect from actual file
        actual_file_ext = Path(download_path).suffix
        if actual_file_ext:
            filename = f"{filename}{actual_file_ext}"
        else:
            # Default based on artifact type if we can't detect
            # But prefer to use the suggested filename which should have the extension
            filename = f"{filename}.png"
    
    # Check if file exists
    if not os.path.exists(download_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Downloaded file not found at {download_path}",
        )
    
    # Determine media type from file extension
    file_ext = Path(filename).suffix.lower()
    media_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".pdf": "application/pdf",
        ".mp4": "video/mp4",
        ".mp3": "audio/mpeg",
        ".json": "application/json",
        ".csv": "text/csv",
        ".txt": "text/plain",
        ".html": "text/html",
        ".xml": "application/xml",
    }
    media_type = media_types.get(file_ext, "application/octet-stream")
    
    # Clean filename for safe header usage
    # Remove any path components and ensure it's a valid filename
    safe_filename = os.path.basename(filename)
    
    # Preserve the file extension
    file_ext = Path(safe_filename).suffix
    
    # Create ASCII-safe filename for Content-Disposition header
    # HTTP headers must be encodable in latin-1
    try:
        # Try to encode as latin-1 to check if it's safe
        safe_filename.encode('latin-1')
        header_filename = safe_filename
    except UnicodeEncodeError:
        # Filename contains non-latin-1 characters
        # Create ASCII version by removing/replacing non-ASCII characters
        # But preserve the extension
        base_name = Path(safe_filename).stem
        ascii_base = base_name.encode('ascii', 'ignore').decode('ascii')
        if not ascii_base or not ascii_base.strip():
            # If base name becomes empty, use artifact name
            ascii_base = artifact_name
        # Always preserve the original extension
        header_filename = f"{ascii_base}{file_ext}" if file_ext else f"{ascii_base}.png"
    
    # Build Content-Disposition header
    # For Unicode filenames, we'll rely on the filename parameter of FileResponse
    # and use a simple ASCII-safe header
    content_disposition = f'attachment; filename="{header_filename}"'
    
    # Verify the header can be encoded in latin-1 (required by HTTP spec)
    try:
        content_disposition.encode('latin-1')
    except UnicodeEncodeError:
        # If still fails (shouldn't happen now), use a basic fallback
        file_ext = Path(safe_filename).suffix or '.png'
        content_disposition = f'attachment; filename="download{file_ext}"'
    
    # Return the file
    # FileResponse will handle the filename parameter for the actual file
    # The header provides a fallback for browsers that don't support the filename parameter
    return FileResponse(
        path=download_path,
        filename=safe_filename,  # This allows Unicode in modern browsers
        media_type=media_type,
        headers={
            "Content-Disposition": content_disposition,
        },
    )


# ============================================================================
# Artifacts - Creation
# ============================================================================


@router.post(
    "/notebooks/{notebook_id}/audio_overview",
    response_model=TaskSubmissionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Artifacts - Creation"],
)
def create_audio_overview_endpoint(
    notebook_id: str,
    payload: AudioOverviewCreateRequest,
    current_user: CurrentUser,
) -> TaskSubmissionResponse:
    return _submit(
        create_audio_overview_task,
        notebook_id,
        _headless(),
        _profile(),
        payload.audio_format.value if payload.audio_format else None,
        payload.language.value if payload.language else None,
        payload.length,
        payload.focus_text,
    )


@router.post(
    "/notebooks/{notebook_id}/video_overview",
    response_model=TaskSubmissionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Artifacts - Creation"],
)
def create_video_overview_endpoint(
    notebook_id: str,
    payload: VideoOverviewCreateRequest,
    current_user: CurrentUser,
) -> TaskSubmissionResponse:
    return _submit(
        create_video_overview_task,
        notebook_id,
        _headless(),
        _profile(),
        payload.video_format.value if payload.video_format else None,
        payload.language.value if payload.language else None,
        payload.visual_style.value if payload.visual_style else None,
        payload.custom_style_description,
        payload.focus_text,
    )


@router.post(
    "/notebooks/{notebook_id}/flashcards",
    response_model=TaskSubmissionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Artifacts - Creation"],
)
def create_flashcards_endpoint(
    notebook_id: str,
    payload: FlashcardCreateRequest,
    current_user: CurrentUser,
) -> TaskSubmissionResponse:
    return _submit(
        create_flashcards_task,
        notebook_id,
        _headless(),
        _profile(),
        payload.card_count,
        payload.difficulty,
        payload.topic,
    )


@router.post(
    "/notebooks/{notebook_id}/quiz",
    response_model=TaskSubmissionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Artifacts - Creation"],
)
def create_quiz_endpoint(
    notebook_id: str,
    payload: QuizCreateRequest,
    current_user: CurrentUser,
) -> TaskSubmissionResponse:
    return _submit(
        create_quiz_task,
        notebook_id,
        _headless(),
        _profile(),
        payload.question_count,
        payload.difficulty,
        payload.topic,
    )


@router.post(
    "/notebooks/{notebook_id}/infographic",
    response_model=TaskSubmissionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Artifacts - Creation"],
)
def create_infographic_endpoint(
    notebook_id: str,
    payload: InfographicCreateRequest,
    current_user: CurrentUser,
) -> TaskSubmissionResponse:
    return _submit(
        create_infographic_task,
        notebook_id,
        _headless(),
        _profile(),
        payload.language,
        payload.orientation,
        payload.detail_level,
        payload.description,
    )


@router.post(
    "/notebooks/{notebook_id}/slide_deck",
    response_model=TaskSubmissionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Artifacts - Creation"],
)
def create_slide_deck_endpoint(
    notebook_id: str,
    payload: SlideDeckCreateRequest,
    current_user: CurrentUser,
) -> TaskSubmissionResponse:
    return _submit(
        create_slide_deck_task,
        notebook_id,
        _headless(),
        _profile(),
        payload.format,
        payload.length,
        payload.language,
        payload.description,
    )


@router.post(
    "/notebooks/{notebook_id}/report",
    response_model=TaskSubmissionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Artifacts - Creation"],
)
def create_report_endpoint(
    notebook_id: str,
    payload: ReportCreateRequest,
    current_user: CurrentUser,
) -> TaskSubmissionResponse:
    return _submit(
        create_report_task,
        notebook_id,
        _headless(),
        _profile(),
        payload.format,
        payload.language,
        payload.description,
    )


@router.post(
    "/notebooks/{notebook_id}/mindmap",
    response_model=TaskSubmissionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Artifacts - Creation"],
)
def create_mindmap_endpoint(
    notebook_id: str, payload: MindmapCreateRequest, current_user: CurrentUser
) -> TaskSubmissionResponse:
    return _submit(create_mindmap_task, notebook_id, _headless(), _profile())


# ============================================================================
# Tasks
# ============================================================================


@router.get(
    "/tasks/{task_id}",
    response_model=TaskStatusResponse,
    status_code=status.HTTP_200_OK,
    tags=["Tasks"],
)
def task_status(task_id: str) -> TaskStatusResponse:
    return _task_status(task_id)
