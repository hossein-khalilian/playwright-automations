"""Sync mind map creation for NotebookLM automation."""

import re
from typing import Dict

from playwright.sync_api import Page

from app.automation.tasks.notebooklm.exceptions import NotebookLMError


def create_mindmap(page: Page, notebook_id: str) -> Dict[str, str]:
    """
    Create mind map artifact.

    Args:
        page: The Playwright Page object
        notebook_id: The ID of the notebook

    Returns:
        Dictionary with status and message

    Raises:
        NotebookLMError: If mind map creation fails
    """
    try:
        page.goto(f"https://notebooklm.google.com/notebook/{notebook_id}")
        mind_button = page.get_by_role(
            "button", name=re.compile("Mind map", re.IGNORECASE)
        ).first
        mind_button.wait_for(timeout=30_000, state="visible")
        mind_button.click()
        page.wait_for_timeout(2_000)
        return {
            "status": "success",
            "message": f"Mind map creation started for {notebook_id}.",
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to create mind map: {exc}") from exc
