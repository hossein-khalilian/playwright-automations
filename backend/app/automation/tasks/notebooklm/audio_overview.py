"""Sync audio overview creation for NotebookLM automation."""

import re
from typing import Dict, Optional

from playwright.sync_api import Page

from app.automation.tasks.notebooklm.exceptions import NotebookLMError
from app.automation.tasks.notebooklm.helpers import check_generation_limits


def create_audio_overview(
    page: Page,
    notebook_id: str,
    audio_format: Optional[str] = None,
    language: Optional[str] = None,
    length: Optional[str] = None,
    focus_text: Optional[str] = None,
) -> Dict[str, str]:
    """
    Create audio overview artifact.

    Args:
        page: The Playwright Page object
        notebook_id: The ID of the notebook
        audio_format: Format for the audio
        language: Language for the audio
        length: Length of the audio
        focus_text: Focus text for the audio

    Returns:
        Dictionary with status and message

    Raises:
        NotebookLMError: If audio overview creation fails
    """
    try:
        # Navigate to notebook
        page.goto(f"https://notebooklm.google.com/notebook/{notebook_id}")
        page.wait_for_timeout(1_000)

        # Open the "Customize Audio Overview" dialog.
        # New UI has a button explicitly named "Customize Audio Overview".
        try:
            customize_button = page.get_by_role(
                "button", name=re.compile("Customize Audio Overview", re.IGNORECASE)
            ).first
            customize_button.wait_for(timeout=30_000, state="visible")
            customize_button.click()
        except Exception:
            # Fallback to older "Audio overview" button if needed.
            audio_button = page.get_by_role(
                "button", name=re.compile("Audio overview", re.IGNORECASE)
            ).first
            audio_button.wait_for(timeout=30_000, state="visible")
            audio_button.click()

        page.wait_for_timeout(1_000)

        # Select audio format (Deep Dive / Brief / Critique / Debate) via radio tiles.
        if audio_format:
            try:
                # Match against the visible tile label text.
                format_radio = page.get_by_role(
                    "radio", name=re.compile(re.escape(audio_format), re.IGNORECASE)
                )
                if format_radio.count() > 0:
                    format_radio.first.wait_for(timeout=5_000, state="visible")
                    format_radio.first.click()
            except Exception:
                # Best-effort only; if it fails we continue with defaults.
                pass

        # Handle language selection if provided.
        if language:
            try:
                # Map logical language values to display names in the UI.
                # Enum values are "english"/"persian" from models.AudioLanguage.
                lang_map = {
                    "english": "English",
                    "persian": "فارسی",
                }
                lang_display_name = lang_map.get(language.lower(), language)

                # Try multiple strategies to open the language selector dropdown
                # Strategy 1: Click the select value element (#mat-select-value-0)
                lang_selector_opened = False
                try:
                    lang_selector = page.locator("#mat-select-value-0")
                    if lang_selector.count() > 0:
                        lang_selector.wait_for(timeout=3_000, state="visible")
                        lang_selector.click()
                        page.wait_for_timeout(500)
                        lang_selector_opened = True
                except Exception:
                    pass

                # Strategy 2: Try clicking the mat-select element directly (by ID or by finding it near the label)
                if not lang_selector_opened:
                    try:
                        # Try finding mat-select by ID first
                        mat_select = page.locator("mat-select#mat-select-0")
                        if mat_select.count() == 0:
                            # Fallback: find mat-select that contains #mat-select-value-0
                            mat_select = page.locator("mat-select").filter(
                                has=page.locator("#mat-select-value-0")
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
                        # Find the select arrow container and click it
                        select_arrow_container = page.locator(".mat-mdc-select-arrow").first
                        if select_arrow_container.count() > 0:
                            select_arrow_container.wait_for(timeout=3_000, state="visible")
                            # Try to find the parent mat-select and click it
                            mat_select = select_arrow_container.locator("xpath=ancestor::mat-select").first
                            if mat_select.count() > 0:
                                mat_select.click()
                            else:
                                # Fallback: click the arrow container itself
                                select_arrow_container.click()
                            page.wait_for_timeout(500)
                            lang_selector_opened = True
                    except Exception:
                        pass

                if not lang_selector_opened:
                    # If we couldn't open the dropdown, skip language selection
                    pass
                else:
                    # Wait for the options panel to appear (it's in a cdk-overlay)
                    # The options appear in a panel with role="listbox"
                    try:
                        options_panel = page.get_by_role("listbox")
                        options_panel.wait_for(timeout=3_000, state="visible")
                    except Exception:
                        # Fallback: just wait a bit
                        page.wait_for_timeout(500)

                    # Click the language option in the overlay panel
                    lang_option = page.get_by_role(
                        "option", name=re.compile(re.escape(lang_display_name), re.IGNORECASE)
                    )
                    if lang_option.count() > 0:
                        lang_option.first.wait_for(timeout=3_000, state="visible")
                        lang_option.first.click()
                        # Wait for the selection to be applied and dropdown to close
                        page.wait_for_timeout(500)

                        # Verify the selection was applied by checking if the value changed
                        # (optional check - if it fails, we still continue)
                        try:
                            selected_value = page.locator("#mat-select-value-0").inner_text()
                            if lang_display_name.lower() not in selected_value.lower():
                                # Selection might not have worked, try clicking again
                                page.locator("#mat-select-value-0").click()
                                page.wait_for_timeout(300)
                                lang_option = page.get_by_role(
                                    "option", name=re.compile(re.escape(lang_display_name), re.IGNORECASE)
                                )
                                if lang_option.count() > 0:
                                    lang_option.first.click()
                                    page.wait_for_timeout(500)
                        except Exception:
                            # Verification failed, but we'll continue anyway
                            pass
            except Exception:
                # If language selection fails, continue with the default language.
                pass

        # Select length (Short / Default / Long) via button-toggle group.
        if length:
            try:
                length_button = page.get_by_role(
                    "button", name=re.compile(re.escape(length), re.IGNORECASE)
                )
                if length_button.count() > 0:
                    length_button.first.wait_for(timeout=5_000, state="visible")
                    length_button.first.click()
            except Exception:
                # Length is optional; ignore failures.
                pass

        # Fill focus text if provided.
        if focus_text:
            text_input = page.get_by_role("textbox").first
            text_input.wait_for(timeout=5_000, state="visible")
            text_input.fill(focus_text)

        # Click Generate button.
        generate_button = page.get_by_role(
            "button", name=re.compile("Generate", re.IGNORECASE)
        )
        generate_button.wait_for(timeout=5_000, state="visible")
        generate_button.click()
        page.wait_for_timeout(2_000)

        # After clicking Generate, check if a daily limit / upsell message appeared.
        check_generation_limits(page, "Audio Overview")

        return {
            "status": "success",
            "message": f"Audio overview creation started for {notebook_id}.",
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to create audio overview: {exc}") from exc
