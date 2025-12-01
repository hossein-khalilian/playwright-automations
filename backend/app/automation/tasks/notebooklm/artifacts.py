"""Artifact listing operations for NotebookLM automation."""

import re
from typing import Any, Dict, List, Optional

from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.automation.tasks.notebooklm.exceptions import NotebookLMError
from app.automation.tasks.notebooklm.helpers import close_dialogs, navigate_to_notebook

# Mapping of icon names to artifact types
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


async def list_artifacts(page: Page, notebook_id: str) -> Dict[str, Any]:
    """
    Lists all artifacts (materials) in a notebook with their status.

    Args:
        page: The Playwright Page object to use for automation
        notebook_id: The ID of the notebook to list artifacts for

    Returns:
        Dictionary with status, message, and list of artifacts

    Raises:
        NotebookLMError: If listing artifacts fails
    """
    try:
        # Navigate directly to the notebook page
        await navigate_to_notebook(page, notebook_id)

        # Close any dialogs that might appear
        await close_dialogs(page)

        # Wait for the artifact library to be ready
        try:
            artifact_library = page.locator("div.artifact-library-container")
            await artifact_library.wait_for(timeout=30_000, state="visible")
        except PlaywrightTimeoutError:
            # Wait a bit more and continue
            await page.wait_for_timeout(2_000)

        # Check for generating messages first
        generating_messages = []
        try:
            generating_divs = page.locator("div").filter(
                has_text=re.compile(r"Generating.*Overview", re.IGNORECASE)
            )
            div_count = await generating_divs.count()
            for i in range(div_count):
                try:
                    div = generating_divs.nth(i)
                    text = await div.inner_text()
                    if text and "Generating" in text:
                        generating_messages.append(text.strip())
                except Exception:
                    continue
        except Exception:
            pass

        artifacts = []

        # Find all artifact-library-item elements
        artifact_items = artifact_library.locator("artifact-library-item")
        item_count = await artifact_items.count()

        for i in range(item_count):
            try:
                artifact_item = artifact_items.nth(i)
                
                # Get the artifact button
                artifact_button = artifact_item.locator("button.artifact-button-content").first
                if await artifact_button.count() == 0:
                    continue

                # Extract artifact type from icon
                artifact_type = None
                icon_element = artifact_item.locator("mat-icon.artifact-icon").first
                if await icon_element.count() > 0:
                    icon_text = await icon_element.inner_text()
                    icon_text = icon_text.strip() if icon_text else ""
                    # Map icon to type
                    for icon_name, type_name in ICON_TO_TYPE.items():
                        if icon_name in icon_text:
                            artifact_type = type_name
                            break
                    if not artifact_type:
                        artifact_type = icon_text if icon_text else "unknown"

                # Extract artifact name/title
                artifact_name = None
                title_element = artifact_button.locator("span.artifact-title").first
                if await title_element.count() > 0:
                    artifact_name = await title_element.inner_text()
                    artifact_name = artifact_name.strip() if artifact_name else None

                # Extract details (source count, time ago)
                details = None
                details_element = artifact_button.locator("span.artifact-details").first
                if await details_element.count() > 0:
                    details = await details_element.inner_text()
                    details = details.strip() if details else None

                # Determine status based on available actions
                status = "ready"
                is_generating = False
                
                # Check if there's a Play button (indicates ready)
                play_button = artifact_button.locator('button[aria-label="Play"]')
                has_play = await play_button.count() > 0
                
                # Check if there's an Interactive mode button
                interactive_button = artifact_button.locator('button[aria-label="Interactive mode"]')
                has_interactive = await interactive_button.count() > 0

                # Check if this artifact is mentioned in generating messages
                if artifact_name:
                    for gen_msg in generating_messages:
                        if artifact_name.lower() in gen_msg.lower() or artifact_type in gen_msg.lower():
                            is_generating = True
                            status = "generating"
                            break

                if not has_play and not has_interactive and not is_generating:
                    # Might be incomplete or error state
                    status = "unknown"

                artifacts.append({
                    "type": artifact_type,
                    "name": artifact_name,
                    "details": details,
                    "status": status,
                    "is_generating": is_generating,
                    "has_play": has_play,
                    "has_interactive": has_interactive,
                })
            except Exception:
                # Skip this artifact if there's an error
                continue

        # Also check for artifact-library-note elements (mind maps as notes)
        artifact_notes = artifact_library.locator("artifact-library-note")
        note_count = await artifact_notes.count()

        for i in range(note_count):
            try:
                artifact_note = artifact_notes.nth(i)
                
                # Get the artifact button
                artifact_button = artifact_note.locator("button.artifact-button-content").first
                if await artifact_button.count() == 0:
                    continue

                # Extract artifact type from icon
                artifact_type = None
                icon_element = artifact_note.locator("mat-icon.artifact-icon").first
                if await icon_element.count() > 0:
                    icon_text = await icon_element.inner_text()
                    icon_text = icon_text.strip() if icon_text else ""
                    for icon_name, type_name in ICON_TO_TYPE.items():
                        if icon_name in icon_text:
                            artifact_type = type_name
                            break
                    if not artifact_type:
                        artifact_type = icon_text if icon_text else "note"

                # Extract artifact name/title
                artifact_name = None
                title_element = artifact_button.locator("span.artifact-title").first
                if await title_element.count() > 0:
                    artifact_name = await title_element.inner_text()
                    artifact_name = artifact_name.strip() if artifact_name else None

                # Extract details
                details = None
                details_element = artifact_button.locator("span.artifact-details").first
                if await details_element.count() > 0:
                    details = await details_element.inner_text()
                    details = details.strip() if details else None

                # Notes are typically ready
                status = "ready"
                is_generating = False
                
                play_button = artifact_button.locator('button[aria-label="Play"]')
                has_play = await play_button.count() > 0
                
                interactive_button = artifact_button.locator('button[aria-label="Interactive mode"]')
                has_interactive = await interactive_button.count() > 0

                artifacts.append({
                    "type": artifact_type or "note",
                    "name": artifact_name,
                    "details": details,
                    "status": status,
                    "is_generating": is_generating,
                    "has_play": has_play,
                    "has_interactive": has_interactive,
                })
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
        raise NotebookLMError(f"Failed to list artifacts from NotebookLM notebook: {exc}") from exc


