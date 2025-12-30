#!/usr/bin/env python3
"""
Codegen script for notebooklm.google.com using initialize_page_sync with stealth mode.

This script runs the standard Playwright codegen CLI (which shows the clean code preview)
but ensures the browser profile is initialized with stealth mode settings first.

Usage:
    python3 backend/scripts/codegen_notebooklm_stealth.py [URL]

Arguments:
    URL     Optional URL to open (default: https://notebooklm.google.com)

Examples:
    python3 backend/scripts/codegen_notebooklm_stealth.py
    python3 backend/scripts/codegen_notebooklm_stealth.py https://notebooklm.google.com
    python3 backend/scripts/codegen_notebooklm_stealth.py https://example.com

The codegen window will show a clean preview of generated code (same format as .sh script).
Note: The JavaScript stealth scripts are applied at runtime via initialize_page_sync,
so the profile needs to be used with initialize_page_sync first to have full stealth mode.
"""

import sys
import subprocess
import argparse
from pathlib import Path

# Add backend to path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.utils.browser_utils import initialize_page_sync


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
    BASE_DIR = Path(__file__).resolve().parents[2]
    profile_path = BASE_DIR / "browser_profiles" / profile_name
    
    # Ensure profile exists and is initialized with stealth mode
    if not profile_path.exists() or not any(profile_path.iterdir()):
        print(f"[*] Profile directory doesn't exist or is empty. Initializing with stealth mode...")
        profile_path.mkdir(parents=True, exist_ok=True)
        # Initialize browser once to set up the profile with stealth mode
        page, context, playwright = initialize_page_sync(
            headless=False,
            user_profile_name=profile_name
        )
        # Just initialize and close - this sets up the profile
        context.close()
        playwright.stop()
        print("[+] Profile initialized with stealth mode settings.")
    else:
        print(f"[+] Using existing profile: {profile_name}")
    
    # Now run codegen - it will use the profile
    # Note: The standard codegen CLI cannot inject the JavaScript stealth scripts
    # at runtime, but it will use the browser arguments and profile settings
    print("[*] Launching Playwright codegen...")
    print("[*] The codegen window will show a clean preview of generated code.\n")
    
    try:
        import os
        os.chdir(PROJECT_ROOT)
        
        # Run codegen with the profile
        # This will show the clean code preview window like the .sh script
        subprocess.run([
            "playwright", "codegen",
            "--user-data-dir", str(profile_path),
            "--browser", "chromium",
            target_url
        ], check=True)
        
    except KeyboardInterrupt:
        print("\n[*] Interrupted by user")
    except subprocess.CalledProcessError as e:
        print(f"\n[!] Codegen exited with error: {e}")
    except Exception as exc:
        print(f"\n[!] Error: {exc}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

