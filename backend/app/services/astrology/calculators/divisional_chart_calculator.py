from abc import ABC, abstractmethod
from typing import Tuple

from app.domain.ascendant import Ascendant
from app.domain.chart import Chart
from app.domain.house import House
from app.domain.house_number import HouseNumber
from app.domain.planet import Planet
from app.domain.zodiac import ZodiacSign
from app.services.astrology.utils import (
    longitude_to_degree,
    longitude_to_nakshatra,
    longitude_to_pada,
    longitude_to_sign,
    normalize_longitude,
)


SIGN_SIZE = 30.0


class DivisionalChartCalculator(ABC):
    """
    Base calculator for divisional charts derived from an existing Rasi chart.
    """

    async def calculate_divisional_chart(self, birth_chart: Chart) -> Chart:
        ascendant = self._calculate_ascendant(birth_chart.ascendant)
        houses = self._build_houses(ascendant.zodiac_sign)
        planets = tuple(
            self._calculate_planet(planet, ascendant.zodiac_sign)
            for planet in birth_chart.planets
        )

        return Chart(
            ascendant=ascendant,
            planets=planets,
            houses=houses,
        )

    @abstractmethod
    def _calculate_divisional_longitude(self, longitude: float) -> float:
        """
        Converts a Rasi longitude into this divisional chart's longitude.
        """

    def _calculate_ascendant(self, ascendant: Ascendant) -> Ascendant:
        divisional_longitude = self._calculate_divisional_longitude(
            ascendant.longitude
        )

        return Ascendant(
            zodiac_sign=longitude_to_sign(divisional_longitude),
            longitude=divisional_longitude,
            nakshatra=longitude_to_nakshatra(divisional_longitude),
            pada=longitude_to_pada(divisional_longitude),
            degree_within_sign=longitude_to_degree(divisional_longitude),
        )

    def _calculate_planet(
        self,
        planet: Planet,
        ascendant_sign: ZodiacSign,
    ) -> Planet:
        divisional_longitude = self._calculate_divisional_longitude(
            planet.longitude
        )
        divisional_sign = longitude_to_sign(divisional_longitude)

        return Planet(
            planet=planet.planet,
            longitude=divisional_longitude,
            latitude=planet.latitude,
            zodiac_sign=divisional_sign,
            house_number=self._calculate_house_number(
                divisional_sign,
                ascendant_sign,
            ),
            retrograde=planet.retrograde,
            nakshatra=longitude_to_nakshatra(divisional_longitude),
            pada=longitude_to_pada(divisional_longitude),
            degree_within_sign=longitude_to_degree(divisional_longitude),
        )

    def _build_houses(self, ascendant_sign: ZodiacSign) -> Tuple[House, ...]:
        signs = list(ZodiacSign)
        ascendant_index = signs.index(ascendant_sign)
        houses: list[House] = []

        for index, house_number in enumerate(HouseNumber):
            sign_index = (ascendant_index + index) % len(signs)
            next_sign_index = (sign_index + 1) % len(signs)
            houses.append(
                House(
                    house_number=house_number,
                    start_longitude=sign_index * SIGN_SIZE,
                    end_longitude=next_sign_index * SIGN_SIZE,
                )
            )

        return tuple(houses)

    def _calculate_house_number(
        self,
        planet_sign: ZodiacSign,
        ascendant_sign: ZodiacSign,
    ) -> HouseNumber:
        signs = list(ZodiacSign)
        offset = (signs.index(planet_sign) - signs.index(ascendant_sign)) % len(signs)
        return list(HouseNumber)[offset]

    def _calculate_cyclic_divisional_longitude(
        self,
        longitude: float,
        divisions: int,
        start_sign_index: int,
    ) -> float:
        normalized_longitude = normalize_longitude(longitude)
        signs = list(ZodiacSign)
        division_size = SIGN_SIZE / divisions
        degree_in_sign = normalized_longitude % SIGN_SIZE
        division_index = int(degree_in_sign // division_size)
        degree_in_division = degree_in_sign % division_size

        divisional_sign_index = (start_sign_index + division_index) % len(signs)
        divisional_degree = degree_in_division * (SIGN_SIZE / division_size)

        return normalize_longitude(
            divisional_sign_index * SIGN_SIZE + divisional_degree
        )
