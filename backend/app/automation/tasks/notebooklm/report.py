"""Sync report creation for NotebookLM automation."""

import re
from typing import Dict, Optional

from playwright.sync_api import Page

from app.automation.tasks.notebooklm.exceptions import NotebookLMError


def create_report(
    page: Page,
    notebook_id: str,
    format: Optional[str] = None,
    language: Optional[str] = None,
    description: Optional[str] = None,
) -> Dict[str, str]:
    """
    Create report artifact.

    Args:
        page: The Playwright Page object
        notebook_id: The ID of the notebook
        format: Format for the report ("Create Your Own", "Briefing Doc", "Study Guide", "Blog Post", etc.)
        language: Language for the report ("english" or "persian")
        description: Description of the report to create

    Returns:
        Dictionary with status and message

    Raises:
        NotebookLMError: If report creation fails
    """
    try:
        # Navigate to notebook
        page.goto(f"https://notebooklm.google.com/notebook/{notebook_id}")
        page.wait_for_timeout(2_000)

        # Click Reports button
        report_button = page.get_by_role(
            "button", name=re.compile("Reports", re.IGNORECASE)
        ).first
        report_button.wait_for(timeout=30_000, state="visible")
        report_button.click()
        page.wait_for_timeout(1_500)

        # Select format
        if format:
            # Try to mirror the UI flow used by Playwright codegen:
            #   - Click the desired report tile
            #   - For templates like "Briefing Doc", click the "Customize Report" button
            #     inside that tile to open the customization dialog.
            try:
                # First, look for a report-customization-tile that contains the format text
                # (e.g. "Briefing Doc", "Study Guide", "Blog Post", etc.)
                format_tile = page.locator("report-customization-tile").filter(
                    has_text=re.compile(re.escape(format), re.IGNORECASE)
                )

                if format_tile.count() > 0:
                    tile = format_tile.first

                    # Prefer the "Customize Report" button inside the tile when it exists,
                    # as this reliably opens the dialog with language + description fields.
                    customize_btn = tile.get_by_label("Customize Report")
                    if customize_btn.count() > 0:
                        customize_btn.first.wait_for(timeout=10_000, state="visible")
                        customize_btn.first.click()
                        page.wait_for_timeout(1_500)
                    else:
                        # Fallback: click the primary action button for the tile
                        primary_btn = tile.get_by_role(
                            "button", name=re.compile(re.escape(format), re.IGNORECASE)
                        )
                        if primary_btn.count() > 0:
                            primary_btn.first.wait_for(timeout=10_000, state="visible")
                            primary_btn.first.click()
                            page.wait_for_timeout(1_500)
                else:
                    # Legacy fallback behaviour: click by button name or generic text match
                    format_button = page.get_by_role("button", name=format)
                    if format_button.count() > 0:
                        format_button.first.wait_for(timeout=10_000, state="visible")
                        format_button.first.click()
                        page.wait_for_timeout(1_500)
                    else:
                        # Fallback: try to find by text content
                        format_locator = (
                            page.locator("button, div, span")
                            .filter(has_text=format)
                            .first
                        )
                        if format_locator.count() > 0:
                            format_locator.click()
                            page.wait_for_timeout(1_500)
            except Exception:
                # If format selection fails, continue – it may already be on the correct screen.
                pass

        # Click the description textbox (Input to describe the kind of)
        desc_textbox = page.get_by_role(
            "textbox", name=re.compile("Input to describe the kind of", re.IGNORECASE)
        )
        if desc_textbox.count() == 0:
            # Fallback: get first textbox
            desc_textbox = page.get_by_role("textbox").first
        desc_textbox.wait_for(timeout=10_000, state="visible")
        desc_textbox.click()
        page.wait_for_timeout(500)

        # Handle language selection if provided
        if language:
            # Click language selector dropdown (#mat-select-value-0)
            lang_selector = page.locator("#mat-select-value-0")
            if lang_selector.count() > 0:
                lang_selector.click()
                page.wait_for_timeout(500)

                # Map language values to display names
                lang_map = {
                    "english": "English (default)",
                    "persian": "فارسی",
                }
                lang_display_name = lang_map.get(language.lower(), language)

                # Click the language option
                lang_option = page.get_by_role("option", name=lang_display_name)
                if lang_option.count() > 0:
                    lang_option.click()
                    page.wait_for_timeout(500)
                else:
                    # Fallback: try mat-option selector
                    # For English, it might be #mat-option-9, but we'll search by text
                    lang_option_locator = page.locator(
                        f'mat-option:has-text("{lang_display_name}")'
                    )
                    if lang_option_locator.count() > 0:
                        lang_option_locator.click()
                        page.wait_for_timeout(500)

        # Fill description if provided
        if description:
            # Click the textbox again to ensure focus
            desc_textbox.click()
            page.wait_for_timeout(300)
            # Clear any existing text and fill with new description
            desc_textbox.fill(description)
            page.wait_for_timeout(500)

        # Click Generate button
        generate_button = page.get_by_role(
            "button", name=re.compile("Generate", re.IGNORECASE)
        )
        generate_button.wait_for(timeout=10_000, state="visible")
        generate_button.click()
        page.wait_for_timeout(2_000)

        return {
            "status": "success",
            "message": f"Report creation started for {notebook_id}.",
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to create report: {exc}") from exc
