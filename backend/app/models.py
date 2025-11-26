from typing import Optional

from pydantic import BaseModel, Field


class GoogleLoginStatusResponse(BaseModel):
    is_logged_in: bool = Field(description="Whether Google is currently logged in")
