from dataclasses import dataclass
from typing import Tuple
from app.domain.planet import Planet
from app.domain.house import House
from app.domain.ascendant import Ascendant


@dataclass(frozen=True)
class Chart:
    """
    The central domain object representing a complete birth chart.
    
    This object aggregates all astronomical calculations and serves as the 
    primary input for interpretation modules (Dasha, Yoga, etc.).
    """
    ascendant: Ascendant
    planets: Tuple[Planet, ...]
    houses: Tuple[House, ...]
