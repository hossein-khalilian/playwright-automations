"""Sync artifact management operations for NotebookLM automation."""

import os
import re
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from PIL import Image
from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from app.automation.tasks.notebooklm.exceptions import NotebookLMError
from app.automation.tasks.notebooklm.helpers import close_dialogs, navigate_to_notebook

ICON_TO_TYPE = {
    "audio_magic_eraser": "audio_overview",
    "subscriptions": "video_overview",
    "quiz": "quiz",
    "cards_star": "flashcards",
    "flowchart": "mind_map",
    "auto_tab_group": "reports",
    "stacked_bar_chart": "infographic",
    "tablet": "slide_deck",
}


def _artifact_library(page: Page):
    """Get the artifact library container."""
    artifact_library = page.locator("div.artifact-library-container")
    try:
        artifact_library.wait_for(timeout=30_000, state="visible")
    except PlaywrightTimeoutError:
        page.wait_for_timeout(2_000)
    return artifact_library


def list_artifacts(page: Page, notebook_id: str) -> Dict[str, Any]:
    """
    List all artifacts in a notebook.

    Args:
        page: The Playwright Page object
        notebook_id: The ID of the notebook

    Returns:
        Dictionary with status, message, and list of artifacts

    Raises:
        NotebookLMError: If listing artifacts fails
    """
    try:
        navigate_to_notebook(page, notebook_id)
        close_dialogs(page)
        artifact_library = _artifact_library(page)
        artifacts: List[Dict[str, Any]] = []
        
        # Get both artifact-library-item and artifact-library-note elements
        artifact_items = artifact_library.locator("artifact-library-item, artifact-library-note")
        for i in range(artifact_items.count()):
            try:
                artifact_item = artifact_items.nth(i)
                artifact_button = artifact_item.locator(
                    "button.artifact-button-content"
                ).first
                if artifact_button.count() == 0:
                    continue
                artifact_type = None
                icon_element = artifact_item.locator("mat-icon.artifact-icon").first
                if icon_element.count() > 0:
                    icon_text = icon_element.inner_text().strip()
                    for icon_name, type_name in ICON_TO_TYPE.items():
                        if icon_name in icon_text:
                            artifact_type = type_name
                            break
                    if not artifact_type:
                        artifact_type = icon_text or "unknown"
                artifact_name = None
                title_element = artifact_button.locator("span.artifact-title").first
                if title_element.count() > 0:
                    artifact_name = title_element.inner_text().strip()
                details = None
                details_element = artifact_button.locator("span.artifact-details").first
                if details_element.count() > 0:
                    details = details_element.inner_text().strip()
                status = "ready"
                play_button = artifact_button.locator('button[aria-label="Play"]')
                interactive_button = artifact_button.locator(
                    'button[aria-label="Interactive mode"]'
                )
                has_play = play_button.count() > 0
                has_interactive = interactive_button.count() > 0
                if not has_play and not has_interactive:
                    status = "unknown"
                artifacts.append(
                    {
                        "type": artifact_type,
                        "name": artifact_name,
                        "details": details,
                        "status": status,
                        "has_play": has_play,
                        "has_interactive": has_interactive,
                    }
                )
            except Exception:
                continue
        return {
            "status": "success",
            "message": f"Found {len(artifacts)} artifact(s).",
            "artifacts": artifacts,
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to list artifacts: {exc}") from exc


def delete_artifact(page: Page, notebook_id: str, artifact_name: str) -> Dict[str, str]:
    """
    Delete an artifact from a notebook.

    Args:
        page: The Playwright Page object
        notebook_id: The ID of the notebook
        artifact_name: Name of the artifact to delete

    Returns:
        Dictionary with status and message

    Raises:
        NotebookLMError: If deleting artifact fails
    """
    try:
        navigate_to_notebook(page, notebook_id)
        close_dialogs(page)
        artifact_library = _artifact_library(page)
        # Find the artifact container (item or note) that contains the artifact
        artifact_container = (
            artifact_library.locator(
                "artifact-library-item, artifact-library-note"
            )
            .filter(has_text=artifact_name)
            .first
        )
        artifact_container.wait_for(timeout=10_000)
        # Find the "More" button within the artifact container
        # The More button is a sibling of the artifact button, so we search within the container
        more_button = artifact_container.get_by_label("More")
        more_button.wait_for(timeout=5_000)
        more_button.click()
        page.wait_for_timeout(300)
        delete_button = page.get_by_role(
            "menuitem", name=re.compile("Delete", re.IGNORECASE)
        )
        delete_button.wait_for(timeout=5_000)
        delete_button.click()
        page.wait_for_timeout(500)
        confirm_button = page.get_by_role(
            "button", name="Confirm deletion"
        )
        confirm_button.wait_for(timeout=5_000)
        confirm_button.click()
        page.wait_for_timeout(1_000)
        return {"status": "success", "message": f"Artifact {artifact_name} deleted."}
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to delete artifact: {exc}") from exc


def rename_artifact(
    page: Page, notebook_id: str, artifact_name: str, new_name: str
) -> Dict[str, str]:
    """
    Rename an artifact in a notebook.

    Args:
        page: The Playwright Page object
        notebook_id: The ID of the notebook
        artifact_name: Current name of the artifact
        new_name: New name for the artifact

    Returns:
        Dictionary with status and message

    Raises:
        NotebookLMError: If renaming artifact fails
    """
    try:
        navigate_to_notebook(page, notebook_id)
        close_dialogs(page)
        artifact_library = _artifact_library(page)
        artifact_button = (
            artifact_library.locator(
                "artifact-library-item button.artifact-button-content, artifact-library-note button.artifact-button-content"
            )
            .filter(has_text=artifact_name)
            .first
        )
        artifact_button.wait_for(timeout=10_000)
        artifact_button.click()
        page.wait_for_timeout(500)
        actions_button = page.get_by_role(
            "button", name=re.compile("More|Actions", re.IGNORECASE)
        ).first
        actions_button.wait_for(timeout=5_000)
        actions_button.click()
        page.wait_for_timeout(300)
        rename_button = page.get_by_role(
            "menuitem", name=re.compile("Rename", re.IGNORECASE)
        )
        rename_button.wait_for(timeout=5_000)
        rename_button.click()
        page.wait_for_timeout(500)
        name_input = page.get_by_role("textbox").first
        name_input.wait_for(timeout=5_000)
        name_input.fill(new_name)
        save_button = page.get_by_role(
            "button", name=re.compile("Save|Rename", re.IGNORECASE)
        )
        save_button.wait_for(timeout=5_000)
        save_button.click()
        page.wait_for_timeout(1_000)
        return {"status": "success", "message": f"Artifact renamed to {new_name}."}
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to rename artifact: {exc}") from exc


def _get_artifact_type(page: Page, artifact_container) -> Optional[str]:
    """
    Get the type of an artifact by checking its icon.

    Args:
        page: The Playwright Page object
        artifact_container: The artifact container locator

    Returns:
        The artifact type string or None if not found
    """
    try:
        icon_element = artifact_container.locator("mat-icon.artifact-icon").first
        if icon_element.count() > 0:
            # Use inner_text() method like in sources.py
            icon_text = icon_element.inner_text().strip()
            if icon_text:
                # Match icon text to artifact type
                for icon_name, type_name in ICON_TO_TYPE.items():
                    if icon_name in icon_text:
                        return type_name
                # Return the icon text if no match found
                return icon_text
    except Exception:
        # Silently fail and return None if we can't determine the type
        pass
    return None


def download_artifact(
    page: Page, notebook_id: str, artifact_name: str
) -> Dict[str, Any]:
    """
    Download an artifact from a notebook.
    Handles different artifact types with appropriate download methods:
    - Mindmaps: Click artifact, collapse nodes, then download
    - Video/Audio: Use menu trigger, expect popup and download
    - Others: Try video/audio pattern first, fallback to direct download

    Args:
        page: The Playwright Page object
        notebook_id: The ID of the notebook
        artifact_name: Name of the artifact to download

    Returns:
        Dictionary with status, message, and download path

    Raises:
        NotebookLMError: If downloading artifact fails
    """
    try:
        navigate_to_notebook(page, notebook_id)
        close_dialogs(page)
        artifact_library = _artifact_library(page)
        # Find the artifact container (item or note) that contains the artifact
        artifact_container = (
            artifact_library.locator(
                "artifact-library-item, artifact-library-note"
            )
            .filter(has_text=artifact_name)
            .first
        )
        artifact_container.wait_for(timeout=10_000)
        
        # Get artifact type to determine download method
        artifact_type = _get_artifact_type(page, artifact_container)
        
        # Handle mindmap downloads differently
        if artifact_type == "mind_map":
            # Click the artifact button to open it
            artifact_button = page.get_by_role("button", name=artifact_name)
            artifact_button.wait_for(timeout=10_000, state="visible")
            artifact_button.click()
            page.wait_for_timeout(1_000)
            
            # Click "Collapse all nodes" button
            collapse_button = page.get_by_role(
                "button", name=re.compile("Collapse all nodes", re.IGNORECASE)
            )
            collapse_button.wait_for(timeout=10_000, state="visible")
            collapse_button.click()
            page.wait_for_timeout(500)
            
            # Wait for download and click Download button
            with page.expect_download(timeout=30_000) as download_info:
                download_button = page.get_by_role(
                    "button", name=re.compile("Download", re.IGNORECASE)
                )
                download_button.wait_for(timeout=5_000, state="visible")
                download_button.click()
            download = download_info.value
        elif artifact_type == "infographic":
            # Handle infographic downloads: open artifact, then download with popup
            # Click the artifact button to open it
            artifact_button = page.get_by_role("button", name=artifact_name)
            artifact_button.wait_for(timeout=10_000, state="visible")
            artifact_button.click()
            page.wait_for_timeout(1_000)
            
            # Wait for both download and popup, then click Download button
            with page.expect_download(timeout=30_000) as download_info:
                with page.expect_popup(timeout=10_000) as popup_info:
                    download_button = page.get_by_role(
                        "button", name=re.compile("Download", re.IGNORECASE)
                    )
                    download_button.wait_for(timeout=5_000, state="visible")
                    download_button.click()
                popup = popup_info.value
            download = download_info.value
            # Close the popup
            popup.close()
            page.wait_for_timeout(500)
        elif artifact_type == "flashcards":
            # Handle flashcard downloads: open artifact, expand, then download from iframe dialog
            # Click the artifact button to open it
            artifact_button = page.get_by_role("button", name=artifact_name).first
            artifact_button.wait_for(timeout=10_000, state="visible")
            artifact_button.click()
            page.wait_for_timeout(1_000)
            
            # Click "Expand" button
            expand_button = page.get_by_role(
                "button", name=re.compile("Expand", re.IGNORECASE)
            )
            expand_button.wait_for(timeout=10_000, state="visible")
            expand_button.click()
            page.wait_for_timeout(1_000)
            
            # Wait for dialog and iframe to appear, then click Download button inside iframe
            with page.expect_download(timeout=30_000) as download_info:
                # Wait for dialog to appear
                dialog = page.get_by_role("dialog")
                dialog.wait_for(timeout=10_000, state="visible")
                page.wait_for_timeout(500)
                
                # Get the iframe inside the dialog and access its content frame
                iframe_locator = dialog.locator("iframe")
                iframe_locator.wait_for(timeout=10_000, state="attached")
                
                # In Playwright Python sync API, use frame_locator to interact with iframe content
                # We need to scope it to the dialog's iframe
                # Use page.frame_locator with a selector that finds the iframe in the dialog
                frame_locator = page.frame_locator('dialog iframe, [role="dialog"] iframe')
                
                # Click Download button inside the iframe
                download_button = frame_locator.get_by_role(
                    "button", name=re.compile("Download", re.IGNORECASE)
                )
                download_button.wait_for(timeout=5_000, state="visible")
                download_button.click()
            download = download_info.value
            page.wait_for_timeout(500)
        elif artifact_type == "reports":
            # Handle report downloads: open artifact, extract content directly from DOM, then create text file
            # Click the artifact button to open it
            artifact_button = page.get_by_role("button", name=artifact_name)
            artifact_button.wait_for(timeout=10_000, state="visible")
            artifact_button.click()
            page.wait_for_timeout(2_000)  # Wait for report content to load
            
            # Extract report content directly from the DOM
            # Wait a bit more for content to fully render
            page.wait_for_timeout(1_000)
            
            # Use page.evaluate to extract text content from the report
            # This approach works better in headless/Docker environments
            report_content = page.evaluate("""() => {
                // Try to find the main report content area
                // Look for common report container classes
                const selectors = [
                    'div[class*="report"]',
                    'div[class*="Report"]',
                    'div[class*="content"]',
                    'div[class*="Content"]',
                    'article',
                    'main',
                    '.document-content',
                    '.artifact-content',
                    '[role="article"]',
                    '[role="main"]'
                ];
                
                let content = '';
                
                // Try each selector
                for (const selector of selectors) {
                    try {
                        const elements = document.querySelectorAll(selector);
                        for (const element of elements) {
                            const text = element.innerText || element.textContent || '';
                            // Prefer longer content (likely the main content)
                            if (text.trim().length > content.length) {
                                content = text.trim();
                            }
                        }
                    } catch (e) {
                        continue;
                    }
                }
                
                // If we found substantial content, return it
                if (content.length > 100) {
                    return content;
                }
                
                // Fallback: get text from body, but filter out navigation/UI elements
                const body = document.body;
                if (body) {
                    // Clone body to avoid modifying the original
                    const clone = body.cloneNode(true);
                    // Remove common UI elements
                    const uiSelectors = ['nav', 'header', 'footer', 'button', '[role="button"]', '.toolbar', '.menu'];
                    uiSelectors.forEach(sel => {
                        const elements = clone.querySelectorAll(sel);
                        elements.forEach(el => el.remove());
                    });
                    return clone.innerText || clone.textContent || '';
                }
                
                return '';
            }""")
            
            if not report_content or len(report_content.strip()) == 0:
                raise NotebookLMError("Failed to extract report content from the page.")
            
            # Create a temporary text file with the content
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
            try:
                temp_file.write(report_content)
            finally:
                temp_file.close()
            
            # Create a mock download object-like structure
            class MockDownload:
                def __init__(self, file_path, filename):
                    self._path = file_path
                    self._filename = filename
                
                def path(self):
                    return self._path
                
                def suggested_filename(self):
                    return self._filename
            
            download = MockDownload(temp_file.name, f"{artifact_name}.txt")
        else:
            # Handle video/audio/slide_deck downloads (and others that trigger popup from menu)
            # This includes: video_overview, audio_overview, slide_deck, reports, quiz, etc.
            # Find the menu trigger button (More button) within the artifact container
            # The More button has class "artifact-more-button" and aria-label="More"
            menu_trigger = artifact_container.locator(".artifact-more-button").first
            # If menu trigger not found, try alternative selector
            if menu_trigger.count() == 0:
                menu_trigger = artifact_container.get_by_label("More")
            menu_trigger.wait_for(timeout=5_000, state="visible")
            menu_trigger.click()
            page.wait_for_timeout(300)
            
            # Wait for both download and popup, then click Download menuitem
            # This pattern is required for video and audio downloads
            with page.expect_download(timeout=30_000) as download_info:
                with page.expect_popup(timeout=10_000) as popup_info:
                    download_menuitem = page.get_by_role(
                        "menuitem", name=re.compile("Download", re.IGNORECASE)
                    )
                    download_menuitem.wait_for(timeout=5_000, state="visible")
                    download_menuitem.click()
                popup = popup_info.value
            download = download_info.value
            # Close the popup
            popup.close()
            page.wait_for_timeout(500)
        
        # Wait for download to complete and get the path
        # Verify download is a Download object, not a string
        if isinstance(download, str):
            raise NotebookLMError(f"Download object is a string, not a Download object: {download}")
        
        # Get download path - path() is a method that waits for download completion
        # Check if path is callable (method) or a property
        if callable(getattr(download, 'path', None)):
            download_path = download.path()
        else:
            # If path is a property, access it directly
            download_path = download.path
        
        # Get suggested filename - suggested_filename() is a method
        # Check if suggested_filename is callable (method) or a property
        if callable(getattr(download, 'suggested_filename', None)):
            suggested_filename = download.suggested_filename()
        else:
            # If suggested_filename is a property, access it directly
            suggested_filename = download.suggested_filename
        
        # Convert mindmap from PNG to JPEG if needed
        if artifact_type == "mind_map" and download_path:
            download_path_str = str(download_path)
            # Check if the file is PNG (or any image format) and convert to JPEG
            if os.path.exists(download_path_str):
                try:
                    # Open the image
                    img = Image.open(download_path_str)
                    
                    # Convert RGBA to RGB if necessary (JPEG doesn't support transparency)
                    if img.mode in ('RGBA', 'LA', 'P'):
                        # Create a white background
                        rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                        img = rgb_img
                    elif img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # Create new filename with .jpg extension
                    original_path = Path(download_path_str)
                    jpeg_path = original_path.with_suffix('.jpg')
                    
                    # Save as JPEG with high quality
                    img.save(str(jpeg_path), 'JPEG', quality=95, optimize=True)
                    
                    # Remove the original PNG file if it's different from the JPEG file
                    if jpeg_path != original_path:
                        try:
                            os.remove(download_path_str)
                        except Exception:
                            # If removal fails, continue anyway
                            pass
                    
                    # Update download_path and filename to point to JPEG
                    download_path = str(jpeg_path)
                    
                    # Update suggested filename to use .jpg extension
                    if suggested_filename:
                        filename_path = Path(suggested_filename)
                        suggested_filename = str(filename_path.with_suffix('.jpg'))
                    else:
                        suggested_filename = f"{artifact_name}.jpg"
                except Exception as exc:
                    # If conversion fails, log but continue with original file
                    # This ensures the download still works even if conversion fails
                    pass
        
        return {
            "status": "success",
            "message": f"Download completed for {artifact_name}.",
            "download_path": str(download_path) if download_path else None,
            "filename": str(suggested_filename) if suggested_filename else None,
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to download artifact: {exc}") from exc
