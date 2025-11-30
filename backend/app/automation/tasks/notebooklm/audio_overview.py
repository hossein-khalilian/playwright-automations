"""Audio overview operations for NotebookLM automation."""

import re
from typing import Any, Dict, Optional

from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.automation.tasks.notebooklm.exceptions import NotebookLMError
from app.automation.tasks.notebooklm.helpers import close_dialogs, navigate_to_notebook


async def _find_audio_overview_button(page: Page) -> Optional[Any]:
    """
    Helper function to find the audio overview button on the page.
    Returns the button locator if found, None otherwise.
    """
    try:
        # Look for buttons that have a "More" button nearby (indicating they're artifacts)
        # Audio overview buttons are typically visible buttons with text
        buttons = page.locator("button")
        button_count = await buttons.count()

        for i in range(button_count):
            try:
                button = buttons.nth(i)
                button_text = await button.inner_text()
                
                # Skip empty buttons or buttons that are clearly not audio overviews
                if not button_text or len(button_text.strip()) == 0:
                    continue
                
                # Skip the "Create artifact" buttons
                if "Create artifact" in button_text:
                    continue
                
                # Check if this button has a "More" button nearby (indicating it's an artifact)
                # The More button is typically a sibling or in the same container
                try:
                    # Try to find More button in the parent container
                    parent = button.locator("xpath=..")
                    more_button = parent.get_by_label("More")
                    if await more_button.count() > 0:
                        return button
                except Exception:
                    # Try alternative approach - look for More button near this button
                    try:
                        more_button = page.get_by_label("More").filter(
                            has=button
                        )
                        if await more_button.count() > 0:
                            return button
                    except Exception:
                        continue
            except Exception:
                continue
        
        return None
    except Exception:
        return None


