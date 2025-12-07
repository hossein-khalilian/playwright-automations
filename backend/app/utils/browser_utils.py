"""
Reusable helpers for Google login automations.
"""

from pathlib import Path
from typing import Tuple

from playwright.sync_api import BrowserContext as SyncBrowserContext
from playwright.sync_api import Page as SyncPage
from playwright.sync_api import Playwright as SyncPlaywright
from playwright.sync_api import sync_playwright

from app.utils.google import check_google_login_status_sync
from app.utils.system_resolution import get_system_resolution

BASE_DIR = Path(__file__).resolve().parents[3]


def setup_stealth_mode_sync(context: SyncBrowserContext, page: SyncPage) -> None:
    """
    Sync variant of stealth setup using CDP.
    """
    stealth_script = """
    (function() {
        'use strict';
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        try { delete navigator.__proto__.webdriver; } catch(e) {}
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
        Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => {
            if (parameters.name === 'notifications') {
                return Promise.resolve({ state: Notification.permission });
            }
            return originalQuery(parameters);
        };
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
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) { return 'Intel Inc.'; }
            if (parameter === 37446) { return 'Intel Iris OpenGL Engine'; }
            return getParameter.call(this, parameter);
        };
    })();
    """
    try:
        cdp_session = context.new_cdp_session(page)
        cdp_session.send(
            "Page.addScriptToEvaluateOnNewDocument", {"source": stealth_script}
        )
    except Exception:
        # Best-effort; keep pool usable even if CDP script fails
        pass
    context.add_init_script(stealth_script)


def initialize_page_sync(
    headless: bool = False, user_profile_name: str = "default"
) -> Tuple[SyncPage, SyncBrowserContext, SyncPlaywright]:
    """
    Sync variant of initialize_page using playwright.sync_api.
    """
    CONTEXT_PATH = BASE_DIR / "browser_profiles" / user_profile_name
    CONTEXT_PATH.mkdir(parents=True, exist_ok=True)

    playwright = sync_playwright().start()

    user_agent = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    )
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
    setup_stealth_mode_sync(context, page)
    return page, context, playwright


def main():
    print("[*] Initializing browser with persistent user data and stealth mode...")
    page = None
    context = None
    playwright = None

    try:
        # Use a test profile to avoid conflicts with running FastAPI app
        test_profile = "test_google_login"
        print(f"[*] Using test profile: {test_profile}")
        page, context, playwright = initialize_page_sync(
            headless=False, user_profile_name=test_profile
        )
        print("[+] Browser initialized successfully!")
        print("[*] Browser is now open. Press Ctrl+C to close.")

        # Navigate to a test page to verify it works
        page.goto("https://www.google.com")
        print(f"[*] Navigated to: {page.url}")
        result = check_google_login_status_sync(page)
        print(f"[*] Google login status: {result}")
        # Keep the browser open - use asyncio to run input in executor to avoid blocking
        input("\n[*] Press Enter to close the browser...")
    except KeyboardInterrupt:
        print("\n[*] Closing browser...")
    except Exception as exc:
        error_msg = str(exc)
        if "Target page, context or browser has been closed" in error_msg:
            print(
                "\n[!] Error: Browser profile is locked or in use by another process."
            )
            print("[!] This usually happens when:")
            print("    - The FastAPI app is running and using the same profile")
            print("    - Another browser instance is using the profile")
            print(
                "[!] Solution: Stop other processes using the profile, or use a different profile name."
            )
        elif "profile appears to be in use" in error_msg.lower():
            print("\n[!] Error: Browser profile is locked by another Chromium process.")
            print(
                "[!] Solution: Close other browser instances or stop the FastAPI app."
            )
        else:
            print(f"\n[!] Error: {exc}")
    finally:
        # Clean up resources
        if context:
            try:
                context.close()
            except Exception as exc:
                print(f"[!] Warning: Error closing context: {exc}")
        if playwright:
            try:
                playwright.stop()
            except Exception as exc:
                print(f"[!] Warning: Error stopping playwright: {exc}")
        print("[+] Browser closed.")


if __name__ == "__main__":
    main()
