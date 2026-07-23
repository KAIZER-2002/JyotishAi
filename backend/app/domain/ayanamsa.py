from enum import Enum


class Ayanamsa(Enum):
    """
    Supported ayanamsas for calculating the difference between 
    Tropical and Sidereal zodiacs.
    """
    LAHIRI = "Lahiri"
    RAMAN = "Raman"
    KRISHNAMURTI = "Krishnamurti"
    TRUE_CHITRA = "True Chitra"
