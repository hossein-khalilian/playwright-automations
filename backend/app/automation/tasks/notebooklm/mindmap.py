"""Mind Map operations for NotebookLM automation."""

from typing import Dict, Optional

from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.automation.tasks.notebooklm.exceptions import NotebookLMError
from app.automation.tasks.notebooklm.helpers import close_dialogs, navigate_to_notebook


async def create_mindmap(
    page: Page,
    notebook_id: str,
) -> Dict[str, str]:
    """
    Creates a mind map for a notebook in NotebookLM.

    Args:
        page: The Playwright Page object to use for automation
        notebook_id: The ID of the notebook to create mind map for

    Returns:
        Dictionary with status and message

    Raises:
        NotebookLMError: If creating mind map fails
    """
    try:
        # Navigate directly to the notebook page
        await navigate_to_notebook(page, notebook_id)

        # Close any dialogs that might appear
        await close_dialogs(page)

        # Wait for the Mind Map button to be visible and click it
        try:
            mindmap_button = page.get_by_label("Mind Map")
            await mindmap_button.wait_for(timeout=30_000, state="visible")
            await mindmap_button.click()
        except PlaywrightTimeoutError as exc:
            raise NotebookLMError(
                "Could not find the 'Mind Map' button. "
                "The notebook page may not have loaded correctly."
            ) from exc

        # Wait for the generating message to appear
        try:
            generating_message = page.locator("artifact-library div").filter(
                has_text="sync Generating Mind Map..."
            )
            await generating_message.wait_for(timeout=10_000, state="visible")
        except PlaywrightTimeoutError as exc:
            raise NotebookLMError(
                "Could not confirm mind map generation started. "
                "The 'Generating Mind Map...' message did not appear."
            ) from exc

        return {
            "status": "success",
            "message": f"Mind map creation started for notebook {notebook_id}. "
            "The mind map is being generated and will be available in a few minutes.",
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(
            f"Failed to create mind map for NotebookLM notebook: {exc}"
        ) from exc

