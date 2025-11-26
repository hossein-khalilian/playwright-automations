from typing import Dict

from playwright.async_api import Page

from app.automation.tasks.notebooklm.create_notebook import (
    NotebookLMError,
    create_notebook,
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