async def delete_artifact(page: Page, notebook_id: str, artifact_name: str) -> Dict[str, str]:
    """
    Deletes an artifact from a notebook.

    Args:
        page: The Playwright Page object to use for automation
        notebook_id: The ID of the notebook
        artifact_name: The name/title of the artifact to delete

    Returns:
        Dictionary with status and message

    Raises:
        NotebookLMError: If deleting artifact fails
    """
    try:
        # Navigate directly to the notebook page
        await navigate_to_notebook(page, notebook_id)

        # Close any dialogs that might appear
        await close_dialogs(page)

        # Wait for the artifact library to be ready
        try:
            artifact_library = page.locator("div.artifact-library-container")
            await artifact_library.wait_for(timeout=30_000, state="visible")
        except PlaywrightTimeoutError:
            await page.wait_for_timeout(2_000)

        # Find the artifact by name
        # Try to match by artifact title first, then fall back to full button text
        artifact_button = None
        artifact_item = None
        
        try:
            # Get all artifact buttons
            artifact_items = artifact_library.locator("artifact-library-item")
            artifact_notes = artifact_library.locator("artifact-library-note")
            
            item_count = await artifact_items.count()
            note_count = await artifact_notes.count()
            
            # Check artifact-library-item elements
            for i in range(item_count):
                try:
                    item = artifact_items.nth(i)
                    button = item.locator("button.artifact-button-content").first
                    if await button.count() == 0:
                        continue
                    
                    # First, try to match by artifact title (more precise)
                    title_element = button.locator("span.artifact-title").first
                    if await title_element.count() > 0:
                        title_text = await title_element.inner_text()
                        title_text = title_text.strip() if title_text else ""
                        if title_text == artifact_name or artifact_name in title_text:
                            artifact_button = button
                            artifact_item = item
                            break
                    
                    # Fallback: check full button text (includes name and details)
                    button_text = await button.inner_text()
                    button_text = button_text.strip() if button_text else ""
                    if artifact_name in button_text:
                        artifact_button = button
                        artifact_item = item
                        break
                except Exception:
                    continue
            
            # If not found, check artifact-library-note elements
            if not artifact_button:
                for i in range(note_count):
                    try:
                        note = artifact_notes.nth(i)
                        button = note.locator("button.artifact-button-content").first
                        if await button.count() == 0:
                            continue
                        
                        # First, try to match by artifact title
                        title_element = button.locator("span.artifact-title").first
                        if await title_element.count() > 0:
                            title_text = await title_element.inner_text()
                            title_text = title_text.strip() if title_text else ""
                            if title_text == artifact_name or artifact_name in title_text:
                                artifact_button = button
                                artifact_item = note
                                break
                        
                        # Fallback: check full button text
                        button_text = await button.inner_text()
                        button_text = button_text.strip() if button_text else ""
                        if artifact_name in button_text:
                            artifact_button = button
                            artifact_item = note
                            break
                    except Exception:
                        continue
            
            if not artifact_button or not artifact_item:
                raise NotebookLMError(
                    f"Could not find artifact with name '{artifact_name}'. "
                    "Please ensure the artifact exists for this notebook."
                )
        except NotebookLMError:
            raise
        except Exception as exc:
            raise NotebookLMError(
                f"Error finding artifact '{artifact_name}': {exc}"
            ) from exc

        # Find and click the "More" button
        more_button = artifact_item.get_by_label("More")
        await more_button.wait_for(timeout=10_000, state="visible")
        await more_button.click()

        # Wait for the menu to appear
        await page.wait_for_timeout(500)

        # Click on "Delete" menuitem
        try:
            delete_menuitem = page.get_by_role("menuitem", name="Delete")
            await delete_menuitem.wait_for(timeout=5_000, state="visible")
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
            await confirm_button.wait_for(timeout=5_000, state="visible")
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
            "message": f"Artifact '{artifact_name}' deleted successfully from notebook {notebook_id}.",
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to delete artifact: {exc}") from exc


