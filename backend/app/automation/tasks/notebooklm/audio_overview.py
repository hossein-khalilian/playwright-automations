"""Audio overview operations for NotebookLM automation."""

from typing import Dict, Optional

from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.automation.tasks.notebooklm.exceptions import NotebookLMError


async def create_audio_overview(
    page: Page,
    notebook_id: str,
    audio_format: Optional[str] = None,
    language: Optional[str] = None,
    length: Optional[str] = None,
    focus_text: Optional[str] = None,
) -> Dict[str, str]:
    """
    Creates an audio overview for a notebook in NotebookLM.

    Args:
        page: The Playwright Page object to use for automation
        notebook_id: The ID of the notebook to create audio overview for
        audio_format: Audio format - "Deep Dive", "Brief", "Critique", or "Debate"
        language: Language - "english" or "persian"
        length: Audio length - format dependent: Deep Dive (Short/Default/Long), 
            Brief (none), Critique/Debate (Short/Default)
        focus_text: Optional focus text for the AI hosts (max 5000 chars)

    Returns:
        Dictionary with status and message

    Raises:
        NotebookLMError: If creating audio overview fails
    """
    try:
        # Navigate directly to the notebook page
        await page.goto(f"https://notebooklm.google.com/notebook/{notebook_id}")

        # Wait for the Audio Overview label to be visible
        try:
            audio_label = page.get_by_label("Audio Overview", exact=True)
            await audio_label.wait_for(timeout=30_000, state="visible")
        except PlaywrightTimeoutError as exc:
            raise NotebookLMError(
                "Could not find the 'Audio Overview' label. "
                "The notebook page may not have loaded correctly."
            ) from exc

        # Click on the "Customize Audio Overview" button
        try:
            customize_button = page.get_by_role("button", name="Customize Audio Overview")
            await customize_button.wait_for(timeout=10_000, state="visible")
            await customize_button.click()
        except PlaywrightTimeoutError as exc:
            raise NotebookLMError(
                "Could not find the 'Customize Audio Overview' button. "
                "The dialog may not be accessible."
            ) from exc

        # Wait for the dialog to be visible
        await page.wait_for_timeout(1_000)

        # Configure format (Deep Dive, Brief, Critique, or Debate)
        # Convert enum to string if needed
        format_str = audio_format.value if hasattr(audio_format, "value") else audio_format
        if format_str:
            format_text_map = {
                "Deep Dive": "A lively conversation between",
                "Brief": "A bite-sized overview to help",
                "Critique": "An expert review of your",
                "Debate": "A thoughtful debate between",
            }
            format_text = format_text_map.get(format_str)
            if format_text:
                try:
                    # Click on the format by its description text
                    format_option = page.get_by_text(format_text)
                    await format_option.wait_for(timeout=5_000, state="visible")
                    await format_option.click()
                except PlaywrightTimeoutError:
                    # Fallback: Try clicking by label (especially for Deep Dive)
                    try:
                        if format_str == "Deep Dive":
                            # For Deep Dive, use label filter as shown in the script
                            format_label = page.locator("label").filter(
                                has_text="Deep DivecheckmarkA lively"
                            )
                        else:
                            # For other formats, use label with format name
                            format_label = page.locator("label").filter(
                                has_text=format_str
                            )
                        await format_label.wait_for(timeout=5_000, state="visible")
                        await format_label.click()
                    except PlaywrightTimeoutError:
                        # Format option might already be selected, continue
                        pass

        # Configure language if provided
        # Map enum values to display names
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

        # Configure length (format-specific)
        # Brief format doesn't support length, so skip if format is Brief
        if length and format_str != "Brief":
            try:
                length_radio = page.get_by_role("radio", name=length)
                await length_radio.wait_for(timeout=5_000, state="visible")
                await length_radio.click()
            except PlaywrightTimeoutError:
                # Length option might already be selected, continue
                pass

        # Fill in focus text if provided
        if focus_text:
            try:
                focus_textarea = page.get_by_role("textbox", name="Text area")
                await focus_textarea.wait_for(timeout=5_000, state="visible")
                await focus_textarea.click()
                # Clear any existing placeholder/example text first
                await focus_textarea.clear()
                await focus_textarea.fill(focus_text)
            except PlaywrightTimeoutError:
                # Focus textarea might not be accessible, continue
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

        # Click "Customize Audio Overview" again (to close the dialog)
        try:
            customize_button = page.get_by_role("button", name="Customize Audio Overview")
            if await customize_button.is_visible(timeout=2_000):
                await customize_button.click()
        except PlaywrightTimeoutError:
            # Dialog might have closed automatically, which is fine
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
