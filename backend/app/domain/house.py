from dataclasses import dataclass
from app.domain.house_number import HouseNumber


@dataclass(frozen=True)
class House:
    """
    Represents a single astrological house and its boundaries.
    """
    house_number: HouseNumber
    start_longitude: float
    end_longitude: float
