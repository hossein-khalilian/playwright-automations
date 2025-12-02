from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator


class GoogleLoginStatusResponse(BaseModel):
    is_logged_in: bool = Field(description="Whether Google is currently logged in")


class NotebookCreateResponse(BaseModel):
    status: str = Field(description="Status of the notebook creation")
    message: str = Field(description="Message describing the result")
    notebook_url: Optional[str] = Field(
        None, description="URL of the created notebook page"
    )


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    username: str


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str


class RegisterResponse(BaseModel):
    message: str
    username: str


class Notebook(BaseModel):
    notebook_id: str = Field(description="Unique identifier for the notebook")
    notebook_url: str = Field(description="URL of the notebook page")
    created_at: datetime = Field(description="Timestamp when the notebook was created")


class NotebookListResponse(BaseModel):
    notebooks: List[Notebook] = Field(
        description="List of notebooks for the current user"
    )


class SourceUploadResponse(BaseModel):
    status: str = Field(description="Status of the source upload")
    message: str = Field(description="Message describing the result")


class Source(BaseModel):
    name: str = Field(description="Name of the source file")
    status: str = Field(
        default="unknown",
        description="Status of the source (processing, ready, unknown)",
    )


class SourceListResponse(BaseModel):
    status: str = Field(description="Status of the operation")
    message: str = Field(description="Message describing the result")
    sources: List[Source] = Field(description="List of sources in the notebook")


class SourceRenameRequest(BaseModel):
    new_name: str = Field(description="The new name for the source")


class SourceRenameResponse(BaseModel):
    status: str = Field(description="Status of the rename operation")
    message: str = Field(description="Message describing the result")


class SourceImageInfo(BaseModel):
    base64: Optional[str] = Field(None, description="Base64-encoded image data")
    mime_type: Optional[str] = Field(None, description="MIME type of the image (e.g., image/png, image/jpeg)")


class SourceReviewResponse(BaseModel):
    status: str = Field(description="Status of the operation")
    message: str = Field(description="Message describing the result")
    title: Optional[str] = Field(None, description="Title/name of the source")
    summary: Optional[str] = Field(None, description="Summary of the source content")
    key_topics: List[str] = Field(
        default_factory=list, description="List of key topics extracted from the source"
    )
    content: Optional[str] = Field(None, description="Full content/transcript of the source")
    images: List[SourceImageInfo] = Field(
        default_factory=list, description="List of images found in the source"
    )


class NotebookQueryRequest(BaseModel):
    query: str = Field(description="The query text to send to the notebook")


class NotebookQueryResponse(BaseModel):
    status: str = Field(description="Status of the query operation")
    message: str = Field(description="Message describing the result")
    query: str = Field(description="The query that was sent")


class ChatMessage(BaseModel):
    role: str = Field(description="Role of the message sender: 'user' or 'assistant'")
    content: str = Field(description="The message content in markdown format")


class ChatHistoryResponse(BaseModel):
    status: str = Field(description="Status of the operation")
    message: str = Field(description="Message describing the result")
    messages: List[ChatMessage] = Field(
        description="List of chat messages in chronological order"
    )


class AudioFormat(str, Enum):
    DEEP_DIVE = "Deep Dive"
    BRIEF = "Brief"
    CRITIQUE = "Critique"
    DEBATE = "Debate"


class AudioLanguage(str, Enum):
    ENGLISH = "english"
    PERSIAN = "persian"


class AudioOverviewCreateRequest(BaseModel):
    audio_format: Optional[AudioFormat] = Field(
        None,
        description='Audio format - "Deep Dive", "Brief", "Critique", or "Debate"',
    )
    language: Optional[AudioLanguage] = Field(
        None,
        description="Language - 'english' or 'persian'",
    )
    length: Optional[str] = Field(
        None,
        description='Audio length - depends on format: Deep Dive (Short/Default/Long), Brief (none), Critique/Debate (Short/Default)',
    )
    focus_text: Optional[str] = Field(
        None,
        description="Optional focus text for the AI hosts (max 5000 chars)",
        max_length=5000,
    )

    @model_validator(mode="after")
    def validate_length_for_format(self):
        """Validate length based on selected audio format."""
        if self.length is None or self.audio_format is None:
            return self
        
        # Map format-specific valid lengths
        valid_lengths = {
            AudioFormat.DEEP_DIVE: ["Short", "Default", "Long"],
            AudioFormat.BRIEF: [],  # No length option for Brief
            AudioFormat.CRITIQUE: ["Short", "Default"],
            AudioFormat.DEBATE: ["Short", "Default"],
        }
        
        valid_for_format = valid_lengths.get(self.audio_format, [])
        
        # Brief format doesn't support length
        if self.audio_format == AudioFormat.BRIEF:
            raise ValueError("Brief format does not support length parameter")
        
        # Check if length is valid for the format
        if valid_for_format and self.length not in valid_for_format:
            raise ValueError(
                f"Invalid length '{self.length}' for format '{self.audio_format.value}'. "
                f"Valid options: {', '.join(valid_for_format)}"
            )
        
        return self


