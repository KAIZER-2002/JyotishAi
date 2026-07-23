from typing import Tuple, List, Optional, Any, Sequence
from datetime import datetime
from dataclasses import replace
from app.domain.house import House
from app.domain.house_number import HouseNumber
from app.domain.planet import Planet
from app.infrastructure.ephemeris.service import SwissEphemerisService
from app.services.astrology.utils import (
    calculate_decimal_hour,
    normalize_longitude
)


class HouseCalculator:
    """
    Calculator for determining house boundaries and planetary house assignments.
    
    This class transforms raw astronomical house cusps into domain-specific 
    House objects and assigns planets to houses based on their longitudes.
    """

    def __init__(self, ephemeris_service: SwissEphemerisService) -> None:
        """
        Initializes the HouseCalculator.
        
        Args:
            ephemeris_service: The infrastructure service used for astronomical data.
        """
        self._ephemeris = ephemeris_service

    def _determine_house(self, planet_longitude: float, houses: Sequence[House]) -> HouseNumber:
        """
        Determines which house a planet belongs to based on its longitude.
        
        Handles the 'wrap-around' case where a house spans across the 360/0 boundary 
        (usually the 12th or 1st house depending on the system).
        """
        planet_long = normalize_longitude(planet_longitude)
        
        for house in houses:
            start = house.start_longitude
            end = house.end_longitude
            
            if start < end:
                # Standard case: House is contained within one circle rotation
                if start <= planet_long < end:
                    return house.house_number
            else:
                # Wrap-around case: House crosses 0 degrees (e.g., 350 to 10)
                if planet_long >= start or planet_long < end:
                    return house.house_number
                    
        # Fallback to the last house in the list if precision issues occur
        return houses[-1].house_number

    def _build_house_objects(self, cusps: Sequence[float]) -> Tuple[House, ...]:
        """
        Constructs a list of 12 House domain objects from raw cusps.
        """
        houses: List[House] = []
        
        # Cusp 1 is the Ascendant. The 1st house goes from Cusp 1 to Cusp 2.
        for i in range(12):
            start = normalize_longitude(cusps[i])
            # The end of house i is the start of house i+1. 
            # For the 12th house, the end is the start of the 1st house (index 0).
            end = normalize_longitude(cusps[(i + 1) % 12])
            
            # Get the correct HouseNumber enum based on the index (0 -> FIRST, 1 -> SECOND...)
            # HouseNumber values are 1-12, so we use list(HouseNumber)[i]
            house_num = list(HouseNumber)[i]
            
            houses.append(House(
                house_number=house_num,
                start_longitude=start,
                end_longitude=end
            ))
            
        return tuple(houses)

    async def calculate_houses(
        self, 
        birth_datetime: datetime, 
        latitude: float, 
        longitude: float, 
        ayanamsa: Any,
        house_system: Optional[int] = None,
    ) -> Tuple[float, Tuple[House, ...]]:
        """
        Calculates house cusps and the Ascendant longitude.
        
        Args:
            birth_datetime: The birth timestamp.
            latitude: Birth latitude.
            longitude: Birth longitude.
            ayanamsa: The Ayanamsa for sidereal calculation.
            house_system: Optional house system identifier.
            
        Returns:
            A tuple of (ascendant_longitude, List of House objects).
        """
        # 1. Setup Ephemeris
        self._ephemeris.set_ayanamsa(ayanamsa)
        
        # 2. Calculate Julian Day
        julian_day = self._ephemeris.calculate_julian_day(
            birth_datetime.year,
            birth_datetime.month,
            birth_datetime.day,
            calculate_decimal_hour(birth_datetime)
        )
        
        # 3. Calculate raw cusps and ascendant from infrastructure
        if house_system is None:
            ascendant, cusps = self._ephemeris.calculate_house_cusps(
                julian_day, latitude, longitude
            )
        else:
            ascendant, cusps = self._ephemeris.calculate_house_cusps(
                julian_day, latitude, longitude, house_system
            )
        
        # 4. Transform raw data into domain objects
        house_objects = self._build_house_objects(cusps)
        
        return ascendant, house_objects

    async def assign_planets_to_houses(
        self, 
        planets: Tuple[Planet, ...], 
        houses: Sequence[House]
    ) -> Tuple[Planet, ...]:
        """
        Assigns each planet to its correct house based on its longitude.
        
        Args:
            planets: Tuple of Planet objects (with house_number=None).
            houses: List of calculated House objects.
            
        Returns:
            A new tuple of Planet objects with populated house_number.
        """
        updated_planets: List[Planet] = []
        
        for planet in planets:
            house_num = self._determine_house(planet.longitude, houses)
            
            # Since Planet is a frozen dataclass, we use replace() to create a new instance
            # This ensures immutability and prevents accidental side effects.
            updated_planet = replace(planet, house_number=house_num)
            updated_planets.append(updated_planet)
            
        return tuple(updated_planets)
