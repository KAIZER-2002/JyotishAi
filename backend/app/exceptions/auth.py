class AuthException(Exception):
    """
    Base exception for all authentication and authorization related errors.
    
    All security-related exceptions in the system should inherit from this class.
    """
    pass


class AuthenticationException(AuthException):
    """
    Raised when the user's identity cannot be verified.
    
    Typically maps to HTTP 401 Unauthorized.
    """
    pass


class AuthorizationException(AuthException):
    """
    Raised when an authenticated user lacks the required permissions for a resource.
    
    Typically maps to HTTP 403 Forbidden.
    """
    pass


class InvalidCredentialsException(AuthenticationException):
    """Raised when the provided email or password is incorrect."""
    pass


class TokenExpiredException(AuthenticationException):
    """Raised when the JWT has passed its expiration date."""
    pass


class TokenInvalidException(AuthenticationException):
    """Raised when the JWT is malformed, has an invalid signature, or is otherwise invalid."""
    pass


class InvalidTokenTypeException(AuthenticationException):
    """Raised when the wrong token type is provided (e.g., using a refresh token for access)."""
    pass


class RefreshTokenException(AuthenticationException):
    """Raised when a refresh token is revoked, non-existent, or otherwise unusable."""
    pass
