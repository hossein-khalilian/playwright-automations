"""Helper utilities for NotebookLM automation."""

import re
from typing import Optional

from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.automation.tasks.notebooklm.exceptions import NotebookLMError


async def navigate_to_notebook(page: Page, notebook_id: str) -> None:
    """
    Navigate to a specific notebook page.

    Args:
        page: The Playwright Page object
        notebook_id: The ID of the notebook to navigate to

    Raises:
        NotebookLMError: If navigation fails
    """
    try:
        await page.goto(
            f"https://notebooklm.google.com/notebook/{notebook_id}",
            wait_until="domcontentloaded",
            timeout=30_000,
        )
        await page.wait_for_timeout(1_000)
    except Exception as exc:
        raise NotebookLMError(
            f"Failed to navigate to notebook {notebook_id}: {exc}"
        ) from exc


async def navigate_to_main_page(page: Page) -> None:
    """
    Navigate to the main NotebookLM page.

    Args:
        page: The Playwright Page object

    Raises:
        NotebookLMError: If navigation fails
    """
    try:
        await page.goto(
            "https://notebooklm.google.com/",
            wait_until="domcontentloaded",
            timeout=30_000,
        )
        await page.wait_for_timeout(1_000)
    except Exception as exc:
        raise NotebookLMError("Failed to navigate to NotebookLM main page") from exc


async def close_dialogs(page: Page) -> None:
    """
    Close any dialogs that might appear on the page.

    Args:
        page: The Playwright Page object
    """
    try:
        close_button = page.get_by_role("button", name="Close dialog")
        await close_button.wait_for(timeout=5_000)
        await close_button.click()
    except PlaywrightTimeoutError:
        # Dialog might not appear, which is fine
        pass


async def extract_notebook_id_from_url(page: Page) -> Optional[str]:
    """
    Extract notebook ID from the current page URL.

    Args:
        page: The Playwright Page object

    Returns:
        The notebook ID if found, None otherwise
    """
    current_url = page.url
    match = re.search(r"/notebook/([^/?]+)", current_url)
    if match:
        return match.group(1)
    return None
