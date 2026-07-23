from typing import List, Tuple, Optional
import swisseph as swe
from app.core.config import settings
from app.domain.ayanamsa import Ayanamsa
from app.domain.planet_type import PlanetType
from app.infrastructure.ephemeris.exceptions import (
    EphemerisException, 
    CalculationException, 
    InvalidBirthDataException
)


class SwissEphemerisService:
    """
    Adapter for the Swiss Ephemeris (pyswisseph) library.
    
    This service handles all direct interactions with the underlying C-library,
    providing a clean, Pythonic interface for raw astronomical calculations.
    It is strictly stateless and returns raw primitive values.
    """

    def __init__(self, ephemeris_path: Optional[str] = None) -> None:
        """
        Initializes the Swiss Ephemeris environment.
        
        Args:
            ephemeris_path: Path to the directory containing .se1 files. 
                           If None, it attempts to use a default path from settings.
        """
        # Use provided path, or fallback to a config value, or use default
        self._path = ephemeris_path or getattr(settings, "EPHEMERIS_PATH", "/usr/local/share/ephe")
        self._set_ephe_path()

    def _set_ephe_path(self) -> None:
        """Configures the library to use the specified ephemeris data directory."""
        try:
            swe.set_ephe_path(self._path)
        except Exception as e:
            # We don't raise here as some environments might have paths set internally,
            # but we log it or handle it during the first calculation.
            pass

    def set_ayanamsa(self, ayanamsa: Ayanamsa) -> None:
        """
        Sets the sidereal mode (Ayanamsa) for subsequent calculations.
        
        Args:
            ayanamsa: The Ayanamsa enum value to apply.
        """
        mapping = {
            Ayanamsa.LAHIRI: swe.SIDM_LAHIRI,
            Ayanamsa.RAMAN: swe.SIDM_RAMAN,
            Ayanamsa.KRISHNAMURTI: swe.SIDM_KRISHNAMURTI,
            Ayanamsa.TRUE_CHITRA: swe.SIDM_TRUE_CHITRA,
        }
        
        mode = mapping.get(ayanamsa)
        if mode is None:
            raise EphemerisException(f"Unsupported ayanamsa: {ayanamsa}")
            
        swe.set_sid_mode(mode)

    def calculate_julian_day(self, year: int, month: int, day: int, hour_utc: float) -> float:
        """
        Converts a Gregorian date and time to a Julian Day.
        
        Args:
            year: Year (e.g., 1990)
            month: Month (1-12)
            day: Day of the month
            hour_utc: Decimal hour in UTC (e.g., 14.5 for 14:30)
            
        Returns:
            The Julian Day as a float.
        """
        try:
            return swe.julday(year, month, day, hour_utc)
        except Exception as e:
            raise InvalidBirthDataException(f"Failed to calculate Julian Day: {str(e)}")

    def calculate_sidereal_time(self, julian_day: float) -> float:
        """
        Calculates the Greenwich sidereal time for a given Julian Day.
        
        Args:
            julian_day: The Julian Day.
            
        Returns:
            Sidereal time in degrees.
        """
        try:
            # returns (sidereal_time, _)
            return swe.sidereal_time(julian_day)[0]
        except Exception as e:
            raise CalculationException(f"Failed to calculate sidereal time: {str(e)}")

    def calculate_planet_positions(
        self, 
        julian_day: float, 
        planet_type: PlanetType, 
        flag: int = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    ) -> Tuple[float, float, float]:
        """
        Calculates the precise position and speed of a planet.
        
        Args:
            julian_day: The Julian Day of the moment.
            planet_type: The domain PlanetType.
            flag: Calculation flags.
            
        Returns:
            A tuple containing (longitude, latitude, speed_longitude) in degrees.
            
        Raises:
            CalculationException: If the planetary position cannot be computed.
        """
        # Map domain PlanetType to Swiss Ephemeris ID
        planet_mapping = {
            PlanetType.SUN: swe.SUN,
            PlanetType.MOON: swe.MOON,
            PlanetType.MARS: swe.MARS,
            PlanetType.MERCURY: swe.MERCURY,
            PlanetType.JUPITER: swe.JUPITER,
            PlanetType.VENUS: swe.VENUS,
            PlanetType.SATURN: swe.SATURN,
            PlanetType.RAHU: swe.TRUE_NODE,
        }
        
        planet_id = planet_mapping.get(planet_type)
        if planet_id is None:
            raise EphemerisException(f"No mapping found for planet type: {planet_type}")

        try:
            # returns (res, return_flag)
            # res is (longitude, latitude, distance, speed_long, speed_lat, ...)
            res = swe.calc_ut(julian_day, planet_id, flag)
            return res[0][0], res[0][1], res[0][3]
        except Exception as e:
            raise CalculationException(f"Failed to calculate position for {planet_type.value}: {str(e)}")

    def calculate_house_cusps(
        self, 
        julian_day: float, 
        latitude: float, 
        longitude: float, 
        house_system: int = swe.houses.P_PLACIDUS
    ) -> Tuple[float, List[float]]:
        """
        Calculates the house cusps and the Ascendant.
        
        Args:
            julian_day: The Julian Day.
            latitude: Geographical latitude in degrees.
            longitude: Geographical longitude in degrees.
            house_system: The house system identifier (e.g., P_PLACIDUS).
            
        Returns:
            A tuple containing (ascendant_longitude, list_of_12_cusps).
        """
        try:
            # returns (cusps, ascmc)
            # ascmc is (ascendant, midheaven, ...)
            cusps, ascmc = swe.houses(house_system, julian_day, latitude, longitude)
            return ascmc[0], cusps
        except Exception as e:
            raise CalculationException(f"Failed to calculate house cusps: {str(e)}")

    def calculate_ascendant(self, julian_day: float, latitude: float, longitude: float) -> float:
        """
        Calculates only the Ascendant (Lagna) longitude.
        
        Args:
            julian_day: The Julian Day.
            latitude: Geographical latitude.
            longitude: Geographical longitude.
            
        Returns:
            The Ascendant longitude in degrees.
        """
        # The ascendant is the first cusp of the house system
        asc, _ = self.calculate_house_cusps(julian_day, latitude, longitude)
        return asc
