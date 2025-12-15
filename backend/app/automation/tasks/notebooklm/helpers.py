"""Sync helper utilities for NotebookLM automation."""

import re
from typing import Optional

from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from app.automation.tasks.notebooklm.exceptions import NotebookLMError


def navigate_to_notebook(page: Page, notebook_id: str) -> None:
    """
    Navigate to a specific notebook page.

    Args:
        page: The Playwright Page object
        notebook_id: The ID of the notebook to navigate to

    Raises:
        NotebookLMError: If navigation fails
    """
    try:
        page.goto(
            f"https://notebooklm.google.com/notebook/{notebook_id}",
            wait_until="domcontentloaded",
            timeout=30_000,
        )
        page.wait_for_timeout(1_000)
    except Exception as exc:
        raise NotebookLMError(
            f"Failed to navigate to notebook {notebook_id}: {exc}"
        ) from exc


def navigate_to_main_page(page: Page) -> None:
    """
    Navigate to the main NotebookLM page.

    Args:
        page: The Playwright Page object

    Raises:
        NotebookLMError: If navigation fails
    """
    try:
        page.goto(
            "https://notebooklm.google.com/",
            wait_until="domcontentloaded",
            timeout=30_000,
        )
        page.wait_for_timeout(1_000)
    except Exception as exc:
        raise NotebookLMError("Failed to navigate to NotebookLM main page") from exc


def close_dialogs(page: Page) -> None:
    """
    Close any dialogs that might appear on the page.
    
    Handles:
    - The "add source" dialog that appears when a notebook has no sources
      (detected by URL with ?addSource=true or textbox "Discover sources based on the")
    - Generic "Close dialog" buttons
    
    Args:
        page: The Playwright Page object
    """
    # Wait a bit for any dialogs to appear
    page.wait_for_timeout(500)
    
    # Check if URL has addSource=true parameter (indicates add source dialog)
    current_url = page.url
    has_add_source_param = "addSource=true" in current_url
    
    # Try to close the "add source" dialog first
    # This dialog appears when a notebook has no sources
    try:
        # Look for the textbox that appears in the add source dialog
        discover_textbox = page.get_by_role("textbox", name="Discover sources based on the")
        discover_textbox.wait_for(timeout=3_000, state="visible")
        # Press Escape to close the dialog
        discover_textbox.press("Escape")
        page.wait_for_timeout(500)
        # Wait for URL to update (remove addSource parameter)
        if has_add_source_param:
            try:
                page.wait_for_function(
                    "() => !window.location.href.includes('addSource=true')",
                    timeout=3_000,
                )
            except PlaywrightTimeoutError:
                pass
    except PlaywrightTimeoutError:
        # Add source dialog might not be present, which is fine
        pass
    
    # Also handle the add source dialog if URL indicates it
    if has_add_source_param:
        try:
            # Try pressing Escape on the page itself as a fallback
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
            # Wait for URL to update
            try:
                page.wait_for_function(
                    "() => !window.location.href.includes('addSource=true')",
                    timeout=3_000,
                )
            except PlaywrightTimeoutError:
                pass
        except Exception:
            pass
    
    # Handle generic "Close dialog" buttons
    try:
        close_button = page.get_by_role("button", name="Close dialog")
        close_button.wait_for(timeout=2_000, state="visible")
        close_button.click()
        page.wait_for_timeout(500)
    except PlaywrightTimeoutError:
        # Dialog might not appear, which is fine
        pass


def extract_notebook_id_from_url(page: Page) -> Optional[str]:
    """
    Extract notebook ID from the current page URL.

    Args:
        page: The Playwright Page object

    Returns:
        The notebook ID if found, None otherwise
    """
    match = re.search(r"/notebook/([^/?]+)", page.url)
    return match.group(1) if match else None
