from datetime import datetime
from app.domain.zodiac import ZodiacSign
from app.domain.nakshatra import Nakshatra


# Astrological Constants
SIGN_SIZE = 30.0
NAKSHATRA_SIZE = 360.0 / 27.0
PADA_SIZE = NAKSHATRA_SIZE / 4.0


def calculate_decimal_hour(dt: datetime) -> float:
    """
    Converts a datetime object to decimal hours of the day.
    """
    return (
        dt.hour + 
        dt.minute / 60.0 + 
        dt.second / 3600.0 + 
        dt.microsecond / 3600000000.0
    )


def normalize_longitude(longitude: float) -> float:
    """Ensures longitude is always within the [0, 360) range."""
    return longitude % 360.0


def longitude_to_sign(longitude: float) -> ZodiacSign:
    """Converts a normalized longitude to a ZodiacSign."""
    signs = list(ZodiacSign)
    index = int((longitude % 360.0) // SIGN_SIZE)
    return signs[index]


def longitude_to_degree(longitude: float) -> float:
    """Calculates the degree of a planet within its current zodiac sign."""
    return longitude % SIGN_SIZE


def longitude_to_nakshatra(longitude: float) -> Nakshatra:
    """Converts a normalized longitude to a Nakshatra."""
    nakshatras = list(Nakshatra)
    index = int((longitude % 360.0) // NAKSHATRA_SIZE)
    return nakshatras[index]


def longitude_to_pada(longitude: float) -> int:
    """Calculates the pada (quarter) of a nakshatra (1-4)."""
    pos_in_nakshatra = (longitude % 360.0) % NAKSHATRA_SIZE
    pada = int(pos_in_nakshatra // PADA_SIZE) + 1
    return min(pada, 4)
