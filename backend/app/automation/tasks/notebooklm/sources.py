"""Source operations for NotebookLM automation."""

from typing import Any, Dict

from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.automation.tasks.notebooklm.exceptions import NotebookLMError
from app.automation.tasks.notebooklm.helpers import close_dialogs, navigate_to_notebook


async def add_source_to_notebook(
    page: Page, notebook_id: str, file_path: str
) -> Dict[str, str]:
    """
    Adds a source file to a notebook in NotebookLM.

    Args:
        page: The Playwright Page object to use for automation
        notebook_id: The ID of the notebook to add the source to
        file_path: The path to the file to upload

    Returns:
        Dictionary with status and message

    Raises:
        NotebookLMError: If adding the source fails
    """
    try:
        # Navigate directly to the notebook page
        await navigate_to_notebook(page, notebook_id)

        # Close any dialogs that might appear
        await close_dialogs(page)

        # Click on "Add source" button
        try:
            add_source_button = page.get_by_role("button", name="Add source")
            await add_source_button.wait_for(timeout=10_000)
            await add_source_button.click()
        except PlaywrightTimeoutError as exc:
            raise NotebookLMError(
                "Could not find the 'Add source' button. "
                "The notebook page may not have loaded correctly."
            ) from exc

        # Wait for the upload dialog to appear
        await page.wait_for_timeout(500)

        # Click on "choose file" button
        try:
            choose_file_button = page.get_by_role("button", name="choose file")
            await choose_file_button.wait_for(timeout=5_000)
            await choose_file_button.click()
        except PlaywrightTimeoutError as exc:
            raise NotebookLMError(
                "Could not find the 'choose file' button. "
                "The upload dialog may not have appeared correctly."
            ) from exc

        # Wait for the file input dialog to appear
        await page.wait_for_timeout(1_000)

        # Find the file input dialog and set the file
        # The dialog has an ID like #mat-mdc-dialog-0, #mat-mdc-dialog-1, etc.
        # The number varies, so we'll find the most recent/visible dialog
        try:
            # Find all dialogs with the mat-mdc-dialog pattern and use the last one (most recent)
            # The dialog ID pattern is #mat-mdc-dialog-{number}
            dialog = page.locator('[id^="mat-mdc-dialog-"]').last
            await dialog.wait_for(timeout=10_000)
            
            # Wait a bit more for the dialog content to fully load
            await page.wait_for_timeout(500)
            
            # Try multiple strategies to find and set the file input
            file_set = False
            
            # Strategy 1: Find file input inside the dialog
            try:
                file_input = dialog.locator('input[type="file"]')
                # Wait for the input to be attached to the DOM
                await file_input.wait_for(timeout=3_000, state="attached")
                await file_input.set_input_files(file_path)
                file_set = True
            except (PlaywrightTimeoutError, Exception):
                pass
            
            # Strategy 2: Try to find file input anywhere in the dialog (including nested elements)
            if not file_set:
                try:
                    # Look for file input with a more flexible selector
                    file_input = dialog.locator('input[type="file"], input[accept]').first
                    await file_input.wait_for(timeout=2_000, state="attached")
                    await file_input.set_input_files(file_path)
                    file_set = True
                except (PlaywrightTimeoutError, Exception):
                    pass
            
            # Strategy 3: Find any file input on the page (as fallback)
            if not file_set:
                try:
                    file_input = page.locator('input[type="file"]').last
                    await file_input.wait_for(timeout=2_000, state="attached")
                    await file_input.set_input_files(file_path)
                    file_set = True
                except (PlaywrightTimeoutError, Exception):
                    pass
            
            if not file_set:
                raise NotebookLMError(
                    "Could not find or set files on the file input element. "
                    "The file upload dialog may not have appeared correctly."
                )
        except PlaywrightTimeoutError as exc:
            raise NotebookLMError(
                "Could not find the file input dialog. "
                "The file upload dialog may not have appeared correctly."
            ) from exc

        # Wait for the file to be processed
        await page.wait_for_timeout(2_000)

        return {
            "status": "success",
            "message": f"Source file added to notebook {notebook_id} successfully.",
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to add source to NotebookLM notebook: {exc}") from exc


async def list_sources(page: Page, notebook_id: str) -> Dict[str, Any]:
    """
    Lists all sources in a notebook.

    Args:
        page: The Playwright Page object to use for automation
        notebook_id: The ID of the notebook to list sources from

    Returns:
        Dictionary with status, message, and list of sources

    Raises:
        NotebookLMError: If listing sources fails
    """
    try:
        # Navigate directly to the notebook page
        await navigate_to_notebook(page, notebook_id)

        # Close any dialogs that might appear
        await close_dialogs(page)

        # Wait for sources to load
        await page.wait_for_timeout(1_000)

        # Find all source containers
        source_containers = page.locator('.single-source-container')
        source_count = await source_containers.count()

        sources = []
        for i in range(source_count):
            try:
                container = source_containers.nth(i)
                # Get the source title from the source-title div
                source_title_element = container.locator('.source-title')
                source_name = await source_title_element.inner_text()
                # Clean up whitespace
                source_name = source_name.strip() if source_name else ""
                
                if source_name:
                    sources.append(source_name)
            except Exception:
                # Skip sources that can't be read
                continue

        return {
            "status": "success",
            "message": f"Found {len(sources)} sources in notebook {notebook_id}.",
            "sources": sources,
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to list sources from NotebookLM notebook: {exc}") from exc


async def delete_source(page: Page, notebook_id: str, source_name: str) -> Dict[str, str]:
    """
    Deletes a source from a notebook.

    Args:
        page: The Playwright Page object to use for automation
        notebook_id: The ID of the notebook to delete the source from
        source_name: The name of the source to delete

    Returns:
        Dictionary with status and message

    Raises:
        NotebookLMError: If deleting the source fails
    """
    try:
        # Navigate directly to the notebook page
        await navigate_to_notebook(page, notebook_id)

        # Close any dialogs that might appear
        await close_dialogs(page)

        # Wait for sources to load
        await page.wait_for_timeout(1_000)

        # Find the source by its name
        # The source title is in a div with class "source-title"
        source_title = page.locator('.source-title').filter(has_text=source_name).first
        
        try:
            await source_title.wait_for(timeout=10_000)
        except PlaywrightTimeoutError as exc:
            raise NotebookLMError(
                f"Could not find source '{source_name}' in notebook {notebook_id}. "
                "The source may not exist."
            ) from exc

        # Find the parent container and then the "More" button
        source_container = source_title.locator("xpath=ancestor::div[contains(@class, 'single-source-container')]")
        more_button = source_container.get_by_role("button", name="More")
        
        try:
            await more_button.wait_for(timeout=5_000)
            await more_button.click()
        except PlaywrightTimeoutError as exc:
            raise NotebookLMError(
                f"Could not find the 'More' button for source '{source_name}'. "
                "The source menu may not be accessible."
            ) from exc

        # Wait for the menu to appear
        await page.wait_for_timeout(500)

        # Click on "Remove source" menuitem
        try:
            remove_menuitem = page.get_by_role("menuitem", name="Remove source")
            await remove_menuitem.wait_for(timeout=5_000)
            await remove_menuitem.click()
        except PlaywrightTimeoutError as exc:
            raise NotebookLMError(
                "Could not find the 'Remove source' menuitem. "
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
            "message": f"Source '{source_name}' deleted from notebook {notebook_id} successfully.",
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to delete source from NotebookLM notebook: {exc}") from exc

