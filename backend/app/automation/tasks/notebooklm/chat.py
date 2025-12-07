"""Sync chat/query operations for NotebookLM automation."""

import re
from typing import Any, Dict

from playwright.sync_api import Page

from app.automation.tasks.notebooklm.exceptions import NotebookLMError
from app.automation.tasks.notebooklm.helpers import close_dialogs, navigate_to_notebook


def query_notebook(page: Page, notebook_id: str, query: str) -> Dict[str, str]:
    """
    Send a query to a notebook.

    Args:
        page: The Playwright Page object
        notebook_id: The ID of the notebook
        query: The query text to send

    Returns:
        Dictionary with status, message, and query

    Raises:
        NotebookLMError: If sending query fails
    """
    try:
        navigate_to_notebook(page, notebook_id)
        close_dialogs(page)
        page.wait_for_timeout(1_000)
        query_box = page.get_by_role("textbox", name="Query box")
        query_box.wait_for(timeout=10_000)
        query_box.click()
        query_box.fill(query)
        page.wait_for_timeout(500)
        try:
            submit_button = page.get_by_role("button", name="Submit")
            submit_button.wait_for(timeout=5_000, state="visible")
            for _ in range(50):
                if not submit_button.is_disabled():
                    break
                page.wait_for_timeout(100)
            submit_button.click()
        except Exception:
            query_box.press("Enter")
        return {
            "status": "success",
            "message": f"Query sent to notebook {notebook_id}.",
            "query": query,
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to send query: {exc}") from exc


def get_chat_history(page: Page, notebook_id: str) -> Dict[str, Any]:
    """
    Get chat history for a notebook.

    Args:
        page: The Playwright Page object
        notebook_id: The ID of the notebook

    Returns:
        Dictionary with status, message, and list of messages

    Raises:
        NotebookLMError: If getting chat history fails
    """
    try:
        navigate_to_notebook(page, notebook_id)
        close_dialogs(page)
        page.wait_for_timeout(1_000)
        message_pairs = page.locator(".chat-message-pair")
        pair_count = message_pairs.count()
        messages = []
        for i in range(pair_count):
            try:
                pair = message_pairs.nth(i)
                user_container = pair.locator(
                    ".from-user-container .message-text-content"
                )
                ai_container = pair.locator(".to-user-container .message-text-content")
                user_text = (
                    user_container.inner_text().strip()
                    if user_container.count() > 0
                    else ""
                )
                ai_text = (
                    ai_container.inner_text().strip()
                    if ai_container.count() > 0
                    else ""
                )
                if user_text:
                    messages.append({"role": "user", "content": user_text})
                if ai_text:
                    ai_text = re.sub(r"\b\d+\b(?=\s|$)", "", ai_text)
                    ai_text = re.sub(r"\s+", " ", ai_text).strip()
                    messages.append({"role": "assistant", "content": ai_text})
            except Exception:
                continue
        return {
            "status": "success",
            "message": f"Retrieved chat history for {notebook_id}.",
            "messages": messages,
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to get chat history: {exc}") from exc


def delete_chat_history(page: Page, notebook_id: str) -> Dict[str, str]:
    """
    Delete chat history for a notebook.

    Args:
        page: The Playwright Page object
        notebook_id: The ID of the notebook

    Returns:
        Dictionary with status and message

    Raises:
        NotebookLMError: If deleting chat history fails
    """
    try:
        navigate_to_notebook(page, notebook_id)
        close_dialogs(page)
        page.wait_for_timeout(1_000)
        chat_options_button = page.get_by_role("button", name="Chat options")
        chat_options_button.wait_for(timeout=10_000)
        chat_options_button.click()
        page.wait_for_timeout(500)
        delete_button = page.get_by_role(
            "menuitem", name=re.compile("Delete chat", re.IGNORECASE)
        )
        delete_button.wait_for(timeout=5_000)
        delete_button.click()
        page.wait_for_timeout(500)
        confirm_button = page.get_by_role(
            "button", name=re.compile("Delete", re.IGNORECASE)
        )
        confirm_button.wait_for(timeout=5_000)
        confirm_button.click()
        page.wait_for_timeout(1_000)
        return {
            "status": "success",
            "message": f"Chat history deleted for {notebook_id}.",
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to delete chat history: {exc}") from exc
