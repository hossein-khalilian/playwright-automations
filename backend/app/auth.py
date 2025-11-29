import os
from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.utils.config import config
from app.utils.db import get_user_by_username

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

JWT_SECRET_KEY = config.get("jwt_secret_key")
JWT_ALGORITHM = config.get("hs256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = config.get("jwt_access_token_expire_minutes")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    username: str


# HTTPBearer is better for Swagger UI Bearer token authentication
bearer_scheme = HTTPBearer()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def verify_credentials(username: str, password: str) -> Optional[User]:
    """
    Verify username/password against database.
    Returns User if valid, None otherwise.
    """
    user_doc = get_user_by_username(username)
    if not user_doc:
        return None

    if not user_doc.get("is_active", True):
        return None

    hashed_password = user_doc.get("hashed_password")
    if not hashed_password:
        return None

    if verify_password(password, hashed_password):
        return User(username=username)
    return None


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta
        else timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    # Verify user exists in database and is active
    user_doc = get_user_by_username(token_data.username)
    if not user_doc or not user_doc.get("is_active", True):
        raise credentials_exception

    return User(username=token_data.username)


CurrentUser = Annotated[User, Depends(get_current_user)]
