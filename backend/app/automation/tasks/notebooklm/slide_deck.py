"""Sync slide deck creation for NotebookLM automation."""

import re
from typing import Dict, Optional

from playwright.sync_api import Page

from app.automation.tasks.notebooklm.exceptions import NotebookLMError
from app.automation.tasks.notebooklm.helpers import check_generation_limits


def create_slide_deck(
    page: Page,
    notebook_id: str,
    format: Optional[str] = None,
    length: Optional[str] = None,
    language: Optional[str] = None,
    description: Optional[str] = None,
) -> Dict[str, str]:
    """
    Create slide deck artifact.

    Args:
        page: The Playwright Page object
        notebook_id: The ID of the notebook
        format: Format for the slide deck
        length: Length of the slide deck
        language: Language for the slide deck
        description: Custom description

    Returns:
        Dictionary with status and message

    Raises:
        NotebookLMError: If slide deck creation fails
    """
    try:
        page.goto(f"https://notebooklm.google.com/notebook/{notebook_id}")
        page.wait_for_timeout(1_000)

        # Open the "Customize Slide Deck" dialog
        try:
            customize_button = page.get_by_role(
                "button", name=re.compile("Customize Slide Deck", re.IGNORECASE)
            ).first
            customize_button.wait_for(timeout=30_000, state="visible")
            customize_button.click()
        except Exception:
            # Fallback to older "Slide deck" or "Slides" button if needed
            sd_button = page.get_by_role(
                "button", name=re.compile("Slide deck|Slides", re.IGNORECASE)
            ).first
            sd_button.wait_for(timeout=30_000, state="visible")
            sd_button.click()

        page.wait_for_timeout(1_000)

        # Select format (Detailed Deck / Presenter Slides) via radio tiles
        if format:
            try:
                # Map format values to display names
                format_map = {
                    "detailed": "Detailed Deck",
                    "detailed deck": "Detailed Deck",
                    "presenter": "Presenter Slides",
                    "presenter slides": "Presenter Slides",
                }
                format_display_name = format_map.get(format.lower(), format)
                
                # Match against the visible tile label text
                format_radio = page.get_by_role(
                    "radio", name=re.compile(re.escape(format_display_name), re.IGNORECASE)
                )
                if format_radio.count() > 0:
                    format_radio.first.wait_for(timeout=5_000, state="visible")
                    format_radio.first.click()
                    page.wait_for_timeout(300)
            except Exception:
                # Best-effort only; if it fails we continue with defaults
                pass

        # Handle language selection if provided
        if language:
            try:
                # Map logical language values to display names in the UI
                lang_map = {
                    "english": "English",
                    "persian": "فارسی",
                }
                lang_display_name = lang_map.get(language.lower(), language)

                # Try multiple strategies to open the language selector dropdown
                # Try both #mat-select-value-0 and #mat-select-value-4 as they may vary
                lang_selector_opened = False
                for selector_id in ["#mat-select-value-0", "#mat-select-value-4"]:
                    if not lang_selector_opened:
                        try:
                            lang_selector = page.locator(selector_id)
                            if lang_selector.count() > 0:
                                lang_selector.wait_for(timeout=3_000, state="visible")
                                lang_selector.click()
                                page.wait_for_timeout(500)
                                lang_selector_opened = True
                        except Exception:
                            pass

                # Strategy 2: Try clicking the mat-select element directly
                if not lang_selector_opened:
                    for select_id in ["mat-select-0", "mat-select-4"]:
                        if not lang_selector_opened:
                            try:
                                mat_select = page.locator(f"mat-select#{select_id}")
                                if mat_select.count() == 0:
                                    # Fallback: find mat-select that contains the value element
                                    value_id = select_id.replace("mat-select", "mat-select-value")
                                    mat_select = page.locator("mat-select").filter(
                                        has=page.locator(f"#{value_id}")
                                    ).first
                                if mat_select.count() > 0:
                                    mat_select.wait_for(timeout=3_000, state="visible")
                                    mat_select.click()
                                    page.wait_for_timeout(500)
                                    lang_selector_opened = True
                            except Exception:
                                pass

                # Strategy 3: Try clicking the select arrow or its container
                if not lang_selector_opened:
                    try:
                        select_arrow_container = page.locator(".mat-mdc-select-arrow").first
                        if select_arrow_container.count() > 0:
                            select_arrow_container.wait_for(timeout=3_000, state="visible")
                            mat_select = select_arrow_container.locator("xpath=ancestor::mat-select").first
                            if mat_select.count() > 0:
                                mat_select.click()
                            else:
                                select_arrow_container.click()
                            page.wait_for_timeout(500)
                            lang_selector_opened = True
                    except Exception:
                        pass

                if lang_selector_opened:
                    # Wait for the options panel to appear
                    try:
                        options_panel = page.get_by_role("listbox")
                        options_panel.wait_for(timeout=3_000, state="visible")
                    except Exception:
                        page.wait_for_timeout(500)

                    # Click the language option
                    lang_option = page.get_by_role(
                        "option", name=re.compile(re.escape(lang_display_name), re.IGNORECASE)
                    )
                    if lang_option.count() > 0:
                        lang_option.first.wait_for(timeout=3_000, state="visible")
                        lang_option.first.click()
                        page.wait_for_timeout(500)

                        # Verify the selection was applied
                        try:
                            # Check both possible selector IDs
                            for selector_id in ["#mat-select-value-0", "#mat-select-value-4"]:
                                try:
                                    selected_value = page.locator(selector_id).inner_text()
                                    if lang_display_name.lower() not in selected_value.lower():
                                        # Selection might not have worked, try clicking again
                                        page.locator(selector_id).click()
                                        page.wait_for_timeout(300)
                                        lang_option = page.get_by_role(
                                            "option", name=re.compile(re.escape(lang_display_name), re.IGNORECASE)
                                        )
                                        if lang_option.count() > 0:
                                            lang_option.first.click()
                                            page.wait_for_timeout(500)
                                        break
                                except Exception:
                                    continue
                        except Exception:
                            pass
            except Exception:
                # If language selection fails, continue with the default language
                pass

        # Handle length selection (Short / Default) via button toggles
        if length:
            try:
                length_button = page.get_by_role(
                    "radio", name=re.compile(re.escape(length), re.IGNORECASE)
                )
                if length_button.count() > 0:
                    length_button.first.wait_for(timeout=5_000, state="visible")
                    length_button.first.click()
                    page.wait_for_timeout(300)
            except Exception:
                # Best-effort only; if it fails we continue with defaults
                pass

        # Fill description if provided
        if description:
            desc_input = page.get_by_role("textbox").first
            desc_input.wait_for(timeout=5_000, state="visible")
            desc_input.fill(description)

        # Click Generate button
        generate_button = page.get_by_role(
            "button", name=re.compile("Generate", re.IGNORECASE)
        )
        generate_button.wait_for(timeout=5_000, state="visible")
        generate_button.click()
        page.wait_for_timeout(2_000)

        # After clicking Generate, check if a daily limit / upsell message appeared.
        check_generation_limits(page, "Slide deck")

        return {
            "status": "success",
            "message": f"Slide deck creation started for {notebook_id}.",
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to create slide deck: {exc}") from exc
