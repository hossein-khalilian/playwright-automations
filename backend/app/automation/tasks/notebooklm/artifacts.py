"""Sync artifact management operations for NotebookLM automation."""

import re
from typing import Any, Dict, List, Optional

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
