"""
Celery tasks for NotebookLM operations using sync Playwright.
"""

import logging
from typing import Any, Callable, Dict, Optional

from app.automation.tasks.google_login import check_or_login_google_sync
from app.automation.tasks.notebooklm.artifacts import (
    delete_artifact,
    download_artifact,
    list_artifacts,
    rename_artifact,
)
from app.automation.tasks.notebooklm.audio_overview import create_audio_overview
from app.automation.tasks.notebooklm.chat import (
    delete_chat_history,
    get_chat_history,
    query_notebook,
)
from app.automation.tasks.notebooklm.exceptions import NotebookLMError
from app.automation.tasks.notebooklm.flashcards import create_flashcards
from app.automation.tasks.notebooklm.infographic import create_infographic
from app.automation.tasks.notebooklm.mindmap import create_mindmap
from app.automation.tasks.notebooklm.notebooks import create_notebook, delete_notebook
from app.automation.tasks.notebooklm.quiz import create_quiz
from app.automation.tasks.notebooklm.report import create_report
from app.automation.tasks.notebooklm.slide_deck import create_slide_deck
from app.automation.tasks.notebooklm.sources import (
    add_source_to_notebook,
    delete_source,
    list_sources,
    rename_source,
    review_source,
)
from app.automation.tasks.notebooklm.video_overview import create_video_overview
from app.celery_app import celery_app
from app.utils.browser_state import get_page_from_pool, return_page_to_pool
from app.utils.browser_utils import initialize_page_sync
from app.utils.config import config
from app.utils.db import delete_notebook_sync, save_notebook_sync

logger = logging.getLogger(__name__)


def _run_with_browser(
    flow_func: Callable, headless: bool, profile: str, *flow_args, **flow_kwargs
) -> Dict[str, Any]:
    """
    Helper function to get page from pool, run flow, and return page to pool.
    Falls back to creating a new browser if pool is not available.

    Args:
        flow_func: The sync flow function to execute (takes page as first arg)
        headless: Whether to run browser in headless mode (used for fallback)
        profile: User profile name for browser
        *flow_args: Positional arguments to pass to flow_func after page
        **flow_kwargs: Keyword arguments to pass to flow_func

    Returns:
        Dictionary with status and message from the flow function
    """
    page = None
    context = None
    playwright = None
    page_from_pool = False

    try:
        # Try to get a page from the pool first
        page = get_page_from_pool()

        if page is not None:
            logger.debug(f"Using page from pool for task")
            page_from_pool = True
        else:
            # Fallback: create a new browser if pool is not available
            logger.warning(
                "No page available in pool, creating new browser instance. "
                "Consider initializing browser pool in Celery worker."
            )
            page, context, playwright = initialize_page_sync(
                headless=headless, user_profile_name=profile
            )
            # Ensure Google login for new browser
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
        logger.error(f"Error in flow function: {exc}", exc_info=True)
        return {
            "status": "error",
            "message": f"Unexpected error: {exc}",
        }
    finally:
        # Return page to pool if it came from pool, otherwise clean up
        if page_from_pool and page is not None:
            try:
                return_page_to_pool(page)
                logger.debug("Returned page to pool")
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


# ============================================================================
# Notebook tasks
# ============================================================================


@celery_app.task(name="notebooklm.create_notebook")
def create_notebook_task(username: str, headless: bool, profile: str) -> Dict[str, Any]:
    """Create a new NotebookLM notebook."""
    email = config.get("gmail_email")
    result = _run_with_browser(create_notebook, headless, profile, email=email)
    
    # Save notebook to MongoDB if creation was successful
    if result.get("status") == "success":
        notebook_id = result.get("notebook_id")
        notebook_url = result.get("page_url")
        if notebook_id and notebook_url:
            try:
                saved = save_notebook_sync(username, notebook_id, notebook_url, email)
                if saved:
                    logger.info(f"Notebook {notebook_id} saved to MongoDB for user {username}")
                else:
                    logger.warning(f"Failed to save notebook {notebook_id} to MongoDB for user {username}")
            except Exception as exc:
                logger.error(f"Error saving notebook {notebook_id} to MongoDB: {exc}", exc_info=True)
    
    return result


@celery_app.task(name="notebooklm.delete_notebook")
def delete_notebook_task(
    username: str, notebook_id: str, headless: bool, profile: str
) -> Dict[str, Any]:
    """Delete a NotebookLM notebook and remove its DB record."""
    result = _run_with_browser(delete_notebook, headless, profile, notebook_id)

    if result.get("status") == "success":
        try:
            deleted = delete_notebook_sync(username, notebook_id)
            if deleted:
                logger.info(f"Notebook {notebook_id} removed from MongoDB for user {username}")
            else:
                logger.warning(
                    f"Notebook {notebook_id} deletion succeeded in UI but failed to remove from MongoDB for user {username}"
                )
        except Exception as exc:
            logger.error(
                f"Error deleting notebook {notebook_id} from MongoDB for user {username}: {exc}",
                exc_info=True,
            )

    return result


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
def get_chat_history_task(
    notebook_id: str, headless: bool, profile: str
) -> Dict[str, Any]:
    """Get chat history for a notebook."""
    return _run_with_browser(get_chat_history, headless, profile, notebook_id)


@celery_app.task(name="notebooklm.delete_chat_history")
def delete_chat_history_task(
    notebook_id: str, headless: bool, profile: str
) -> Dict[str, Any]:
    """Delete chat history for a notebook."""
    return _run_with_browser(delete_chat_history, headless, profile, notebook_id)


# ============================================================================
# Artifact management tasks
# ============================================================================


@celery_app.task(name="notebooklm.list_artifacts")
def list_artifacts_task(
    notebook_id: str, headless: bool, profile: str
) -> Dict[str, Any]:
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
def create_mindmap_task(
    notebook_id: str, headless: bool, profile: str
) -> Dict[str, Any]:
    """Create a mind map artifact."""
    return _run_with_browser(create_mindmap, headless, profile, notebook_id)
