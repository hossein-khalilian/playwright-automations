from typing import Any, Dict

from playwright.async_api import Page

from app.automation.tasks.notebooklm.create_notebook import (
    NotebookLMError,
    add_source_to_notebook,
    create_notebook,
    delete_notebook,
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
