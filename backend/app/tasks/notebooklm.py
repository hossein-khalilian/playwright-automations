"""
Celery tasks for NotebookLM operations using sync Playwright.
"""

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict

from app.automation.tasks.google_login import check_or_login_google_sync
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
from app.utils.browser_pool import (
    acquire_browser,
    ensure_pool_initialized,
    release_browser,
)

pool_size = int(os.getenv("BROWSER_POOL_SIZE", "1"))


def _run_with_browser(
    headless: bool, user_profile_name: str, fn, *args, **kwargs
) -> Dict[str, Any]:
    ensure_pool_initialized(
        pool_size=pool_size, headless=headless, base_profile=user_profile_name
    )
    resource = acquire_browser(headless=headless, base_profile=user_profile_name)
    try:
        check_or_login_google_sync(resource.page)
        return fn(resource.page, *args, **kwargs)
    finally:
        release_browser(resource)


def _threaded(fn, *args, **kwargs) -> Dict[str, Any]:
    def _call():
        # Ensure Playwright sync API sees no running asyncio loop in this thread
        asyncio.set_event_loop(asyncio.new_event_loop())
        return fn(*args, **kwargs)

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_call)
        return future.result()


# -------- Notebooks --------


@celery_app.task(name="notebooklm.create_notebook")
def create_notebook_task(headless: bool, user_profile_name: str) -> Dict[str, Any]:
    return _threaded(_run_with_browser, headless, user_profile_name, create_notebook)


@celery_app.task(name="notebooklm.delete_notebook")
def delete_notebook_task(
    notebook_id: str, headless: bool, user_profile_name: str
) -> Dict[str, Any]:
    return _threaded(
        _run_with_browser, headless, user_profile_name, delete_notebook, notebook_id
    )


# -------- Sources --------


@celery_app.task(name="notebooklm.list_sources")
def list_sources_task(
    notebook_id: str, headless: bool, user_profile_name: str
) -> Dict[str, Any]:
    return _threaded(
        _run_with_browser, headless, user_profile_name, list_sources, notebook_id
    )


@celery_app.task(name="notebooklm.add_source")
def add_source_task(
    notebook_id: str, file_path: str, headless: bool, user_profile_name: str
) -> Dict[str, Any]:
    return _threaded(
        _run_with_browser,
        headless,
        user_profile_name,
        add_source_to_notebook,
        notebook_id,
        file_path,
    )


@celery_app.task(name="notebooklm.delete_source")
def delete_source_task(
    notebook_id: str, source_name: str, headless: bool, user_profile_name: str
) -> Dict[str, Any]:
    return _threaded(
        _run_with_browser,
        headless,
        user_profile_name,
        delete_source,
        notebook_id,
        source_name,
    )


@celery_app.task(name="notebooklm.rename_source")
def rename_source_task(
    notebook_id: str,
    source_name: str,
    new_name: str,
    headless: bool,
    user_profile_name: str,
) -> Dict[str, Any]:
    return _threaded(
        _run_with_browser,
        headless,
        user_profile_name,
        rename_source,
        notebook_id,
        source_name,
        new_name,
    )


@celery_app.task(name="notebooklm.review_source")
def review_source_task(
    notebook_id: str, source_name: str, headless: bool, user_profile_name: str
) -> Dict[str, Any]:
    return _threaded(
        _run_with_browser,
        headless,
        user_profile_name,
        review_source,
        notebook_id,
        source_name,
    )


# -------- Chat / Query --------


@celery_app.task(name="notebooklm.query")
def query_notebook_task(
    notebook_id: str, query: str, headless: bool, user_profile_name: str
) -> Dict[str, Any]:
    return _threaded(
        _run_with_browser,
        headless,
        user_profile_name,
        query_notebook,
        notebook_id,
        query,
    )


@celery_app.task(name="notebooklm.get_chat_history")
def get_chat_history_task(
    notebook_id: str, headless: bool, user_profile_name: str
) -> Dict[str, Any]:
    return _threaded(
        _run_with_browser, headless, user_profile_name, get_chat_history, notebook_id
    )


@celery_app.task(name="notebooklm.delete_chat_history")
def delete_chat_history_task(
    notebook_id: str, headless: bool, user_profile_name: str
) -> Dict[str, Any]:
    return _threaded(
        _run_with_browser, headless, user_profile_name, delete_chat_history, notebook_id
    )


