"""
Sync Playwright implementations for NotebookLM automations used by Celery tasks.
These are best-effort ports of the async flows, focused on parity for core actions.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from app.automation.tasks.notebooklm.exceptions import NotebookLMError

# -------- Shared helpers --------


def navigate_to_notebook(page: Page, notebook_id: str) -> None:
    try:
        page.goto(
            f"https://notebooklm.google.com/notebook/{notebook_id}",
            wait_until="domcontentloaded",
            timeout=30_000,
        )
        page.wait_for_timeout(1_000)
    except Exception as exc:
        raise NotebookLMError(
            f"Failed to navigate to notebook {notebook_id}: {exc}"
        ) from exc


def navigate_to_main_page(page: Page) -> None:
    try:
        page.goto(
            "https://notebooklm.google.com/",
            wait_until="domcontentloaded",
            timeout=30_000,
        )
        page.wait_for_timeout(1_000)
    except Exception as exc:
        raise NotebookLMError("Failed to navigate to NotebookLM main page") from exc


def close_dialogs(page: Page) -> None:
    try:
        close_button = page.get_by_role("button", name="Close dialog")
        close_button.wait_for(timeout=5_000)
        close_button.click()
    except PlaywrightTimeoutError:
        pass


def extract_notebook_id_from_url(page: Page) -> Optional[str]:
    match = re.search(r"/notebook/([^/?]+)", page.url)
    return match.group(1) if match else None


# -------- Notebook actions --------


def create_notebook(page: Page) -> Dict[str, str]:
    try:
        navigate_to_main_page(page)
        create_button = page.locator("mat-card").filter(
            has_text="addCreate new notebook"
        )
        create_button.wait_for(timeout=15_000)
        create_button.click()
        close_dialogs(page)
        try:
            page.wait_for_url("**/notebook/**", timeout=10_000)
        except PlaywrightTimeoutError:
            pass
        page.wait_for_timeout(1_000)
        current_url = page.url
        if "/notebook/" not in current_url:
            raise NotebookLMError("Notebook creation verification failed.")
        notebook_id = extract_notebook_id_from_url(page)
        return {
            "status": "success",
            "message": "Notebook created.",
            "page_url": current_url,
            "notebook_id": notebook_id,
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to create NotebookLM notebook: {exc}") from exc


def delete_notebook(page: Page, notebook_id: str) -> Dict[str, str]:
    try:
        navigate_to_main_page(page)
        close_dialogs(page)
        mat_card = page.locator(
            f'mat-card[aria-labelledby*="project-{notebook_id}-title"]'
        )
        mat_card.wait_for(timeout=10_000)
        actions_menu = mat_card.get_by_role("button", name="Project Actions Menu")
        actions_menu.wait_for(timeout=5_000)
        actions_menu.click()
        page.wait_for_timeout(500)
        delete_menuitem = page.get_by_role("menuitem", name="Delete")
        delete_menuitem.wait_for(timeout=5_000)
        delete_menuitem.click()
        page.wait_for_timeout(500)
        confirm_button = page.get_by_role("button", name="Confirm deletion")
        confirm_button.wait_for(timeout=5_000)
        confirm_button.click()
        page.wait_for_timeout(1_000)
        return {"status": "success", "message": f"Notebook {notebook_id} deleted."}
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to delete NotebookLM notebook: {exc}") from exc


# -------- Source actions --------


def add_source_to_notebook(
    page: Page, notebook_id: str, file_path: str
) -> Dict[str, str]:
    try:
        navigate_to_notebook(page, notebook_id)
        close_dialogs(page)
        add_source_button = page.get_by_role("button", name="Add source")
        add_source_button.wait_for(timeout=10_000)
        add_source_button.click()
        page.wait_for_timeout(500)
        choose_file_button = page.get_by_role("button", name="choose file")
        choose_file_button.wait_for(timeout=5_000)
        choose_file_button.click()
        page.wait_for_timeout(1_000)
        dialog = page.locator('[id^="mat-mdc-dialog-"]').last
        dialog.wait_for(timeout=10_000)
        file_input = dialog.locator('input[type="file"]').first
        file_input.wait_for(timeout=3_000, state="attached")
        file_input.set_input_files(file_path)
        page.wait_for_timeout(2_000)
        return {
            "status": "success",
            "message": f"Source added to notebook {notebook_id}.",
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to add source: {exc}") from exc


def list_sources(page: Page, notebook_id: str) -> Dict[str, Any]:
    try:
        navigate_to_notebook(page, notebook_id)
        close_dialogs(page)
        page.wait_for_timeout(1_000)
        source_containers = page.locator(".single-source-container")
        source_count = source_containers.count()
        sources = []
        for i in range(source_count):
            try:
                container = source_containers.nth(i)
                source_title_element = container.locator(".source-title")
                source_name = source_title_element.inner_text().strip()
                if not source_name:
                    continue
                status = "ready"
                try:
                    loading_spinner_container = container.locator(
                        ".loading-spinner-container"
                    )
                    if loading_spinner_container.count() > 0:
                        spinner = loading_spinner_container.first
                        if spinner.is_visible():
                            status = "processing"
                except Exception:
                    pass
                try:
                    more_button = container.get_by_role("button", name="More").first
                    disabled_attr = more_button.get_attribute("disabled")
                    class_attr = more_button.get_attribute("class") or ""
                    is_disabled = disabled_attr is not None or (
                        "mat-mdc-button-disabled" in class_attr
                    )
                    if is_disabled and status == "ready":
                        status = "processing"
                except Exception:
                    pass
                sources.append({"name": source_name, "status": status})
            except Exception:
                continue
        return {
            "status": "success",
            "message": f"Found {len(sources)} sources.",
            "sources": sources,
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to list sources: {exc}") from exc


def delete_source(page: Page, notebook_id: str, source_name: str) -> Dict[str, str]:
    try:
        navigate_to_notebook(page, notebook_id)
        close_dialogs(page)
        page.wait_for_timeout(1_000)
        source_title = page.locator(".source-title").filter(has_text=source_name).first
        source_title.wait_for(timeout=10_000)
        container = source_title.locator(
            "xpath=ancestor::div[contains(@class,'single-source-container')]"
        )
        actions_button = container.get_by_role("button", name="More")
        actions_button.wait_for(timeout=5_000)
        actions_button.click()
        page.wait_for_timeout(500)
        delete_button = page.get_by_role("menuitem", name="Delete")
        delete_button.wait_for(timeout=5_000)
        delete_button.click()
        page.wait_for_timeout(500)
        confirm_button = page.get_by_role(
            "button", name=re.compile("Delete", re.IGNORECASE)
        )
        confirm_button.wait_for(timeout=5_000)
        confirm_button.click()
        page.wait_for_timeout(1_000)
        return {"status": "success", "message": f"Source {source_name} deleted."}
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to delete source: {exc}") from exc


def rename_source(
    page: Page, notebook_id: str, source_name: str, new_name: str
) -> Dict[str, str]:
    try:
        navigate_to_notebook(page, notebook_id)
        close_dialogs(page)
        page.wait_for_timeout(1_000)
        source_title = page.locator(".source-title").filter(has_text=source_name).first
        source_title.wait_for(timeout=10_000)
        container = source_title.locator(
            "xpath=ancestor::div[contains(@class,'single-source-container')]"
        )
        actions_button = container.get_by_role("button", name="More")
        actions_button.wait_for(timeout=5_000)
        actions_button.click()
        page.wait_for_timeout(500)
        rename_button = page.get_by_role(
            "menuitem", name=re.compile("Rename", re.IGNORECASE)
        )
        rename_button.wait_for(timeout=5_000)
        rename_button.click()
        page.wait_for_timeout(500)
        name_input = page.get_by_role("textbox").first
        name_input.wait_for(timeout=5_000)
        name_input.fill(new_name)
        save_button = page.get_by_role(
            "button", name=re.compile("Save|Rename", re.IGNORECASE)
        )
        save_button.wait_for(timeout=5_000)
        save_button.click()
        page.wait_for_timeout(1_000)
        return {"status": "success", "message": f"Source renamed to {new_name}."}
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to rename source: {exc}") from exc


def review_source(page: Page, notebook_id: str, source_name: str) -> Dict[str, Any]:
    try:
        navigate_to_notebook(page, notebook_id)
        close_dialogs(page)
        page.wait_for_timeout(1_000)
        source_title = page.locator(".source-title").filter(has_text=source_name).first
        source_title.wait_for(timeout=10_000)
        source_title.click()
        page.wait_for_timeout(1_000)
        return {"status": "success", "message": f"Opened source {source_name}."}
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to review source: {exc}") from exc


# -------- Chat / Query --------


def query_notebook(page: Page, notebook_id: str, query: str) -> Dict[str, str]:
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


# -------- Artifacts --------

ICON_TO_TYPE = {
    "audio_magic_eraser": "audio_overview",
    "subscriptions": "video_overview",
    "quiz": "quiz",
    "cards_star": "flashcards",
    "flowchart": "mind_map",
    "auto_tab_group": "reports",
    "stacked_bar_chart": "infographic",
    "tablet": "slide_deck",
}


def _artifact_library(page: Page):
    artifact_library = page.locator("div.artifact-library-container")
    try:
        artifact_library.wait_for(timeout=30_000, state="visible")
    except PlaywrightTimeoutError:
        page.wait_for_timeout(2_000)
    return artifact_library


def list_artifacts(page: Page, notebook_id: str) -> Dict[str, Any]:
    try:
        navigate_to_notebook(page, notebook_id)
        close_dialogs(page)
        artifact_library = _artifact_library(page)
        artifacts: List[Dict[str, Any]] = []
        artifact_items = artifact_library.locator("artifact-library-item")
        for i in range(artifact_items.count()):
            try:
                artifact_item = artifact_items.nth(i)
                artifact_button = artifact_item.locator(
                    "button.artifact-button-content"
                ).first
                if artifact_button.count() == 0:
                    continue
                artifact_type = None
                icon_element = artifact_item.locator("mat-icon.artifact-icon").first
                if icon_element.count() > 0:
                    icon_text = icon_element.inner_text().strip()
                    for icon_name, type_name in ICON_TO_TYPE.items():
                        if icon_name in icon_text:
                            artifact_type = type_name
                            break
                    if not artifact_type:
                        artifact_type = icon_text or "unknown"
                artifact_name = None
                title_element = artifact_button.locator("span.artifact-title").first
                if title_element.count() > 0:
                    artifact_name = title_element.inner_text().strip()
                details = None
                details_element = artifact_button.locator("span.artifact-details").first
                if details_element.count() > 0:
                    details = details_element.inner_text().strip()
                status = "ready"
                play_button = artifact_button.locator('button[aria-label="Play"]')
                interactive_button = artifact_button.locator(
                    'button[aria-label="Interactive mode"]'
                )
                has_play = play_button.count() > 0
                has_interactive = interactive_button.count() > 0
                if not has_play and not has_interactive:
                    status = "unknown"
                artifacts.append(
                    {
                        "type": artifact_type,
                        "name": artifact_name,
                        "details": details,
                        "status": status,
                        "has_play": has_play,
                        "has_interactive": has_interactive,
                    }
                )
            except Exception:
                continue
        return {
            "status": "success",
            "message": f"Found {len(artifacts)} artifact(s).",
            "artifacts": artifacts,
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to list artifacts: {exc}") from exc


def delete_artifact(page: Page, notebook_id: str, artifact_name: str) -> Dict[str, str]:
    try:
        navigate_to_notebook(page, notebook_id)
        close_dialogs(page)
        artifact_library = _artifact_library(page)
        artifact_button = (
            artifact_library.locator(
                "artifact-library-item button.artifact-button-content"
            )
            .filter(has_text=artifact_name)
            .first
        )
        artifact_button.wait_for(timeout=10_000)
        artifact_button.click()
        page.wait_for_timeout(500)
        actions_button = page.get_by_role(
            "button", name=re.compile("More|Actions", re.IGNORECASE)
        ).first
        actions_button.wait_for(timeout=5_000)
        actions_button.click()
        page.wait_for_timeout(300)
        delete_button = page.get_by_role(
            "menuitem", name=re.compile("Delete", re.IGNORECASE)
        )
        delete_button.wait_for(timeout=5_000)
        delete_button.click()
        page.wait_for_timeout(500)
        confirm_button = page.get_by_role(
            "button", name=re.compile("Delete|Confirm", re.IGNORECASE)
        )
        confirm_button.wait_for(timeout=5_000)
        confirm_button.click()
        page.wait_for_timeout(1_000)
        return {"status": "success", "message": f"Artifact {artifact_name} deleted."}
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to delete artifact: {exc}") from exc


def rename_artifact(
    page: Page, notebook_id: str, artifact_name: str, new_name: str
) -> Dict[str, str]:
    try:
        navigate_to_notebook(page, notebook_id)
        close_dialogs(page)
        artifact_library = _artifact_library(page)
        artifact_button = (
            artifact_library.locator(
                "artifact-library-item button.artifact-button-content"
            )
            .filter(has_text=artifact_name)
            .first
        )
        artifact_button.wait_for(timeout=10_000)
        artifact_button.click()
        page.wait_for_timeout(500)
        actions_button = page.get_by_role(
            "button", name=re.compile("More|Actions", re.IGNORECASE)
        ).first
        actions_button.wait_for(timeout=5_000)
        actions_button.click()
        page.wait_for_timeout(300)
        rename_button = page.get_by_role(
            "menuitem", name=re.compile("Rename", re.IGNORECASE)
        )
        rename_button.wait_for(timeout=5_000)
        rename_button.click()
        page.wait_for_timeout(500)
        name_input = page.get_by_role("textbox").first
        name_input.wait_for(timeout=5_000)
        name_input.fill(new_name)
        save_button = page.get_by_role(
            "button", name=re.compile("Save|Rename", re.IGNORECASE)
        )
        save_button.wait_for(timeout=5_000)
        save_button.click()
        page.wait_for_timeout(1_000)
        return {"status": "success", "message": f"Artifact renamed to {new_name}."}
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to rename artifact: {exc}") from exc


# Placeholder: download artifact - best effort to click download action
def download_artifact(
    page: Page, notebook_id: str, artifact_name: str
) -> Dict[str, Any]:
    try:
        navigate_to_notebook(page, notebook_id)
        close_dialogs(page)
        artifact_library = _artifact_library(page)
        artifact_button = (
            artifact_library.locator(
                "artifact-library-item button.artifact-button-content"
            )
            .filter(has_text=artifact_name)
            .first
        )
        artifact_button.wait_for(timeout=10_000)
        artifact_button.click()
        page.wait_for_timeout(500)
        download_button = page.get_by_role(
            "button", name=re.compile("Download", re.IGNORECASE)
        ).first
        download_button.wait_for(timeout=5_000)
        download_button.click()
        page.wait_for_timeout(2_000)
        return {
            "status": "success",
            "message": f"Download triggered for {artifact_name}.",
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to download artifact: {exc}") from exc


# -------- Generative actions --------


def create_flashcards(
    page: Page,
    notebook_id: str,
    card_count: Optional[str] = None,
    difficulty: Optional[str] = None,
    topic: Optional[str] = None,
) -> Dict[str, str]:
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


def create_quiz(
    page: Page,
    notebook_id: str,
    question_count: Optional[str] = None,
    difficulty: Optional[str] = None,
    topic: Optional[str] = None,
) -> Dict[str, str]:
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
        return {
            "status": "success",
            "message": f"Quiz creation started for {notebook_id}.",
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to create quiz: {exc}") from exc


def create_infographic(
    page: Page,
    notebook_id: str,
    language: Optional[str] = None,
    orientation: Optional[str] = None,
    detail_level: Optional[str] = None,
    description: Optional[str] = None,
) -> Dict[str, str]:
    try:
        page.goto(f"https://notebooklm.google.com/notebook/{notebook_id}")
        inf_button = page.get_by_role(
            "button", name=re.compile("Infographic", re.IGNORECASE)
        ).first
        inf_button.wait_for(timeout=30_000, state="visible")
        inf_button.click()
        page.wait_for_timeout(1_000)
        for value in [language, orientation, detail_level]:
            if value:
                btn = page.locator("button").filter(has_text=value)
                btn.wait_for(timeout=5_000, state="visible")
                btn.click()
        if description:
            desc_input = page.get_by_role("textbox").first
            desc_input.wait_for(timeout=5_000, state="visible")
            desc_input.fill(description)
        generate_button = page.get_by_role(
            "button", name=re.compile("Generate", re.IGNORECASE)
        )
        generate_button.wait_for(timeout=5_000, state="visible")
        generate_button.click()
        page.wait_for_timeout(2_000)
        return {
            "status": "success",
            "message": f"Infographic creation started for {notebook_id}.",
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to create infographic: {exc}") from exc


def create_slide_deck(
    page: Page,
    notebook_id: str,
    format: Optional[str] = None,
    length: Optional[str] = None,
    language: Optional[str] = None,
    description: Optional[str] = None,
) -> Dict[str, str]:
    try:
        page.goto(f"https://notebooklm.google.com/notebook/{notebook_id}")
        sd_button = page.get_by_role(
            "button", name=re.compile("Slide deck|Slides", re.IGNORECASE)
        ).first
        sd_button.wait_for(timeout=30_000, state="visible")
        sd_button.click()
        page.wait_for_timeout(1_000)
        for value in [format, length, language]:
            if value:
                btn = page.locator("button").filter(has_text=value)
                btn.wait_for(timeout=5_000, state="visible")
                btn.click()
        if description:
            desc_input = page.get_by_role("textbox").first
            desc_input.wait_for(timeout=5_000, state="visible")
            desc_input.fill(description)
        generate_button = page.get_by_role(
            "button", name=re.compile("Generate", re.IGNORECASE)
        )
        generate_button.wait_for(timeout=5_000, state="visible")
        generate_button.click()
        page.wait_for_timeout(2_000)
        return {
            "status": "success",
            "message": f"Slide deck creation started for {notebook_id}.",
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to create slide deck: {exc}") from exc


def create_report(
    page: Page,
    notebook_id: str,
    format: Optional[str] = None,
    language: Optional[str] = None,
    description: Optional[str] = None,
) -> Dict[str, str]:
    try:
        page.goto(f"https://notebooklm.google.com/notebook/{notebook_id}")
        report_button = page.get_by_role(
            "button", name=re.compile("Report", re.IGNORECASE)
        ).first
        report_button.wait_for(timeout=30_000, state="visible")
        report_button.click()
        page.wait_for_timeout(1_000)
        for value in [format, language]:
            if value:
                btn = page.locator("button").filter(has_text=value)
                btn.wait_for(timeout=5_000, state="visible")
                btn.click()
        if description:
            desc_input = page.get_by_role("textbox").first
            desc_input.wait_for(timeout=5_000, state="visible")
            desc_input.fill(description)
        generate_button = page.get_by_role(
            "button", name=re.compile("Generate", re.IGNORECASE)
        )
        generate_button.wait_for(timeout=5_000, state="visible")
        generate_button.click()
        page.wait_for_timeout(2_000)
        return {
            "status": "success",
            "message": f"Report creation started for {notebook_id}.",
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to create report: {exc}") from exc


def create_mindmap(page: Page, notebook_id: str) -> Dict[str, str]:
    try:
        page.goto(f"https://notebooklm.google.com/notebook/{notebook_id}")
        mind_button = page.get_by_role(
            "button", name=re.compile("Mind map", re.IGNORECASE)
        ).first
        mind_button.wait_for(timeout=30_000, state="visible")
        mind_button.click()
        page.wait_for_timeout(2_000)
        return {
            "status": "success",
            "message": f"Mind map creation started for {notebook_id}.",
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to create mind map: {exc}") from exc


def create_audio_overview(
    page: Page,
    notebook_id: str,
    audio_format: Optional[str] = None,
    language: Optional[str] = None,
    length: Optional[str] = None,
    focus_text: Optional[str] = None,
) -> Dict[str, str]:
    try:
        page.goto(f"https://notebooklm.google.com/notebook/{notebook_id}")
        audio_button = page.get_by_role(
            "button", name=re.compile("Audio overview", re.IGNORECASE)
        ).first
        audio_button.wait_for(timeout=30_000, state="visible")
        audio_button.click()
        page.wait_for_timeout(1_000)
        for value in [audio_format, language, length]:
            if value:
                btn = page.locator("button").filter(has_text=value)
                btn.wait_for(timeout=5_000, state="visible")
                btn.click()
        if focus_text:
            text_input = page.get_by_role("textbox").first
            text_input.wait_for(timeout=5_000, state="visible")
            text_input.fill(focus_text)
        generate_button = page.get_by_role(
            "button", name=re.compile("Generate", re.IGNORECASE)
        )
        generate_button.wait_for(timeout=5_000, state="visible")
        generate_button.click()
        page.wait_for_timeout(2_000)
        return {
            "status": "success",
            "message": f"Audio overview creation started for {notebook_id}.",
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to create audio overview: {exc}") from exc


def create_video_overview(
    page: Page,
    notebook_id: str,
    video_format: Optional[str] = None,
    language: Optional[str] = None,
    visual_style: Optional[str] = None,
    custom_style_description: Optional[str] = None,
    focus_text: Optional[str] = None,
) -> Dict[str, str]:
    try:
        page.goto(f"https://notebooklm.google.com/notebook/{notebook_id}")
        video_button = page.get_by_role(
            "button", name=re.compile("Video overview", re.IGNORECASE)
        ).first
        video_button.wait_for(timeout=30_000, state="visible")
        video_button.click()
        page.wait_for_timeout(1_000)
        for value in [video_format, language, visual_style]:
            if value:
                btn = page.locator("button").filter(has_text=value)
                btn.wait_for(timeout=5_000, state="visible")
                btn.click()
        if custom_style_description:
            style_input = page.get_by_role("textbox").first
            style_input.wait_for(timeout=5_000, state="visible")
            style_input.fill(custom_style_description)
        if focus_text:
            text_input = page.get_by_role("textbox").nth(1)
            text_input.fill(focus_text)
        generate_button = page.get_by_role(
            "button", name=re.compile("Generate", re.IGNORECASE)
        )
        generate_button.wait_for(timeout=5_000, state="visible")
        generate_button.click()
        page.wait_for_timeout(2_000)
        return {
            "status": "success",
            "message": f"Video overview creation started for {notebook_id}.",
        }
    except NotebookLMError:
        raise
    except Exception as exc:
        raise NotebookLMError(f"Failed to create video overview: {exc}") from exc
