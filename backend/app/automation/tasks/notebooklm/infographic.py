"""Infographic operations for NotebookLM automation."""

from typing import Dict, Optional

from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.automation.tasks.notebooklm.exceptions import NotebookLMError


async def create_infographic(
    page: Page,
    notebook_id: str,
    language: Optional[str] = None,
    orientation: Optional[str] = None,
    detail_level: Optional[str] = None,
    description: Optional[str] = None,
) -> Dict[str, str]:
    """
    Creates an infographic for a notebook in NotebookLM.

    Args:
        page: The Playwright Page object to use for automation
        notebook_id: The ID of the notebook to create infographic for
        language: Language - "english" or "persian"
        orientation: Orientation - "Landscape", "Portrait", or "Square"
        detail_level: Level of detail - "Concise", "Standard", or "Detailed BETA"
        description: Optional description for the infographic (max 5000 chars)

    Returns:
        Dictionary with status and message

    Raises:
        NotebookLMError: If creating infographic fails
    """
    try:
        # Navigate directly to the notebook page
        await page.goto(f"https://notebooklm.google.com/notebook/{notebook_id}")

        # Wait for the Infographic button to be visible
        try:
            infographic_button = page.get_by_role("button", name="Infographic", exact=True)
            await infographic_button.wait_for(timeout=30_000, state="visible")
        except PlaywrightTimeoutError as exc:
            raise NotebookLMError(
                "Could not find the 'Infographic' button. "
                "The notebook page may not have loaded correctly."
            ) from exc

        # Click on the "Customize Infographic" button
        try:
            customize_button = page.get_by_role("button", name="Customize Infographic")
            await customize_button.wait_for(timeout=10_000, state="visible")
            await customize_button.click()
        except PlaywrightTimeoutError as exc:
            raise NotebookLMError(
                "Could not find the 'Customize Infographic' button. "
                "The dialog may not be accessible."
            ) from exc

        # Wait for the dialog to be visible
        await page.wait_for_timeout(1_000)

        # Configure language if provided
        if language:
            language_map = {
                "english": "English",
                "persian": "فارسی",
            }
            # Convert enum to string if needed
            lang_str = language.value if hasattr(language, "value") else language
            display_name = language_map.get(lang_str.lower(), lang_str)

            try:
                # Click on the language select dropdown
                language_select = page.locator("#mat-select-value-0")
                await language_select.wait_for(timeout=5_000, state="visible")
                await language_select.click()

                # Wait for dropdown options to appear
                await page.wait_for_timeout(500)

                # Select the language option by display name
                language_option = page.get_by_role("option", name=display_name)
                await language_option.wait_for(timeout=5_000, state="visible")
                await language_option.click()
            except PlaywrightTimeoutError:
                # Language dropdown might not be accessible or already set, continue
                pass

        # Configure orientation if provided
        if orientation:
            orientation_str = (
                orientation.value if hasattr(orientation, "value") else orientation
            )
            try:
                orientation_radio = page.get_by_role("radio", name=orientation_str)
                await orientation_radio.wait_for(timeout=5_000, state="visible")
                await orientation_radio.click()
            except PlaywrightTimeoutError:
                # Orientation option might already be selected, continue
                pass

        # Configure detail level if provided
        if detail_level:
            detail_str = (
                detail_level.value if hasattr(detail_level, "value") else detail_level
            )
            try:
                detail_radio = page.get_by_role("radio", name=detail_str)
                await detail_radio.wait_for(timeout=5_000, state="visible")
                await detail_radio.click()
            except PlaywrightTimeoutError:
                # Detail level option might already be selected, continue
                pass

        # Fill in description text if provided
        if description:
            try:
                description_textarea = page.get_by_role("textbox", name="Text area")
                await description_textarea.wait_for(timeout=5_000, state="visible")
                await description_textarea.click()
                # Clear any existing placeholder text first
                await description_textarea.clear()
                await description_textarea.fill(description)
            except PlaywrightTimeoutError:
                # Description textarea might not be accessible, continue
                pass

        # Click the Generate button
        try:
            generate_button = page.get_by_role("button", name="Generate")
            await generate_button.wait_for(timeout=5_000, state="visible")
            await generate_button.click()
        except PlaywrightTimeoutError as exc:
            raise NotebookLMError(
                "Could not find the 'Generate' button in the customization dialog."
            ) from exc

        # Wait for generation to start
        await page.wait_for_timeout(2_000)

        return {
            "status": "success",
            "message": f"Infographic creation started for notebook {notebook_id}. "
            "The infographic is being generated and will be available in a few minutes.",
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(
            f"Failed to create infographic for NotebookLM notebook: {exc}"
        ) from exc

