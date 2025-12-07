"""
Celery tasks for NotebookLM operations using sync Playwright.
"""

from typing import Any, Callable, Dict, Optional

from app.automation.tasks.google_login import check_or_login_google_sync
from app.automation.tasks.notebooklm.exceptions import NotebookLMError
from app.automation.tasks.notebooklm.sync_flows import (
    add_source_to_notebook,
    create_audio_overview,
    create_flashcards,
    create_infographic,
    create_mindmap,
    create_notebook,
    create_quiz,
    create_report,
    create_slide_deck,
    create_video_overview,
    delete_artifact,
    delete_chat_history,
    delete_notebook,
    delete_source,
    download_artifact,
    get_chat_history,
    list_artifacts,
    list_sources,
    query_notebook,
    rename_artifact,
    rename_source,
    review_source,
)
from app.celery_app import celery_app
from app.utils.browser_utils import initialize_page_sync


def _run_with_browser(
    flow_func: Callable, headless: bool, profile: str, *flow_args, **flow_kwargs
) -> Dict[str, Any]:
    """
    Helper function to initialize browser, ensure login, run flow, and clean up.
    
    Args:
        flow_func: The sync flow function to execute (takes page as first arg)
        headless: Whether to run browser in headless mode
        profile: User profile name for browser
        *flow_args: Positional arguments to pass to flow_func after page
        **flow_kwargs: Keyword arguments to pass to flow_func
    
    Returns:
        Dictionary with status and message from the flow function
    """
    page = None
    context = None
    playwright = None

    try:
        # Initialize browser
        page, context, playwright = initialize_page_sync(
            headless=headless, user_profile_name=profile
        )

        # Ensure Google login
        check_or_login_google_sync(page)

        # Run the flow function with the page and other args
        result = flow_func(page, *flow_args, **flow_kwargs)
        return result

    except NotebookLMError as exc:
        return {
            "status": "error",
            "message": str(exc),
        }
    except Exception as exc:
        return {
            "status": "error",
            "message": f"Unexpected error: {exc}",
        }
    finally:
        # Clean up browser resources
        if context:
            try:
                context.close()
            except Exception:
                pass
        if playwright:
            try:
                playwright.stop()
            except Exception:
                pass


# ============================================================================
# Notebook tasks
# ============================================================================


@celery_app.task(name="notebooklm.create_notebook")
def create_notebook_task(headless: bool, profile: str) -> Dict[str, Any]:
    """Create a new NotebookLM notebook."""
    return _run_with_browser(create_notebook, headless, profile)


@celery_app.task(name="notebooklm.delete_notebook")
def delete_notebook_task(
    notebook_id: str, headless: bool, profile: str
) -> Dict[str, Any]:
    """Delete a NotebookLM notebook."""
    return _run_with_browser(delete_notebook, headless, profile, notebook_id)


# ============================================================================
# Source tasks
# ============================================================================


@celery_app.task(name="notebooklm.add_source")
def add_source_task(
    notebook_id: str, file_path: str, headless: bool, profile: str
) -> Dict[str, Any]:
    """Add a source file to a notebook."""
    return _run_with_browser(
        add_source_to_notebook, headless, profile, notebook_id, file_path
    )


@celery_app.task(name="notebooklm.list_sources")
def list_sources_task(notebook_id: str, headless: bool, profile: str) -> Dict[str, Any]:
    """List all sources in a notebook."""
    return _run_with_browser(list_sources, headless, profile, notebook_id)


@celery_app.task(name="notebooklm.delete_source")
def delete_source_task(
    notebook_id: str, source_name: str, headless: bool, profile: str
) -> Dict[str, Any]:
    """Delete a source from a notebook."""
    return _run_with_browser(delete_source, headless, profile, notebook_id, source_name)


@celery_app.task(name="notebooklm.rename_source")
def rename_source_task(
    notebook_id: str,
    source_name: str,
    new_name: str,
    headless: bool,
    profile: str,
) -> Dict[str, Any]:
    """Rename a source in a notebook."""
    return _run_with_browser(
        rename_source, headless, profile, notebook_id, source_name, new_name
    )


@celery_app.task(name="notebooklm.review_source")
def review_source_task(
    notebook_id: str, source_name: str, headless: bool, profile: str
) -> Dict[str, Any]:
    """Open and review a source in a notebook."""
    return _run_with_browser(review_source, headless, profile, notebook_id, source_name)


# ============================================================================
# Chat/Query tasks
# ============================================================================


@celery_app.task(name="notebooklm.query_notebook")
def query_notebook_task(
    notebook_id: str, query: str, headless: bool, profile: str
) -> Dict[str, Any]:
    """Send a query to a notebook."""
    return _run_with_browser(query_notebook, headless, profile, notebook_id, query)


@celery_app.task(name="notebooklm.get_chat_history")
def get_chat_history_task(notebook_id: str, headless: bool, profile: str) -> Dict[str, Any]:
    """Get chat history for a notebook."""
    return _run_with_browser(get_chat_history, headless, profile, notebook_id)


