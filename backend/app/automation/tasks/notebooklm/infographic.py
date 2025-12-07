"""Sync infographic creation for NotebookLM automation."""

import re
from typing import Dict, Optional

from playwright.sync_api import Page

from app.automation.tasks.notebooklm.exceptions import NotebookLMError


def create_infographic(
    page: Page,
    notebook_id: str,
    language: Optional[str] = None,
    orientation: Optional[str] = None,
    detail_level: Optional[str] = None,
    description: Optional[str] = None,
) -> Dict[str, str]:
    """
    Create infographic artifact.

    Args:
        page: The Playwright Page object
        notebook_id: The ID of the notebook
        language: Language for the infographic
        orientation: Orientation (portrait/landscape)
        detail_level: Level of detail
        description: Custom description

    Returns:
        Dictionary with status and message

    Raises:
        NotebookLMError: If infographic creation fails
    """
    try:
        page.goto(f"https://notebooklm.google.com/notebook/{notebook_id}")
        inf_button = page.get_by_role(
            "button", name=re.compile("Infographic", re.IGNORECASE)
        ).first
        inf_button.wait_for(timeout=30_000, state="visible")
        inf_button.click()
        page.wait_for_timeout(1_000)
        for value in [language, orientation, detail_level]:
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
            "message": f"Infographic creation started for {notebook_id}.",
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to create infographic: {exc}") from exc
