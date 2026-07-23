from uuid import UUID
from typing import Annotated, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.repositories.user_repository import UserRepository
from app.db.models.user import User
from app.core.jwt import decode_token, TokenExpiredException, TokenInvalidException


# HTTPBearer extracts the Authorization: Bearer <token> header automatically.
_bearer = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency that validates the Bearer token and returns the
    authenticated User model instance.

    Raises:
        HTTP 401 Unauthorized – if the token is missing, expired, or invalid.
        HTTP 401 Unauthorized – if the user no longer exists.
        HTTP 403 Forbidden   – if the user account is inactive.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token=credentials.credentials, expected_type="access")
    except TokenExpiredException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except TokenInvalidException:
        raise credentials_exception

    user_id_str: str | None = payload.get("sub")
    if not user_id_str:
        raise credentials_exception

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise credentials_exception

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise credentials_exception

    # Check token version claim to support revoking all sessions
    token_version = payload.get("v")
    if token_version is not None and user.token_version != token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has been revoked or expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated.",
        )

    return user


_bearer_optional = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(_bearer_optional)],
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    FastAPI dependency that optionally validates a Bearer token and returns the User if valid,
    otherwise returns None without raising authentication exceptions.
    """
    if not credentials:
        return None
    try:
        payload = decode_token(token=credentials.credentials, expected_type="access")
        user_id_str = payload.get("sub")
        if not user_id_str:
            return None
        user_id = UUID(user_id_str)
        user_repo = UserRepository(db)
        user = await user_repo.get_by_id(user_id)
        if user and user.is_active:
            token_version = payload.get("v")
            if token_version is None or user.token_version == token_version:
                return user
    except Exception:
        pass
    return None

