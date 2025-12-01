"""Source operations for NotebookLM automation."""

import base64
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
        source_containers = page.locator(".single-source-container")
        source_count = await source_containers.count()

        sources = []
        for i in range(source_count):
            try:
                container = source_containers.nth(i)
                # Get the source title from the source-title div
                source_title_element = container.locator(".source-title")
                source_name = await source_title_element.inner_text()
                # Clean up whitespace
                source_name = source_name.strip() if source_name else ""

                if not source_name:
                    continue

                # Determine source status.
                # Heuristic based on UI:
                # - If a loading spinner container is visible or the "More" button is disabled,
                #   we consider the source to be in "processing" state.
                # - Otherwise, we consider it "ready".
                status = "ready"

                try:
                    loading_spinner_container = container.locator(
                        ".loading-spinner-container"
                    )
                    if await loading_spinner_container.count() > 0:
                        # If any spinner is visible, treat as processing
                        spinner = loading_spinner_container.first
                        if await spinner.is_visible():
                            status = "processing"
                except Exception:
                    # Ignore errors when checking spinner; fall back to other checks
                    pass

                # Fallback: infer processing state from the "More" button if available
                try:
                    more_button = container.get_by_role("button", name="More")
                    if await more_button.count() > 0:
                        more_button = more_button.first
                        disabled_attr = await more_button.get_attribute("disabled")
                        class_attr = await more_button.get_attribute("class") or ""
                        is_disabled = disabled_attr is not None or (
                            "mat-mdc-button-disabled" in class_attr
                        )
                        if is_disabled and status == "ready":
                            status = "processing"
                except Exception:
                    # If we cannot reliably read the button state, keep existing status
                    pass

                sources.append(
                    {
                        "name": source_name,
                        "status": status,
                    }
                )
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


