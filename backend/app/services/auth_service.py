from typing import Dict
from app.db.repositories.user_repository import UserRepository
from app.db.models.user import User
from app.core.security import verify_password
from app.core.jwt import create_access_token, create_refresh_token, decode_token
from app.exceptions.auth import InvalidCredentialsException, AuthException, TokenInvalidException, AuthenticationException


class UserInactiveException(AuthException):
    """Raised when the user account is disabled."""
    pass


class AuthService:
    """
    Service layer for handling user authentication and session management.
    
    Coordinates between user data (UserRepository), credential verification (security),
    and token issuance (jwt).
    """

    def __init__(self, user_repository: UserRepository) -> None:
        self._repo = user_repository

    async def authenticate_user(self, email: str, password: str) -> User:
        """
        Verifies a user's credentials and returns the user model if successful.
        """
        # 1. Find user by email
        user = await self._repo.get_by_email(email)
        if not user:
            raise InvalidCredentialsException("Invalid email or password.")
            
        # 2. Verify password
        if not verify_password(password, user.hashed_password):
            raise InvalidCredentialsException("Invalid email or password.")
            
        # 3. Check if account is active
        if not user.is_active:
            raise UserInactiveException("Your account is deactivated. Please contact support.")
            
        return user

    async def create_token_pair(self, user: User) -> Dict[str, str]:
        """
        Generates a pair of access and refresh tokens for a user.
        """
        claims = {"v": user.token_version}
        access_token = create_access_token(subject=str(user.id), additional_claims=claims)
        refresh_token = create_refresh_token(subject=str(user.id), additional_claims=claims)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    async def refresh_tokens(self, refresh_token: str) -> Dict[str, str]:
        """
        Validates a refresh token and issues a new token pair.
        
        Args:
            refresh_token: The refresh token provided by the client.
            
        Returns:
            A new dictionary containing the access and refresh tokens.
            
        Raises:
            TokenInvalidException: If the token is malformed or type is incorrect.
            AuthenticationException: If the user no longer exists.
            UserInactiveException: If the user account is disabled.
        """
        # 1. Decode and validate token type ("refresh")
        payload = decode_token(token=refresh_token, expected_type="refresh")
        
        # 2. Extract user UUID from 'sub'
        user_id = payload.get("sub")
        if not user_id:
            raise TokenInvalidException("Token payload missing subject.")
            
        # 3. Load user and verify state
        user = await self._repo.get_by_id(user_id)
        if not user:
            raise AuthenticationException("User associated with this token no longer exists.")
        
        if not user.is_active:
            raise UserInactiveException("User account is deactivated.")

        if payload.get("v") != user.token_version:
            raise TokenInvalidException("Token version mismatch. Session has been revoked.")
            
        # 4. Rotate tokens (Issue new pair)
        return await self.create_token_pair(user)
