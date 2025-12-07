"""
Synchronous browser pool for Celery tasks.
Creates a small pool of Playwright contexts and reuses them across tasks.
"""

import queue
import threading
from dataclasses import dataclass
from typing import Optional

from playwright.sync_api import BrowserContext, Page, Playwright

from app.utils.browser_utils import initialize_page_sync


@dataclass
class BrowserResource:
    page: Page
    context: BrowserContext
    playwright: Playwright
    profile_name: str
    index: int


_pool_queue: Optional[queue.Queue[BrowserResource]] = None
_pool_lock = threading.Lock()


def _create_resource(idx: int, headless: bool, base_profile: str) -> BrowserResource:
    profile_name = f"{base_profile}_pool_{idx}"
    page, context, playwright = initialize_page_sync(
        headless=headless, user_profile_name=profile_name
    )
    return BrowserResource(
        page=page,
        context=context,
        playwright=playwright,
        profile_name=profile_name,
        index=idx,
    )


def _refresh_resource_if_needed(
    resource: BrowserResource, headless: bool, base_profile: str
) -> BrowserResource:
    """Recreate the resource if the context is closed or invalid."""
    recreate = False
    try:
        recreate = resource.context.is_closed()
    except Exception:
        recreate = True

    if recreate:
        return _create_resource(resource.index, headless, base_profile)

    return resource


def ensure_pool_initialized(
    pool_size: int = 1, headless: bool = True, base_profile: str = "default"
) -> None:
    """Initialize the global pool once."""
    global _pool_queue
    if _pool_queue is not None:
        return

    with _pool_lock:
        if _pool_queue is not None:
            return

        _pool_queue = queue.Queue()
        for i in range(pool_size):
            resource = _create_resource(i, headless, base_profile)
            _pool_queue.put(resource)


def acquire_browser(
    headless: bool = True, base_profile: str = "default"
) -> BrowserResource:
    """Acquire a browser resource from the pool."""
    if _pool_queue is None:
        raise RuntimeError(
            "Browser pool not initialized. Call ensure_pool_initialized first."
        )

    resource: BrowserResource = _pool_queue.get()
    return _refresh_resource_if_needed(resource, headless, base_profile)


def release_browser(resource: BrowserResource) -> None:
    """Return a browser resource to the pool."""
    if _pool_queue is None:
        return
    _pool_queue.put(resource)


def shutdown_pool() -> None:
    """Close all resources and clear the pool."""
    global _pool_queue
    if _pool_queue is None:
        return

    resources: list[BrowserResource] = []
    while True:
        try:
            resources.append(_pool_queue.get_nowait())
        except queue.Empty:
            break

    _pool_queue = None

    for resource in resources:
        try:
            if not resource.context.is_closed():
                resource.context.close()
        except Exception:
            pass
        try:
            resource.playwright.stop()
        except Exception:
            pass
