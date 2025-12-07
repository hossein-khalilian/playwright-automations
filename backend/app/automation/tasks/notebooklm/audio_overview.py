"""Sync audio overview creation for NotebookLM automation."""

import re
from typing import Dict, Optional

from playwright.sync_api import Page

from app.automation.tasks.notebooklm.exceptions import NotebookLMError


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
        page.goto(f"https://notebooklm.google.com/notebook/{notebook_id}")
        audio_button = page.get_by_role(
            "button", name=re.compile("Audio overview", re.IGNORECASE)
        ).first
        audio_button.wait_for(timeout=30_000, state="visible")
        audio_button.click()
        page.wait_for_timeout(1_000)
        for value in [audio_format, language, length]:
            if value:
                btn = page.locator("button").filter(has_text=value)
                btn.wait_for(timeout=5_000, state="visible")
                btn.click()
        if focus_text:
            text_input = page.get_by_role("textbox").first
            text_input.wait_for(timeout=5_000, state="visible")
            text_input.fill(focus_text)
        generate_button = page.get_by_role(
            "button", name=re.compile("Generate", re.IGNORECASE)
        )
        generate_button.wait_for(timeout=5_000, state="visible")
        generate_button.click()
        page.wait_for_timeout(2_000)
        return {
            "status": "success",
            "message": f"Audio overview creation started for {notebook_id}.",
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to create audio overview: {exc}") from exc
