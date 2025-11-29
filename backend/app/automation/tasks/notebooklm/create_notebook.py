import asyncio
import re
from typing import Dict, Optional

from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.utils.browser_utils import initialize_page


class NotebookLMError(Exception):
    """Custom exception for NotebookLM automation errors."""

    pass


async def create_notebook(page: Page) -> Dict[str, str]:
    """
    Navigates to NotebookLM and triggers creation of a new notebook
    by clicking on the "Create new notebook" button.

    Args:
        page: The Playwright Page object to use for automation

    Returns:
        Dictionary with status, message, and page URL

    Raises:
        NotebookLMError: If the notebook creation fails
    """
    try:
        # Navigate to NotebookLM
        await page.goto(
            "https://notebooklm.google.com/",
            wait_until="domcontentloaded",
            timeout=30_000,
        )

        # Find and click the mat-card element with text "addCreate new notebook"
        try:
            create_button = page.locator("mat-card").filter(
                has_text="addCreate new notebook"
            )
            await create_button.wait_for(timeout=15_000)
            await create_button.click()
        except PlaywrightTimeoutError as exc:
            raise NotebookLMError(
                "Could not find the 'Create new notebook' button. "
                "The page may not have loaded correctly or the element structure has changed."
            ) from exc

        # Close the dialog if it appears
        try:
            close_button = page.get_by_role("button", name="Close dialog")
            await close_button.wait_for(timeout=5_000)
            await close_button.click()
        except PlaywrightTimeoutError:
            # Dialog might not appear, which is fine
            pass

        # Wait for navigation to notebook page
        # The page should navigate to a URL like: https://notebooklm.google.com/notebook/{notebook_id}
        try:
            await page.wait_for_url(
                "**/notebook/**",
                timeout=10_000,
            )
        except PlaywrightTimeoutError:
            # If navigation didn't happen, check if we're still on the main page
            pass

        # Wait briefly for any navigation or UI updates
        await page.wait_for_timeout(1_000)

        # Verify success: check if URL changed (notebook page) or dialog closed
        current_url = page.url
        is_notebook_page = "/notebook/" in current_url

        # Extract notebook ID from URL if we're on a notebook page
        notebook_id: Optional[str] = None
        if is_notebook_page:
            # Extract notebook ID from URL pattern: https://notebooklm.google.com/notebook/{notebook_id}
            match = re.search(r"/notebook/([^/?]+)", current_url)
            if match:
                notebook_id = match.group(1)

        # Check if dialog is still open (indicating potential failure)
        dialog_still_open = await page.get_by_role("button", name="Close dialog").count() > 0

        if not is_notebook_page and dialog_still_open:
            raise NotebookLMError(
                "Notebook creation verification failed. "
                "The dialog is still open, indicating the notebook may not have been created."
            )

        if not is_notebook_page:
            raise NotebookLMError(
                "Notebook creation verification failed. "
                "The page did not navigate to a notebook URL."
            )

        return {
            "status": "success",
            "message": "NotebookLM notebook creation triggered and verified successfully.",
            "page_url": current_url,
            "notebook_id": notebook_id,
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to create NotebookLM notebook: {exc}") from exc


async def delete_notebook(page: Page, notebook_id: str) -> Dict[str, str]:
    """
    Deletes a notebook in NotebookLM by its ID.

    Args:
        page: The Playwright Page object to use for automation
        notebook_id: The ID of the notebook to delete

    Returns:
        Dictionary with status and message

    Raises:
        NotebookLMError: If the notebook deletion fails
    """
    try:
        # Navigate to the main NotebookLM page
        await page.goto(
            "https://notebooklm.google.com/",
            wait_until="domcontentloaded",
            timeout=30_000,
        )

        # Close any dialogs that might appear
        try:
            close_button = page.get_by_role("button", name="Close dialog")
            await close_button.wait_for(timeout=5_000)
            await close_button.click()
        except PlaywrightTimeoutError:
            # Dialog might not appear, which is fine
            pass

        # Wait for the page to load
        await page.wait_for_timeout(1_000)

        # Find and click the "Project Actions Menu" button for the specific notebook
        # The button is inside the project-button component for that specific notebook
        try:
            # Find the mat-card that contains this notebook by its aria-labelledby attribute
            # The mat-card has aria-labelledby="project-{notebook_id}-title project-{notebook_id}-emoji"
            mat_card = page.locator(f'mat-card[aria-labelledby*="project-{notebook_id}-title"]')
            
            # Check if the project exists on the page
            await mat_card.wait_for(timeout=10_000)
            
            # Find the "Project Actions Menu" button within this specific mat-card
            actions_menu = mat_card.get_by_role("button", name="Project Actions Menu")
            await actions_menu.wait_for(timeout=5_000)
            await actions_menu.click()
        except PlaywrightTimeoutError as exc:
            raise NotebookLMError(
                f"Could not find the 'Project Actions Menu' button for notebook {notebook_id}. "
                "The notebook may not exist or the page structure has changed."
            ) from exc

        # Wait for the menu to appear
        await page.wait_for_timeout(500)

        # Click on the "Delete" menuitem
        try:
            delete_menuitem = page.get_by_role("menuitem", name="Delete")
            await delete_menuitem.wait_for(timeout=5_000)
            await delete_menuitem.click()
        except PlaywrightTimeoutError as exc:
            raise NotebookLMError(
                "Could not find the 'Delete' menuitem. "
                "The menu may not have appeared correctly."
            ) from exc

        # Wait for the confirmation dialog
        await page.wait_for_timeout(500)

        # Click the "Confirm deletion" button
        try:
            confirm_button = page.get_by_role("button", name="Confirm deletion")
            await confirm_button.wait_for(timeout=5_000)
            await confirm_button.click()
        except PlaywrightTimeoutError as exc:
            raise NotebookLMError(
                "Could not find the 'Confirm deletion' button. "
                "The confirmation dialog may not have appeared."
            ) from exc

        # Wait for the deletion to complete
        await page.wait_for_timeout(1_000)

        return {
            "status": "success",
            "message": f"NotebookLM notebook {notebook_id} deleted successfully.",
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to delete NotebookLM notebook: {exc}") from exc


async def main():
    """Test function to visually test create_notebook."""
    print("[*] Initializing browser for visual testing...")
    page = None
    context = None
    playwright = None

    try:
        # Use a test profile to avoid conflicts with running FastAPI app
        test_profile = "test_notebooklm"
        print(f"[*] Using test profile: {test_profile}")
        page, context, playwright = await initialize_page(
            headless=False, user_profile_name=test_profile
        )
        print("[+] Browser initialized successfully!")

        # Test the create_notebook function
        print("[*] Testing create_notebook function...")
        result = await create_notebook(page)
        print(f"[+] Success! Result: {result}")

        # Keep the browser open for visual inspection
        print("[*] Browser will stay open for 30 seconds for visual inspection...")
        print("[*] Press Ctrl+C to close early.")
        await asyncio.sleep(30)
    except KeyboardInterrupt:
        print("\n[*] Closing browser...")
    except Exception as exc:
        print(f"\n[!] Error: {exc}")
        import traceback
        traceback.print_exc()
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
