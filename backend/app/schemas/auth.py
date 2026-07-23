from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    """
    Schema for returning JWT tokens after successful authentication 
    or token refresh.
    """
    access_token: str = Field(..., description="Short-lived JWT access token")
    refresh_token: str = Field(..., description="Long-lived JWT refresh token")
    token_type: str = Field("bearer", description="The type of token issued")


class RefreshTokenRequest(BaseModel):
    """
    Schema for requesting a new access token using a refresh token.
    """
    refresh_token: str = Field(..., description="The refresh token used to obtain a new access token")


class MessageResponse(BaseModel):
    """
    Generic schema for returning a simple message response from the API.
    """
    message: str = Field(..., description="The notification or status message")
