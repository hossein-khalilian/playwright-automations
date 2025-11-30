"""Video overview operations for NotebookLM automation."""

import re
from typing import Any, Dict, List, Optional

from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.automation.tasks.notebooklm.exceptions import NotebookLMError
from app.automation.tasks.notebooklm.helpers import close_dialogs, navigate_to_notebook


async def _find_video_overview_buttons(page: Page) -> List[Any]:
    """
    Helper function to find all video overview buttons on the page.
    Returns a list of button locators if found, empty list otherwise.
    """
    try:
        video_buttons = []
        # Look for buttons that have a "More" button nearby (indicating they're artifacts)
        buttons = page.locator("button")
        button_count = await buttons.count()

        for i in range(button_count):
            try:
                button = buttons.nth(i)
                button_text = await button.inner_text()
                
                # Skip empty buttons or buttons that are clearly not video overviews
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
                        # Check if this button has a Play button, which indicates it's a video
                        try:
                            play_button = button.get_by_label("Play")
                            if await play_button.count() > 0:
                                video_buttons.append(button)
                        except Exception:
                            # Try alternative approach - check if it's in a video container
                            try:
                                # Video artifacts typically have specific patterns
                                artifact_item = button.locator("xpath=ancestor::artifact-library-item").first
                                if await artifact_item.count() > 0:
                                    video_buttons.append(button)
                            except Exception:
                                pass
                except Exception:
                    # Try alternative approach - look for More button near this button
                    try:
                        more_button = page.get_by_label("More").filter(
                            has=button
                        )
                        if await more_button.count() > 0:
                            video_buttons.append(button)
                    except Exception:
                        continue
            except Exception:
                continue
        
        return video_buttons
    except Exception:
        return []


