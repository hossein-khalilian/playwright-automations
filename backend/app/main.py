import os
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from app.automation.tasks.google_login import login_to_google
from app.routes.google import router as google_router
from app.utils.browser_state import clear_browser_resources, set_browser_resources
from app.utils.browser_utils import initialize_page
from app.utils.google import check_google_login_status, load_credentials_from_env

# from app.routes.notebooklm import router as notebooklm_router

api_router = APIRouter()
# api_router.include_router(notebooklm_router)
api_router.include_router(google_router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown event handler for FastAPI app.
    Initializes browser page with user profile at startup and cleans up at shutdown.
    """
    # Startup: Initialize browser page with user profile
    user_profile_name = os.getenv("USER_PROFILE_NAME", "default")
    headless = os.getenv("HEADLESS", "true").lower() == "true"

    print(f"[*] Initializing browser with user profile: {user_profile_name}")
    print(f"[*] Headless mode: {headless}")

    try:
        page, context, playwright = await initialize_page(
            headless=headless, user_profile_name=user_profile_name
        )
        set_browser_resources(page, context, playwright)
        print("[+] Browser initialized successfully!")

        # Check or login to Google
        print("[*] Checking Google login status...")
        try:
            if await check_google_login_status(page):
                print("[+] Google is already logged in.")
            else:
                print("[*] Not logged in to Google. Attempting to login...")
                email, password = load_credentials_from_env()
                success = await login_to_google(page, email, password)
                if success:
                    print("[+] Google login completed successfully!")
                else:
                    print(
                        "[!] Warning: Google login failed. Some endpoints may not work correctly."
                    )
        except Exception as exc:
            print(f"[!] Warning: Error during Google login check: {exc}")
            print("[!] Some Google-dependent endpoints may not work correctly.")
    except Exception as exc:
        print(f"[!] Warning: Failed to initialize browser: {exc}")
        print("[!] Browser-dependent endpoints may not work correctly.")

    yield

    # Shutdown: Clean up browser resources
    print("[*] Shutting down browser...")
    try:
        from app.utils.browser_state import get_browser_context, get_playwright

        context = get_browser_context()
        playwright = get_playwright()
        if context:
            await context.close()
        if playwright:
            await playwright.stop()
        clear_browser_resources()
        print("[+] Browser closed successfully.")
    except Exception as exc:
        print(f"[!] Warning: Error closing browser: {exc}")


app = FastAPI(
    title="Playwright Automations API",
    version="1.0.0",
    lifespan=lifespan,
)
app.include_router(api_router)


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok"}
