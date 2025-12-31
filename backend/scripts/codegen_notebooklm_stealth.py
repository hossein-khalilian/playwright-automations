#!/usr/bin/env python3
"""
Codegen script for notebooklm.google.com using initialize_page_sync with stealth mode.

This script uses Playwright's Python API with stealth mode enabled, providing a codegen-like
interface that maintains stealth mode throughout the session.

Usage:
    python3 backend/scripts/codegen_notebooklm_stealth.py [URL]

Arguments:
    URL     Optional URL to open (default: https://notebooklm.google.com)

Examples:
    python3 backend/scripts/codegen_notebooklm_stealth.py
    python3 backend/scripts/codegen_notebooklm_stealth.py https://notebooklm.google.com
    python3 backend/scripts/codegen_notebooklm_stealth.py https://example.com

The browser will open with stealth mode enabled. Use the browser console or Playwright Inspector
(PWDEBUG=1) to debug and see generated code.
"""

import sys
import argparse
import time
from pathlib import Path

# Add backend to path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.utils.browser_utils import initialize_page_sync
from app.utils.google import check_google_login_status_sync
from app.automation.tasks.google_login import check_or_login_google_sync


def main():
    """Run codegen with stealth mode browser configuration."""
    parser = argparse.ArgumentParser(
        description="Run Playwright codegen with stealth mode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s
  %(prog)s https://notebooklm.google.com
  %(prog)s https://example.com
        """
    )
    parser.add_argument(
        "url",
        nargs="?",
        default="https://notebooklm.google.com",
        help="URL to open in codegen (default: https://notebooklm.google.com)"
    )
    
    args = parser.parse_args()
    target_url = args.url
    
    print("[*] Starting codegen with stealth mode browser configuration...")
    print(f"[*] Target URL: {target_url}")
    print("[*] This will show the clean codegen preview window (same as .sh script).\n")
    
    profile_name = "test_google_login"
    BACKEND_DIR = Path(__file__).resolve().parent.parent  # backend/
    profile_path = BACKEND_DIR / "browser_profiles" / profile_name
    
    # Ensure profile exists and is initialized with stealth mode and Google login
    profile_needs_init = not profile_path.exists() or not any(profile_path.iterdir())
    
    if profile_needs_init:
        print(f"[*] Profile directory doesn't exist or is empty. Initializing with stealth mode...")
        profile_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize browser with stealth mode enabled
    print(f"[*] Initializing browser with profile: {profile_name}")
    print("[*] Stealth mode will be active throughout the session.\n")
    page, context, playwright = initialize_page_sync(
        headless=False,
        user_profile_name=profile_name
    )
    
    try:
        # Check if Google is logged in
        print("[*] Checking if Google is already logged in...")
        if check_google_login_status_sync(page):
            print("[+] Google is already logged in.")
        else:
            print("[*] Google is not logged in. Attempting to login...")
            # This will check login status and login if needed (using GMAIL_EMAIL and GMAIL_PASSWORD from env)
            check_or_login_google_sync(page)
            print("[+] Google login check completed.")
        
        # Navigate to target URL
        print(f"\n[*] Navigating to: {target_url}")
        page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
        print("[+] Page loaded with stealth mode enabled.")
        
        # Verify stealth mode is working
        print("\n[*] Verifying stealth mode...")
        stealth_check = page.evaluate("""
            () => {
                return {
                    webdriver: navigator.webdriver,
                    plugins: navigator.plugins.length,
                    chrome: typeof window.chrome !== 'undefined',
                    languages: navigator.languages
                };
            }
        """)
        print(f"[*] Stealth mode check: webdriver={stealth_check.get('webdriver')}, "
              f"chrome={stealth_check.get('chrome')}, plugins={stealth_check.get('plugins')}")
        
        if stealth_check.get('webdriver') is None and stealth_check.get('chrome'):
            print("[+] Stealth mode is ACTIVE - browser appears as a normal browser")
        else:
            print("[!] Warning: Stealth mode may not be fully active")
        
        # Enable Playwright Inspector mode if PWDEBUG is set
        import os
        if os.environ.get('PWDEBUG') == '1':
            print("\n[*] PWDEBUG mode enabled - Inspector will show generated code")
        else:
            print("\n[*] Tip: Set PWDEBUG=1 to enable Playwright Inspector for codegen")
            print("    Example: PWDEBUG=1 python3 backend/scripts/codegen_notebooklm_stealth.py")
        
        print("\n" + "="*70)
        print("[*] Browser is now open with STEALTH MODE ACTIVE")
        print("[*] Stealth scripts are injected and active in this session")
        print("[*] Navigate and interact with the page")
        print("[*] Press Ctrl+C to close the browser")
        print("="*70 + "\n")
        
        # Keep browser open and wait for user interaction
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[*] Closing browser...")
        
    except Exception as exc:
        print(f"\n[!] Error: {exc}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up resources
        try:
            context.close()
        except Exception:
            pass
        try:
            playwright.stop()
        except Exception:
            pass
        print("[+] Browser closed.")


if __name__ == "__main__":
    main()