# -------- Artifacts --------


@celery_app.task(name="notebooklm.list_artifacts")
def list_artifacts_task(
    notebook_id: str, headless: bool, user_profile_name: str
) -> Dict[str, Any]:
    return _threaded(
        _run_with_browser, headless, user_profile_name, list_artifacts, notebook_id
    )


@celery_app.task(name="notebooklm.delete_artifact")
def delete_artifact_task(
    notebook_id: str, artifact_name: str, headless: bool, user_profile_name: str
) -> Dict[str, Any]:
    return _threaded(
        _run_with_browser,
        headless,
        user_profile_name,
        delete_artifact,
        notebook_id,
        artifact_name,
    )


@celery_app.task(name="notebooklm.rename_artifact")
def rename_artifact_task(
    notebook_id: str,
    artifact_name: str,
    new_name: str,
    headless: bool,
    user_profile_name: str,
) -> Dict[str, Any]:
    return _threaded(
        _run_with_browser,
        headless,
        user_profile_name,
        rename_artifact,
        notebook_id,
        artifact_name,
        new_name,
    )


@celery_app.task(name="notebooklm.download_artifact")
def download_artifact_task(
    notebook_id: str, artifact_name: str, headless: bool, user_profile_name: str
) -> Dict[str, Any]:
    return _threaded(
        _run_with_browser,
        headless,
        user_profile_name,
        download_artifact,
        notebook_id,
        artifact_name,
    )


# -------- Generative assets --------


@celery_app.task(name="notebooklm.create_audio_overview")
def create_audio_overview_task(
    notebook_id: str,
    headless: bool,
    user_profile_name: str,
    audio_format: str | None = None,
    language: str | None = None,
    length: str | None = None,
    focus_text: str | None = None,
) -> Dict[str, Any]:
    return _threaded(
        _run_with_browser,
        headless,
        user_profile_name,
        create_audio_overview,
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
    user_profile_name: str,
    video_format: str | None = None,
    language: str | None = None,
    visual_style: str | None = None,
    custom_style_description: str | None = None,
    focus_text: str | None = None,
) -> Dict[str, Any]:
    return _threaded(
        _run_with_browser,
        headless,
        user_profile_name,
        create_video_overview,
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
    user_profile_name: str,
    card_count: str | None = None,
    difficulty: str | None = None,
    topic: str | None = None,
) -> Dict[str, Any]:
    return _threaded(
        _run_with_browser,
        headless,
        user_profile_name,
        create_flashcards,
        notebook_id,
        card_count,
        difficulty,
        topic,
    )


@celery_app.task(name="notebooklm.create_quiz")
def create_quiz_task(
    notebook_id: str,
    headless: bool,
    user_profile_name: str,
    question_count: str | None = None,
    difficulty: str | None = None,
    topic: str | None = None,
) -> Dict[str, Any]:
    return _threaded(
        _run_with_browser,
        headless,
        user_profile_name,
        create_quiz,
        notebook_id,
        question_count,
        difficulty,
        topic,
    )


@celery_app.task(name="notebooklm.create_infographic")
def create_infographic_task(
    notebook_id: str,
    headless: bool,
    user_profile_name: str,
    language: str | None = None,
    orientation: str | None = None,
    detail_level: str | None = None,
    description: str | None = None,
) -> Dict[str, Any]:
    return _threaded(
        _run_with_browser,
        headless,
        user_profile_name,
        create_infographic,
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
    user_profile_name: str,
    format: str | None = None,
    length: str | None = None,
    language: str | None = None,
    description: str | None = None,
) -> Dict[str, Any]:
    return _threaded(
        _run_with_browser,
        headless,
        user_profile_name,
        create_slide_deck,
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
    user_profile_name: str,
    format: str | None = None,
    language: str | None = None,
    description: str | None = None,
) -> Dict[str, Any]:
    return _threaded(
        _run_with_browser,
        headless,
        user_profile_name,
        create_report,
        notebook_id,
        format,
        language,
        description,
    )


@celery_app.task(name="notebooklm.create_mindmap")
def create_mindmap_task(
    notebook_id: str, headless: bool, user_profile_name: str
) -> Dict[str, Any]:
    return _threaded(
        _run_with_browser, headless, user_profile_name, create_mindmap, notebook_id
    )
