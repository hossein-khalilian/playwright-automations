"""Flashcard operations for NotebookLM automation."""

from typing import Dict, Optional

from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.automation.tasks.notebooklm.exceptions import NotebookLMError


async def create_flashcards(
    page: Page,
    notebook_id: str,
    card_count: Optional[str] = None,
    difficulty: Optional[str] = None,
    topic: Optional[str] = None,
) -> Dict[str, str]:
    """
    Creates flashcards for a notebook in NotebookLM.

    Args:
        page: The Playwright Page object to use for automation
        notebook_id: The ID of the notebook to create flashcards for
        card_count: Number of cards - "Fewer", "Standard (Default)", or "More"
        difficulty: Level of difficulty - "Easy", "Medium (Default)", or "Hard"
        topic: Optional topic description for the flashcards (max 5000 chars)

    Returns:
        Dictionary with status and message

    Raises:
        NotebookLMError: If creating flashcards fails
    """
    try:
        # Navigate directly to the notebook page
        await page.goto(f"https://notebooklm.google.com/notebook/{notebook_id}")

        # Wait for the Flashcards button to be visible
        try:
            flashcards_button = page.get_by_role("button", name="Flashcards", exact=True)
            await flashcards_button.wait_for(timeout=30_000, state="visible")
        except PlaywrightTimeoutError as exc:
            raise NotebookLMError(
                "Could not find the 'Flashcards' button. "
                "The notebook page may not have loaded correctly."
            ) from exc

        # Click on the "Customize Flashcards" button
        try:
            customize_button = page.get_by_role("button", name="Customize Flashcards")
            await customize_button.wait_for(timeout=10_000, state="visible")
            await customize_button.click()
        except PlaywrightTimeoutError as exc:
            raise NotebookLMError(
                "Could not find the 'Customize Flashcards' button. "
                "The dialog may not be accessible."
            ) from exc

        # Wait for the dialog to be visible
        await page.wait_for_timeout(1_000)

        # Configure number of cards if provided
        if card_count:
            card_count_str = card_count.value if hasattr(card_count, "value") else card_count
            try:
                # Find button by text filter
                card_count_button = page.locator("button").filter(has_text=card_count_str)
                await card_count_button.wait_for(timeout=5_000, state="visible")
                await card_count_button.click()
            except PlaywrightTimeoutError:
                # Card count option might already be selected, continue
                pass

        # Configure difficulty level if provided
        if difficulty:
            difficulty_str = difficulty.value if hasattr(difficulty, "value") else difficulty
            try:
                # Find button by text filter
                difficulty_button = page.locator("button").filter(has_text=difficulty_str)
                await difficulty_button.wait_for(timeout=5_000, state="visible")
                await difficulty_button.click()
            except PlaywrightTimeoutError:
                # Difficulty option might already be selected, continue
                pass

        # Fill in topic text if provided
        if topic:
            try:
                topic_textarea = page.get_by_role("textbox", name="Text area for custom topic")
                await topic_textarea.wait_for(timeout=5_000, state="visible")
                await topic_textarea.click()
                # Clear any existing placeholder text first
                await topic_textarea.clear()
                await topic_textarea.fill(topic)
            except PlaywrightTimeoutError:
                # Topic textarea might not be accessible, continue
                pass

        # Click the Generate button
        try:
            generate_button = page.get_by_role("button", name="Generate")
            await generate_button.wait_for(timeout=5_000, state="visible")
            await generate_button.click()
        except PlaywrightTimeoutError as exc:
            raise NotebookLMError(
                "Could not find the 'Generate' button in the customization dialog."
            ) from exc

        # Wait for generation to start
        await page.wait_for_timeout(2_000)

        return {
            "status": "success",
            "message": f"Flashcard creation started for notebook {notebook_id}. "
            "The flashcards are being generated and will be available in a few minutes.",
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(
            f"Failed to create flashcards for NotebookLM notebook: {exc}"
        ) from exc

