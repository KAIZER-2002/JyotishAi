from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.repositories.user_repository import UserRepository
from app.services.user_service import UserService, UserAlreadyExistsException
from app.services.auth_service import AuthService, UserInactiveException
from app.schemas.user import UserCreate, UserResponse, UserLogin
from app.schemas.auth import TokenResponse, RefreshTokenRequest
from app.exceptions.auth import (
    InvalidCredentialsException,
    AuthenticationException,
    TokenExpiredException,
    TokenInvalidException,
    InvalidTokenTypeException,
)


router = APIRouter(prefix="/auth", tags=["Authentication"])


async def get_user_service_async(db: AsyncSession = Depends(get_db)) -> UserService:
    """
    Dependency that constructs the UserService chain.
    """
    user_repo = UserRepository(db)
    return UserService(user_repo)


async def get_auth_service_async(db: AsyncSession = Depends(get_db)) -> AuthService:
    """
    Dependency that constructs the AuthService chain.
    """
    user_repo = UserRepository(db)
    return AuthService(user_repo)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Creates a new user account in the system."
)
async def register(
    user_in: UserCreate,
    user_service: UserService = Depends(get_user_service_async)
) -> UserResponse:
    """
    Endpoint to register a new user.
    """
    try:
        return await user_service.register_user(user_in)
    except UserAlreadyExistsException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        # Catch-all for unexpected errors to avoid leaking internal stack traces
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during registration: {str(e)}"
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User Login",
    description="Authenticates user credentials and returns a JWT token pair."
)
async def login(
    login_data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service_async)
) -> TokenResponse:
    """
    Endpoint to authenticate users and issue tokens.
    """
    try:
        # 1. Authenticate the user
        user = await auth_service.authenticate_user(
            email=login_data.email,
            password=login_data.password
        )
        
        # 2. Generate the token pair
        token_pair = await auth_service.create_token_pair(user)
        
        return token_pair
        
    except InvalidCredentialsException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except UserInactiveException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal server error occurred during login: {str(e)}"
        )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh Access Token",
    description="Issues a new access token (and optionally a new refresh token) using a valid refresh token."
)
async def refresh(
    refresh_request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service_async)
) -> TokenResponse:
    """
    Endpoint to refresh the access token.
    """
    try:
        return await auth_service.refresh_tokens(refresh_request.refresh_token)
        
    except TokenExpiredException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except (TokenInvalidException, InvalidTokenTypeException, AuthenticationException) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except UserInactiveException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during token refresh: {str(e)}"
        )