class AudioOverviewCreateResponse(BaseModel):
    status: str = Field(description="Status of the audio overview creation")
    message: str = Field(description="Message describing the result")


class VideoFormat(str, Enum):
    EXPLAINER = "Explainer"
    BRIEF = "Brief"


class VideoVisualStyle(str, Enum):
    AUTO_SELECT = "Auto-select"
    CUSTOM = "Custom"
    CLASSIC = "Classic"
    WHITEBOARD = "Whiteboard"
    KAWAII = "Kawaii"
    ANIME = "Anime"
    WATERCOLOR = "Watercolor"
    RETRO_PRINT = "Retro print"
    HERITAGE = "Heritage"
    PAPER_CRAFT = "Paper-craft"


class VideoOverviewCreateRequest(BaseModel):
    video_format: Optional[VideoFormat] = Field(
        None,
        description='Video format - "Explainer" or "Brief"',
    )
    language: Optional[AudioLanguage] = Field(
        None,
        description="Language - 'english' or 'persian'",
    )
    visual_style: Optional[VideoVisualStyle] = Field(
        None,
        description='Visual style - "Auto-select", "Custom", "Classic", "Whiteboard", "Kawaii", "Anime", "Watercolor", "Retro print", "Heritage", or "Paper-craft"',
    )
    custom_style_description: Optional[str] = Field(
        None,
        description="Custom visual style description (required when visual_style is Custom, max 5000 chars)",
        max_length=5000,
    )
    focus_text: Optional[str] = Field(
        None,
        description="Optional focus text for the AI hosts (max 5000 chars)",
        max_length=5000,
    )

    @model_validator(mode="after")
    def validate_custom_style_description(self):
        """Validate that custom_style_description is provided when visual_style is Custom."""
        if self.visual_style == VideoVisualStyle.CUSTOM:
            if not self.custom_style_description or not self.custom_style_description.strip():
                raise ValueError(
                    "custom_style_description is required when visual_style is 'Custom'"
                )
        return self


class VideoOverviewCreateResponse(BaseModel):
    status: str = Field(description="Status of the video overview creation")
    message: str = Field(description="Message describing the result")


class ArtifactInfo(BaseModel):
    type: Optional[str] = Field(
        None,
        description="Type of artifact (audio_overview, video_overview, quiz, etc.)",
    )
    name: Optional[str] = Field(None, description="Name/title of the artifact")
    details: Optional[str] = Field(
        None, description="Additional details (source count, time ago, etc.)"
    )
    status: str = Field(
        description="Status of the artifact (ready, generating, unknown)"
    )
    is_generating: bool = Field(
        False, description="Whether the artifact is currently being generated"
    )
    has_play: bool = Field(
        False,
        description="Whether the artifact has a play button (available for playback)",
    )
    has_interactive: bool = Field(
        False, description="Whether the artifact has interactive mode"
    )


class ArtifactListResponse(BaseModel):
    status: str = Field(description="Status of the operation")
    message: str = Field(description="Message describing the result")
    artifacts: List[ArtifactInfo] = Field(
        default_factory=list, description="List of artifacts in the notebook"
    )


class ArtifactDeleteResponse(BaseModel):
    status: str = Field(description="Status of the deletion operation")
    message: str = Field(description="Message describing the result")


class ArtifactRenameRequest(BaseModel):
    new_name: str = Field(description="The new name for the artifact")


class ArtifactRenameResponse(BaseModel):
    status: str = Field(description="Status of the rename operation")
    message: str = Field(description="Message describing the result")
