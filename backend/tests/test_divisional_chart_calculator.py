import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.domain.ascendant import Ascendant
from app.domain.chart import Chart
from app.domain.house import House
from app.domain.house_number import HouseNumber
from app.domain.planet import Planet
from app.domain.planet_type import PlanetType
from app.services.astrology.calculators.divisional_chart_calculator import (
    DivisionalChartCalculator,
)
from app.services.astrology.utils import (
    longitude_to_degree,
    longitude_to_nakshatra,
    longitude_to_pada,
    longitude_to_sign,
)


class IdentityDivisionalChartCalculator(DivisionalChartCalculator):
    def _calculate_divisional_longitude(self, longitude: float) -> float:
        return longitude


def build_ascendant(longitude: float) -> Ascendant:
    return Ascendant(
        zodiac_sign=longitude_to_sign(longitude),
        longitude=longitude,
        nakshatra=longitude_to_nakshatra(longitude),
        pada=longitude_to_pada(longitude),
        degree_within_sign=longitude_to_degree(longitude),
    )


def build_planet(longitude: float) -> Planet:
    return Planet(
        planet=PlanetType.SUN,
        longitude=longitude,
        latitude=0.0,
        zodiac_sign=longitude_to_sign(longitude),
        house_number=None,
        retrograde=False,
        nakshatra=longitude_to_nakshatra(longitude),
        pada=longitude_to_pada(longitude),
        degree_within_sign=longitude_to_degree(longitude),
    )


def test_divisional_base_builds_chart_from_transformed_longitudes() -> None:
    calculator = IdentityDivisionalChartCalculator()
    chart = Chart(
        ascendant=build_ascendant(30.0),
        planets=(build_planet(90.0),),
        houses=(
            House(
                house_number=HouseNumber.FIRST,
                start_longitude=30.0,
                end_longitude=60.0,
            ),
        ),
    )

    divisional_chart = asyncio.run(calculator.calculate_divisional_chart(chart))

    assert divisional_chart.ascendant.zodiac_sign.value == "Taurus"
    assert divisional_chart.planets[0].zodiac_sign.value == "Cancer"
    assert divisional_chart.planets[0].house_number == HouseNumber.THIRD
    assert divisional_chart.houses[0].start_longitude == 30.0
    assert divisional_chart.houses[-1].end_longitude == 30.0
