from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.repositories.user_repository import UserRepository
from app.db.session import get_db
from app.schemas.user import UserProfileResponse, UserProfileUpdate, UserSettingsSchema, UserSettingsUpdate
from app.services.user_service import UserService, UserNotFoundException
from app.services.avatar_storage import LocalAvatarStorageService, AvatarStorageService

router = APIRouter(prefix="/users", tags=["Users"])

CurrentUser = Annotated[User, Depends(get_current_user)]


def _build_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """Dependency: constructs UserService with the request-scoped DB session."""
    return UserService(UserRepository(db))


def _build_avatar_storage() -> AvatarStorageService:
    """Dependency: constructs LocalAvatarStorageService for processing uploads."""
    return LocalAvatarStorageService()


@router.get(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    description="Returns the full profile (personal + birth information) of the authenticated user.",
)
async def get_my_profile(
    current_user: CurrentUser,
    user_service: UserService = Depends(_build_user_service),
) -> UserProfileResponse:
    """Retrieve the authenticated user's full profile."""
    try:
        return await user_service.get_profile(current_user.id)
    except UserNotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.patch(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Update current user profile",
    description=(
        "Partially updates the profile of the authenticated user. "
        "Only fields present in the request body are written; omitted fields are left unchanged."
    ),
)
async def update_my_profile(
    payload: UserProfileUpdate,
    current_user: CurrentUser,
    user_service: UserService = Depends(_build_user_service),
) -> UserProfileResponse:
    """Partially update the authenticated user's profile (personal + birth information)."""
    try:
        return await user_service.update_profile(current_user.id, payload)
    except UserNotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/me/avatar",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload user avatar",
    description="Uploads an image file to update the user's profile avatar.",
)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: CurrentUser = None,
    user_service: UserService = Depends(_build_user_service),
    storage_service: AvatarStorageService = Depends(_build_avatar_storage),
) -> UserProfileResponse:
    """Uploads an image file, saves it via storage abstraction, and updates avatar_url in the database."""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image."
        )

    try:
        content = await file.read()
        return await user_service.update_avatar(
            user_id=current_user.id,
            file_content=content,
            filename=file.filename or "avatar.png",
            storage_service=storage_service,
        )
    except UserNotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process image upload: {str(exc)}"
        )


@router.get(
    "/me/settings",
    response_model=UserSettingsSchema,
    status_code=status.HTTP_200_OK,
    summary="Get current user settings",
    description="Returns the nested preference configurations of the authenticated user.",
)
async def get_my_settings(
    current_user: CurrentUser,
    user_service: UserService = Depends(_build_user_service),
) -> UserSettingsSchema:
    try:
        return await user_service.get_settings(current_user.id)
    except UserNotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.patch(
    "/me/settings",
    response_model=UserSettingsSchema,
    status_code=status.HTTP_200_OK,
    summary="Update current user settings",
    description="Partially updates user preferences, merging sections dynamically.",
)
async def update_my_settings(
    payload: UserSettingsUpdate,
    current_user: CurrentUser,
    user_service: UserService = Depends(_build_user_service),
) -> UserSettingsSchema:
    try:
        return await user_service.update_settings(current_user.id, payload)
    except UserNotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete(
    "/me",
    status_code=status.HTTP_200_OK,
    summary="Delete user account",
    description="Permanently deletes the current user's profile and credentials.",
)
async def delete_my_account(
    current_user: CurrentUser,
    user_service: UserService = Depends(_build_user_service),
    storage_service: AvatarStorageService = Depends(_build_avatar_storage),
):
    deleted = await user_service.delete_user(current_user.id, storage_service)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account not found or could not be deleted."
        )
    return {"message": "Account deleted successfully."}


@router.post(
    "/me/logout-all",
    status_code=status.HTTP_200_OK,
    summary="Logout all sessions",
    description="Invalidates all active client sessions/tokens by incrementing the security token version.",
)
async def logout_all_sessions(
    current_user: CurrentUser,
    user_service: UserService = Depends(_build_user_service),
):
    await user_service.logout_all_sessions(current_user.id)
    return {"message": "Successfully logged out of all active sessions."}


