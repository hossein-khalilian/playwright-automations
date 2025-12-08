"""Sync source operations for NotebookLM automation."""

import re
from typing import Any, Dict

from playwright.sync_api import Page

from app.automation.tasks.notebooklm.exceptions import NotebookLMError
from app.automation.tasks.notebooklm.helpers import close_dialogs, navigate_to_notebook


def add_source_to_notebook(
    page: Page, notebook_id: str, file_path: str
) -> Dict[str, str]:
    """
    Add a source file to a notebook.

    Args:
        page: The Playwright Page object
        notebook_id: The ID of the notebook
        file_path: Path to the file to upload

    Returns:
        Dictionary with status and message

    Raises:
        NotebookLMError: If adding source fails
    """
    try:
        navigate_to_notebook(page, notebook_id)
        close_dialogs(page)
        add_source_button = page.get_by_role("button", name="Add source")
        add_source_button.wait_for(timeout=10_000)
        add_source_button.click()
        page.wait_for_timeout(500)
        
        # Check if dialog appears (only shows if no sources exist)
        dialog = page.locator('[id^="mat-mdc-dialog-"]').last
        dialog_appeared = False
        try:
            dialog.wait_for(timeout=3_000, state="visible")
            dialog_appeared = True
        except Exception:
            # Dialog didn't appear - sources might already exist
            pass
        
        if dialog_appeared:
            # Dialog appeared - use the "choose file" button flow
            choose_file_button = page.get_by_role("button", name="choose file")
            choose_file_button.wait_for(timeout=5_000)
            choose_file_button.click()
            page.wait_for_timeout(1_000)
            # Wait for dialog to be ready and find file input within it
            dialog.wait_for(timeout=5_000)
            file_input = dialog.locator('input[type="file"]')
            file_input.wait_for(timeout=5_000, state="attached")
        else:
            # Dialog didn't appear - look for file input directly on page
            file_input = page.locator('input[type="file"]')
            file_input.wait_for(timeout=5_000, state="attached")
        
        file_input.set_input_files(file_path)
        page.wait_for_timeout(2_000)
        return {
            "status": "success",
            "message": f"Source added to notebook {notebook_id}.",
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to add source: {exc}") from exc


def list_sources(page: Page, notebook_id: str) -> Dict[str, Any]:
    """
    List all sources in a notebook.

    Args:
        page: The Playwright Page object
        notebook_id: The ID of the notebook

    Returns:
        Dictionary with status, message, and list of sources

    Raises:
        NotebookLMError: If listing sources fails
    """
    try:
        navigate_to_notebook(page, notebook_id)
        close_dialogs(page)
        page.wait_for_timeout(1_000)
        source_containers = page.locator(".single-source-container")
        source_count = source_containers.count()
        sources = []
        for i in range(source_count):
            try:
                container = source_containers.nth(i)
                source_title_element = container.locator(".source-title")
                source_name = source_title_element.inner_text().strip()
                if not source_name:
                    continue
                status = "ready"
                try:
                    loading_spinner_container = container.locator(
                        ".loading-spinner-container"
                    )
                    if loading_spinner_container.count() > 0:
                        spinner = loading_spinner_container.first
                        if spinner.is_visible():
                            status = "processing"
                except Exception:
                    pass
                try:
                    more_button = container.get_by_role("button", name="More").first
                    disabled_attr = more_button.get_attribute("disabled")
                    class_attr = more_button.get_attribute("class") or ""
                    is_disabled = disabled_attr is not None or (
                        "mat-mdc-button-disabled" in class_attr
                    )
                    if is_disabled and status == "ready":
                        status = "processing"
                except Exception:
                    pass
                sources.append({"name": source_name, "status": status})
            except Exception:
                continue
        return {
            "status": "success",
            "message": f"Found {len(sources)} sources.",
            "sources": sources,
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to list sources: {exc}") from exc


def delete_source(page: Page, notebook_id: str, source_name: str) -> Dict[str, str]:
    """
    Delete a source from a notebook.

    Args:
        page: The Playwright Page object
        notebook_id: The ID of the notebook
        source_name: Name of the source to delete

    Returns:
        Dictionary with status and message

    Raises:
        NotebookLMError: If deleting source fails
    """
    try:
        navigate_to_notebook(page, notebook_id)
        close_dialogs(page)
        page.wait_for_timeout(1_000)
        source_title = page.locator(".source-title").filter(has_text=source_name).first
        source_title.wait_for(timeout=10_000)
        container = source_title.locator(
            "xpath=ancestor::div[contains(@class,'single-source-container')]"
        )
        actions_button = container.get_by_role("button", name="More")
        actions_button.wait_for(timeout=5_000)
        actions_button.click()
        page.wait_for_timeout(500)
        delete_button = page.get_by_role(
            "menuitem", name=re.compile("Remove source", re.IGNORECASE)
        )
        delete_button.wait_for(timeout=5_000)
        delete_button.click()
        page.wait_for_timeout(500)
        confirm_button = page.get_by_role(
            "button", name=re.compile("Confirm deletion", re.IGNORECASE)
        )
        confirm_button.wait_for(timeout=5_000)
        confirm_button.click()
        page.wait_for_timeout(1_000)
        return {"status": "success", "message": f"Source {source_name} deleted."}
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to delete source: {exc}") from exc


def rename_source(
    page: Page, notebook_id: str, source_name: str, new_name: str
) -> Dict[str, str]:
    """
    Rename a source in a notebook.

    Args:
        page: The Playwright Page object
        notebook_id: The ID of the notebook
        source_name: Current name of the source
        new_name: New name for the source

    Returns:
        Dictionary with status and message

    Raises:
        NotebookLMError: If renaming source fails
    """
    try:
        navigate_to_notebook(page, notebook_id)
        close_dialogs(page)
        page.wait_for_timeout(1_000)
        source_title = page.locator(".source-title").filter(has_text=source_name).first
        source_title.wait_for(timeout=10_000)
        container = source_title.locator(
            "xpath=ancestor::div[contains(@class,'single-source-container')]"
        )
        actions_button = container.get_by_role("button", name="More")
        actions_button.wait_for(timeout=5_000)
        actions_button.click()
        page.wait_for_timeout(500)
        rename_button = page.get_by_role(
            "menuitem", name=re.compile("Rename source", re.IGNORECASE)
        )
        rename_button.wait_for(timeout=5_000)
        rename_button.click()
        page.wait_for_timeout(500)
        name_input = page.get_by_role("textbox", name="Source Name")
        name_input.wait_for(timeout=5_000)
        name_input.click()
        name_input.press("ControlOrMeta+a")
        name_input.fill(new_name)
        save_button = page.get_by_role("button", name="Save")
        save_button.wait_for(timeout=5_000)
        save_button.click()
        page.wait_for_timeout(1_000)
        return {"status": "success", "message": f"Source renamed to {new_name}."}
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to rename source: {exc}") from exc


def review_source(page: Page, notebook_id: str, source_name: str) -> Dict[str, Any]:
    """
    Open and review a source in a notebook.

    Args:
        page: The Playwright Page object
        notebook_id: The ID of the notebook
        source_name: Name of the source to review

    Returns:
        Dictionary with status and message

    Raises:
        NotebookLMError: If reviewing source fails
    """
    try:
        navigate_to_notebook(page, notebook_id)
        close_dialogs(page)
        page.wait_for_timeout(1_000)
        source_title = page.locator(".source-title").filter(has_text=source_name).first
        source_title.wait_for(timeout=10_000)
        source_title.click()
        page.wait_for_timeout(1_000)
        return {"status": "success", "message": f"Opened source {source_name}."}
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to review source: {exc}") from exc
