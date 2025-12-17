"""Sync quiz creation for NotebookLM automation."""

import re
from typing import Dict, Optional

from playwright.sync_api import Page

from app.automation.tasks.notebooklm.exceptions import NotebookLMError
from app.automation.tasks.notebooklm.helpers import check_generation_limits


def create_quiz(
    page: Page,
    notebook_id: str,
    question_count: Optional[str] = None,
    difficulty: Optional[str] = None,
    topic: Optional[str] = None,
) -> Dict[str, str]:
    """
    Create quiz artifact.

    Args:
        page: The Playwright Page object
        notebook_id: The ID of the notebook
        question_count: Number of questions
        difficulty: Difficulty level
        topic: Custom topic for quiz

    Returns:
        Dictionary with status and message

    Raises:
        NotebookLMError: If quiz creation fails
    """
    try:
        page.goto(f"https://notebooklm.google.com/notebook/{notebook_id}")
        quiz_button = page.get_by_role("button", name="Quiz", exact=True)
        quiz_button.wait_for(timeout=30_000, state="visible")
        quiz_button.click()
        page.wait_for_timeout(1_000)
        if question_count:
            btn = page.locator("button").filter(has_text=question_count)
            btn.wait_for(timeout=5_000, state="visible")
            btn.click()
        if difficulty:
            btn = page.locator("button").filter(has_text=difficulty)
            btn.wait_for(timeout=5_000, state="visible")
            btn.click()
        if topic:
            topic_textarea = page.get_by_role(
                "textbox", name=re.compile("topic", re.IGNORECASE)
            ).first
            topic_textarea.wait_for(timeout=5_000, state="visible")
            topic_textarea.fill(topic)
        generate_button = page.get_by_role(
            "button", name=re.compile("Generate", re.IGNORECASE)
        )
        generate_button.wait_for(timeout=5_000, state="visible")
        generate_button.click()
        page.wait_for_timeout(2_000)

        # After clicking Generate, check if a daily limit / upsell message appeared.
        check_generation_limits(page, "Quiz")

        return {
            "status": "success",
            "message": f"Quiz creation started for {notebook_id}.",
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to create quiz: {exc}") from exc
