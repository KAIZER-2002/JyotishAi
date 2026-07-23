from dataclasses import dataclass


@dataclass(frozen=True)
class Coordinate:
    """
    Represents a geographical coordinate and timezone for birth location.
    """
    latitude: float
    longitude: float
    timezone: str
