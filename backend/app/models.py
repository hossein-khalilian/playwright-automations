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
    notebooks: List[Notebook] = Field(description="List of notebooks for the current user")


class SourceUploadResponse(BaseModel):
    status: str = Field(description="Status of the source upload")
    message: str = Field(description="Message describing the result")


class Source(BaseModel):
    name: str = Field(description="Name of the source file")


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
    messages: List[ChatMessage] = Field(description="List of chat messages in chronological order")


class AudioOverviewCreateResponse(BaseModel):
    status: str = Field(description="Status of the audio overview creation")
    message: str = Field(description="Message describing the result")


class AudioOverviewStatusResponse(BaseModel):
    status: str = Field(description="Status of the operation")
    message: str = Field(description="Message describing the result")
    is_generating: bool = Field(description="Whether the audio overview is currently being generated")
    audio_name: Optional[str] = Field(None, description="Name of the audio overview if it exists")


class AudioOverviewRenameRequest(BaseModel):
    new_name: str = Field(description="The new name for the audio overview")


class AudioOverviewRenameResponse(BaseModel):
    status: str = Field(description="Status of the rename operation")
    message: str = Field(description="Message describing the result")


class AudioOverviewDownloadResponse(BaseModel):
    status: str = Field(description="Status of the download operation")
    message: str = Field(description="Message describing the result")
    download_path: Optional[str] = Field(None, description="Path to the downloaded file")
    suggested_filename: Optional[str] = Field(None, description="Suggested filename for the download")


class AudioOverviewDeleteResponse(BaseModel):
    status: str = Field(description="Status of the deletion operation")
    message: str = Field(description="Message describing the result")


class VideoOverviewCreateResponse(BaseModel):
    status: str = Field(description="Status of the video overview creation")
    message: str = Field(description="Message describing the result")


class VideoInfo(BaseModel):
    name: str = Field(description="Name of the video overview")


class VideoOverviewStatusResponse(BaseModel):
    status: str = Field(description="Status of the operation")
    message: str = Field(description="Message describing the result")
    is_generating: bool = Field(description="Whether the video overview is currently being generated")
    videos: List[VideoInfo] = Field(default_factory=list, description="List of video overviews if they exist")


class VideoOverviewRenameRequest(BaseModel):
    video_name: str = Field(description="The current name of the video overview to rename")
    new_name: str = Field(description="The new name for the video overview")


class VideoOverviewRenameResponse(BaseModel):
    status: str = Field(description="Status of the rename operation")
    message: str = Field(description="Message describing the result")


class VideoOverviewDownloadRequest(BaseModel):
    video_name: Optional[str] = Field(None, description="Optional name of the specific video to download. If not provided, downloads the first video.")


class VideoOverviewDownloadResponse(BaseModel):
    status: str = Field(description="Status of the download operation")
    message: str = Field(description="Message describing the result")
    download_path: Optional[str] = Field(None, description="Path to the downloaded file")
    suggested_filename: Optional[str] = Field(None, description="Suggested filename for the download")


class VideoOverviewDeleteRequest(BaseModel):
    video_name: Optional[str] = Field(None, description="Optional name of the specific video to delete. If not provided, deletes the first video.")


class VideoOverviewDeleteResponse(BaseModel):
    status: str = Field(description="Status of the deletion operation")
    message: str = Field(description="Message describing the result")
