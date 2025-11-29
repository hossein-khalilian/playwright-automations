from typing import Optional

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