async def rename_source(
    page: Page, notebook_id: str, source_name: str, new_name: str
) -> Dict[str, str]:
    """
    Renames a source in a notebook.

    Args:
        page: The Playwright Page object to use for automation
        notebook_id: The ID of the notebook
        source_name: The current name of the source to rename
        new_name: The new name for the source

    Returns:
        Dictionary with status and message

    Raises:
        NotebookLMError: If renaming the source fails
    """
    try:
        # Navigate directly to the notebook page
        await navigate_to_notebook(page, notebook_id)

        # Close any dialogs that might appear
        await close_dialogs(page)

        # Wait for sources to load
        await page.wait_for_timeout(1_000)

        # Find the source by its name
        source_title = page.locator(".source-title").filter(has_text=source_name).first

        try:
            await source_title.wait_for(timeout=10_000)
        except PlaywrightTimeoutError as exc:
            raise NotebookLMError(
                f"Could not find source '{source_name}' in notebook {notebook_id}. "
                "The source may not exist."
            ) from exc

        # Find the parent container and then the "More" button
        source_container = source_title.locator(
            "xpath=ancestor::div[contains(@class, 'single-source-container')]"
        )
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

        # Click on "Rename source" menuitem
        try:
            rename_menuitem = page.get_by_role("menuitem", name="Rename source")
            await rename_menuitem.wait_for(timeout=5_000)
            await rename_menuitem.click()
        except PlaywrightTimeoutError as exc:
            raise NotebookLMError(
                "Could not find the 'Rename source' menuitem. "
                "The menu may not have appeared correctly."
            ) from exc

        # Wait for the textbox to be ready
        await page.wait_for_timeout(500)

        # Find and edit the textbox
        try:
            textbox = page.get_by_role("textbox", name="Source Name")
            await textbox.wait_for(timeout=5_000)
            await textbox.click()
            # Select all and replace with new name
            await textbox.press("ControlOrMeta+a")
            await textbox.fill(new_name)
        except PlaywrightTimeoutError as exc:
            raise NotebookLMError(
                "Could not find or edit the rename textbox. "
                "The rename UI may not have appeared correctly."
            ) from exc

        # Click the "Save" button
        try:
            save_button = page.get_by_role("button", name="Save")
            await save_button.wait_for(timeout=5_000)
            await save_button.click()
        except PlaywrightTimeoutError as exc:
            raise NotebookLMError(
                "Could not find the 'Save' button. "
                "The rename dialog may not have appeared correctly."
            ) from exc

        # Wait for the rename to complete
        await page.wait_for_timeout(1_000)

        return {
            "status": "success",
            "message": f"Source '{source_name}' renamed to '{new_name}' successfully.",
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to rename source: {exc}") from exc


async def review_source(page: Page, notebook_id: str, source_name: str) -> Dict[str, Any]:
    """
    Opens and retrieves the review/content of a source in a notebook.

    Args:
        page: The Playwright Page object to use for automation
        notebook_id: The ID of the notebook
        source_name: The name of the source to review

    Returns:
        Dictionary with status, message, and source review data (title, summary, key_topics, content)

    Raises:
        NotebookLMError: If reviewing the source fails
    """
    try:
        # Navigate directly to the notebook page
        await navigate_to_notebook(page, notebook_id)

        # Close any dialogs that might appear
        await close_dialogs(page)

        # Wait for sources to load
        await page.wait_for_timeout(1_000)

        # Find and click the source in source-picker
        try:
            source_picker = page.locator("source-picker")
            source_link = source_picker.get_by_text(source_name).first
            await source_link.wait_for(timeout=10_000)
            await source_link.click()
        except PlaywrightTimeoutError as exc:
            raise NotebookLMError(
                f"Could not find source '{source_name}' in source-picker. "
                "The source may not exist or may not be accessible."
            ) from exc

        # Wait for the source panel to open
        await page.wait_for_timeout(2_000)

        # Extract source review data
        review_data = {
            "title": None,
            "summary": None,
            "key_topics": [],
            "content": None,
            "images": [],
        }

        # Extract source title
        try:
            source_title_element = page.locator(".source-title").first
            if await source_title_element.count() > 0:
                review_data["title"] = await source_title_element.inner_text()
                review_data["title"] = (
                    review_data["title"].strip() if review_data["title"] else None
                )
        except Exception:
            pass

        # Extract summary from source-guide
        try:
            summary_element = page.locator(".summary").first
            if await summary_element.count() > 0:
                summary_text = await summary_element.inner_text()
                review_data["summary"] = summary_text.strip() if summary_text else None
        except Exception:
            pass

        # Extract key topics (chips)
        try:
            key_topics_chips = page.locator(".key-topics-chip")
            chip_count = await key_topics_chips.count()
            for i in range(chip_count):
                try:
                    chip = key_topics_chips.nth(i)
                    chip_text = await chip.inner_text()
                    if chip_text:
                        review_data["key_topics"].append(chip_text.strip())
                except Exception:
                    continue
        except Exception:
            pass

        # Extract source content (transcript/text) and images
        try:
            # The content is in labs-tailwind-doc-viewer with paragraph elements
            content_paragraphs = page.locator(
                "labs-tailwind-doc-viewer .paragraph span"
            )
            paragraph_count = await content_paragraphs.count()
            content_parts = []
            for i in range(paragraph_count):
                try:
                    paragraph = content_paragraphs.nth(i)
                    text = await paragraph.inner_text()
                    if text:
                        content_parts.append(text.strip())
                except Exception:
                    continue
            if content_parts:
                review_data["content"] = "\n\n".join(content_parts)
        except Exception:
            pass

        # Extract images from the document viewer and convert to base64
        try:
            images = []
            # Find all img tags within the document viewer
            img_elements = page.locator("labs-tailwind-doc-viewer img")
            img_count = await img_elements.count()
            for i in range(img_count):
                try:
                    img = img_elements.nth(i)
                    src = await img.get_attribute("src")
                    if src:
                        image_data = {
                            "base64": None,
                            "mime_type": None,
                        }
                        
                        # Download and convert image to base64
                        try:
                            # Use Playwright's request context to download the image
                            response = await page.request.get(src)
                            if response.ok:
                                image_bytes = await response.body()
                                # Determine MIME type from response headers or URL
                                content_type = response.headers.get("content-type", "")
                                if not content_type:
                                    # Try to infer from URL extension
                                    if src.lower().endswith((".png",)):
                                        content_type = "image/png"
                                    elif src.lower().endswith((".jpg", ".jpeg")):
                                        content_type = "image/jpeg"
                                    elif src.lower().endswith((".gif",)):
                                        content_type = "image/gif"
                                    elif src.lower().endswith((".webp",)):
                                        content_type = "image/webp"
                                    else:
                                        content_type = "image/png"  # Default
                                
                                # Encode to base64
                                base64_data = base64.b64encode(image_bytes).decode("utf-8")
                                image_data["base64"] = base64_data
                                image_data["mime_type"] = content_type
                                
                                # Only add image if we successfully downloaded and encoded it
                                images.append(image_data)
                        except Exception:
                            # If download fails, skip this image
                            continue
                except Exception:
                    continue
            review_data["images"] = images
        except Exception:
            review_data["images"] = []

        return {
            "status": "success",
            "message": f"Source '{source_name}' review retrieved successfully.",
            "title": review_data["title"],
            "summary": review_data["summary"],
            "key_topics": review_data["key_topics"],
            "content": review_data["content"],
            "images": review_data["images"],
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to review source: {exc}") from exc

