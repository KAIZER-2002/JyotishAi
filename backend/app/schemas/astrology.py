from pydantic import BaseModel, Field, field_validator
from typing import List
from datetime import datetime
from app.domain.ayanamsa import Ayanamsa
from app.domain.dasha import DashaLevel, DashaLord
from app.domain.zodiac import ZodiacSign
from app.domain.nakshatra import Nakshatra
from app.domain.planet_type import PlanetType
from app.domain.house_number import HouseNumber


class BirthData(BaseModel):
    """Request schema for calculating a birth chart."""
    date: datetime = Field(..., description="Birth date and time in UTC")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Birth latitude")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Birth longitude")
    timezone: str = Field(..., description="IANA timezone identifier (e.g., 'Asia/Kolkata')")

    @field_validator("date")
    @classmethod
    def validate_timezone_aware_datetime(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Birth date and time must include timezone information.")
        return value


class BirthChartRequest(BirthData):
    """Request schema for generating a birth chart."""
    ayanamsa: Ayanamsa = Field(..., description="Ayanamsa to use for sidereal calculation")
    house_system: int = Field(..., ge=1, description="House system identifier")


class PlanetPosition(BaseModel):
    """API response schema for a single planet's position."""
    planet: PlanetType
    longitude: float
    zodiac_sign: ZodiacSign
    house_number: HouseNumber
    retrograde: bool
    nakshatra: Nakshatra
    pada: int
    degree_within_sign: float


class HousePosition(BaseModel):
    """API response schema for a house's position."""
    house_number: HouseNumber
    start_longitude: float
    end_longitude: float


class AscendantPosition(BaseModel):
    """API response schema for the Ascendant."""
    zodiac_sign: ZodiacSign
    longitude: float
    nakshatra: Nakshatra
    pada: int
    degree_within_sign: float


class BirthChartResponse(BaseModel):
    """Complete API response for a birth chart."""
    ascendant: AscendantPosition
    planets: List[PlanetPosition]
    houses: List[HousePosition]


class NavamsaChartResponse(BirthChartResponse):
    """Complete API response for a Navamsa chart."""
    pass


class DasamsaChartResponse(BirthChartResponse):
    """Complete API response for a Dasamsa chart."""
    pass


class ShastiamsaChartResponse(BirthChartResponse):
    """Complete API response for a Shastiamsa chart."""
    pass


class PratyantarDashaResponse(BaseModel):
    """API response schema for a Pratyantar Dasha period."""
    lord: DashaLord
    start_datetime: datetime
    end_datetime: datetime
    duration_days: float
    level: DashaLevel


class AntardashaResponse(BaseModel):
    """API response schema for an Antardasha period."""
    lord: DashaLord
    start_datetime: datetime
    end_datetime: datetime
    duration_days: float
    level: DashaLevel
    pratyantars: List[PratyantarDashaResponse]


class MahadashaResponse(BaseModel):
    """API response schema for a Mahadasha period."""
    lord: DashaLord
    start_datetime: datetime
    end_datetime: datetime
    duration_days: float
    level: DashaLevel
    antardashas: List[AntardashaResponse]


class VimshottariDashaResponse(BaseModel):
    """Complete API response for a Vimshottari Dasha timeline."""
    mahadashas: List[MahadashaResponse]
