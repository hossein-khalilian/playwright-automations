"""
Browser state management for the FastAPI application.
Stores the initialized browser page, context, and playwright instance.
"""

from typing import Optional

from playwright.sync_api import BrowserContext, Page, Playwright

# Global state to store browser resources
browser_state: dict[str, Optional[Page | BrowserContext | Playwright]] = {
    "page": None,
    "context": None,
    "playwright": None,
}


def get_browser_page() -> Optional[Page]:
    """Get the initialized browser page from app state."""
    return browser_state.get("page")


def get_browser_context() -> Optional[BrowserContext]:
    """Get the initialized browser context from app state."""
    return browser_state.get("context")


def get_playwright() -> Optional[Playwright]:
    """Get the playwright instance from app state."""
    return browser_state.get("playwright")


def set_browser_resources(
    page: Page,
    context: BrowserContext,
    playwright: Playwright,
) -> None:
    """Set the browser resources in app state."""
    browser_state["page"] = page
    browser_state["context"] = context
    browser_state["playwright"] = playwright


def clear_browser_resources() -> None:
    """Clear the browser resources from app state."""
    browser_state["page"] = None
    browser_state["context"] = None
    browser_state["playwright"] = None

