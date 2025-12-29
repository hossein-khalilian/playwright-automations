from datetime import timedelta

from app.auth import (
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    CurrentAdmin,
    CurrentUser,
    create_access_token,
    hash_password,
    verify_credentials,
)
from app.models import LoginRequest, RegisterRequest, RegisterResponse, Token
from app.utils.db import create_user, user_exists
from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
)
async def login(request: LoginRequest) -> Token:
    """
    Username/password login that returns a JWT Bearer token.
    Credentials are validated against the database.
    """
    user = await verify_credentials(request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    access_token_expires = timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires,
    )
    return Token(access_token=access_token, token_type="bearer")


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(request: RegisterRequest) -> RegisterResponse:
    """
    Create a new user account.
    Username must be unique. Password will be hashed before storage.
    """
    # Validate username (basic validation)
    if not request.username or len(request.username.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username cannot be empty",
        )

    if len(request.username) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be at least 3 characters long",
        )

    # Validate password
    if not request.password or len(request.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long",
        )

    # Check if user already exists
    if await user_exists(request.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )

    # Hash password and create user
    hashed_password = hash_password(request.password)
    success = await create_user(request.username, hashed_password)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user. Database may be unavailable.",
        )

    return RegisterResponse(
        message="User created successfully",
        username=request.username,
    )


@router.get(
    "/me",
    response_model=str,
    status_code=status.HTTP_200_OK,
)
async def read_me(current_user: CurrentUser) -> str:
    """
    Simple endpoint to verify that JWT authentication works.
    """
    return current_user.username


@router.get(
    "/admin/test",
    response_model=dict,
    status_code=status.HTTP_200_OK,
)
async def admin_test(current_admin: CurrentAdmin) -> dict:
    """
    Test endpoint that requires admin role.
    Only users with admin role can access this endpoint.
    """
    return {
        "message": "Admin access granted",
        "username": current_admin.username,
        "role": current_admin.role,
    }
