from typing import Any, Dict, Optional

from playwright.async_api import Page

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
from app.automation.tasks.notebooklm.notebooks import create_notebook, delete_notebook
from app.automation.tasks.notebooklm.sources import (
    add_source_to_notebook,
    delete_source,
    list_sources,
    rename_source,
    review_source,
)
from app.automation.tasks.notebooklm.flashcards import create_flashcards
from app.automation.tasks.notebooklm.infographic import create_infographic
from app.automation.tasks.notebooklm.quiz import create_quiz
from app.automation.tasks.notebooklm.report import create_report
from app.automation.tasks.notebooklm.slide_deck import create_slide_deck
from app.automation.tasks.notebooklm.video_overview import create_video_overview


async def trigger_notebook_creation(page: Page) -> Dict[str, str]:
    """
    Thin wrapper to invoke the NotebookLM automation task.
    Keeping this indirection makes it easier to swap implementations later.
    """
    try:
        return await create_notebook(page)
    except NotebookLMError:
        raise


async def trigger_notebook_deletion(page: Page, notebook_id: str) -> Dict[str, str]:
    """
    Thin wrapper to invoke the NotebookLM deletion task.
    Keeping this indirection makes it easier to swap implementations later.
    """
    try:
        return await delete_notebook(page, notebook_id)
    except NotebookLMError:
        raise


async def trigger_source_upload(
    page: Page, notebook_id: str, file_path: str
) -> Dict[str, str]:
    """
    Thin wrapper to invoke the NotebookLM source upload task.
    Keeping this indirection makes it easier to swap implementations later.
    """
    try:
        return await add_source_to_notebook(page, notebook_id, file_path)
    except NotebookLMError:
        raise


async def trigger_source_listing(page: Page, notebook_id: str) -> Dict[str, Any]:
    """
    Thin wrapper to invoke the NotebookLM source listing task.
    Keeping this indirection makes it easier to swap implementations later.
    """
    try:
        return await list_sources(page, notebook_id)
    except NotebookLMError:
        raise


async def trigger_source_deletion(
    page: Page, notebook_id: str, source_name: str
) -> Dict[str, str]:
    """
    Thin wrapper to invoke the NotebookLM source deletion task.
    Keeping this indirection makes it easier to swap implementations later.
    """
    try:
        return await delete_source(page, notebook_id, source_name)
    except NotebookLMError:
        raise


async def trigger_source_rename(
    page: Page, notebook_id: str, source_name: str, new_name: str
) -> Dict[str, str]:
    """
    Thin wrapper to invoke the NotebookLM source rename task.
    Keeping this indirection makes it easier to swap implementations later.
    """
    try:
        return await rename_source(page, notebook_id, source_name, new_name)
    except NotebookLMError:
        raise


async def trigger_source_review(
    page: Page, notebook_id: str, source_name: str
) -> Dict[str, Any]:
    """
    Thin wrapper to invoke the NotebookLM source review task.
    Keeping this indirection makes it easier to swap implementations later.
    """
    try:
        return await review_source(page, notebook_id, source_name)
    except NotebookLMError:
        raise


async def trigger_notebook_query(
    page: Page, notebook_id: str, query: str
) -> Dict[str, str]:
    """
    Thin wrapper to invoke the NotebookLM query task.
    Keeping this indirection makes it easier to swap implementations later.
    """
    try:
        return await query_notebook(page, notebook_id, query)
    except NotebookLMError:
        raise


async def trigger_chat_history(page: Page, notebook_id: str) -> Dict[str, Any]:
    """
    Thin wrapper to invoke the NotebookLM chat history retrieval task.
    Keeping this indirection makes it easier to swap implementations later.
    """
    try:
        return await get_chat_history(page, notebook_id)
    except NotebookLMError:
        raise


async def trigger_chat_history_deletion(page: Page, notebook_id: str) -> Dict[str, str]:
    """
    Thin wrapper to invoke the NotebookLM chat history deletion task.
    Keeping this indirection makes it easier to swap implementations later.
    """
    try:
        return await delete_chat_history(page, notebook_id)
    except NotebookLMError:
        raise


async def trigger_audio_overview_creation(
    page: Page,
    notebook_id: str,
    audio_format: Optional[str] = None,
    language: Optional[str] = None,
    length: Optional[str] = None,
    focus_text: Optional[str] = None,
) -> Dict[str, str]:
    """
    Thin wrapper to invoke the NotebookLM audio overview creation task.
    Keeping this indirection makes it easier to swap implementations later.
    """
    try:
        return await create_audio_overview(
            page, notebook_id, audio_format, language, length, focus_text
        )
    except NotebookLMError:
        raise


