from dataclasses import dataclass
from app.domain.zodiac import ZodiacSign
from app.domain.nakshatra import Nakshatra


@dataclass(frozen=True)
class Ascendant:
    """
    Represents the Lagna (Ascendant), the starting point of the birth chart.
    """
    zodiac_sign: ZodiacSign
    longitude: float
    nakshatra: Nakshatra
    pada: int
    degree_within_sign: float
