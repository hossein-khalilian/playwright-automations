import random
import time
from pathlib import Path
from typing import Dict, Optional

from playwright.sync_api import BrowserContext, Page, Playwright

from automation.utils.system_resolution import get_system_resolution

# Base directory for automation backend
BASE_DIR = Path(__file__).resolve().parent.parent

# Path to store browser context (persistent profile)
DEFAULT_CONTEXT_PATH = BASE_DIR / "browser_profiles" / "default"


def setup_stealth_mode(context: BrowserContext, page: Page) -> None:
    """
    Inject comprehensive stealth scripts using CDP to make the browser appear as a real user browser.
    This helps bypass Google's automation detection.
    """
    # Comprehensive stealth script that runs before any page script
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
    except Exception as e:
        print(f"[!] Warning: Could not set up CDP stealth: {e}")

    # Also add via context init script for additional coverage
    context.add_init_script(stealth_script)


def get_browser_context(
    playwright: Playwright,
    profile_name: str = "default",
    headless: bool = False,
    user_agent: Optional[str] = None,
    viewport: Optional[Dict[str, int]] = None,
) -> BrowserContext:
    """
    Create a persistent browser context with stealth mode configuration.
    
    Args:
        playwright: Playwright instance
        profile_name: Name of the browser profile to use (default: "default")
        headless: Run browser in headless mode
        user_agent: Custom user agent string (default: realistic Chrome UA)
        viewport: Custom viewport size (default: system resolution)
        
    Returns:
        BrowserContext with persistent profile and stealth mode
    """
    context_path = BASE_DIR / "browser_profiles" / profile_name
    
    print(f"[*] Using browser profile at: {context_path}")

    # Use a realistic Chrome user agent if not provided
    if user_agent is None:
        user_agent = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        )

    # Get system resolution for viewport if not provided
    if viewport is None:
        viewport = get_system_resolution()

    context = playwright.chromium.launch_persistent_context(
        user_data_dir=str(context_path),
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

    return context


def initialize_browser_session(
    context: BrowserContext,
    initial_url: str = "https://www.google.com",
) -> Page:
    """
    Initialize a browser session with stealth mode and navigate to initial page.
    
    Args:
        context: Browser context
        initial_url: URL to navigate to initially (default: Google)
        
    Returns:
        Page object with stealth mode enabled
    """
    page = context.pages[0] if context.pages else context.new_page()

    # Navigate to a neutral page first to establish normal browsing pattern
    print("[*] Establishing browser session...")
    page.goto(initial_url, wait_until="domcontentloaded", timeout=10000)
    time.sleep(random.uniform(1.0, 2.0))

    # Apply comprehensive stealth mode using CDP
    setup_stealth_mode(context, page)

    # Small delay to let stealth scripts initialize
    time.sleep(0.5)

    return page



