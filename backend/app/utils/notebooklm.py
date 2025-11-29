from typing import Dict

from playwright.async_api import Page

from app.automation.tasks.notebooklm.create_notebook import (
    NotebookLMError,
    create_notebook,
    delete_notebook,
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
