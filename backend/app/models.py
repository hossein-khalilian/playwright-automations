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
