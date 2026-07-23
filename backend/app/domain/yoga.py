from dataclasses import dataclass
from enum import Enum
from typing import Tuple

from app.domain.house_number import HouseNumber
from app.domain.planet_type import PlanetType


class YogaType(Enum):
    """
    Supported high-level Yoga categories.
    """
    RAJ_YOGA = "Raj Yoga"
    DHANA_YOGA = "Dhana Yoga"
    VIPAREETA_YOGA = "Vipareeta Yoga"
    NEECHA_BHANGA_RAJA_YOGA = "Neecha Bhanga Raja Yoga"
    PANCHA_MAHAPURUSHA_YOGA = "Pancha Mahapurusha Yoga"
    GAJA_KESARI_YOGA = "Gaja Kesari Yoga"
    BUDHADITYA_YOGA = "Budhaditya Yoga"
    CHANDRA_MANGALA_YOGA = "Chandra Mangala Yoga"
    OTHER = "Other"


class YogaStrength(Enum):
    """
    Qualitative strength of a detected Yoga.
    """
    WEAK = "Weak"
    MODERATE = "Moderate"
    STRONG = "Strong"
    EXCEPTIONAL = "Exceptional"


@dataclass(frozen=True)
class Yoga:
    """
    Immutable definition of an astrological Yoga.
    """
    key: str
    name: str
    yoga_type: YogaType
    description: str = ""


@dataclass(frozen=True)
class YogaResult:
    """
    Immutable result for a detected Yoga in a chart.
    """
    yoga: Yoga
    strength: YogaStrength
    involved_planets: Tuple[PlanetType, ...] = ()
    involved_houses: Tuple[HouseNumber, ...] = ()
    evidence: Tuple[str, ...] = ()