async def rename_artifact(
    page: Page, notebook_id: str, artifact_name: str, new_name: str
) -> Dict[str, str]:
    """
    Renames an audio or video overview artifact in a notebook.

    Args:
        page: The Playwright Page object to use for automation
        notebook_id: The ID of the notebook
        artifact_name: The current name/title of the artifact to rename
        new_name: The new name for the artifact

    Returns:
        Dictionary with status and message

    Raises:
        NotebookLMError: If renaming the artifact fails
    """
    try:
        # Navigate directly to the notebook page
        await navigate_to_notebook(page, notebook_id)

        # Close any dialogs that might appear
        await close_dialogs(page)

        # Wait for the artifact library to be ready
        try:
            artifact_library = page.locator("div.artifact-library-container")
            await artifact_library.wait_for(timeout=30_000, state="visible")
        except PlaywrightTimeoutError:
            await page.wait_for_timeout(2_000)

        # Find the artifact by name (audio or video only)
        artifact_button = None
        artifact_item = None
        artifact_type = None

        try:
            artifact_items = artifact_library.locator("artifact-library-item")
            item_count = await artifact_items.count()

            # Check artifact-library-item elements
            for i in range(item_count):
                try:
                    item = artifact_items.nth(i)
                    button = item.locator("button.artifact-button-content").first
                    if await button.count() == 0:
                        continue

                    # Get artifact type from icon
                    icon_element = item.locator("mat-icon.artifact-icon").first
                    if await icon_element.count() > 0:
                        icon_text = await icon_element.inner_text()
                        icon_text = icon_text.strip() if icon_text else ""
                        # Only support audio/video artifacts here
                        if "audio_magic_eraser" in icon_text:
                            artifact_type = "audio_overview"
                        elif "subscriptions" in icon_text:
                            artifact_type = "video_overview"
                        else:
                            continue

                    # First, try to match by artifact title (more precise)
                    title_element = button.locator("span.artifact-title").first
                    if await title_element.count() > 0:
                        title_text = await title_element.inner_text()
                        title_text = title_text.strip() if title_text else ""
                        if title_text == artifact_name or artifact_name in title_text:
                            artifact_button = button
                            artifact_item = item
                            break

                    # Fallback: check full button text (includes name and details)
                    button_text = await button.inner_text()
                    button_text = button_text.strip() if button_text else ""
                    if artifact_name in button_text:
                        artifact_button = button
                        artifact_item = item
                        break
                except Exception:
                    continue

            if not artifact_button or not artifact_item:
                raise NotebookLMError(
                    f"Could not find audio or video artifact with name '{artifact_name}'. "
                    "Please ensure the artifact exists and is of type audio_overview or video_overview."
                )

            if not artifact_type:
                raise NotebookLMError(
                    f"Artifact '{artifact_name}' is not an audio or video overview. "
                    "Only audio_overview and video_overview artifacts can be renamed."
                )
        except NotebookLMError:
            raise
        except Exception as exc:
            raise NotebookLMError(
                f"Error finding artifact '{artifact_name}' to rename: {exc}"
            ) from exc

        # Find and click the "More" button
        more_button = artifact_item.get_by_label("More")
        await more_button.wait_for(timeout=10_000, state="visible")
        await more_button.click()

        # Wait for the menu to appear
        await page.wait_for_timeout(500)

        # Click on "Rename" menuitem
        try:
            rename_menuitem = page.get_by_role("menuitem", name="Rename")
            await rename_menuitem.wait_for(timeout=5_000, state="visible")
            await rename_menuitem.click()
        except PlaywrightTimeoutError as exc:
            raise NotebookLMError(
                "Could not find the 'Rename' menuitem. "
                "The menu may not have appeared correctly."
            ) from exc

        # Wait for the textbox to be ready
        await page.wait_for_timeout(500)

        # Find and edit the textbox
        try:
            textbox = artifact_item.get_by_role("textbox")
            if await textbox.count() == 0:
                textbox = artifact_button.get_by_role("textbox")

            textbox = textbox.first
            await textbox.wait_for(timeout=5_000)
            await textbox.dblclick()
            await textbox.click()
            # Select all and replace with new name
            await textbox.press("ControlOrMeta+a")
            await textbox.fill(new_name)
            await textbox.press("Enter")
        except PlaywrightTimeoutError as exc:
            raise NotebookLMError(
                "Could not find or edit the rename textbox. "
                "The rename UI may not have appeared correctly."
            ) from exc

        # Wait for the rename to complete
        await page.wait_for_timeout(1_000)

        return {
            "status": "success",
            "message": f"Artifact '{artifact_name}' renamed to '{new_name}' successfully.",
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to rename artifact: {exc}") from exc


async def download_artifact(page: Page, notebook_id: str, artifact_name: str) -> Dict[str, Any]:
    """
    Downloads an artifact (audio or video overview) from a notebook.

    Args:
        page: The Playwright Page object to use for automation
        notebook_id: The ID of the notebook
        artifact_name: The name/title of the artifact to download

    Returns:
        Dictionary with status, message, and download info

    Raises:
        NotebookLMError: If downloading artifact fails
    """
    try:
        # Navigate directly to the notebook page
        await navigate_to_notebook(page, notebook_id)

        # Close any dialogs that might appear
        await close_dialogs(page)

        # Wait for the artifact library to be ready
        try:
            artifact_library = page.locator("div.artifact-library-container")
            await artifact_library.wait_for(timeout=30_000, state="visible")
        except PlaywrightTimeoutError:
            await page.wait_for_timeout(2_000)

        # Find the artifact by name
        artifact_button = None
        artifact_item = None
        artifact_type = None
        
        try:
            # Get all artifact buttons
            artifact_items = artifact_library.locator("artifact-library-item")
            artifact_notes = artifact_library.locator("artifact-library-note")
            
            item_count = await artifact_items.count()
            note_count = await artifact_notes.count()
            
            # Check artifact-library-item elements
            for i in range(item_count):
                try:
                    item = artifact_items.nth(i)
                    button = item.locator("button.artifact-button-content").first
                    if await button.count() == 0:
                        continue
                    
                    # Get artifact type from icon
                    icon_element = item.locator("mat-icon.artifact-icon").first
                    if await icon_element.count() > 0:
                        icon_text = await icon_element.inner_text()
                        icon_text = icon_text.strip() if icon_text else ""
                        # Check if it's audio or video
                        if "audio_magic_eraser" in icon_text:
                            artifact_type = "audio_overview"
                        elif "subscriptions" in icon_text:
                            artifact_type = "video_overview"
                        else:
                            continue  # Skip non-audio/video artifacts
                    
                    # First, try to match by artifact title (more precise)
                    title_element = button.locator("span.artifact-title").first
                    if await title_element.count() > 0:
                        title_text = await title_element.inner_text()
                        title_text = title_text.strip() if title_text else ""
                        if title_text == artifact_name or artifact_name in title_text:
                            artifact_button = button
                            artifact_item = item
                            break
                    
                    # Fallback: check full button text (includes name and details)
                    button_text = await button.inner_text()
                    button_text = button_text.strip() if button_text else ""
                    if artifact_name in button_text:
                        artifact_button = button
                        artifact_item = item
                        break
                except Exception:
                    continue
            
            # If not found, check artifact-library-note elements (unlikely for audio/video, but just in case)
            if not artifact_button:
                for i in range(note_count):
                    try:
                        note = artifact_notes.nth(i)
                        button = note.locator("button.artifact-button-content").first
                        if await button.count() == 0:
                            continue
                        
                        # Get artifact type from icon
                        icon_element = note.locator("mat-icon.artifact-icon").first
                        if await icon_element.count() > 0:
                            icon_text = await icon_element.inner_text()
                            icon_text = icon_text.strip() if icon_text else ""
                            if "audio_magic_eraser" in icon_text:
                                artifact_type = "audio_overview"
                            elif "subscriptions" in icon_text:
                                artifact_type = "video_overview"
                            else:
                                continue
                        
                        # First, try to match by artifact title
                        title_element = button.locator("span.artifact-title").first
                        if await title_element.count() > 0:
                            title_text = await title_element.inner_text()
                            title_text = title_text.strip() if title_text else ""
                            if title_text == artifact_name or artifact_name in title_text:
                                artifact_button = button
                                artifact_item = note
                                break
                        
                        # Fallback: check full button text
                        button_text = await button.inner_text()
                        button_text = button_text.strip() if button_text else ""
                        if artifact_name in button_text:
                            artifact_button = button
                            artifact_item = note
                            break
                    except Exception:
                        continue
            
            if not artifact_button or not artifact_item:
                raise NotebookLMError(
                    f"Could not find audio or video artifact with name '{artifact_name}'. "
                    "Please ensure the artifact exists and is of type audio_overview or video_overview."
                )
            
            if not artifact_type:
                raise NotebookLMError(
                    f"Artifact '{artifact_name}' is not an audio or video overview. "
                    "Only audio_overview and video_overview artifacts can be downloaded."
                )
        except NotebookLMError:
            raise
        except Exception as exc:
            raise NotebookLMError(
                f"Error finding artifact '{artifact_name}': {exc}"
            ) from exc

        # Find and click the "More" button
        more_button = artifact_item.get_by_label("More")
        await more_button.wait_for(timeout=10_000, state="visible")
        await more_button.click()

        # Wait for the menu to appear and be ready
        await page.wait_for_timeout(1_500)

        # Set up download listener (video needs popup handling, audio doesn't)
        download_path_str = None
        suggested_filename = None
        
        try:
            if artifact_type == "video_overview":
                # Video downloads open a popup that needs to be closed
                async with page.expect_download() as download_info:
                    async with page.expect_popup() as popup_info:
                        # Click on "Download" menuitem
                        await _click_download_menuitem(page)
                    
                    # Wait for popup and close it
                    popup = await popup_info.value
                    await popup.close()
                
                # Get the download
                download = await download_info.value
            else:
                # Audio downloads don't need popup handling
                async with page.expect_download() as download_info:
                    # Click on "Download" menuitem
                    await _click_download_menuitem(page)
                
                # Get the download
                download = await download_info.value

            # Get download path and convert to string
            download_path = await download.path()
            download_path_str = str(download_path) if download_path else None
            suggested_filename = download.suggested_filename
        except Exception as exc:
            raise NotebookLMError(
                f"Failed to download artifact '{artifact_name}': {exc}"
            ) from exc

        return {
            "status": "success",
            "message": f"Artifact '{artifact_name}' download initiated successfully.",
            "download_path": download_path_str,
            "suggested_filename": suggested_filename,
            "artifact_type": artifact_type,
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to download artifact: {exc}") from exc


async def _click_download_menuitem(page: Page) -> None:
    """
    Helper function to click the Download menuitem with multiple fallback strategies.
    """
    try:
        # Strategy 1: Find by role and name
        download_menuitem = page.get_by_role("menuitem", name="Download")
        await download_menuitem.wait_for(timeout=10_000, state="visible")
        await download_menuitem.click()
    except PlaywrightTimeoutError:
        # Strategy 2: Find button with role="menuitem" containing Download text
        try:
            download_menuitem = page.locator("button[role='menuitem']").filter(has_text="Download")
            await download_menuitem.wait_for(timeout=10_000, state="visible")
            await download_menuitem.click()
        except PlaywrightTimeoutError:
            # Strategy 3: Find any button with Download text in mat-menu
            try:
                download_menuitem = page.locator("mat-menu button").filter(has_text="Download")
                await download_menuitem.wait_for(timeout=10_000, state="visible")
                await download_menuitem.click()
            except PlaywrightTimeoutError:
                # Strategy 4: Find in overlay panel (Material menus are often in overlays)
                try:
                    download_menuitem = page.locator(".cdk-overlay-pane button").filter(has_text="Download")
                    await download_menuitem.wait_for(timeout=10_000, state="visible")
                    await download_menuitem.click()
                except PlaywrightTimeoutError:
                    # Strategy 5: Find any visible button with Download text
                    try:
                        download_menuitem = page.locator("button:visible").filter(has_text=re.compile(r"Download", re.IGNORECASE))
                        await download_menuitem.wait_for(timeout=10_000, state="visible")
                        await download_menuitem.click()
                    except PlaywrightTimeoutError as exc:
                        raise NotebookLMError(
                            "Could not find the 'Download' menuitem. "
                            "The menu may not have appeared correctly."
                        ) from exc

