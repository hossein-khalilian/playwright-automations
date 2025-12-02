"""Report operations for NotebookLM automation."""

from typing import Dict, Optional

from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.automation.tasks.notebooklm.exceptions import NotebookLMError


async def create_report(
    page: Page,
    notebook_id: str,
    format: Optional[str] = None,
    language: Optional[str] = None,
    description: Optional[str] = None,
) -> Dict[str, str]:
    """
    Creates a report for a notebook in NotebookLM.

    Args:
        page: The Playwright Page object to use for automation
        notebook_id: The ID of the notebook to create report for
        format: Report format - "Create Your Own", "Briefing Doc", "Study Guide", etc.
        language: Language - "english" or "persian"
        description: Description of the report to create (max 5000 chars)

    Returns:
        Dictionary with status and message

    Raises:
        NotebookLMError: If creating report fails
    """
    try:
        # Navigate directly to the notebook page
        await page.goto(f"https://notebooklm.google.com/notebook/{notebook_id}")

        # Wait for the Reports button to be visible
        try:
            reports_button = page.get_by_role("button", name="Reports")
            await reports_button.wait_for(timeout=30_000, state="visible")
            await reports_button.click()
        except PlaywrightTimeoutError as exc:
            raise NotebookLMError(
                "Could not find the 'Reports' button. "
                "The notebook page may not have loaded correctly."
            ) from exc

        # Wait for the report format selection dialog
        await page.wait_for_timeout(1_000)

        # Select report format if provided
        if format:
            format_str = format.value if hasattr(format, "value") else format
            
            # Map format names to button text patterns
            format_button_map = {
                "Create Your Own": "Create Your Own",
                "Briefing Doc": "Briefing Doc Overview of your",
                "Study Guide": "Study Guide Short-answer quiz",
                "Blog Post": "Blog Post",
                "Technical Whitepaper": "Technical Whitepaper",
                "Architectural Patterns Guide": "Architectural Patterns Guide",
                "Concept Explainer": "Concept Explainer",
                "Key Terminology Primer": "Key Terminology Primer",
            }
            
            button_text = format_button_map.get(format_str, format_str)
            
            # Try multiple strategies to click the format button
            clicked = False
            
            # Strategy 1: Try clicking button by name matching the button text pattern
            # This matches the Playwright pattern: get_by_role("button", name="Briefing Doc Overview of your")
            try:
                format_button = page.get_by_role("button", name=button_text)
                await format_button.wait_for(timeout=3_000, state="visible")
                # The Playwright script shows getting a button inside, so try that too
                inner_button = format_button.get_by_role("button").first
                if await inner_button.is_visible(timeout=1_000):
                    await inner_button.click()
                else:
                    await format_button.click()
                clicked = True
            except PlaywrightTimeoutError:
                pass
            
            if not clicked:
                # Strategy 2: Try clicking button that contains the button text pattern
                try:
                    format_button = page.get_by_role("button").filter(has_text=button_text)
                    await format_button.wait_for(timeout=3_000, state="visible")
                    await format_button.click()
                    clicked = True
                except PlaywrightTimeoutError:
                    pass
            
            if not clicked:
                # Strategy 3: Try clicking button with exact format name
                try:
                    format_button = page.get_by_role("button").filter(has_text=format_str)
                    await format_button.wait_for(timeout=3_000, state="visible")
                    await format_button.click()
                    clicked = True
                except PlaywrightTimeoutError:
                    pass
            
            if not clicked:
                # Strategy 4: Try finding the report-customization-tile with the format name
                try:
                    format_card = page.locator("report-customization-tile").filter(has_text=format_str)
                    await format_card.wait_for(timeout=3_000, state="visible")
                    format_button_in_card = format_card.get_by_role("button").first
                    await format_button_in_card.click()
                    clicked = True
                except PlaywrightTimeoutError:
                    pass
            
            if not clicked:
                raise NotebookLMError(
                    f"Could not find the report format '{format_str}'. "
                    "Please check that the format name is correct."
                )
        else:
            # Default to "Create Your Own" if no format specified
            try:
                create_button = page.get_by_role("button", name="Create Your Own Craft reports")
                await create_button.wait_for(timeout=10_000, state="visible")
                await create_button.click()
            except PlaywrightTimeoutError:
                # Try alternative button name
                try:
                    create_button = page.get_by_role("button", name="Create Your Own")
                    await create_button.wait_for(timeout=10_000, state="visible")
                    await create_button.click()
                except PlaywrightTimeoutError as exc:
                    raise NotebookLMError(
                        "Could not find the 'Create Your Own' button. "
                        "The dialog may not be accessible."
                    ) from exc

        # Wait for the customization dialog to be visible
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
                # Try different select value IDs (they vary based on dialog state)
                language_select = None
                for select_id in ["#mat-select-value-2", "#mat-select-value-3", "#mat-select-value-1", "#mat-select-value-0"]:
                    try:
                        language_select = page.locator(select_id)
                        if await language_select.is_visible(timeout=1_000):
                            await language_select.click()
                            break
                    except PlaywrightTimeoutError:
                        continue
                
                if language_select is None:
                    # Fallback: try finding by label
                    language_select = page.get_by_label("Choose language").locator("mat-select")
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

        # Fill in description text (required)
        if description:
            try:
                description_textarea = page.get_by_role(
                    "textbox", name="Input to describe the kind of"
                )
                await description_textarea.wait_for(timeout=5_000, state="visible")
                await description_textarea.click()
                # Clear any existing placeholder text first
                await description_textarea.clear()
                await description_textarea.fill(description)
            except PlaywrightTimeoutError:
                # Try alternative aria-label
                try:
                    description_textarea = page.get_by_role(
                        "textbox", name="Input to describe the kind of report to create"
                    )
                    await description_textarea.wait_for(timeout=5_000, state="visible")
                    await description_textarea.click()
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
            "message": f"Report creation started for notebook {notebook_id}. "
            "The report is being generated and will be available in a few minutes.",
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(
            f"Failed to create report for NotebookLM notebook: {exc}"
        ) from exc

