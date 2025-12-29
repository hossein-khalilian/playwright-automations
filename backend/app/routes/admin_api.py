from datetime import datetime

from app.auth import CurrentAdmin
from app.models import (
    GoogleCredentialCreateRequest,
    GoogleCredentialCreateResponse,
    GoogleCredentialDeleteResponse,
    GoogleCredentialListResponse,
    GoogleCredentialResponse,
    GoogleCredentialUpdateRequest,
    GoogleCredentialUpdateResponse,
)
from app.utils.db import (
    create_google_credential,
    delete_google_credential,
    get_all_google_credentials,
    get_google_credential_by_email,
    update_google_credential,
)
from app.utils.encryption import encrypt_password
from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get(
    "/google-credentials",
    response_model=GoogleCredentialListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_google_credentials(current_admin: CurrentAdmin) -> GoogleCredentialListResponse:
    """
    List all Google credentials (admin only).
    Passwords are not included in the response for security.
    """
    credentials = await get_all_google_credentials()
    
    credential_responses = [
        GoogleCredentialResponse(
            email=cred["email"],
            created_at=cred.get("created_at", datetime.now()),
            is_active=cred.get("is_active", True),
        )
        for cred in credentials
    ]
    
    return GoogleCredentialListResponse(credentials=credential_responses)


@router.post(
    "/google-credentials",
    response_model=GoogleCredentialCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_google_credential_endpoint(
    request: GoogleCredentialCreateRequest,
    current_admin: CurrentAdmin,
) -> GoogleCredentialCreateResponse:
    """
    Create a new Google credential (admin only).
    Password will be encrypted before storage.
    """
    # Validate email
    if not request.email or len(request.email.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email cannot be empty",
        )

    # Basic email validation
    if "@" not in request.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format",
        )

    # Validate password
    if not request.password or len(request.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long",
        )

    # Check if credential already exists
    existing = await get_google_credential_by_email(request.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists",
        )

    # Encrypt password
    try:
        encrypted_password = encrypt_password(request.password)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to encrypt password: {str(e)}",
        )

    # Create credential
    success = await create_google_credential(request.email, encrypted_password)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create credential. Database may be unavailable.",
        )

    return GoogleCredentialCreateResponse(
        status="success",
        message="Google credential created successfully",
        email=request.email,
    )


@router.put(
    "/google-credentials/{email}",
    response_model=GoogleCredentialUpdateResponse,
    status_code=status.HTTP_200_OK,
)
async def update_google_credential_endpoint(
    email: str,
    request: GoogleCredentialUpdateRequest,
    current_admin: CurrentAdmin,
) -> GoogleCredentialUpdateResponse:
    """
    Update a Google credential (admin only).
    Can update password and/or is_active status.
    """
    # Check if credential exists
    existing = await get_google_credential_by_email(email)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Google credential not found",
        )

    # Encrypt password if provided
    encrypted_password = None
    if request.password is not None:
        if len(request.password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 6 characters long",
            )
        try:
            encrypted_password = encrypt_password(request.password)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to encrypt password: {str(e)}",
            )

    # Update credential
    success = await update_google_credential(
        email,
        encrypted_password=encrypted_password,
        is_active=request.is_active,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update credential. Database may be unavailable.",
        )

    return GoogleCredentialUpdateResponse(
        status="success",
        message="Google credential updated successfully",
    )


@router.delete(
    "/google-credentials/{email}",
    response_model=GoogleCredentialDeleteResponse,
    status_code=status.HTTP_200_OK,
)
async def delete_google_credential_endpoint(
    email: str,
    current_admin: CurrentAdmin,
) -> GoogleCredentialDeleteResponse:
    """
    Delete a Google credential (admin only).
    Performs a soft delete by setting is_active to False.
    """
    # Check if credential exists
    existing = await get_google_credential_by_email(email)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Google credential not found",
        )

    # Delete credential (soft delete)
    success = await delete_google_credential(email)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete credential. Database may be unavailable.",
        )

    return GoogleCredentialDeleteResponse(
        status="success",
        message="Google credential deleted successfully",
    )


