"""
Browser state management for the FastAPI application.
Stores the initialized browser pages pool, context, and playwright instance.
"""

import queue
import threading
from typing import List, Optional

from playwright.sync_api import BrowserContext, Page, Playwright

# Global state to store browser resources
browser_state: dict[str, Optional[Page | BrowserContext | Playwright | queue.Queue | List[Page]]] = {
    "pages": None,  # Queue of available pages
    "all_pages": None,  # List of all pages for cleanup
    "context": None,
    "playwright": None,
}

# Thread-safe lock for pool operations
_pool_lock = threading.Lock()


def get_browser_page() -> Optional[Page]:
    """
    Get an available browser page from the pool.
    Returns None if no pages are available.
    Note: This is for backward compatibility. Use get_page_from_pool() for new code.
    """
    return get_page_from_pool()


def get_page_from_pool() -> Optional[Page]:
    """
    Get an available browser page from the pool (thread-safe).
    Returns None if no pages are available.
    Caller should return the page using return_page_to_pool() when done.
    """
    pages_queue = browser_state.get("pages")
    if pages_queue is None:
        return None
    
    try:
        # Get page with timeout to avoid blocking indefinitely
        page = pages_queue.get(timeout=1.0)
        return page
    except queue.Empty:
        return None


def return_page_to_pool(page: Page) -> None:
    """
    Return a page to the pool (thread-safe).
    This should be called after using a page obtained from get_page_from_pool().
    """
    pages_queue = browser_state.get("pages")
    if pages_queue is None:
        return
    
    # Check if page is still valid (not closed)
    try:
        if page.is_closed():
            # Page was closed, create a new one
            context = get_browser_context()
            if context:
                new_page = context.new_page()
                pages_queue.put(new_page)
                # Update all_pages list
                with _pool_lock:
                    all_pages = browser_state.get("all_pages", [])
                    if all_pages:
                        try:
                            all_pages.remove(page)
                        except ValueError:
                            pass
                        all_pages.append(new_page)
        else:
            pages_queue.put(page)
    except Exception:
        # Page is invalid, try to create a new one
        context = get_browser_context()
        if context:
            try:
                new_page = context.new_page()
                pages_queue.put(new_page)
                # Update all_pages list
                with _pool_lock:
                    all_pages = browser_state.get("all_pages", [])
                    if all_pages:
                        try:
                            all_pages.remove(page)
                        except ValueError:
                            pass
                        all_pages.append(new_page)
            except Exception:
                pass  # Failed to create replacement page


def get_browser_context() -> Optional[BrowserContext]:
    """Get the initialized browser context from app state."""
    return browser_state.get("context")


def get_playwright() -> Optional[Playwright]:
    """Get the playwright instance from app state."""
    return browser_state.get("playwright")


def get_all_pages() -> List[Page]:
    """Get all pages in the pool (for cleanup purposes)."""
    return browser_state.get("all_pages", [])


def set_browser_resources(
    pages: List[Page],
    context: BrowserContext,
    playwright: Playwright,
) -> None:
    """
    Set the browser resources in app state.
    Args:
        pages: List of pages to add to the pool
        context: Browser context
        playwright: Playwright instance
    """
    with _pool_lock:
        # Create a queue and add all pages to it
        pages_queue = queue.Queue()
        for page in pages:
            pages_queue.put(page)
        
        browser_state["pages"] = pages_queue
        browser_state["all_pages"] = pages.copy()
        browser_state["context"] = context
        browser_state["playwright"] = playwright


def clear_browser_resources() -> None:
    """Clear the browser resources from app state."""
    with _pool_lock:
        # Close all pages
        all_pages = browser_state.get("all_pages", [])
        for page in all_pages:
            try:
                if not page.is_closed():
                    page.close()
            except Exception:
                pass
        
        browser_state["pages"] = None
        browser_state["all_pages"] = None
        browser_state["context"] = None
        browser_state["playwright"] = None

