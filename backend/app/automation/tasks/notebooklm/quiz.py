"""Quiz operations for NotebookLM automation."""

from typing import Dict, Optional

from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.automation.tasks.notebooklm.exceptions import NotebookLMError


async def create_quiz(
    page: Page,
    notebook_id: str,
    question_count: Optional[str] = None,
    difficulty: Optional[str] = None,
    topic: Optional[str] = None,
) -> Dict[str, str]:
    """
    Creates a quiz for a notebook in NotebookLM.

    Args:
        page: The Playwright Page object to use for automation
        notebook_id: The ID of the notebook to create quiz for
        question_count: Number of questions - "Fewer", "Standard", or "More"
        difficulty: Level of difficulty - "Easy", "Medium", or "Hard"
        topic: Optional topic description for the quiz (max 5000 chars)

    Returns:
        Dictionary with status and message

    Raises:
        NotebookLMError: If creating quiz fails
    """
    try:
        # Navigate directly to the notebook page
        await page.goto(f"https://notebooklm.google.com/notebook/{notebook_id}")

        # Wait for the Quiz button to be visible
        try:
            quiz_button = page.get_by_role("button", name="Quiz", exact=True)
            await quiz_button.wait_for(timeout=30_000, state="visible")
        except PlaywrightTimeoutError as exc:
            raise NotebookLMError(
                "Could not find the 'Quiz' button. "
                "The notebook page may not have loaded correctly."
            ) from exc

        # Click on the "Customize Quiz" button
        try:
            customize_button = page.get_by_role("button", name="Customize Quiz")
            await customize_button.wait_for(timeout=10_000, state="visible")
            await customize_button.click()
        except PlaywrightTimeoutError as exc:
            raise NotebookLMError(
                "Could not find the 'Customize Quiz' button. "
                "The dialog may not be accessible."
            ) from exc

        # Wait for the dialog to be visible
        await page.wait_for_timeout(1_000)

        # Configure number of questions if provided
        if question_count:
            question_count_str = (
                question_count.value if hasattr(question_count, "value") else question_count
            )
            try:
                # Find button by text filter
                question_count_button = page.locator("button").filter(
                    has_text=question_count_str
                )
                await question_count_button.wait_for(timeout=5_000, state="visible")
                await question_count_button.click()
            except PlaywrightTimeoutError:
                # Question count option might already be selected, continue
                pass

        # Configure difficulty level if provided
        if difficulty:
            difficulty_str = (
                difficulty.value if hasattr(difficulty, "value") else difficulty
            )
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
            "message": f"Quiz creation started for notebook {notebook_id}. "
            "The quiz is being generated and will be available in a few minutes.",
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(
            f"Failed to create quiz for NotebookLM notebook: {exc}"
        ) from exc

