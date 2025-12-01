"""Video overview operations for NotebookLM automation."""

import re
from typing import Any, Dict, List

from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.automation.tasks.notebooklm.exceptions import NotebookLMError


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
            audio_indicator = (
                page.locator("div").filter(has_text="audio_magic_eraser Audio").nth(5)
            )
            await audio_indicator.wait_for(timeout=30_000, state="visible")
        except PlaywrightTimeoutError:
            # Fallback: wait for the create artifact buttons container
            try:
                buttons_container = page.locator(
                    "div.create-artifact-buttons-container"
                )
                await buttons_container.wait_for(timeout=30_000, state="visible")
            except PlaywrightTimeoutError:
                # Page might be ready even without visible content
                await page.wait_for_timeout(2_000)

        # Check if Video Overview button is visible (it should be in studio-panel)
        try:
            video_overview_button = page.locator("studio-panel").get_by_role(
                "button", name="Video Overview"
            )
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
                video_button = page.get_by_role(
                    "button", name=re.compile(r"Create artifact.*Video", re.IGNORECASE)
                )
                await video_button.wait_for(timeout=10_000, state="visible")
                await video_button.click()
            except PlaywrightTimeoutError:
                # Strategy 3: Find div with role="button" containing "Video Overview" text
                try:
                    video_button = page.locator("div[role='button']").filter(
                        has_text="Video Overview"
                    )
                    await video_button.wait_for(timeout=10_000, state="visible")
                    await video_button.click()
                except PlaywrightTimeoutError:
                    # Strategy 4: Find by the create-artifact-button-container class with Video Overview text
                    try:
                        video_button = page.locator(
                            "div.create-artifact-button-container"
                        ).filter(has_text="Video Overview")
                        await video_button.wait_for(timeout=10_000, state="visible")
                        await video_button.click()
                    except PlaywrightTimeoutError:
                        # Strategy 5: Find by role and accessible name
                        try:
                            video_button = page.get_by_role(
                                "button", name="Video Overview"
                            )
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
                has_text=re.compile(
                    r"^sync Generating Video Overview\.\.\. This may take a while$"
                )
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
        raise NotebookLMError(
            f"Failed to create video overview for NotebookLM notebook: {exc}"
        ) from exc
