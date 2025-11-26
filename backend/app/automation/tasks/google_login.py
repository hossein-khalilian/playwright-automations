import asyncio
import random
import re

from playwright.async_api import Page

from app.utils.browser_utils import initialize_page
from app.utils.google import check_google_login_status, load_credentials_from_env

NAVIGATION_DELAY_RANGE = (2.0, 3.0)
PAGE_WARMUP_DELAY_RANGE = (1.0, 2.0)


async def _human_pause(min_seconds: float = 0.5, max_seconds: float = 1.0) -> None:
    """Pause for a random duration to better mimic human interaction."""
    await asyncio.sleep(random.uniform(min_seconds, max_seconds))


async def _type_with_human_delay(field, value: str) -> None:
    """Type text into a field using small randomized delays."""
    await field.click()
    await _human_pause()
    await field.type(value, delay=random.randint(50, 150))
    await _human_pause()


async def _click_next_button(page: Page) -> None:
    """Click the generic Next button and wait for Google to progress."""
    next_button = page.get_by_role("button", name=re.compile("^next$", re.IGNORECASE))
    await next_button.click()
    await _human_pause(*NAVIGATION_DELAY_RANGE)


async def login_to_google(
    page: Page,
    email: str,
    password: str,
    force_renew=False,
) -> bool:
    """
    Perform the Gmail login process using provided credentials.

    NOTE:
        - If Google requires additional verification (2FA, phone, etc.),
          this function will stop after submitting the password and ask
          you to complete the flow manually.
    """
    try:
        print("\n[*] Opening Gmail login page...")
        await page.goto(
            "https://accounts.google.com/signin/v2/identifier?service=mail&passive=true",
            wait_until="domcontentloaded",
            timeout=60_000,
        )

        # ---- Email step ----
        print("[*] Entering email...")
        email_input = page.get_by_role(
            "textbox", name=re.compile("email|phone", re.IGNORECASE)
        )
        await email_input.wait_for(timeout=15_000)

        # Human-like typing with random delays
        await _type_with_human_delay(email_input, email)
        await _click_next_button(page)

        # Wait for password field to appear
        print("[*] Waiting for password field...")
        password_input = page.get_by_role(
            "textbox", name=re.compile("password", re.IGNORECASE)
        )
        await password_input.wait_for(timeout=20_000)
        await asyncio.sleep(random.uniform(0.5, 1.0))

        # ---- Password step ----
        print("[*] Entering password...")
        await _type_with_human_delay(password_input, password)
        await _click_next_button(page)

        # Let Google redirect after password
        print("[*] Waiting for Gmail to load after password submission...")
        await page.wait_for_load_state("networkidle", timeout=60_000)

        if await check_google_login_status(page):
            print("\n[+] Successfully logged into Gmail!")
            return True

        # At this point Google most likely wants additional verification.
        print(
            "\n[!] Google is asking for additional verification (2FA, phone, etc.). "
            "Complete the steps manually in the opened browser."
        )
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, input, "    When you see your inbox, press Enter here to continue..."
        )

        if await check_google_login_status(page):
            print("\n[+] Gmail login completed manually and session is now active.")
            return True

        print("\n[-] Login did not reach the inbox even after manual steps.")
        return False

    except Exception as exc:
        print(f"\n[-] Error during Gmail login: {exc}")
        return False


async def check_or_login_to_google(
    user_profile_name: str = "test_google_login", headless: bool = False
):
    print("[*] Initializing browser...")
    page = None
    context = None
    playwright = None

    try:
        # Use a test profile to avoid conflicts with running FastAPI app
        print(f"[*] Using profile: {user_profile_name}")
        page, context, playwright = await initialize_page(
            headless=headless, user_profile_name=user_profile_name
        )

        # Check if already logged in
        print("[*] Checking if Google is already logged in...")
        if await check_google_login_status(page):
            print("[+] Google is already logged in. No need to login again.")
            print("[*] Browser will remain open for 5 seconds. Press Ctrl+C to close.")
            await asyncio.sleep(5)
        else:
            print("[*] Not logged in. Starting login process...")
            # Load credentials from environment
            email, password = load_credentials_from_env()

            # Perform login
            success = await login_to_google(page, email, password)

            if success:
                print("[+] Login process completed successfully!")
            else:
                print("[-] Login process failed.")

            print("[*] Browser will remain open for 5 seconds. Press Ctrl+C to close.")
            await asyncio.sleep(5)
    except KeyboardInterrupt:
        print("\n[*] Interrupted by user. Closing browser...")
    except Exception as exc:
        error_msg = str(exc)
        if "Target page, context or browser has been closed" in error_msg:
            print(
                "\n[!] Error: Browser profile is locked or in use by another process."
            )
            print(
                "[!] Solution: Stop other processes using the profile, or use a different profile name."
            )
        elif "profile appears to be in use" in error_msg.lower():
            print("\n[!] Error: Browser profile is locked by another Chromium process.")
            print(
                "[!] Solution: Close other browser instances or stop the FastAPI app."
            )
        else:
            print(f"\n[-] Error: {exc}")
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
    asyncio.run(check_or_login_to_google())
