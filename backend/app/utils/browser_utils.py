"""
Reusable helpers for Google login automations.
"""

import os
import shutil
from pathlib import Path
from typing import Tuple

from app.utils.system_resolution import get_system_resolution
from playwright.sync_api import BrowserContext, Page, Playwright, sync_playwright

BASE_DIR = Path(__file__).resolve().parent.parent


def initialize_page(
    headless: bool = False, user_profile_name="default"
) -> Tuple[Page, BrowserContext, Playwright]:
    """
    Initialize a browser page with persistent user data and stealth mode.

    Args:
        headless: Whether to run the browser in headless mode (default: False)

    Returns:
        Tuple of (page, context, playwright). The caller is responsible for closing
        the context and stopping the playwright instance when done.
    """
    # Create user data directory if it doesn't exist
    CONTEXT_PATH = BASE_DIR / "automation" / "browser_profiles" / user_profile_name
    CONTEXT_PATH.mkdir(parents=True, exist_ok=True)

    playwright = sync_playwright().start()

    # Use a realistic Chrome user agent
    user_agent = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    )

    # Get system resolution for viewport
    viewport = get_system_resolution()

    context = playwright.chromium.launch_persistent_context(
        user_data_dir=str(CONTEXT_PATH),
        headless=headless,
        viewport=viewport,
        user_agent=user_agent,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-infobars",
            "--exclude-switches=enable-automation",
            "--start-maximized",
        ],
        locale="en-US",
        timezone_id="America/New_York",
        extra_http_headers={
            "Accept-Language": "en-US,en;q=0.9",
        },
    )

    page = context.pages[0] if context.pages else context.new_page()

    # Apply comprehensive stealth mode using CDP
    setup_stealth_mode(context, page)

    return page, context, playwright


def clear_user_profile(user_profile_name: str = "default") -> None:
    """Delete the saved persistent browser profile directory."""
    CONTEXT_PATH = BASE_DIR / "automation" / "browser_profiles" / user_profile_name
    context_path_str = str(CONTEXT_PATH)
    if os.path.exists(context_path_str):
        shutil.rmtree(context_path_str)
        print(f"[+] Cleared user profile from {context_path_str}")
    else:
        print("[*] No user profile found.")


def setup_stealth_mode(context: BrowserContext, page: Page) -> None:
    """
    Inject comprehensive stealth scripts using CDP to make the browser appear as a real user browser.
    This helps bypass Google's automation detection.
    """
    stealth_script = """
    (function() {
        'use strict';

        // Remove webdriver property completely - this is the most important
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });

        // Delete webdriver from prototype chain
        try {
            delete navigator.__proto__.webdriver;
        } catch(e) {}

        // Override plugins to look real
        Object.defineProperty(navigator, 'plugins', {
            get: () => {
                const plugins = [
                    { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
                    { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
                    { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' }
                ];
                plugins.item = function(index) { return this[index] || null; };
                plugins.namedItem = function(name) {
                    for (let i = 0; i < this.length; i++) {
                        if (this[i].name === name) return this[i];
                    }
                    return null;
                };
                return plugins;
            }
        });

        // Override languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });

        // Override permissions API
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => {
            if (parameters.name === 'notifications') {
                return Promise.resolve({ state: Notification.permission });
            }
            return originalQuery(parameters);
        };

        // Full Chrome object - Google checks for this
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {
                isInstalled: false,
                InstallState: {
                    DISABLED: "disabled",
                    INSTALLED: "installed",
                    NOT_INSTALLED: "not_installed"
                },
                RunningState: {
                    CANNOT_RUN: "cannot_run",
                    READY_TO_RUN: "ready_to_run",
                    RUNNING: "running"
                }
            }
        };

        // Override WebGL vendor/renderer
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) {
                return 'Intel Inc.';
            }
            if (parameter === 37446) {
                return 'Intel Iris OpenGL Engine';
            }
            return getParameter.call(this, parameter);
        };
    })();
    """

    # Inject via CDP which runs before page scripts - this is critical
    try:
        cdp_session = context.new_cdp_session(page)
        cdp_session.send(
            "Page.addScriptToEvaluateOnNewDocument", {"source": stealth_script}
        )
    except Exception as exc:  # pragma: no cover - best effort
        print(f"[!] Warning: Could not set up CDP stealth: {exc}")

    # Also add via context init script for additional coverage
    context.add_init_script(stealth_script)


if __name__ == "__main__":
    print("[*] Initializing browser with persistent user data and stealth mode...")
    page, context, playwright = initialize_page(headless=False)
    print("[+] Browser initialized successfully!")
    print("[*] Browser is now open. Press Ctrl+C to close.")

    try:
        # Navigate to a test page to verify it works
        page.goto("https://www.google.com")
        print(f"[*] Navigated to: {page.url}")
        # Keep the browser open
        input("\n[*] Press Enter to close the browser...")
    except KeyboardInterrupt:
        print("\n[*] Closing browser...")
    finally:
        context.close()
        playwright.stop()
        print("[+] Browser closed.")
