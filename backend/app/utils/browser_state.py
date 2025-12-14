"""
Browser state management for the FastAPI application.
Stores the initialized browser pages pool, each with its own context and playwright instance.
"""

import queue
import threading
from typing import Dict, List, Optional

from playwright.sync_api import BrowserContext, Page, Playwright

# Global state to store browser resources
browser_state: dict[str, Optional[Page | BrowserContext | Playwright | queue.Queue | List[Page] | Dict[Page, BrowserContext]]] = {
    "pages": None,  # Queue of available pages
    "all_pages": None,  # List of all pages for cleanup
    "contexts": None,  # Dictionary mapping page to its context
    "all_contexts": None,  # List of all contexts for cleanup
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
            # Page was closed, create a new one from the same context
            page_to_context = browser_state.get("contexts", {})
            context = page_to_context.get(page)
            if context:
                try:
                    new_page = context.new_page()
                    pages_queue.put(new_page)
                    # Update mappings
                    with _pool_lock:
                        all_pages = browser_state.get("all_pages", [])
                        if all_pages:
                            try:
                                all_pages.remove(page)
                            except ValueError:
                                pass
                            all_pages.append(new_page)
                        # Update context mapping
                        page_to_context[new_page] = context
                        if page in page_to_context:
                            del page_to_context[page]
                except Exception:
                    pass  # Failed to create replacement page
        else:
            pages_queue.put(page)
    except Exception:
        # Page is invalid, try to create a new one from the same context
        page_to_context = browser_state.get("contexts", {})
        context = page_to_context.get(page)
        if context:
            try:
                new_page = context.new_page()
                pages_queue.put(new_page)
                # Update mappings
                with _pool_lock:
                    all_pages = browser_state.get("all_pages", [])
                    if all_pages:
                        try:
                            all_pages.remove(page)
                        except ValueError:
                            pass
                        all_pages.append(new_page)
                    # Update context mapping
                    page_to_context[new_page] = context
                    if page in page_to_context:
                        del page_to_context[page]
            except Exception:
                pass  # Failed to create replacement page


def get_browser_context() -> Optional[BrowserContext]:
    """
    Get a browser context from app state.
    For backward compatibility, returns the first context if multiple exist.
    """
    all_contexts = browser_state.get("all_contexts", [])
    if all_contexts:
        return all_contexts[0]
    return None


def get_all_contexts() -> List[BrowserContext]:
    """Get all browser contexts from app state."""
    return browser_state.get("all_contexts", [])


def get_playwright() -> Optional[Playwright]:
    """Get the playwright instance from app state."""
    return browser_state.get("playwright")


def get_all_pages() -> List[Page]:
    """Get all pages in the pool (for cleanup purposes)."""
    return browser_state.get("all_pages", [])


def set_browser_resources(
    pages: List[Page],
    contexts: List[BrowserContext],
    playwright: Playwright,
) -> None:
    """
    Set the browser resources in app state.
    Each page should have a corresponding context at the same index.
    Args:
        pages: List of pages to add to the pool (one per browser)
        contexts: List of browser contexts (one per browser, same length as pages)
        playwright: Playwright instance
    """
    with _pool_lock:
        if len(pages) != len(contexts):
            raise ValueError("Number of pages must match number of contexts")
        
        # Create a queue and add all pages to it
        pages_queue = queue.Queue()
        for page in pages:
            pages_queue.put(page)
        
        # Create mapping from page to its context
        page_to_context = {page: context for page, context in zip(pages, contexts)}
        
        browser_state["pages"] = pages_queue
        browser_state["all_pages"] = pages.copy()
        browser_state["contexts"] = page_to_context
        browser_state["all_contexts"] = contexts.copy()
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
        
        # Close all contexts
        all_contexts = browser_state.get("all_contexts", [])
        for context in all_contexts:
            try:
                context.close()
            except Exception:
                pass  # Context might already be closed
        
        browser_state["pages"] = None
        browser_state["all_pages"] = None
        browser_state["contexts"] = None
        browser_state["all_contexts"] = None
        browser_state["playwright"] = None