async def create_video_overview(page: Page, notebook_id: str) -> Dict[str, str]:
    """
    Creates a video overview for a notebook in NotebookLM.

    Args:
        page: The Playwright Page object to use for automation
        notebook_id: The ID of the notebook to create video overview for

    Returns:
        Dictionary with status and message

    Raises:
        NotebookLMError: If creating video overview fails
    """
    try:
        # Navigate directly to the notebook page
        await page.goto(f"https://notebooklm.google.com/notebook/{notebook_id}")

        # Wait for the audio artifact indicator (audio_magic_eraser Audio) to be visible
        # This indicates the page has loaded artifacts section
        try:
            audio_indicator = page.locator("div").filter(has_text="audio_magic_eraser Audio").nth(5)
            await audio_indicator.wait_for(timeout=30_000, state="visible")
        except PlaywrightTimeoutError:
            # Fallback: wait for the create artifact buttons container
            try:
                buttons_container = page.locator("div.create-artifact-buttons-container")
                await buttons_container.wait_for(timeout=30_000, state="visible")
            except PlaywrightTimeoutError:
                # Page might be ready even without visible content
                await page.wait_for_timeout(2_000)

        # Check if Video Overview button is visible (it should be in studio-panel)
        try:
            video_overview_button = page.locator("studio-panel").get_by_role("button", name="Video Overview")
            await video_overview_button.wait_for(timeout=10_000, state="visible")
        except PlaywrightTimeoutError:
            # Fallback: try to find the button without studio-panel
            pass

        # Click on the "Create artifact icon Video" button
        try:
            # Strategy 1: Find button with exact name "Create artifact icon Video"
            video_button = page.get_by_role("button", name="Create artifact icon Video")
            await video_button.wait_for(timeout=10_000, state="visible")
            await video_button.click()
        except PlaywrightTimeoutError:
            # Strategy 2: Find button with role="button" and name containing "Video"
            try:
                video_button = page.get_by_role("button", name=re.compile(r"Create artifact.*Video", re.IGNORECASE))
                await video_button.wait_for(timeout=10_000, state="visible")
                await video_button.click()
            except PlaywrightTimeoutError:
                # Strategy 3: Find div with role="button" containing "Video Overview" text
                try:
                    video_button = page.locator("div[role='button']").filter(has_text="Video Overview")
                    await video_button.wait_for(timeout=10_000, state="visible")
                    await video_button.click()
                except PlaywrightTimeoutError:
                    # Strategy 4: Find by the create-artifact-button-container class with Video Overview text
                    try:
                        video_button = page.locator("div.create-artifact-button-container").filter(has_text="Video Overview")
                        await video_button.wait_for(timeout=10_000, state="visible")
                        await video_button.click()
                    except PlaywrightTimeoutError:
                        # Strategy 5: Find by role and accessible name
                        try:
                            video_button = page.get_by_role("button", name="Video Overview")
                            await video_button.wait_for(timeout=10_000, state="visible")
                            await video_button.click()
                        except PlaywrightTimeoutError as exc:
                            raise NotebookLMError(
                                "Could not find the 'Video Overview' or 'Create artifact icon Video' button. "
                                "The notebook page may not have loaded correctly."
                            ) from exc

        # Wait for the generation message to appear
        try:
            generating_message = page.locator("div").filter(
                has_text=re.compile(r"^sync Generating Video Overview\.\.\. This may take a while$")
            )
            await generating_message.wait_for(timeout=10_000, state="visible")
        except PlaywrightTimeoutError:
            # Also check for alternative message format
            try:
                generating_message = page.locator("div").filter(
                    has_text=re.compile(r"Generating Video Overview", re.IGNORECASE)
                )
                await generating_message.wait_for(timeout=10_000, state="visible")
            except PlaywrightTimeoutError:
                # Message might not appear immediately, which is fine
                pass

        return {
            "status": "success",
            "message": f"Video overview creation started for notebook {notebook_id}. "
            "The video overview is being generated and will be available in a few minutes.",
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to create video overview for NotebookLM notebook: {exc}") from exc


async def get_video_overview_status(page: Page, notebook_id: str) -> Dict[str, Any]:
    """
    Gets the status of the video overview for a notebook.

    Args:
        page: The Playwright Page object to use for automation
        notebook_id: The ID of the notebook to check video overview status for

    Returns:
        Dictionary with status, message, and video overview info if available

    Raises:
        NotebookLMError: If getting video overview status fails
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
                has_text=re.compile(r"Generating Video Overview", re.IGNORECASE)
            )
            if await generating_message.count() > 0:
                return {
                    "status": "success",
                    "message": "Video overview is currently being generated.",
                    "is_generating": True,
                    "videos": [],
                }
        except Exception:
            pass

        # Look for existing video overview buttons
        video_buttons = await _find_video_overview_buttons(page)

        videos = []
        for video_button in video_buttons:
            try:
                video_name = await video_button.inner_text()
                video_name = video_name.strip() if video_name else None
                if video_name:
                    videos.append({"name": video_name})
            except Exception:
                pass

        if videos:
            return {
                "status": "success",
                "message": f"Found {len(videos)} video overview(s).",
                "is_generating": False,
                "videos": videos,
            }
        else:
            return {
                "status": "success",
                "message": "No video overview found for this notebook.",
                "is_generating": False,
                "videos": [],
            }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to get video overview status from NotebookLM notebook: {exc}") from exc


async def rename_video_overview(
    page: Page, notebook_id: str, video_name: str, new_name: str
) -> Dict[str, str]:
    """
    Renames a video overview in a notebook.

    Args:
        page: The Playwright Page object to use for automation
        notebook_id: The ID of the notebook
        video_name: The current name of the video overview to rename
        new_name: The new name for the video overview

    Returns:
        Dictionary with status and message

    Raises:
        NotebookLMError: If renaming video overview fails
    """
    try:
        # Navigate directly to the notebook page
        await navigate_to_notebook(page, notebook_id)

        # Close any dialogs that might appear
        await close_dialogs(page)

        # Wait for the page to be ready
        await page.wait_for_timeout(1_000)

        # Find the video overview button by name
        video_button = None
        video_buttons = await _find_video_overview_buttons(page)
        
        for btn in video_buttons:
            try:
                btn_text = await btn.inner_text()
                if btn_text and btn_text.strip() == video_name:
                    video_button = btn
                    break
            except Exception:
                continue

        if not video_button:
            raise NotebookLMError(
                f"Could not find the video overview '{video_name}'. "
                "Please ensure a video overview with this name exists for this notebook."
            )

        # Click the "More" button for the video overview
        try:
            # Find the More button in the same container as the video button
            artifact_item = video_button.locator("xpath=ancestor::artifact-library-item").first
            if await artifact_item.count() == 0:
                artifact_item = video_button.locator("xpath=..")
            
            more_button = artifact_item.get_by_label("More")
            await more_button.wait_for(timeout=5_000)
            await more_button.click()
        except PlaywrightTimeoutError:
            # Fallback: try to find More button directly
            more_button = page.get_by_label("More").first
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
            textbox = video_button.get_by_role("textbox")
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
            "message": f"Video overview '{video_name}' renamed to '{new_name}' successfully.",
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to rename video overview: {exc}") from exc


async def download_video_overview(
    page: Page, notebook_id: str, video_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Downloads a video overview from a notebook.

    Args:
        page: The Playwright Page object to use for automation
        notebook_id: The ID of the notebook
        video_name: Optional name of the specific video to download. If None, downloads the first video.

    Returns:
        Dictionary with status, message, and download info

    Raises:
        NotebookLMError: If downloading video overview fails
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

        # Find the video overview button
        video_button = None
        video_buttons = await _find_video_overview_buttons(page)
        
        if not video_buttons:
            raise NotebookLMError(
                "Could not find any video overviews in the artifact library. "
                "Please ensure a video overview exists for this notebook."
            )

        # If video_name is specified, find that specific video
        if video_name:
            for btn in video_buttons:
                try:
                    btn_text = await btn.inner_text()
                    if btn_text and btn_text.strip() == video_name:
                        video_button = btn
                        break
                except Exception:
                    continue
            
            if not video_button:
                raise NotebookLMError(
                    f"Could not find the video overview '{video_name}'. "
                    "Please ensure a video overview with this name exists for this notebook."
                )
        else:
            # Use the first video found
            video_button = video_buttons[0]

        # Wait for the video button to be visible
        await video_button.wait_for(timeout=5_000, state="visible")

        # Find the "More" button within the video artifact item
        try:
            # Get the parent artifact-library-item if video_button is a button
            try:
                artifact_item = video_button.locator("xpath=ancestor::artifact-library-item").first
                # Check if we found the parent
                if await artifact_item.count() == 0:
                    artifact_item = video_button.locator("xpath=..")
            except Exception:
                artifact_item = video_button.locator("xpath=..")
            
            # The More button is within the artifact item, with aria-label="More"
            more_button = artifact_item.get_by_label("More")
            await more_button.wait_for(timeout=10_000, state="visible")
        except PlaywrightTimeoutError:
            # Fallback: find by class
            try:
                try:
                    artifact_item = video_button.locator("xpath=ancestor::artifact-library-item").first
                    if await artifact_item.count() == 0:
                        artifact_item = video_button.locator("xpath=..")
                except Exception:
                    artifact_item = video_button.locator("xpath=..")
                
                more_button = artifact_item.locator("button.artifact-more-button")
                await more_button.wait_for(timeout=10_000, state="visible")
            except PlaywrightTimeoutError as exc:
                raise NotebookLMError(
                    "Could not find the 'More' button for the video overview. "
                    "The artifact may not be fully loaded."
                ) from exc

        # Click the More button
        await more_button.click()

        # Wait for the menu to appear and be ready
        await page.wait_for_timeout(1_500)

        # Set up download listener and popup handler
        download_path_str = None
        suggested_filename = None
        
        try:
            async with page.expect_download() as download_info:
                async with page.expect_popup() as popup_info:
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

                # Wait for popup and close it
                popup = await popup_info.value
                await popup.close()

            # Get the download
            download = await download_info.value

            # Get download path and convert to string
            download_path = await download.path()
            download_path_str = str(download_path) if download_path else None
            suggested_filename = download.suggested_filename
        except Exception as exc:
            raise NotebookLMError(
                f"Failed to download video overview: {exc}"
            ) from exc

        return {
            "status": "success",
            "message": "Video overview download initiated successfully.",
            "download_path": download_path_str,
            "suggested_filename": suggested_filename,
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to download video overview: {exc}") from exc


async def delete_video_overview(
    page: Page, notebook_id: str, video_name: Optional[str] = None
) -> Dict[str, str]:
    """
    Deletes a video overview from a notebook.

    Args:
        page: The Playwright Page object to use for automation
        notebook_id: The ID of the notebook
        video_name: Optional name of the specific video to delete. If None, deletes the first video.

    Returns:
        Dictionary with status and message

    Raises:
        NotebookLMError: If deleting video overview fails
    """
    try:
        # Navigate directly to the notebook page
        await navigate_to_notebook(page, notebook_id)

        # Close any dialogs that might appear
        await close_dialogs(page)

        # Wait for the page to be ready
        await page.wait_for_timeout(1_000)

        # Find the video overview button
        video_button = None
        video_buttons = await _find_video_overview_buttons(page)
        
        if not video_buttons:
            raise NotebookLMError(
                "Could not find any video overviews. "
                "Please ensure a video overview exists for this notebook."
            )

        # If video_name is specified, find that specific video
        if video_name:
            for btn in video_buttons:
                try:
                    btn_text = await btn.inner_text()
                    if btn_text and btn_text.strip() == video_name:
                        video_button = btn
                        break
                except Exception:
                    continue
            
            if not video_button:
                raise NotebookLMError(
                    f"Could not find the video overview '{video_name}'. "
                    "Please ensure a video overview with this name exists for this notebook."
                )
        else:
            # Use the first video found
            video_button = video_buttons[0]

        # Find the "More" button for this video overview
        try:
            artifact_item = video_button.locator("xpath=ancestor::artifact-library-item").first
            if await artifact_item.count() == 0:
                artifact_item = video_button.locator("xpath=..")
            
            more_button = artifact_item.get_by_label("More")
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

        video_display_name = video_name or "video overview"
        return {
            "status": "success",
            "message": f"Video overview '{video_display_name}' deleted successfully from notebook {notebook_id}.",
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to delete video overview: {exc}") from exc

