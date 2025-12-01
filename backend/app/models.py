from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


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


class AudioOverviewCreateResponse(BaseModel):
    status: str = Field(description="Status of the audio overview creation")
    message: str = Field(description="Message describing the result")


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
