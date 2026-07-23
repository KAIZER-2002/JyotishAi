from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.domain.ayanamsa import Ayanamsa

class AstrologyAnalysisRequest(BaseModel):
    """Request schema for generating a complete astrology analysis."""
    date: datetime = Field(..., description="Birth date and time in UTC")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Birth latitude")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Birth longitude")
    timezone: str = Field(..., description="IANA timezone identifier (e.g., 'Asia/Kolkata')")
    ayanamsa: Ayanamsa = Field(..., description="Ayanamsa to use for sidereal calculation")
    house_system: int = Field(..., ge=1, description="House system identifier")