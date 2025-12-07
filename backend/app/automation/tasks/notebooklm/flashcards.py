"""Sync flashcard creation for NotebookLM automation."""

from typing import Dict, Optional

from playwright.sync_api import Page

from app.automation.tasks.notebooklm.exceptions import NotebookLMError


def create_flashcards(
    page: Page,
    notebook_id: str,
    card_count: Optional[str] = None,
    difficulty: Optional[str] = None,
    topic: Optional[str] = None,
) -> Dict[str, str]:
    """
    Create flashcards artifact.

    Args:
        page: The Playwright Page object
        notebook_id: The ID of the notebook
        card_count: Number of cards to create
        difficulty: Difficulty level
        topic: Custom topic for flashcards

    Returns:
        Dictionary with status and message

    Raises:
        NotebookLMError: If flashcard creation fails
    """
    try:
        page.goto(f"https://notebooklm.google.com/notebook/{notebook_id}")
        flashcards_button = page.get_by_role("button", name="Flashcards", exact=True)
        flashcards_button.wait_for(timeout=30_000, state="visible")
        flashcards_button.click()
        customize_button = page.get_by_role("button", name="Customize Flashcards")
        customize_button.wait_for(timeout=10_000, state="visible")
        customize_button.click()
        page.wait_for_timeout(1_000)
        if card_count:
            btn = page.locator("button").filter(has_text=card_count)
            btn.wait_for(timeout=5_000, state="visible")
            btn.click()
        if difficulty:
            btn = page.locator("button").filter(has_text=difficulty)
            btn.wait_for(timeout=5_000, state="visible")
            btn.click()
        if topic:
            topic_textarea = page.get_by_role(
                "textbox", name="Text area for custom topic"
            )
            topic_textarea.wait_for(timeout=5_000, state="visible")
            topic_textarea.click()
            topic_textarea.fill(topic)
        generate_button = page.get_by_role("button", name="Generate")
        generate_button.wait_for(timeout=5_000, state="visible")
        generate_button.click()
        page.wait_for_timeout(2_000)
        return {
            "status": "success",
            "message": f"Flashcard creation started for {notebook_id}.",
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to create flashcards: {exc}") from exc
