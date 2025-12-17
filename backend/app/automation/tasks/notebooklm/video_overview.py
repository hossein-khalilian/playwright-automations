"""Sync video overview creation for NotebookLM automation."""

import re
from typing import Dict, Optional

from playwright.sync_api import Page

from app.automation.tasks.notebooklm.exceptions import NotebookLMError
from app.automation.tasks.notebooklm.helpers import check_generation_limits


def create_video_overview(
    page: Page,
    notebook_id: str,
    video_format: Optional[str] = None,
    language: Optional[str] = None,
    visual_style: Optional[str] = None,
    custom_style_description: Optional[str] = None,
    focus_text: Optional[str] = None,
) -> Dict[str, str]:
    """
    Create video overview artifact.

    Args:
        page: The Playwright Page object
        notebook_id: The ID of the notebook
        video_format: Format for the video
        language: Language for the video
        visual_style: Visual style for the video
        custom_style_description: Custom style description
        focus_text: Focus text for the video

    Returns:
        Dictionary with status and message

    Raises:
        NotebookLMError: If video overview creation fails
    """
    try:
        page.goto(f"https://notebooklm.google.com/notebook/{notebook_id}")
        page.wait_for_timeout(1_000)

        # Open the "Customize Video Overview" dialog
        try:
            customize_button = page.get_by_role(
                "button", name=re.compile("Customize Video Overview", re.IGNORECASE)
            ).first
            customize_button.wait_for(timeout=30_000, state="visible")
            customize_button.click()
        except Exception:
            # Fallback to older "Video overview" button if needed
            video_button = page.get_by_role(
                "button", name=re.compile("Video overview", re.IGNORECASE)
            ).first
            video_button.wait_for(timeout=30_000, state="visible")
            video_button.click()

        page.wait_for_timeout(1_000)

        # Select video format (Explainer / Brief) via radio tiles
        if video_format:
            try:
                # Map format values to display names
                format_map = {
                    "explainer": "Explainer",
                    "brief": "Brief",
                }
                format_display_name = format_map.get(video_format.lower(), video_format)
                
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
                # Try both #mat-select-value-0 and #mat-select-value-5 as they may vary
                lang_selector_opened = False
                for selector_id in ["#mat-select-value-0", "#mat-select-value-5"]:
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
                    for select_id in ["mat-select-0", "mat-select-5"]:
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
                            for selector_id in ["#mat-select-value-0", "#mat-select-value-5"]:
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

        # Handle visual style selection via radio buttons in carousel
        if visual_style:
            try:
                # Map visual style values to display names
                style_map = {
                    "auto-select": "Auto-select",
                    "auto": "Auto-select",
                    "custom": "Custom",
                    "classic": "Classic",
                    "whiteboard": "Whiteboard",
                    "kawaii": "Kawaii",
                    "anime": "Anime",
                    "watercolor": "Watercolor",
                    "retro print": "Retro print",
                    "retro": "Retro print",
                    "heritage": "Heritage",
                    "paper-craft": "Paper-craft",
                    "papercraft": "Paper-craft",
                }
                style_display_name = style_map.get(visual_style.lower(), visual_style)
                
                # Find the radio button by the label text in the carousel
                style_radio = page.get_by_role(
                    "radio", name=re.compile(re.escape(style_display_name), re.IGNORECASE)
                )
                if style_radio.count() > 0:
                    style_radio.first.wait_for(timeout=5_000, state="visible")
                    style_radio.first.click()
                    page.wait_for_timeout(300)
            except Exception:
                # Best-effort only; if it fails we continue with defaults
                pass

        # Fill custom style description if provided
        if custom_style_description:
            # This would be the first textbox if it exists
            try:
                style_input = page.get_by_role("textbox").first
                style_input.wait_for(timeout=5_000, state="visible")
                style_input.fill(custom_style_description)
            except Exception:
                pass

        # Fill focus text if provided
        if focus_text:
            # Focus text is in a textarea with label "What should the AI hosts focus on?"
            try:
                focus_label = page.locator("label").filter(
                    has_text=re.compile("What should the AI hosts focus on", re.IGNORECASE)
                )
                if focus_label.count() > 0:
                    # Find the textarea associated with this label
                    text_input = page.get_by_role("textbox").filter(
                        has=page.locator("textarea")
                    ).first
                    if text_input.count() == 0:
                        # Fallback: try getting textbox by index
                        text_input = page.get_by_role("textbox").nth(1)
                    text_input.wait_for(timeout=5_000, state="visible")
                    text_input.fill(focus_text)
                else:
                    # Fallback: just use the last textbox
                    text_input = page.get_by_role("textbox").last
                    text_input.wait_for(timeout=5_000, state="visible")
                    text_input.fill(focus_text)
            except Exception:
                # Final fallback: try nth(1) textbox
                try:
                    text_input = page.get_by_role("textbox").nth(1)
                    text_input.wait_for(timeout=5_000, state="visible")
                    text_input.fill(focus_text)
                except Exception:
                    pass

        # Click Generate button
        generate_button = page.get_by_role(
            "button", name=re.compile("Generate", re.IGNORECASE)
        )
        generate_button.wait_for(timeout=5_000, state="visible")
        generate_button.click()
        page.wait_for_timeout(2_000)

        # After clicking Generate, check if a daily limit / upsell message appeared.
        check_generation_limits(page, "Video Overview")

        return {
            "status": "success",
            "message": f"Video overview creation started for {notebook_id}.",
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to create video overview: {exc}") from exc