async def create_audio_overview(page: Page, notebook_id: str) -> Dict[str, str]:
    """
    Creates an audio overview for a notebook in NotebookLM.

    Args:
        page: The Playwright Page object to use for automation
        notebook_id: The ID of the notebook to create audio overview for

    Returns:
        Dictionary with status and message

    Raises:
        NotebookLMError: If creating audio overview fails
    """
    try:
        # Navigate directly to the notebook page
        await page.goto(f"https://notebooklm.google.com/notebook/{notebook_id}")

        # Wait for the create artifact buttons container to be visible
        # This ensures the page has fully loaded before attempting to click the button
        try:
            buttons_container = page.locator("div.create-artifact-buttons-container")
            await buttons_container.wait_for(timeout=30_000, state="visible")
        except PlaywrightTimeoutError:
            # Fallback: wait for any audio-related content
            try:
                audio_content = page.locator("div").filter(has_text=re.compile(r"Audio Overview", re.IGNORECASE))
                await audio_content.wait_for(timeout=10_000, state="visible")
            except PlaywrightTimeoutError:
                # Page might be ready even without visible content
                await page.wait_for_timeout(2_000)

        # Click on the Audio Overview button
        # The button is a div with role="button" containing "Audio Overview" text
        # It's inside a basic-create-artifact-button component within create-artifact-buttons-container
        try:
            # Strategy 1: Find div with role="button" containing "Audio Overview" text
            # This is the most reliable since the text is nested in spans
            audio_button = page.locator("div[role='button']").filter(has_text="Audio Overview")
            await audio_button.wait_for(timeout=10_000, state="visible")
            await audio_button.click()
        except PlaywrightTimeoutError:
            # Strategy 2: Find by the create-artifact-button-container class with Audio Overview text
            try:
                audio_button = page.locator("div.create-artifact-button-container").filter(has_text="Audio Overview")
                await audio_button.wait_for(timeout=10_000, state="visible")
                await audio_button.click()
            except PlaywrightTimeoutError:
                # Strategy 3: Find by role and accessible name (may not work if text is nested)
                try:
                    audio_button = page.get_by_role("button", name="Audio Overview")
                    await audio_button.wait_for(timeout=10_000, state="visible")
                    await audio_button.click()
                except PlaywrightTimeoutError as exc:
                    raise NotebookLMError(
                        "Could not find the 'Audio Overview' button. "
                        "The notebook page may not have loaded correctly."
                    ) from exc

        # Wait for the generation message to appear
        try:
            generating_message = page.locator("div").filter(
                has_text=re.compile(r"^sync Generating Audio Overview\.\.\. Come back in a few minutes$")
            )
            await generating_message.wait_for(timeout=10_000, state="visible")
        except PlaywrightTimeoutError:
            # Message might not appear immediately, which is fine
            pass

        return {
            "status": "success",
            "message": f"Audio overview creation started for notebook {notebook_id}. "
            "The audio overview is being generated and will be available in a few minutes.",
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to create audio overview for NotebookLM notebook: {exc}") from exc


async def get_audio_overview_status(page: Page, notebook_id: str) -> Dict[str, Any]:
    """
    Gets the status of the audio overview for a notebook.

    Args:
        page: The Playwright Page object to use for automation
        notebook_id: The ID of the notebook to check audio overview status for

    Returns:
        Dictionary with status, message, and audio overview info if available

    Raises:
        NotebookLMError: If getting audio overview status fails
    """
    try:
        # Navigate directly to the notebook page
        await navigate_to_notebook(page, notebook_id)

        # Close any dialogs that might appear
        await close_dialogs(page)

        # Wait for the page to be ready
        await page.wait_for_timeout(1_000)

        # Check if there's a generating message
        try:
            generating_message = page.locator("div").filter(
                has_text=re.compile(r"Generating Audio Overview")
            )
            if await generating_message.count() > 0:
                return {
                    "status": "success",
                    "message": "Audio overview is currently being generated.",
                    "is_generating": True,
                    "audio_name": None,
                }
        except Exception:
            pass

        # Look for existing audio overview button
        audio_button = await _find_audio_overview_button(page)

        if audio_button:
            try:
                audio_name = await audio_button.inner_text()
                audio_name = audio_name.strip() if audio_name else None
            except Exception:
                audio_name = None

            if audio_name:
                return {
                    "status": "success",
                    "message": f"Audio overview found: {audio_name}",
                    "is_generating": False,
                    "audio_name": audio_name,
                }
        else:
            return {
                "status": "success",
                "message": "No audio overview found for this notebook.",
                "is_generating": False,
                "audio_name": None,
            }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to get audio overview status from NotebookLM notebook: {exc}") from exc


async def rename_audio_overview(
    page: Page, notebook_id: str, new_name: str
) -> Dict[str, str]:
    """
    Renames an audio overview in a notebook.

    Args:
        page: The Playwright Page object to use for automation
        notebook_id: The ID of the notebook
        new_name: The new name for the audio overview

    Returns:
        Dictionary with status and message

    Raises:
        NotebookLMError: If renaming audio overview fails
    """
    try:
        # Navigate directly to the notebook page
        await navigate_to_notebook(page, notebook_id)

        # Close any dialogs that might appear
        await close_dialogs(page)

        # Wait for the page to be ready
        await page.wait_for_timeout(1_000)

        # Find the audio overview button
        audio_button = await _find_audio_overview_button(page)

        if not audio_button:
            raise NotebookLMError(
                "Could not find the audio overview. "
                "Please ensure an audio overview exists for this notebook."
            )

        # Click the "More" button for the audio overview
        more_button = audio_button.locator("..").get_by_label("More")
        await more_button.wait_for(timeout=5_000)
        await more_button.click()

        # Wait for the menu to appear
        await page.wait_for_timeout(500)

        # Click on "Rename" menuitem
        try:
            rename_menuitem = page.get_by_role("menuitem", name="Rename")
            await rename_menuitem.wait_for(timeout=5_000)
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
            textbox = audio_button.get_by_role("textbox")
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
                "The rename dialog may not have appeared correctly."
            ) from exc

        # Wait for the rename to complete
        await page.wait_for_timeout(1_000)

        return {
            "status": "success",
            "message": f"Audio overview renamed to '{new_name}' successfully.",
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to rename audio overview: {exc}") from exc


async def download_audio_overview(page: Page, notebook_id: str) -> Dict[str, Any]:
    """
    Downloads an audio overview from a notebook.

    Args:
        page: The Playwright Page object to use for automation
        notebook_id: The ID of the notebook

    Returns:
        Dictionary with status, message, and download info

    Raises:
        NotebookLMError: If downloading audio overview fails
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

        # Find the audio overview in the artifact library
        # Look for artifact library item with audio icon (audio_magic_eraser)
        try:
            # Strategy 1: Find the artifact button that contains the audio icon
            # The audio icon text is "audio_magic_eraser"
            audio_buttons = page.locator("button.artifact-button-content")
            button_count = await audio_buttons.count()
            
            audio_artifact = None
            for i in range(button_count):
                button = audio_buttons.nth(i)
                # Check if this button contains the audio icon
                icon = button.locator("mat-icon").filter(has_text=re.compile(r"audio_magic_eraser", re.IGNORECASE))
                if await icon.count() > 0:
                    audio_artifact = button
                    break
            
            if not audio_artifact:
                raise PlaywrightTimeoutError("Audio artifact button not found")
            
            await audio_artifact.wait_for(timeout=5_000, state="visible")
        except (PlaywrightTimeoutError, Exception):
            # Fallback: Find the artifact-library-item directly
            try:
                # Find all artifact items and check which one has the audio icon
                artifact_items = page.locator("artifact-library-item")
                item_count = await artifact_items.count()
                
                audio_artifact = None
                for i in range(item_count):
                    item = artifact_items.nth(i)
                    icon = item.locator("mat-icon").filter(has_text=re.compile(r"audio_magic_eraser", re.IGNORECASE))
                    if await icon.count() > 0:
                        audio_artifact = item
                        break
                
                if not audio_artifact:
                    raise PlaywrightTimeoutError("Audio artifact item not found")
                
                await audio_artifact.wait_for(timeout=5_000, state="visible")
            except PlaywrightTimeoutError as exc:
                raise NotebookLMError(
                    "Could not find the audio overview in the artifact library. "
                    "Please ensure an audio overview exists for this notebook."
                ) from exc

        # Find the "More" button within the audio artifact item
        # The More button is in the same artifact-library-item as the artifact button
        try:
            # Get the parent artifact-library-item if audio_artifact is a button
            try:
                artifact_item = audio_artifact.locator("xpath=ancestor::artifact-library-item").first
                # Check if we found the parent
                if await artifact_item.count() == 0:
                    artifact_item = audio_artifact
            except Exception:
                artifact_item = audio_artifact
            
            # The More button is within the artifact item, with aria-label="More"
            more_button = artifact_item.get_by_label("More")
            await more_button.wait_for(timeout=10_000, state="visible")
        except PlaywrightTimeoutError:
            # Fallback: find by class
            try:
                try:
                    artifact_item = audio_artifact.locator("xpath=ancestor::artifact-library-item").first
                    if await artifact_item.count() == 0:
                        artifact_item = audio_artifact
                except Exception:
                    artifact_item = audio_artifact
                
                more_button = artifact_item.locator("button.artifact-more-button")
                await more_button.wait_for(timeout=10_000, state="visible")
            except PlaywrightTimeoutError as exc:
                raise NotebookLMError(
                    "Could not find the 'More' button for the audio overview. "
                    "The artifact may not be fully loaded."
                ) from exc

        # Click the More button
        await more_button.click()

        # Wait for the menu to appear and be ready
        await page.wait_for_timeout(1_500)

        # Set up download listener
        async with page.expect_download() as download_info:
            # Click on "Download" menuitem
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

        # Get the download
        download = await download_info.value

        # Get download path and convert to string
        download_path = await download.path()
        download_path_str = str(download_path) if download_path else None

        return {
            "status": "success",
            "message": "Audio overview download initiated successfully.",
            "download_path": download_path_str,
            "suggested_filename": download.suggested_filename,
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to download audio overview: {exc}") from exc


async def delete_audio_overview(page: Page, notebook_id: str) -> Dict[str, str]:
    """
    Deletes an audio overview from a notebook.

    Args:
        page: The Playwright Page object to use for automation
        notebook_id: The ID of the notebook

    Returns:
        Dictionary with status and message

    Raises:
        NotebookLMError: If deleting audio overview fails
    """
    try:
        # Navigate directly to the notebook page
        await navigate_to_notebook(page, notebook_id)

        # Close any dialogs that might appear
        await close_dialogs(page)

        # Wait for the page to be ready
        await page.wait_for_timeout(1_000)

        # Find the audio overview button
        audio_button = await _find_audio_overview_button(page)

        if not audio_button:
            raise NotebookLMError(
                "Could not find the audio overview. "
                "Please ensure an audio overview exists for this notebook."
            )

        # Find the "More" button for this audio overview
        try:
            more_button = audio_button.locator("xpath=..").get_by_label("More")
            if await more_button.count() == 0:
                more_button = page.get_by_label("More").first
        except Exception:
            more_button = page.get_by_label("More").first

        await more_button.wait_for(timeout=5_000)
        await more_button.click()

        # Wait for the menu to appear
        await page.wait_for_timeout(500)

        # Click on "Delete" menuitem
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
            "message": f"Audio overview deleted successfully from notebook {notebook_id}.",
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to delete audio overview: {exc}") from exc

