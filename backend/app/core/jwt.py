from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from uuid import uuid4
from jose import JWTError, jwt
from app.core.config import settings


class JWTException(Exception):
    """Base exception for JWT related errors."""
    pass


class TokenExpiredException(JWTException):
    """Raised when a token has expired."""
    pass


class TokenInvalidException(JWTException):
    """Raised when a token is invalid or malformed."""
    pass


def _generate_token(
    subject: str, 
    expires_delta: timedelta, 
    token_type: str, 
    additional_claims: Optional[Dict[str, Any]] = None
) -> str:
    """
    Internal helper to create a JWT token with standard and custom claims.
    """
    now = datetime.now(timezone.utc)
    
    payload = {
        "sub": subject,
        "iat": now,
        "nbf": now,
        "exp": now + expires_delta,
        "jti": str(uuid4()),
        "type": token_type
    }
    
    if additional_claims:
        payload.update(additional_claims)
        
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(subject: str, additional_claims: Optional[Dict[str, Any]] = None) -> str:
    """
    Generates a short-lived access token.
    """
    return _generate_token(
        subject=subject, 
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES), 
        token_type="access",
        additional_claims=additional_claims
    )


def create_refresh_token(subject: str, additional_claims: Optional[Dict[str, Any]] = None) -> str:
    """
    Generates a long-lived refresh token.
    """
    return _generate_token(
        subject=subject, 
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS), 
        token_type="refresh",
        additional_claims=additional_claims
    )


def decode_token(token: str, expected_type: str) -> Dict[str, Any]:
    """
    Decodes and validates a JWT token, enforcing the expected token type.
    
    Args:
        token: The JWT token string.
        expected_type: The expected value of the 'type' claim (e.g., 'access' or 'refresh').
        
    Returns:
        The decoded payload as a dictionary.
        
        Raises:
            TokenExpiredException: If the token has expired.
            TokenInvalidException: If the token is malformed, signature is invalid, 
                                   or the token type does not match expected_type.
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        # Validate token type to prevent substitution attacks
        if payload.get("type") != expected_type:
            raise TokenInvalidException(
                f"Invalid token type. Expected {expected_type}, got {payload.get('type')}"
            )
            
        return payload
    except jwt.ExpiredSignatureError as e:
        raise TokenExpiredException("The token has expired.") from e
    except JWTError as e:
        raise TokenInvalidException(f"Invalid token: {str(e)}") from e
