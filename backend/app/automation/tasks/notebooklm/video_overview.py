"""Video overview operations for NotebookLM automation."""

from typing import Dict, Optional

from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.automation.tasks.notebooklm.exceptions import NotebookLMError


async def create_video_overview(
    page: Page,
    notebook_id: str,
    video_format: Optional[str] = None,
    language: Optional[str] = None,
    visual_style: Optional[str] = None,
    custom_style_description: Optional[str] = None,
    focus_text: Optional[str] = None,
) -> Dict[str, str]:
    """
    Creates a video overview for a notebook in NotebookLM.

    Args:
        page: The Playwright Page object to use for automation
        notebook_id: The ID of the notebook to create video overview for
        video_format: Video format - "Explainer" or "Brief"
        language: Language - "english" or "persian"
        visual_style: Visual style - "Auto-select", "Custom", "Classic", "Whiteboard", "Kawaii", "Anime", "Watercolor", "Retro print", "Heritage", or "Paper-craft"
        custom_style_description: Custom visual style description (required when visual_style is Custom, max 5000 chars)
        focus_text: Optional focus text for the AI hosts (max 5000 chars)

    Returns:
        Dictionary with status and message

    Raises:
        NotebookLMError: If creating video overview fails
    """
    try:
        # Navigate directly to the notebook page
        await page.goto(f"https://notebooklm.google.com/notebook/{notebook_id}")

        # Wait for the Video Overview label to be visible
        try:
            video_label = page.get_by_label("Video Overview", exact=True)
            await video_label.wait_for(timeout=30_000, state="visible")
        except PlaywrightTimeoutError as exc:
            raise NotebookLMError(
                "Could not find the 'Video Overview' label. "
                "The notebook page may not have loaded correctly."
            ) from exc

        # Click on the "Customize Video Overview" button
        try:
            customize_button = page.get_by_role("button", name="Customize Video Overview")
            await customize_button.wait_for(timeout=10_000, state="visible")
            await customize_button.click()
        except PlaywrightTimeoutError as exc:
            raise NotebookLMError(
                "Could not find the 'Customize Video Overview' button. "
                "The dialog may not be accessible."
            ) from exc

        # Wait for the dialog to be visible
        await page.wait_for_timeout(1_000)

        # Configure format (Explainer or Brief)
        if video_format:
            format_str = video_format.value if hasattr(video_format, "value") else video_format
            if format_str in ["Explainer", "Brief"]:
                try:
                    format_option = page.get_by_text(format_str, exact=True)
                    await format_option.wait_for(timeout=5_000, state="visible")
                    await format_option.click()
                except PlaywrightTimeoutError:
                    # Format option might already be selected, continue
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
                # Click on the language select dropdown arrow
                language_select_arrow = page.locator(".mat-mdc-select-arrow > svg")
                await language_select_arrow.wait_for(timeout=5_000, state="visible")
                await language_select_arrow.click()

                # Wait for dropdown options to appear
                await page.wait_for_timeout(500)

                # Select the language option by display name
                language_option = page.get_by_role("option", name=display_name)
                await language_option.wait_for(timeout=5_000, state="visible")
                await language_option.click()
            except PlaywrightTimeoutError:
                # Language dropdown might not be accessible or already set, continue
                pass

        # Configure visual style if provided
        if visual_style:
            style_str = visual_style.value if hasattr(visual_style, "value") else visual_style
            try:
                # Visual styles are in a carousel, try clicking by text
                style_option = page.get_by_text(style_str, exact=True)
                await style_option.wait_for(timeout=5_000, state="visible")
                await style_option.click()
            except PlaywrightTimeoutError:
                # Try alternative approach - click on the carousel radio button
                try:
                    # Find the radio button by its label text
                    style_radio = page.get_by_role("radio").filter(has_text=style_str)
                    await style_radio.wait_for(timeout=5_000, state="visible")
                    await style_radio.click()
                except PlaywrightTimeoutError:
                    # Visual style might already be selected, continue
                    pass

            # If Custom style is selected, fill in the custom style description
            if style_str == "Custom" and custom_style_description:
                try:
                    # Wait a bit for the custom style textarea to appear after selecting Custom
                    await page.wait_for_timeout(500)
                    
                    # Strategy 1: Find by placeholder text which is unique to custom style textarea
                    try:
                        custom_textarea = page.locator("textarea[placeholder*='story-like style']")
                        await custom_textarea.wait_for(timeout=5_000, state="visible")
                        await custom_textarea.click()
                        await custom_textarea.clear()
                        await custom_textarea.fill(custom_style_description)
                    except PlaywrightTimeoutError:
                        # Strategy 2: Find by locating the label and then the textarea in the same section
                        try:
                            # Find the label first
                            label = page.locator("label").filter(has_text="Describe a custom visual style")
                            await label.wait_for(timeout=5_000, state="visible")
                            # Find textarea in the same dialog section (find closest textarea)
                            custom_textarea = page.locator("#stylePrompt-label").locator("..").locator("textarea")
                            await custom_textarea.wait_for(timeout=5_000, state="visible")
                            await custom_textarea.click()
                            await custom_textarea.clear()
                            await custom_textarea.fill(custom_style_description)
                        except PlaywrightTimeoutError:
                            # Strategy 3: Find all textareas and use the first one (should be custom style)
                            try:
                                all_textareas = page.get_by_role("textbox", name="Text area")
                                textarea_count = await all_textareas.count()
                                if textarea_count > 0:
                                    # The custom style description is typically the first textarea when Custom is selected
                                    custom_textarea = all_textareas.nth(0)
                                    await custom_textarea.wait_for(timeout=5_000, state="visible")
                                    await custom_textarea.click()
                                    await custom_textarea.clear()
                                    await custom_textarea.fill(custom_style_description)
                            except PlaywrightTimeoutError:
                                # Custom style textarea might not be accessible, continue
                                pass
                except Exception:
                    # If custom style description can't be filled, continue
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
