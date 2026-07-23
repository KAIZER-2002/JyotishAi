from typing import Optional
from uuid import UUID
from datetime import datetime, date
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    """Base user schema containing common fields."""
    email: EmailStr = Field(..., description="User's unique email address")
    username: str = Field(
        ...,
        min_length=3,
        max_length=30,
        description="Unique username (3-30 characters)"
    )
    full_name: Optional[str] = Field(None, description="User's full legal name")


class UserCreate(UserBase):
    """Schema for user registration."""
    password: str = Field(
        ...,
        min_length=8,
        description="User password (minimum 8 characters)"
    )


class UserUpdate(BaseModel):
    """Schema for updating user profile information."""
    full_name: Optional[str] = Field(None, description="Updated full name")
    password: Optional[str] = Field(
        None,
        min_length=8,
        description="Updated password (minimum 8 characters)"
    )


class UserProfileUpdate(BaseModel):
    """
    Schema for updating extended profile information via PATCH /users/me.
    Only fields provided in the request body will be updated (exclude_unset).
    """
    full_name: Optional[str] = Field(None, max_length=100, description="Full legal name")
    timezone: Optional[str] = Field(None, max_length=64, description="IANA timezone identifier")
    date_of_birth: Optional[date] = Field(None, description="Date of birth (YYYY-MM-DD)")
    time_of_birth: Optional[str] = Field(
        None,
        pattern=r"^\d{2}:\d{2}(:\d{2})?$",
        description="Time of birth in HH:MM or HH:MM:SS format"
    )
    birth_place: Optional[str] = Field(None, max_length=200, description="City / place of birth")
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Birth latitude")
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Birth longitude")
    ayanamsa: Optional[str] = Field(None, max_length=50, description="Preferred ayanamsa")
    avatar_url: Optional[str] = Field(None, max_length=2048, description="Base64 data URI or URL of the avatar image")
    gender: Optional[str] = Field(None, max_length=20, description="Gender")


class UserLogin(BaseModel):
    """Schema for user authentication."""
    email: EmailStr = Field(..., description="Registered email address")
    password: str = Field(..., description="User password")


class UserResponse(BaseModel):
    """Schema for returning user data in API responses."""
    id: UUID
    email: EmailStr
    username: str
    full_name: Optional[str]
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserProfileResponse(BaseModel):
    """
    Full profile response including both auth and birth/personal data.
    Returned by GET /users/me and PATCH /users/me.
    """
    id: UUID
    email: EmailStr
    username: str
    full_name: Optional[str]
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    # Profile fields
    timezone: Optional[str]
    date_of_birth: Optional[date]
    time_of_birth: Optional[str]
    birth_place: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    ayanamsa: Optional[str]
    avatar_url: Optional[str]
    gender: Optional[str]
    settings: Optional["UserSettingsSchema"] = None

    model_config = ConfigDict(from_attributes=True)


class GeneralSettings(BaseModel):
    theme: str = Field("dark", description="UI theme preference")
    language: str = Field("en", description="Preferred language")
    timezone: str = Field("Asia/Kolkata", description="Astrological/local timezone")
    date_format: str = Field("YYYY-MM-DD", description="Date formatting style")
    time_format: str = Field("HH:mm", description="Time formatting style")


class AISettings(BaseModel):
    default_ai_model: str = Field("gemini-2.5-flash", description="Preferred Gemini model")
    response_length: str = Field("medium", description="Length: short, medium, long")
    streaming_toggle: bool = Field(True, description="Enable streamed token generation")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Creativity temperature")


class AstrologySettings(BaseModel):
    default_ayanamsa: str = Field("Lahiri", description="Preferred Ayanamsa system")
    house_system: int = Field(1, description="Preferred house system index")
    preferred_chart_style: str = Field("North Indian", description="Style: North Indian, South Indian, East Indian")
    default_divisional_chart: str = Field("D1", description="Default divisional chart viewed")


class NotificationSettings(BaseModel):
    email_notifications: bool = Field(True, description="Enable email alerts")
    product_updates: bool = Field(True, description="Enable product update announcements")
    marketing_emails: bool = Field(False, description="Enable marketing notifications")


class UserSettingsSchema(BaseModel):
    general: GeneralSettings = Field(default_factory=GeneralSettings)
    ai: AISettings = Field(default_factory=AISettings)
    astrology: AstrologySettings = Field(default_factory=AstrologySettings)
    notifications: NotificationSettings = Field(default_factory=NotificationSettings)


class UserSettingsUpdate(BaseModel):
    general: Optional[GeneralSettings] = None
    ai: Optional[AISettings] = None
    astrology: Optional[AstrologySettings] = None
    notifications: Optional[NotificationSettings] = None

