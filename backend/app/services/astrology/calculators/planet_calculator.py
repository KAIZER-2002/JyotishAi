from typing import Tuple, List
from datetime import datetime
from app.domain.planet import Planet
from app.domain.planet_type import PlanetType
from app.domain.zodiac import ZodiacSign
from app.domain.nakshatra import Nakshatra
from app.domain.ayanamsa import Ayanamsa
from app.infrastructure.ephemeris.service import SwissEphemerisService


# Astrological Constants
SIGN_SIZE = 30.0
NAKSHATRA_SIZE = 360.0 / 27.0
PADA_SIZE = NAKSHATRA_SIZE / 4.0


class PlanetCalculator:
    """
    Calculator for transforming raw astronomical coordinates into 
    Vedic Astrology Planet domain objects.
    
    This class handles the mathematical conversion of longitudes 
    into signs, nakshatras, and padas.
    """

    def __init__(self, ephemeris_service: SwissEphemerisService) -> None:
        """
        Initializes the PlanetCalculator.
        
        Args:
            ephemeris_service: The infrastructure service used to fetch raw coordinates.
        """
        self._ephemeris = ephemeris_service

    def _normalize_longitude(self, longitude: float) -> float:
        """Ensures longitude is always within the [0, 360) range."""
        return longitude % 360.0

    def _longitude_to_sign(self, longitude: float) -> ZodiacSign:
        """Converts a normalized longitude to a ZodiacSign."""
        signs = list(ZodiacSign)
        index = int(longitude // SIGN_SIZE)
        return signs[index]

    def _longitude_to_degree(self, longitude: float) -> float:
        """Calculates the degree of a planet within its current zodiac sign."""
        return longitude % SIGN_SIZE

    def _longitude_to_nakshatra(self, longitude: float) -> Nakshatra:
        """Converts a normalized longitude to a Nakshatra."""
        nakshatras = list(Nakshatra)
        index = int(longitude // NAKSHATRA_SIZE)
        return nakshatras[index]

    def _longitude_to_pada(self, longitude: float) -> int:
        """Calculates the pada (quarter) of a nakshatra (1-4)."""
        pos_in_nakshatra = longitude % NAKSHATRA_SIZE
        pada = int(pos_in_nakshatra // PADA_SIZE) + 1
        return min(pada, 4)

    async def calculate_planets(
        self, 
        birth_datetime: datetime, 
        latitude: float, 
        longitude: float, 
        ayanamsa: Ayanamsa
    ) -> Tuple[Planet, ...]:
        """
        Calculates the precise astrological state of all planets for a given birth moment.
        
        Args:
            birth_datetime: The birth timestamp in UTC.
            latitude: Birth latitude.
            longitude: Birth longitude.
            ayanamsa: The Ayanamsa to apply for sidereal calculation.
            
        Returns:
            A tuple of immutable Planet domain objects.
        """
        # 1. Setup Ephemeris
        self._ephemeris.set_ayanamsa(ayanamsa)
        
        # 2. Accurate Julian Day conversion (including microseconds)
        # Julian Day = Days since Jan 1, 4713 BC. 
        # Decimal hours = hour + min/60 + sec/3600 + microsec/3.6e9
        decimal_hour = (
            birth_datetime.hour + 
            birth_datetime.minute / 60.0 + 
            birth_datetime.second / 3600.0 + 
            birth_datetime.microsecond / 3600000000.0
        )
        julian_day = self._ephemeris.calculate_julian_day(
            birth_datetime.year,
            birth_datetime.month,
            birth_datetime.day,
            decimal_hour
        )
        
        planets_list: List[Planet] = []
        
        # 3. Process primary planets
        # We iterate over PlanetType directly; the infrastructure handles the Swiss mapping
        for p_type in PlanetType:
            if p_type == PlanetType.KETU:
                continue
                
            raw_long, raw_lat, speed_long = self._ephemeris.calculate_planet_positions(
                julian_day, p_type
            )
            
            norm_long = self._normalize_longitude(raw_long)
            
            planet = Planet(
                planet=p_type,
                longitude=norm_long,
                latitude=raw_lat,
                zodiac_sign=self._longitude_to_sign(norm_long),
                house_number=None, # Assigned by HouseCalculator
                retrograde=speed_long < 0,
                nakshatra=self._longitude_to_nakshatra(norm_long),
                pada=self._longitude_to_pada(norm_long),
                degree_within_sign=self._longitude_to_degree(norm_long)
            )
            planets_list.append(planet)
            
        # 4. Derive Ketu from Rahu
        rahu_planet = next(p for p in planets_list if p.planet == PlanetType.RAHU)
        ketu_long = self._normalize_longitude(rahu_planet.longitude + 180.0)
        
        ketu = Planet(
            planet=PlanetType.KETU,
            longitude=ketu_long,
            latitude=-rahu_planet.latitude,
            zodiac_sign=self._longitude_to_sign(ketu_long),
            house_number=None,
            retrograde=rahu_planet.retrograde, # Ketu always moves opposite to Rahu
            nakshatra=self._longitude_to_nakshatra(ketu_long),
            pada=self._longitude_to_pada(ketu_long),
            degree_within_sign=self._longitude_to_degree(ketu_long)
        )
        planets_list.append(ketu)
        
        return tuple(planets_list)
