from datetime import datetime
from app.domain.chart import Chart
from app.domain.ascendant import Ascendant
from app.domain.ayanamsa import Ayanamsa
from app.infrastructure.ephemeris.service import SwissEphemerisService
from app.services.astrology.calculators.planet_calculator import PlanetCalculator
from app.services.astrology.calculators.house_calculator import HouseCalculator
from app.services.astrology.utils import (
    longitude_to_degree,
    longitude_to_nakshatra,
    longitude_to_pada,
    longitude_to_sign,
)


class BirthChartCalculator:
    """
    Orchestration layer for generating a complete Vedic Birth Chart.
    
    This calculator coordinates the PlanetCalculator and HouseCalculator
    to produce a single, immutable Chart domain object.
    """

    def __init__(
        self, 
        ephemeris_service: SwissEphemerisService,
        planet_calculator: PlanetCalculator,
        house_calculator: HouseCalculator
    ) -> None:
        """
        Initializes the BirthChartCalculator.
        
        Args:
            ephemeris_service: The raw astronomy service.
            planet_calculator: The calculator for planetary positions.
            house_calculator: The calculator for house boundaries.
        """
        self._ephemeris = ephemeris_service
        self._planet_calc = planet_calculator
        self._house_calc = house_calculator

    async def calculate_chart(
        self, 
        birth_datetime: datetime, 
        latitude: float, 
        longitude: float, 
        ayanamsa: Ayanamsa,
        house_system: int # Future: Replace with HouseSystem Enum
    ) -> Chart:
        """
        Orchestrates the full calculation of a birth chart.
        
        Args:
            birth_datetime: Birth timestamp in UTC.
            latitude: Birth latitude.
            longitude: Birth longitude.
            ayanamsa: Sidereal offset.
            house_system: The house system identifier (e.g., P_PLACIDUS).
            
        Returns:
            A complete, immutable Chart domain object.
        """
        planets = await self._planet_calc.calculate_planets(
            birth_datetime, latitude, longitude, ayanamsa
        )
        
        asc_long, houses = await self._house_calc.calculate_houses(
            birth_datetime, latitude, longitude, ayanamsa, house_system
        )
        
        planets_with_houses = await self._house_calc.assign_planets_to_houses(
            planets, houses
        )
        
        ascendant = Ascendant(
            zodiac_sign=longitude_to_sign(asc_long),
            longitude=asc_long,
            nakshatra=longitude_to_nakshatra(asc_long),
            pada=longitude_to_pada(asc_long),
            degree_within_sign=longitude_to_degree(asc_long)
        )
        
        return Chart(
            ascendant=ascendant,
            planets=planets_with_houses,
            houses=houses
        )
