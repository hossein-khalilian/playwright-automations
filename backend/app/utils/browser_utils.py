"""
Reusable helpers for Google login automations.
"""

import asyncio
import os
import shutil
from pathlib import Path
from typing import Tuple

from playwright.async_api import BrowserContext, Page, Playwright, async_playwright

from app.utils.google import check_google_login_status
from app.utils.system_resolution import get_system_resolution

BASE_DIR = Path(__file__).resolve().parent.parent


async def initialize_page(
    headless: bool = False, user_profile_name="default"
) -> Tuple[Page, BrowserContext, Playwright]:
    """
    Initialize a browser page with persistent user data and stealth mode.

    Args:
        headless: Whether to run the browser in headless mode (default: False)
        user_profile_name: Name of the user profile directory (default: "default")

    Returns:
        Tuple of (page, context, playwright). The caller is responsible for closing
        the context and stopping the playwright instance when done.
    """
    # Create user data directory if it doesn't exist
    CONTEXT_PATH = BASE_DIR / "automation" / "browser_profiles" / user_profile_name
    CONTEXT_PATH.mkdir(parents=True, exist_ok=True)

    playwright = await async_playwright().start()

    # Use a realistic Chrome user agent
    user_agent = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    )

    # Get system resolution for viewport
    viewport = get_system_resolution()

    context = await playwright.chromium.launch_persistent_context(
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

    page = context.pages[0] if context.pages else await context.new_page()

    # Apply comprehensive stealth mode using CDP
    await setup_stealth_mode(context, page)

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


async def setup_stealth_mode(context: BrowserContext, page: Page) -> None:
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
        cdp_session = await context.new_cdp_session(page)
        await cdp_session.send(
            "Page.addScriptToEvaluateOnNewDocument", {"source": stealth_script}
        )
    except Exception as exc:  # pragma: no cover - best effort
        print(f"[!] Warning: Could not set up CDP stealth: {exc}")

    # Also add via context init script for additional coverage
    await context.add_init_script(stealth_script)


async def main():
    print("[*] Initializing browser with persistent user data and stealth mode...")
    page = None
    context = None
    playwright = None
    
    try:
        # Use a test profile to avoid conflicts with running FastAPI app
        test_profile = "test_standalone"
        print(f"[*] Using test profile: {test_profile}")
        page, context, playwright = await initialize_page(
            headless=False, user_profile_name=test_profile
        )
        print("[+] Browser initialized successfully!")
        print("[*] Browser is now open. Press Ctrl+C to close.")

        # Navigate to a test page to verify it works
        await page.goto("https://www.google.com")
        print(f"[*] Navigated to: {page.url}")
        result = await check_google_login_status(page)
        print(f"[*] Google login status: {result}")
        # Keep the browser open - use asyncio to run input in executor to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, input, "\n[*] Press Enter to close the browser..."
        )
    except KeyboardInterrupt:
        print("\n[*] Closing browser...")
    except Exception as exc:
        error_msg = str(exc)
        if "Target page, context or browser has been closed" in error_msg:
            print("\n[!] Error: Browser profile is locked or in use by another process.")
            print("[!] This usually happens when:")
            print("    - The FastAPI app is running and using the same profile")
            print("    - Another browser instance is using the profile")
            print("[!] Solution: Stop other processes using the profile, or use a different profile name.")
        elif "profile appears to be in use" in error_msg.lower():
            print("\n[!] Error: Browser profile is locked by another Chromium process.")
            print("[!] Solution: Close other browser instances or stop the FastAPI app.")
        else:
            print(f"\n[!] Error: {exc}")
    finally:
        # Clean up resources
        if context:
            try:
                await context.close()
            except Exception as exc:
                print(f"[!] Warning: Error closing context: {exc}")
        if playwright:
            try:
                await playwright.stop()
            except Exception as exc:
                print(f"[!] Warning: Error stopping playwright: {exc}")
        print("[+] Browser closed.")


if __name__ == "__main__":
    asyncio.run(main())
