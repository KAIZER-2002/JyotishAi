from typing import Optional
from uuid import UUID
from app.db.repositories.user_repository import UserRepository
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserProfileUpdate,
    UserProfileResponse,
    UserSettingsSchema,
    UserSettingsUpdate,
)
from app.core.security import hash_password
from app.services.avatar_storage import AvatarStorageService


class UserServiceException(Exception):
    """Base exception for user service errors."""
    pass


class UserAlreadyExistsException(UserServiceException):
    """Raised when a user with the same email or username already exists."""
    pass


class UserNotFoundException(UserServiceException):
    """Raised when a requested user cannot be found."""
    pass


class UserService:
    """
    Service layer for managing user business logic.

    Acts as a mediator between the API routes and the UserRepository,
    handling validation, password hashing, and data transformation.
    """

    def __init__(self, user_repository: UserRepository) -> None:
        self._repo = user_repository

    async def register_user(self, data: UserCreate) -> UserResponse:
        """
        Registers a new user in the system.

        Args:
            data: User creation details.

        Returns:
            The created user as a UserResponse schema.

        Raises:
            UserAlreadyExistsException: If email or username is already taken.
        """
        # 1. Validation: Check for duplicate email
        if await self._repo.exists_email(data.email):
            raise UserAlreadyExistsException(f"User with email {data.email} already exists.")

        # 2. Validation: Check for duplicate username
        if await self._repo.exists_username(data.username):
            raise UserAlreadyExistsException(f"Username {data.username} is already taken.")

        # 3. Security: Hash the plain-text password
        hashed_pwd = hash_password(data.password)

        # 4. Persistence: Create user via repository
        user_data = data.model_dump()
        user_data["hashed_password"] = hashed_pwd
        # Remove plain text password from the dict before passing to repo
        del user_data["password"]

        user = await self._repo.create(user_data)

        # 5. Transformation: Return as UserResponse
        return UserResponse.model_validate(user)

    async def get_user_by_id(self, user_id: UUID) -> UserResponse:
        """
        Retrieve a user by their ID.

        Raises:
            UserNotFoundException: If no user is found.
        """
        user = await self._repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundException(f"User with ID {user_id} not found.")
        return UserResponse.model_validate(user)

    async def get_user_by_email(self, email: str) -> UserResponse:
        """
        Retrieve a user by their email.

        Raises:
            UserNotFoundException: If no user is found.
        """
        user = await self._repo.get_by_email(email)
        if not user:
            raise UserNotFoundException(f"User with email {email} not found.")
        return UserResponse.model_validate(user)

    async def get_user_by_username(self, username: str) -> UserResponse:
        """
        Retrieve a user by their username.

        Raises:
            UserNotFoundException: If no user is found.
        """
        user = await self._repo.get_by_username(username)
        if not user:
            raise UserNotFoundException(f"User with username {username} not found.")
        return UserResponse.model_validate(user)

    async def update_user(self, user_id: UUID, data: UserUpdate) -> UserResponse:
        """
        Update user profile information.

        Args:
            user_id: ID of the user to update.
            data: Fields to update.

        Returns:
            The updated user.

        Raises:
            UserNotFoundException: If user does not exist.
        """
        # Verify user existence first
        user = await self._repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundException(f"User with ID {user_id} not found.")

        update_data = data.model_dump(exclude_unset=True)

        # If password is being updated, hash it first
        if "password" in update_data:
            plain_password = update_data.pop("password")
            update_data["hashed_password"] = hash_password(plain_password)

        updated_user = await self._repo.update(user_id, update_data)
        return UserResponse.model_validate(updated_user)

    async def get_profile(self, user_id: UUID) -> UserProfileResponse:
        """
        Retrieve the full profile (personal + birth information) for a user.

        Raises:
            UserNotFoundException: If no user is found.
        """
        user = await self._repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundException(f"User with ID {user_id} not found.")
        return UserProfileResponse.model_validate(user)

    async def update_profile(self, user_id: UUID, data: UserProfileUpdate) -> UserProfileResponse:
        """
        Update extended profile fields (personal + birth information).

        Only fields explicitly provided in the request body are updated
        (exclude_unset semantics).

        Args:
            user_id: ID of the authenticated user.
            data: Profile fields to update.

        Returns:
            The updated profile as UserProfileResponse.

        Raises:
            UserNotFoundException: If user does not exist.
        """
        user = await self._repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundException(f"User with ID {user_id} not found.")

        update_data = data.model_dump(exclude_unset=True)

        # Serialize date to ISO string if provided (SQLAlchemy Date column accepts date objects)
        updated_user = await self._repo.update(user_id, update_data)
        return UserProfileResponse.model_validate(updated_user)

    async def update_avatar(
        self,
        user_id: UUID,
        file_content: bytes,
        filename: str,
        storage_service: AvatarStorageService,
    ) -> UserProfileResponse:
        """
        Orchestrates uploading the avatar using the storage service abstraction
        and updating the database record.
        """
        user = await self._repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundException(f"User with ID {user_id} not found.")

        # Service orchestrates the storage upload
        avatar_path = await storage_service.upload_avatar(user_id, file_content, filename)

        # Service updates database state
        updated_user = await self._repo.update(user_id, {"avatar_url": avatar_path})
        return UserProfileResponse.model_validate(updated_user)

    async def deactivate_user(self, user_id: UUID) -> bool:
        """
        Deactivates a user account (soft delete).

        Returns:
            True if deactivated, False if user not found.
        """
        user = await self._repo.get_by_id(user_id)
        if not user:
            return False

        await self._repo.update(user_id, {"is_active": False})
        return True

    async def get_settings(self, user_id: UUID) -> UserSettingsSchema:
        """Retrieves settings for the given user, returning defaults if not yet set."""
        user = await self._repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundException(f"User with ID {user_id} not found.")

        if not user.settings:
            return UserSettingsSchema()

        return UserSettingsSchema.model_validate(user.settings)

    async def update_settings(self, user_id: UUID, data: UserSettingsUpdate) -> UserSettingsSchema:
        """Partially updates the user's settings, merging nested JSON dictionaries."""
        user = await self._repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundException(f"User with ID {user_id} not found.")

        current_settings = user.settings or UserSettingsSchema().model_dump()
        update_dict = data.model_dump(exclude_unset=True)

        # Merge nested structures (general, ai, astrology, notifications)
        for section, fields in update_dict.items():
            if fields:
                if section not in current_settings:
                    current_settings[section] = {}
                current_settings[section].update(fields)

        # Persistence via UserRepository
        updated_user = await self._repo.update(user_id, {"settings": current_settings})
        return UserSettingsSchema.model_validate(updated_user.settings)

    async def delete_user(self, user_id: UUID, storage_service: Optional[AvatarStorageService] = None) -> bool:
        """Permanently deletes the user account (hard delete) and cleans up storage resources."""
        user = await self._repo.get_by_id(user_id)
        if not user:
            return False

        if user.avatar_url and storage_service:
            try:
                await storage_service.delete_avatar(user_id, user.avatar_url)
            except Exception:
                pass

        return await self._repo.delete(user_id)

    async def logout_all_sessions(self, user_id: UUID) -> bool:
        """Invalidates all active client sessions/tokens by incrementing the security token version."""
        user = await self._repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundException(f"User with ID {user_id} not found.")

        await self._repo.update(user_id, {"token_version": user.token_version + 1})
        return True



