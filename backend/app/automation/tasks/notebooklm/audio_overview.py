"""Audio overview operations for NotebookLM automation."""

import re
from typing import Dict

from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.automation.tasks.notebooklm.exceptions import NotebookLMError


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
                audio_content = page.locator("div").filter(
                    has_text=re.compile(r"Audio Overview", re.IGNORECASE)
                )
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
            audio_button = page.locator("div[role='button']").filter(
                has_text="Audio Overview"
            )
            await audio_button.wait_for(timeout=10_000, state="visible")
            await audio_button.click()
        except PlaywrightTimeoutError:
            # Strategy 2: Find by the create-artifact-button-container class with Audio Overview text
            try:
                audio_button = page.locator(
                    "div.create-artifact-button-container"
                ).filter(has_text="Audio Overview")
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
                has_text=re.compile(
                    r"^sync Generating Audio Overview\.\.\. Come back in a few minutes$"
                )
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
        raise NotebookLMError(
            f"Failed to create audio overview for NotebookLM notebook: {exc}"
        ) from exc
