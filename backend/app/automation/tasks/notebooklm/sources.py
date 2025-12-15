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
        page.wait_for_timeout(1_000)

        # Always start from a clean state
        close_dialogs(page)

        add_source_button = page.get_by_role("button", name=re.compile("^Add source$", re.IGNORECASE))
        add_source_button.wait_for(timeout=10_000, state="visible")
        add_source_button.click()
        page.wait_for_timeout(500)

        # The new UI opens a dialog with multiple source types (upload, link, drive, etc.)
        # Target the upload option and then the underlying file input.
        dialog = page.get_by_role("dialog").last
        dialog.wait_for(timeout=5_000, state="visible")

        upload_button = dialog.get_by_role(
            "button", name=re.compile("^Upload files$", re.IGNORECASE)
        ).first
        upload_button.wait_for(timeout=5_000, state="visible")
        upload_button.click()
        page.wait_for_timeout(300)

        # The upload button wires to a hidden file input inside the dialog
        file_input = dialog.locator('input[type="file"]').first
        try:
            file_input.wait_for(timeout=5_000, state="attached")
        except Exception:
            # Fallback: some variants render the input at the page level
            file_input = page.locator('input[type="file"]').first
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
        Dictionary with status, message, and detailed source information in markdown

    Raises:
        NotebookLMError: If reviewing source fails
    """
    try:
        navigate_to_notebook(page, notebook_id)
        close_dialogs(page)
        page.wait_for_timeout(1_000)
        
        # Wait for the sources panel to be visible
        # Look for elements indicating the sources panel is loaded
        add_sources_div = page.locator("div").filter(has_text="add Add sources 🔎 Try Deep").nth(2)
        add_sources_div.wait_for(timeout=10_000, state="visible")
        
        select_all_div = page.locator("div").filter(has_text="Select all sources").nth(5)
        select_all_div.wait_for(timeout=10_000, state="visible")
        
        # Click on the source within the source-picker element
        source_picker = page.locator("source-picker")
        source_picker.wait_for(timeout=10_000, state="visible")
        source_link = source_picker.get_by_text(source_name)
        source_link.wait_for(timeout=10_000, state="visible")
        source_link.click()
        
        # Wait for the source panel view to open (check for source-panel-view class)
        source_panel_view = page.locator("section.source-panel-view")
        source_panel_view.wait_for(timeout=10_000, state="visible")
        page.wait_for_timeout(2_000)  # Give extra time for content to load
        
        # Extract source information
        source_viewer = source_panel_view.locator("source-viewer")
        source_viewer.wait_for(timeout=5_000, state="attached")
        
        # Extract source title
        source_title_elem = source_viewer.locator(".source-title")
        source_title = ""
        if source_title_elem.count() > 0:
            source_title = source_title_elem.inner_text().strip()
        
        # Extract summary from source guide
        summary_text = ""
        try:
            summary_container = source_viewer.locator(".summary-container .summary")
            if summary_container.count() > 0:
                summary_elem = summary_container.locator(".mat-body-medium")
                if summary_elem.count() > 0:
                    summary_text = summary_elem.inner_text().strip()
        except Exception:
            pass
        
        # Extract key topics (chips)
        key_topics = []
        try:
            key_topics_container = source_viewer.locator(".key-topics-container")
            if key_topics_container.count() > 0:
                chip_listbox = key_topics_container.locator("mat-chip-listbox")
                if chip_listbox.count() > 0:
                    chips = chip_listbox.locator("mat-chip-option")
                    chip_count = chips.count()
                    for i in range(chip_count):
                        try:
                            chip = chips.nth(i)
                            chip_text = chip.locator(".key-topics-text p").inner_text().strip()
                            if chip_text:
                                key_topics.append(chip_text)
                        except Exception:
                            continue
        except Exception:
            pass
        
        # Extract source content
        content_parts = []
        try:
            doc_viewer = source_viewer.locator("labs-tailwind-doc-viewer")
            doc_viewer.wait_for(timeout=5_000, state="attached")
            if doc_viewer.count() > 0:
                structural_elements = doc_viewer.locator("labs-tailwind-structural-element-view-v2")
                structural_elements.first.wait_for(timeout=5_000, state="attached")
                element_count = structural_elements.count()
                for i in range(element_count):
                    try:
                        element = structural_elements.nth(i)
                        paragraph = element.locator(".paragraph.normal")
                        if paragraph.count() > 0:
                            # Try to get text from span with data-start-index
                            text_span = paragraph.locator("span[data-start-index]")
                            if text_span.count() > 0:
                                text = text_span.inner_text().strip()
                                if text:
                                    content_parts.append(text)
                            else:
                                # Fallback: try to get all text from paragraph
                                text = paragraph.inner_text().strip()
                                if text:
                                    content_parts.append(text)
                    except Exception:
                        continue
        except Exception:
            # If doc-viewer approach fails, try alternative method
            try:
                scroll_area = source_viewer.locator(".scroll-area")
                if scroll_area.count() > 0:
                    all_text = scroll_area.inner_text()
                    if all_text.strip():
                        content_parts.append(all_text.strip())
            except Exception:
                pass
        
        # Build markdown content
        markdown_parts = []
        
        # Add title
        if source_title:
            markdown_parts.append(f"# {source_title}\n")
        
        # Add source guide section
        if summary_text or key_topics:
            markdown_parts.append("## Source Guide\n")
            
            if summary_text:
                markdown_parts.append("### Summary\n")
                markdown_parts.append(f"{summary_text}\n")
            
            if key_topics:
                markdown_parts.append("### Key Topics\n")
                for topic in key_topics:
                    markdown_parts.append(f"- {topic}")
                markdown_parts.append("")
        
        # Add source content
        if content_parts:
            markdown_parts.append("## Source Content\n")
            markdown_parts.append("\n".join(content_parts))
        
        markdown_content = "\n".join(markdown_parts).strip()
        
        result = {
            "status": "success",
            "message": f"Opened source {source_name}.",
            "source_name": source_title or source_name,
            "summary": summary_text if summary_text else None,
            "key_topics": key_topics,
            "content": "\n".join(content_parts).strip() if content_parts else None,
            "markdown": markdown_content if markdown_content else None,
        }
        
        # Also include title for backward compatibility
        result["title"] = result["source_name"]
        
        return result
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to review source: {exc}") from exc
