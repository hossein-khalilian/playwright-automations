import os
import tempfile
from pathlib import Path

from celery.result import AsyncResult
from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.auth import CurrentUser
from app.celery_app import celery_app
from app.celery_tasks.notebooklm import (
    add_source_task,
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
    """
    notebooks_data = await get_notebooks_by_user(current_user.username)
    notebooks = [
        Notebook(
            notebook_id=doc["notebook_id"],
            notebook_url=doc["notebook_url"],
            created_at=doc["created_at"],
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
    return _submit(create_notebook_task, _headless(), _profile())


@router.delete(
    "/notebooks/{notebook_id}",
    response_model=TaskSubmissionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Notebooks"],
)
def delete_notebook_endpoint(
    notebook_id: str, current_user: CurrentUser
) -> TaskSubmissionResponse:
    return _submit(delete_notebook_task, notebook_id, _headless(), _profile())


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
    return _submit(add_source_task, notebook_id, tmp_path, _headless(), _profile())


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
    response_model=TaskSubmissionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Artifacts - Management"],
)
def download_artifact_endpoint(
    notebook_id: str, artifact_name: str, current_user: CurrentUser
) -> TaskSubmissionResponse:
    return _submit(
        download_artifact_task, notebook_id, artifact_name, _headless(), _profile()
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
