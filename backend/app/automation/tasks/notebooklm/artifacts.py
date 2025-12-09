"""Sync artifact management operations for NotebookLM automation."""

import re
from typing import Any, Dict, List

from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from app.automation.tasks.notebooklm.exceptions import NotebookLMError
from app.automation.tasks.notebooklm.helpers import close_dialogs, navigate_to_notebook

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
    """Get the artifact library container."""
    artifact_library = page.locator("div.artifact-library-container")
    try:
        artifact_library.wait_for(timeout=30_000, state="visible")
    except PlaywrightTimeoutError:
        page.wait_for_timeout(2_000)
    return artifact_library


def list_artifacts(page: Page, notebook_id: str) -> Dict[str, Any]:
    """
    List all artifacts in a notebook.

    Args:
        page: The Playwright Page object
        notebook_id: The ID of the notebook

    Returns:
        Dictionary with status, message, and list of artifacts

    Raises:
        NotebookLMError: If listing artifacts fails
    """
    try:
        navigate_to_notebook(page, notebook_id)
        close_dialogs(page)
        artifact_library = _artifact_library(page)
        artifacts: List[Dict[str, Any]] = []
        
        # Get both artifact-library-item and artifact-library-note elements
        artifact_items = artifact_library.locator("artifact-library-item, artifact-library-note")
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
    """
    Delete an artifact from a notebook.

    Args:
        page: The Playwright Page object
        notebook_id: The ID of the notebook
        artifact_name: Name of the artifact to delete

    Returns:
        Dictionary with status and message

    Raises:
        NotebookLMError: If deleting artifact fails
    """
    try:
        navigate_to_notebook(page, notebook_id)
        close_dialogs(page)
        artifact_library = _artifact_library(page)
        # Find the artifact container (item or note) that contains the artifact
        artifact_container = (
            artifact_library.locator(
                "artifact-library-item, artifact-library-note"
            )
            .filter(has_text=artifact_name)
            .first
        )
        artifact_container.wait_for(timeout=10_000)
        # Find the "More" button within the artifact container
        # The More button is a sibling of the artifact button, so we search within the container
        more_button = artifact_container.get_by_label("More")
        more_button.wait_for(timeout=5_000)
        more_button.click()
        page.wait_for_timeout(300)
        delete_button = page.get_by_role(
            "menuitem", name=re.compile("Delete", re.IGNORECASE)
        )
        delete_button.wait_for(timeout=5_000)
        delete_button.click()
        page.wait_for_timeout(500)
        confirm_button = page.get_by_role(
            "button", name="Confirm deletion"
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
    """
    Rename an artifact in a notebook.

    Args:
        page: The Playwright Page object
        notebook_id: The ID of the notebook
        artifact_name: Current name of the artifact
        new_name: New name for the artifact

    Returns:
        Dictionary with status and message

    Raises:
        NotebookLMError: If renaming artifact fails
    """
    try:
        navigate_to_notebook(page, notebook_id)
        close_dialogs(page)
        artifact_library = _artifact_library(page)
        artifact_button = (
            artifact_library.locator(
                "artifact-library-item button.artifact-button-content, artifact-library-note button.artifact-button-content"
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


def download_artifact(
    page: Page, notebook_id: str, artifact_name: str
) -> Dict[str, Any]:
    """
    Download an artifact from a notebook.

    Args:
        page: The Playwright Page object
        notebook_id: The ID of the notebook
        artifact_name: Name of the artifact to download

    Returns:
        Dictionary with status and message

    Raises:
        NotebookLMError: If downloading artifact fails
    """
    try:
        navigate_to_notebook(page, notebook_id)
        close_dialogs(page)
        artifact_library = _artifact_library(page)
        artifact_button = (
            artifact_library.locator(
                "artifact-library-item button.artifact-button-content, artifact-library-note button.artifact-button-content"
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
