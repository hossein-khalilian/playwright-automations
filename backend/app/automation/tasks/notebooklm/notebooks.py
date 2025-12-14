"""Sync notebook operations for NotebookLM automation."""

from typing import Dict

from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from app.automation.tasks.notebooklm.exceptions import NotebookLMError
from app.automation.tasks.notebooklm.helpers import (
    close_dialogs,
    extract_notebook_id_from_url,
    navigate_to_main_page,
)


def create_notebook(page: Page, email: str = None) -> Dict[str, str]:
    """
    Create a new NotebookLM notebook.

    Args:
        page: The Playwright Page object
        email: The email address used to create the notebook

    Returns:
        Dictionary with status, message, page_url, notebook_id, and email

    Raises:
        NotebookLMError: If notebook creation fails
    """
    try:
        navigate_to_main_page(page)
        create_button = page.locator("mat-card").filter(
            has_text="addCreate new notebook"
        )
        create_button.wait_for(timeout=15_000)
        create_button.click()
        close_dialogs(page)
        try:
            page.wait_for_url("**/notebook/**", timeout=10_000)
        except PlaywrightTimeoutError:
            pass
        page.wait_for_timeout(1_000)
        current_url = page.url
        if "/notebook/" not in current_url:
            raise NotebookLMError("Notebook creation verification failed.")
        notebook_id = extract_notebook_id_from_url(page)
        return {
            "status": "success",
            "message": "Notebook created.",
            "page_url": current_url,
            "notebook_id": notebook_id,
            "email": email,
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to create NotebookLM notebook: {exc}") from exc


def delete_notebook(page: Page, notebook_id: str) -> Dict[str, str]:
    """
    Delete a NotebookLM notebook.

    Args:
        page: The Playwright Page object
        notebook_id: The ID of the notebook to delete

    Returns:
        Dictionary with status and message

    Raises:
        NotebookLMError: If notebook deletion fails
    """
    try:
        navigate_to_main_page(page)
        close_dialogs(page)
        mat_card = page.locator(
            f'mat-card[aria-labelledby*="project-{notebook_id}-title"]'
        )
        mat_card.wait_for(timeout=10_000)
        actions_menu = mat_card.get_by_role("button", name="Project Actions Menu")
        actions_menu.wait_for(timeout=5_000)
        actions_menu.click()
        page.wait_for_timeout(500)
        delete_menuitem = page.get_by_role("menuitem", name="Delete")
        delete_menuitem.wait_for(timeout=5_000)
        delete_menuitem.click()
        page.wait_for_timeout(500)
        confirm_button = page.get_by_role("button", name="Confirm deletion")
        confirm_button.wait_for(timeout=5_000)
        confirm_button.click()
        page.wait_for_timeout(1_000)
        return {"status": "success", "message": f"Notebook {notebook_id} deleted."}
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to delete NotebookLM notebook: {exc}") from exc
