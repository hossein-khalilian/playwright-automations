"""Chat operations for NotebookLM automation."""

import re
from typing import Any, Dict

from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.automation.tasks.notebooklm.exceptions import NotebookLMError
from app.automation.tasks.notebooklm.helpers import close_dialogs, navigate_to_notebook


async def query_notebook(page: Page, notebook_id: str, query: str) -> Dict[str, str]:
    """
    Sends a query to a notebook in NotebookLM without waiting for the response.

    Args:
        page: The Playwright Page object to use for automation
        notebook_id: The ID of the notebook to query
        query: The query text to send to the notebook

    Returns:
        Dictionary with status, message, and the query that was sent

    Raises:
        NotebookLMError: If sending the query fails
    """
    try:
        # Navigate directly to the notebook page
        await navigate_to_notebook(page, notebook_id)

        # Close any dialogs that might appear
        await close_dialogs(page)

        # Wait for the query box to be available
        await page.wait_for_timeout(1_000)

        # Find and fill the "Query box" textarea
        try:
            query_box = page.get_by_role("textbox", name="Query box")
            await query_box.wait_for(timeout=10_000)
            await query_box.click()
        except PlaywrightTimeoutError as exc:
            raise NotebookLMError(
                "Could not find the 'Query box' textbox. "
                "The notebook page may not have loaded correctly."
            ) from exc

        # Fill the query box with the query text
        await query_box.fill(query)

        # Wait a bit for the form to process the input
        await page.wait_for_timeout(500)

        # Find and click the submit button (the button with aria-label="Submit")
        # The submit button becomes enabled after the textarea has content
        try:
            submit_button = page.get_by_role("button", name="Submit")
            await submit_button.wait_for(timeout=5_000, state="visible")
            
            # Wait for the button to become enabled (not disabled)
            # The button starts as disabled and becomes enabled when there's text
            # Wait up to 5 seconds for the button to be enabled
            for _ in range(50):  # Check 50 times with 100ms intervals = 5 seconds max
                is_disabled = await submit_button.is_disabled()
                if not is_disabled:
                    break
                await page.wait_for_timeout(100)
            
            # Click the submit button
            await submit_button.click()
        except (PlaywrightTimeoutError, Exception):
            # If submit button approach doesn't work, try pressing Enter on the textarea
            try:
                await query_box.press("Enter")
            except Exception as exc:
                raise NotebookLMError(
                    "Could not submit the query. "
                    "The submit button may not be accessible or the form may not be ready."
                ) from exc

        # Query submitted successfully - return immediately without waiting for response
        return {
            "status": "success",
            "message": f"Query sent successfully to notebook {notebook_id}.",
            "query": query,
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to send query to NotebookLM notebook: {exc}") from exc


async def get_chat_history(page: Page, notebook_id: str) -> Dict[str, Any]:
    """
    Gets the complete chat history from a notebook in NotebookLM.

    Args:
        page: The Playwright Page object to use for automation
        notebook_id: The ID of the notebook to get chat history from

    Returns:
        Dictionary with status, message, and list of chat messages

    Raises:
        NotebookLMError: If getting chat history fails
    """
    try:
        # Navigate directly to the notebook page
        await navigate_to_notebook(page, notebook_id)

        # Close any dialogs that might appear
        await close_dialogs(page)

        # Wait for chat panel to load
        await page.wait_for_timeout(1_000)

        # Find all chat message pairs
        message_pairs = page.locator(".chat-message-pair")
        pair_count = await message_pairs.count()

        messages = []
        
        # Process each message pair
        for i in range(pair_count):
            try:
                pair = message_pairs.nth(i)
                
                # Get user message (from-user-container)
                user_message_container = pair.locator(".from-user-container .message-text-content")
                user_text = ""
                if await user_message_container.count() > 0:
                    user_text = await user_message_container.inner_text()
                    user_text = user_text.strip() if user_text else ""
                
                # Get AI response (to-user-container)
                ai_message_container = pair.locator(".to-user-container .message-text-content")
                ai_text = ""
                if await ai_message_container.count() > 0:
                    # Extract and convert to markdown
                    ai_text = await ai_message_container.evaluate("""
                        (element) => {
                            if (!element) return '';
                            
                            // Clone the element to avoid modifying the original
                            const clone = element.cloneNode(true);
                            
                            // Remove citation markers and buttons
                            clone.querySelectorAll('.citation-marker, button[class*="citation"], button[aria-label*="citation"]').forEach(el => el.remove());
                            
                            // Convert bold/strong to markdown
                            clone.querySelectorAll('b, strong').forEach(el => {
                                const text = el.textContent.trim();
                                if (text) {
                                    const markdown = document.createTextNode(`**${text}**`);
                                    el.replaceWith(markdown);
                                } else {
                                    el.remove();
                                }
                            });
                            
                            // Convert italic/em to markdown
                            clone.querySelectorAll('i, em').forEach(el => {
                                const text = el.textContent.trim();
                                if (text) {
                                    const markdown = document.createTextNode(`*${text}*`);
                                    el.replaceWith(markdown);
                                } else {
                                    el.remove();
                                }
                            });
                            
                            // Get all text content
                            let text = clone.textContent || clone.innerText || '';
                            
                            // Clean up whitespace
                            text = text.replace(/\\s+/g, ' ').trim();
                            
                            // Remove standalone citation numbers and dots
                            text = text.replace(/\\b\\d+\\b(?=\\s|$)/g, '');
                            text = text.replace(/\\.\\.\\./g, '');
                            text = text.replace(/\\s+/g, ' ').trim();
                            
                            return text;
                        }
                    """)
                    
                    # Fallback if JavaScript fails
                    if not ai_text or len(ai_text.strip()) == 0:
                        ai_text = await ai_message_container.inner_text()
                        ai_text = re.sub(r'\b\d+\b(?=\s|$)', '', ai_text)
                        ai_text = re.sub(r'\.\.\.', '', ai_text)
                        ai_text = re.sub(r'\s+', ' ', ai_text).strip()
                
                # Add messages if they exist
                if user_text:
                    messages.append({
                        "role": "user",
                        "content": user_text,
                    })
                
                if ai_text:
                    messages.append({
                        "role": "assistant",
                        "content": ai_text,
                    })
                    
            except Exception:
                # Skip messages that can't be read
                continue

        return {
            "status": "success",
            "message": f"Retrieved chat history from notebook {notebook_id}.",
            "messages": messages,
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to get chat history from NotebookLM notebook: {exc}") from exc


async def delete_chat_history(page: Page, notebook_id: str) -> Dict[str, str]:
    """
    Deletes the chat history from a notebook in NotebookLM.

    Args:
        page: The Playwright Page object to use for automation
        notebook_id: The ID of the notebook to delete chat history from

    Returns:
        Dictionary with status and message

    Raises:
        NotebookLMError: If deleting chat history fails
    """
    try:
        # Navigate directly to the notebook page
        await navigate_to_notebook(page, notebook_id)

        # Close any dialogs that might appear
        await close_dialogs(page)

        # Wait for the page to be ready
        await page.wait_for_timeout(1_000)

        # Click on "Chat options" button
        try:
            chat_options_button = page.get_by_role("button", name="Chat options")
            await chat_options_button.wait_for(timeout=10_000)
            await chat_options_button.click()
        except PlaywrightTimeoutError as exc:
            raise NotebookLMError(
                "Could not find the 'Chat options' button. "
                "The notebook page may not have loaded correctly."
            ) from exc

        # Wait for the menu to appear
        await page.wait_for_timeout(500)

        # Click on "Delete chat history Chat" menuitem
        try:
            delete_menuitem = page.get_by_role("menuitem", name="Delete chat history Chat")
            await delete_menuitem.wait_for(timeout=5_000)
            await delete_menuitem.click()
        except PlaywrightTimeoutError as exc:
            raise NotebookLMError(
                "Could not find the 'Delete chat history Chat' menuitem. "
                "The menu may not have appeared correctly."
            ) from exc

        # Wait for the confirmation dialog
        await page.wait_for_timeout(500)

        # Click the "Delete" button to confirm
        try:
            confirm_delete_button = page.get_by_role("button", name="Delete")
            await confirm_delete_button.wait_for(timeout=5_000)
            await confirm_delete_button.click()
        except PlaywrightTimeoutError as exc:
            raise NotebookLMError(
                "Could not find the 'Delete' confirmation button. "
                "The confirmation dialog may not have appeared."
            ) from exc

        # Wait for the deletion to complete
        await page.wait_for_timeout(1_000)

        return {
            "status": "success",
            "message": f"Chat history deleted successfully from notebook {notebook_id}.",
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to delete chat history from NotebookLM notebook: {exc}") from exc