async def trigger_video_overview_creation(
    page: Page,
    notebook_id: str,
    video_format: Optional[str] = None,
    language: Optional[str] = None,
    visual_style: Optional[str] = None,
    custom_style_description: Optional[str] = None,
    focus_text: Optional[str] = None,
) -> Dict[str, str]:
    """
    Thin wrapper to invoke the NotebookLM video overview creation task.
    Keeping this indirection makes it easier to swap implementations later.
    """
    try:
        return await create_video_overview(
            page,
            notebook_id,
            video_format,
            language,
            visual_style,
            custom_style_description,
            focus_text,
        )
    except NotebookLMError:
        raise


async def trigger_flashcard_creation(
    page: Page,
    notebook_id: str,
    card_count: Optional[str] = None,
    difficulty: Optional[str] = None,
    topic: Optional[str] = None,
) -> Dict[str, str]:
    """
    Thin wrapper to invoke the NotebookLM flashcard creation task.
    Keeping this indirection makes it easier to swap implementations later.
    """
    try:
        return await create_flashcards(page, notebook_id, card_count, difficulty, topic)
    except NotebookLMError:
        raise


async def trigger_quiz_creation(
    page: Page,
    notebook_id: str,
    question_count: Optional[str] = None,
    difficulty: Optional[str] = None,
    topic: Optional[str] = None,
) -> Dict[str, str]:
    """
    Thin wrapper to invoke the NotebookLM quiz creation task.
    Keeping this indirection makes it easier to swap implementations later.
    """
    try:
        return await create_quiz(page, notebook_id, question_count, difficulty, topic)
    except NotebookLMError:
        raise


async def trigger_infographic_creation(
    page: Page,
    notebook_id: str,
    language: Optional[str] = None,
    orientation: Optional[str] = None,
    detail_level: Optional[str] = None,
    description: Optional[str] = None,
) -> Dict[str, str]:
    """
    Thin wrapper to invoke the NotebookLM infographic creation task.
    Keeping this indirection makes it easier to swap implementations later.
    """
    try:
        return await create_infographic(
            page, notebook_id, language, orientation, detail_level, description
        )
    except NotebookLMError:
        raise


async def trigger_slide_deck_creation(
    page: Page,
    notebook_id: str,
    format: Optional[str] = None,
    length: Optional[str] = None,
    language: Optional[str] = None,
    description: Optional[str] = None,
) -> Dict[str, str]:
    """
    Thin wrapper to invoke the NotebookLM slide deck creation task.
    Keeping this indirection makes it easier to swap implementations later.
    """
    try:
        return await create_slide_deck(
            page, notebook_id, format, length, language, description
        )
    except NotebookLMError:
        raise


async def trigger_report_creation(
    page: Page,
    notebook_id: str,
    format: Optional[str] = None,
    language: Optional[str] = None,
    description: Optional[str] = None,
) -> Dict[str, str]:
    """
    Thin wrapper to invoke the NotebookLM report creation task.
    Keeping this indirection makes it easier to swap implementations later.
    """
    try:
        return await create_report(page, notebook_id, format, language, description)
    except NotebookLMError:
        raise


async def trigger_artifact_listing(page: Page, notebook_id: str) -> Dict[str, Any]:
    """
    Thin wrapper to invoke the NotebookLM artifact listing task.
    Keeping this indirection makes it easier to swap implementations later.
    """
    try:
        return await list_artifacts(page, notebook_id)
    except NotebookLMError:
        raise


async def trigger_artifact_deletion(
    page: Page, notebook_id: str, artifact_name: str
) -> Dict[str, str]:
    """
    Thin wrapper to invoke the NotebookLM artifact deletion task.
    Keeping this indirection makes it easier to swap implementations later.
    """
    try:
        return await delete_artifact(page, notebook_id, artifact_name)
    except NotebookLMError:
        raise


async def trigger_artifact_download(
    page: Page, notebook_id: str, artifact_name: str
) -> Dict[str, Any]:
    """
    Thin wrapper to invoke the NotebookLM artifact download task.
    Keeping this indirection makes it easier to swap implementations later.
    """
    try:
        return await download_artifact(page, notebook_id, artifact_name)
    except NotebookLMError:
        raise


async def trigger_artifact_rename(
    page: Page, notebook_id: str, artifact_name: str, new_name: str
) -> Dict[str, str]:
    """
    Thin wrapper to invoke the NotebookLM artifact rename task.
    Keeping this indirection makes it easier to swap implementations later.
    """
    try:
        return await rename_artifact(page, notebook_id, artifact_name, new_name)
    except NotebookLMError:
        raise
