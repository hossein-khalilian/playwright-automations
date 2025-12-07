"""Sync slide deck creation for NotebookLM automation."""

import re
from typing import Dict, Optional

from playwright.sync_api import Page

from app.automation.tasks.notebooklm.exceptions import NotebookLMError


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
        sd_button = page.get_by_role(
            "button", name=re.compile("Slide deck|Slides", re.IGNORECASE)
        ).first
        sd_button.wait_for(timeout=30_000, state="visible")
        sd_button.click()
        page.wait_for_timeout(1_000)
        for value in [format, length, language]:
            if value:
                btn = page.locator("button").filter(has_text=value)
                btn.wait_for(timeout=5_000, state="visible")
                btn.click()
        if description:
            desc_input = page.get_by_role("textbox").first
            desc_input.wait_for(timeout=5_000, state="visible")
            desc_input.fill(description)
        generate_button = page.get_by_role(
            "button", name=re.compile("Generate", re.IGNORECASE)
        )
        generate_button.wait_for(timeout=5_000, state="visible")
        generate_button.click()
        page.wait_for_timeout(2_000)
        return {
            "status": "success",
            "message": f"Slide deck creation started for {notebook_id}.",
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to create slide deck: {exc}") from exc
