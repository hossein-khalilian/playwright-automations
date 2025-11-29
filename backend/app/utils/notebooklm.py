from typing import Any, Dict

from playwright.async_api import Page

from app.automation.tasks.notebooklm.audio_overview import (
    create_audio_overview,
    delete_audio_overview,
    download_audio_overview,
    get_audio_overview_status,
    rename_audio_overview,
)
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
)


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
    page: Page, notebook_id: str
) -> Dict[str, str]:
    """
    Thin wrapper to invoke the NotebookLM audio overview creation task.
    Keeping this indirection makes it easier to swap implementations later.
    """
    try:
        return await create_audio_overview(page, notebook_id)
    except NotebookLMError:
        raise


async def trigger_audio_overview_status(page: Page, notebook_id: str) -> Dict[str, Any]:
    """
    Thin wrapper to invoke the NotebookLM audio overview status retrieval task.
    Keeping this indirection makes it easier to swap implementations later.
    """
    try:
        return await get_audio_overview_status(page, notebook_id)
    except NotebookLMError:
        raise


async def trigger_audio_overview_rename(
    page: Page, notebook_id: str, new_name: str
) -> Dict[str, str]:
    """
    Thin wrapper to invoke the NotebookLM audio overview rename task.
    Keeping this indirection makes it easier to swap implementations later.
    """
    try:
        return await rename_audio_overview(page, notebook_id, new_name)
    except NotebookLMError:
        raise


async def trigger_audio_overview_download(
    page: Page, notebook_id: str
) -> Dict[str, Any]:
    """
    Thin wrapper to invoke the NotebookLM audio overview download task.
    Keeping this indirection makes it easier to swap implementations later.
    """
    try:
        return await download_audio_overview(page, notebook_id)
    except NotebookLMError:
        raise


async def trigger_audio_overview_deletion(
    page: Page, notebook_id: str
) -> Dict[str, str]:
    """
    Thin wrapper to invoke the NotebookLM audio overview deletion task.
    Keeping this indirection makes it easier to swap implementations later.
    """
    try:
        return await delete_audio_overview(page, notebook_id)
    except NotebookLMError:
        raise