@celery_app.task(name="notebooklm.delete_chat_history")
def delete_chat_history_task(notebook_id: str, headless: bool, profile: str) -> Dict[str, Any]:
    """Delete chat history for a notebook."""
    return _run_with_browser(delete_chat_history, headless, profile, notebook_id)


# ============================================================================
# Artifact management tasks
# ============================================================================


@celery_app.task(name="notebooklm.list_artifacts")
def list_artifacts_task(notebook_id: str, headless: bool, profile: str) -> Dict[str, Any]:
    """List all artifacts in a notebook."""
    return _run_with_browser(list_artifacts, headless, profile, notebook_id)


@celery_app.task(name="notebooklm.delete_artifact")
def delete_artifact_task(
    notebook_id: str, artifact_name: str, headless: bool, profile: str
) -> Dict[str, Any]:
    """Delete an artifact from a notebook."""
    return _run_with_browser(
        delete_artifact, headless, profile, notebook_id, artifact_name
    )


@celery_app.task(name="notebooklm.rename_artifact")
def rename_artifact_task(
    notebook_id: str,
    artifact_name: str,
    new_name: str,
    headless: bool,
    profile: str,
) -> Dict[str, Any]:
    """Rename an artifact in a notebook."""
    return _run_with_browser(
        rename_artifact, headless, profile, notebook_id, artifact_name, new_name
    )


@celery_app.task(name="notebooklm.download_artifact")
def download_artifact_task(
    notebook_id: str, artifact_name: str, headless: bool, profile: str
) -> Dict[str, Any]:
    """Download an artifact from a notebook."""
    return _run_with_browser(
        download_artifact, headless, profile, notebook_id, artifact_name
    )


# ============================================================================
# Artifact creation tasks
# ============================================================================


@celery_app.task(name="notebooklm.create_audio_overview")
def create_audio_overview_task(
    notebook_id: str,
    headless: bool,
    profile: str,
    audio_format: Optional[str] = None,
    language: Optional[str] = None,
    length: Optional[str] = None,
    focus_text: Optional[str] = None,
) -> Dict[str, Any]:
    """Create an audio overview artifact."""
    return _run_with_browser(
        create_audio_overview,
        headless,
        profile,
        notebook_id,
        audio_format,
        language,
        length,
        focus_text,
    )


@celery_app.task(name="notebooklm.create_video_overview")
def create_video_overview_task(
    notebook_id: str,
    headless: bool,
    profile: str,
    video_format: Optional[str] = None,
    language: Optional[str] = None,
    visual_style: Optional[str] = None,
    custom_style_description: Optional[str] = None,
    focus_text: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a video overview artifact."""
    return _run_with_browser(
        create_video_overview,
        headless,
        profile,
        notebook_id,
        video_format,
        language,
        visual_style,
        custom_style_description,
        focus_text,
    )


@celery_app.task(name="notebooklm.create_flashcards")
def create_flashcards_task(
    notebook_id: str,
    headless: bool,
    profile: str,
    card_count: Optional[str] = None,
    difficulty: Optional[str] = None,
    topic: Optional[str] = None,
) -> Dict[str, Any]:
    """Create flashcards artifact."""
    return _run_with_browser(
        create_flashcards,
        headless,
        profile,
        notebook_id,
        card_count,
        difficulty,
        topic,
    )


@celery_app.task(name="notebooklm.create_quiz")
def create_quiz_task(
    notebook_id: str,
    headless: bool,
    profile: str,
    question_count: Optional[str] = None,
    difficulty: Optional[str] = None,
    topic: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a quiz artifact."""
    return _run_with_browser(
        create_quiz,
        headless,
        profile,
        notebook_id,
        question_count,
        difficulty,
        topic,
    )


@celery_app.task(name="notebooklm.create_infographic")
def create_infographic_task(
    notebook_id: str,
    headless: bool,
    profile: str,
    language: Optional[str] = None,
    orientation: Optional[str] = None,
    detail_level: Optional[str] = None,
    description: Optional[str] = None,
) -> Dict[str, Any]:
    """Create an infographic artifact."""
    return _run_with_browser(
        create_infographic,
        headless,
        profile,
        notebook_id,
        language,
        orientation,
        detail_level,
        description,
    )


@celery_app.task(name="notebooklm.create_slide_deck")
def create_slide_deck_task(
    notebook_id: str,
    headless: bool,
    profile: str,
    format: Optional[str] = None,
    length: Optional[str] = None,
    language: Optional[str] = None,
    description: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a slide deck artifact."""
    return _run_with_browser(
        create_slide_deck,
        headless,
        profile,
        notebook_id,
        format,
        length,
        language,
        description,
    )


@celery_app.task(name="notebooklm.create_report")
def create_report_task(
    notebook_id: str,
    headless: bool,
    profile: str,
    format: Optional[str] = None,
    language: Optional[str] = None,
    description: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a report artifact."""
    return _run_with_browser(
        create_report,
        headless,
        profile,
        notebook_id,
        format,
        language,
        description,
    )


@celery_app.task(name="notebooklm.create_mindmap")
def create_mindmap_task(notebook_id: str, headless: bool, profile: str) -> Dict[str, Any]:
    """Create a mind map artifact."""
    return _run_with_browser(create_mindmap, headless, profile, notebook_id)
