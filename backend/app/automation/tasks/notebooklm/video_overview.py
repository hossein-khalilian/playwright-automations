"""Sync video overview creation for NotebookLM automation."""

import re
from typing import Dict, Optional

from playwright.sync_api import Page

from app.automation.tasks.notebooklm.exceptions import NotebookLMError


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
        video_button = page.get_by_role(
            "button", name=re.compile("Video overview", re.IGNORECASE)
        ).first
        video_button.wait_for(timeout=30_000, state="visible")
        video_button.click()
        page.wait_for_timeout(1_000)
        for value in [video_format, language, visual_style]:
            if value:
                btn = page.locator("button").filter(has_text=value)
                btn.wait_for(timeout=5_000, state="visible")
                btn.click()
        if custom_style_description:
            style_input = page.get_by_role("textbox").first
            style_input.wait_for(timeout=5_000, state="visible")
            style_input.fill(custom_style_description)
        if focus_text:
            text_input = page.get_by_role("textbox").nth(1)
            text_input.fill(focus_text)
        generate_button = page.get_by_role(
            "button", name=re.compile("Generate", re.IGNORECASE)
        )
        generate_button.wait_for(timeout=5_000, state="visible")
        generate_button.click()
        page.wait_for_timeout(2_000)
        return {
            "status": "success",
            "message": f"Video overview creation started for {notebook_id}.",
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to create video overview: {exc}") from exc
