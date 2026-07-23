from dataclasses import dataclass
from typing import Optional
from app.domain.zodiac import ZodiacSign
from app.domain.nakshatra import Nakshatra
from app.domain.planet_type import PlanetType
from app.domain.house_number import HouseNumber


@dataclass(frozen=True)
class Planet:
    """
    Represents the precise position and astrological state of a planet.
    """
    planet: PlanetType
    longitude: float
    latitude: float
    zodiac_sign: ZodiacSign
    house_number: Optional[HouseNumber]
    retrograde: bool
    nakshatra: Nakshatra
    pada: int
    degree_within_sign: float
