class EphemerisException(Exception):
    """Base exception for all Swiss Ephemeris infrastructure errors."""
    pass


class CalculationException(EphemerisException):
    """Raised when an astronomical calculation fails to converge or returns an error."""
    pass


class InvalidBirthDataException(EphemerisException):
    """Raised when the provided birth data (date, time, coords) is invalid or out of range."""
    pass
