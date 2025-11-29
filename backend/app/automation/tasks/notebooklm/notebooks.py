"""Notebook operations for NotebookLM automation."""

from typing import Dict, Optional

from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.automation.tasks.notebooklm.exceptions import NotebookLMError
from app.automation.tasks.notebooklm.helpers import (
    close_dialogs,
    extract_notebook_id_from_url,
    navigate_to_main_page,
)


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
        await navigate_to_main_page(page)

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

        # Close the dialog if it appears
        await close_dialogs(page)

        # Wait for navigation to notebook page
        # The page should navigate to a URL like: https://notebooklm.google.com/notebook/{notebook_id}
        try:
            await page.wait_for_url(
                "**/notebook/**",
                timeout=10_000,
            )
        except PlaywrightTimeoutError:
            # If navigation didn't happen, check if we're still on the main page
            pass

        # Wait briefly for any navigation or UI updates
        await page.wait_for_timeout(1_000)

        # Verify success: check if URL changed (notebook page) or dialog closed
        current_url = page.url
        is_notebook_page = "/notebook/" in current_url

        # Extract notebook ID from URL if we're on a notebook page
        notebook_id: Optional[str] = None
        if is_notebook_page:
            notebook_id = await extract_notebook_id_from_url(page)

        # Check if dialog is still open (indicating potential failure)
        dialog_still_open = await page.get_by_role("button", name="Close dialog").count() > 0

        if not is_notebook_page and dialog_still_open:
            raise NotebookLMError(
                "Notebook creation verification failed. "
                "The dialog is still open, indicating the notebook may not have been created."
            )

        if not is_notebook_page:
            raise NotebookLMError(
                "Notebook creation verification failed. "
                "The page did not navigate to a notebook URL."
            )

        return {
            "status": "success",
            "message": "NotebookLM notebook creation triggered and verified successfully.",
            "page_url": current_url,
            "notebook_id": notebook_id,
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to create NotebookLM notebook: {exc}") from exc


async def delete_notebook(page: Page, notebook_id: str) -> Dict[str, str]:
    """
    Deletes a notebook in NotebookLM by its ID.

    Args:
        page: The Playwright Page object to use for automation
        notebook_id: The ID of the notebook to delete

    Returns:
        Dictionary with status and message

    Raises:
        NotebookLMError: If the notebook deletion fails
    """
    try:
        # Navigate to the main NotebookLM page
        await navigate_to_main_page(page)

        # Close any dialogs that might appear
        await close_dialogs(page)

        # Find and click the "Project Actions Menu" button for the specific notebook
        # The button is inside the project-button component for that specific notebook
        try:
            # Find the mat-card that contains this notebook by its aria-labelledby attribute
            # The mat-card has aria-labelledby="project-{notebook_id}-title project-{notebook_id}-emoji"
            mat_card = page.locator(f'mat-card[aria-labelledby*="project-{notebook_id}-title"]')
            
            # Check if the project exists on the page
            await mat_card.wait_for(timeout=10_000)
            
            # Find the "Project Actions Menu" button within this specific mat-card
            actions_menu = mat_card.get_by_role("button", name="Project Actions Menu")
            await actions_menu.wait_for(timeout=5_000)
            await actions_menu.click()
        except PlaywrightTimeoutError as exc:
            raise NotebookLMError(
                f"Could not find the 'Project Actions Menu' button for notebook {notebook_id}. "
                "The notebook may not exist or the page structure has changed."
            ) from exc

        # Wait for the menu to appear
        await page.wait_for_timeout(500)

        # Click on the "Delete" menuitem
        try:
            delete_menuitem = page.get_by_role("menuitem", name="Delete")
            await delete_menuitem.wait_for(timeout=5_000)
            await delete_menuitem.click()
        except PlaywrightTimeoutError as exc:
            raise NotebookLMError(
                "Could not find the 'Delete' menuitem. "
                "The menu may not have appeared correctly."
            ) from exc

        # Wait for the confirmation dialog
        await page.wait_for_timeout(500)

        # Click the "Confirm deletion" button
        try:
            confirm_button = page.get_by_role("button", name="Confirm deletion")
            await confirm_button.wait_for(timeout=5_000)
            await confirm_button.click()
        except PlaywrightTimeoutError as exc:
            raise NotebookLMError(
                "Could not find the 'Confirm deletion' button. "
                "The confirmation dialog may not have appeared."
            ) from exc

        # Wait for the deletion to complete
        await page.wait_for_timeout(1_000)

        return {
            "status": "success",
            "message": f"NotebookLM notebook {notebook_id} deleted successfully.",
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to delete NotebookLM notebook: {exc}") from exc

