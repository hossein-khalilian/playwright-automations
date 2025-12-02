"""Slide deck operations for NotebookLM automation."""

from typing import Dict, Optional

from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.automation.tasks.notebooklm.exceptions import NotebookLMError


async def create_slide_deck(
    page: Page,
    notebook_id: str,
    format: Optional[str] = None,
    length: Optional[str] = None,
    language: Optional[str] = None,
    description: Optional[str] = None,
) -> Dict[str, str]:
    """
    Creates a slide deck for a notebook in NotebookLM.

    Args:
        page: The Playwright Page object to use for automation
        notebook_id: The ID of the notebook to create slide deck for
        format: Slide deck format - "Detailed Deck" or "Presenter Slides"
        length: Slide deck length - "Short" or "Default"
        language: Language - "english" or "persian"
        description: Optional description for the slide deck (max 5000 chars)

    Returns:
        Dictionary with status and message

    Raises:
        NotebookLMError: If creating slide deck fails
    """
    try:
        # Navigate directly to the notebook page
        await page.goto(f"https://notebooklm.google.com/notebook/{notebook_id}")

        # Wait for the Slide Deck button to be visible
        try:
            slide_deck_button = page.get_by_role("button", name="Slide Deck", exact=True)
            await slide_deck_button.wait_for(timeout=30_000, state="visible")
        except PlaywrightTimeoutError as exc:
            raise NotebookLMError(
                "Could not find the 'Slide Deck' button. "
                "The notebook page may not have loaded correctly."
            ) from exc

        # Click on the "Customize Slide Deck" button
        try:
            customize_button = page.get_by_role("button", name="Customize Slide Deck")
            await customize_button.wait_for(timeout=10_000, state="visible")
            await customize_button.click()
        except PlaywrightTimeoutError as exc:
            raise NotebookLMError(
                "Could not find the 'Customize Slide Deck' button. "
                "The dialog may not be accessible."
            ) from exc

        # Wait for the dialog to be visible
        await page.wait_for_timeout(1_000)

        # Configure format (Detailed Deck or Presenter Slides)
        if format:
            format_str = format.value if hasattr(format, "value") else format
            if format_str in ["Detailed Deck", "Presenter Slides"]:
                try:
                    # Click by text for format selection
                    format_option = page.get_by_text(format_str)
                    await format_option.wait_for(timeout=5_000, state="visible")
                    await format_option.click()
                except PlaywrightTimeoutError:
                    # Format option might already be selected, continue
                    pass

        # Configure length (Short or Default)
        if length:
            length_str = length.value if hasattr(length, "value") else length
            try:
                length_radio = page.get_by_role("radio", name=length_str)
                await length_radio.wait_for(timeout=5_000, state="visible")
                await length_radio.click()
            except PlaywrightTimeoutError:
                # Length option might already be selected, continue
                pass

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
                # Click on the language select dropdown (uses #mat-select-value-1 for slide deck)
                language_select = page.locator("#mat-select-value-1")
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
            "message": f"Slide deck creation started for notebook {notebook_id}. "
            "The slide deck is being generated and will be available in a few minutes.",
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(
            f"Failed to create slide deck for NotebookLM notebook: {exc}"
        ) from exc

