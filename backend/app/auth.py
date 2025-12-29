import os
from datetime import datetime, timedelta, timezone
from typing import Annotated, List, Optional

import bcrypt
from app.models import TokenData, User
from app.utils.config import config
from app.utils.db import get_user_by_username, get_user_roles, user_has_permission, user_has_role
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

JWT_SECRET_KEY = config.get("jwt_secret_key")
JWT_ALGORITHM = config.get("jwt_algorithm")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = config.get("jwt_access_token_expire_minutes")


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


async def verify_credentials(username: str, password: str) -> Optional[User]:
    """
    Verify username/password against database.
    Returns User if valid, None otherwise.
    """
    user_doc = await get_user_by_username(username)
    if not user_doc:
        return None

    if not user_doc.get("is_active", True):
        return None

    hashed_password = user_doc.get("hashed_password")
    if not hashed_password:
        return None

    if verify_password(password, hashed_password):
        # Get roles from database
        roles = await get_user_roles(username)
        return User(username=username, roles=roles)
    return None


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta
        else timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    # Ensure roles are in the token (support both formats for backward compatibility)
    if "roles" not in to_encode and "role" in to_encode:
        to_encode["roles"] = [to_encode["role"]]
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
        roles: List[str] | None = payload.get("roles")
        # Support legacy single role in token
        if roles is None:
            role: str | None = payload.get("role")
            roles = [role] if role else None
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username, roles=roles)
    except JWTError:
        raise credentials_exception

    # Verify user exists in database and is active
    user_doc = await get_user_by_username(token_data.username)
    if not user_doc or not user_doc.get("is_active", True):
        raise credentials_exception

    # Get roles from database (preferred) or from token (fallback)
    user_roles = await get_user_roles(token_data.username)
    if not user_roles and token_data.roles:
        user_roles = token_data.roles
    if not user_roles:
        user_roles = ["user"]
    
    return User(username=token_data.username, roles=user_roles)


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Dependency that ensures the current user has admin role.
    Raises 403 Forbidden if user is not an admin.
    """
    has_admin = await user_has_role(current_user.username, "admin")
    if not has_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin role required.",
        )
    return current_user


async def require_permission(
    current_user: Annotated[User, Depends(get_current_user)],
    permission: str,
) -> User:
    """
    Dependency that ensures the current user has a specific permission.
    Raises 403 Forbidden if user doesn't have the permission.
    """
    has_perm = await user_has_permission(current_user.username, permission)
    if not has_perm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Not enough permissions. '{permission}' permission required.",
        )
    return current_user


CurrentAdmin = Annotated[User, Depends(get_current_admin)]
