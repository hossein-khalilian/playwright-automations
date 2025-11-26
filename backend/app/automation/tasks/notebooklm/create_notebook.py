from typing import Dict

from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError


class NotebookLMError(Exception):
    """Custom exception for NotebookLM automation errors."""

    pass


async def create_notebook(page: Page) -> Dict[str, str]:
    """
    Navigates to NotebookLM and triggers creation of a new notebook
    by clicking on the "Create new notebook" button.

    Args:
        page: The Playwright Page object to use for automation

    Returns:
        Dictionary with status, message, and page URL

    Raises:
        NotebookLMError: If the notebook creation fails
    """
    try:
        # Navigate to NotebookLM
        await page.goto(
            "https://notebooklm.google.com/?pli=1",
            wait_until="domcontentloaded",
            timeout=30_000,
        )

        # Wait a bit for the page to fully load
        await page.wait_for_timeout(1000)

        # Find and click the mat-card element with text "addCreate new notebook"
        try:
            create_button = page.locator("mat-card").filter(
                has_text="addCreate new notebook"
            )
            await create_button.wait_for(timeout=15_000)
            await create_button.click()
        except PlaywrightTimeoutError as exc:
            raise NotebookLMError(
                "Could not find the 'Create new notebook' button. "
                "The page may not have loaded correctly or the element structure has changed."
            ) from exc

        # Wait for the page to load after clicking
        try:
            await page.wait_for_load_state("networkidle", timeout=30_000)
        except PlaywrightTimeoutError:
            # NotebookLM keeps long-lived connections; networkidle may never fire.
            # Fall back to confirming the page finished loading at least once.
            await page.wait_for_load_state("load", timeout=15_000)

        return {
            "status": "success",
            "message": "NotebookLM notebook creation triggered successfully.",
            "page_url": page.url,
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to create NotebookLM notebook: {exc}") from exc
