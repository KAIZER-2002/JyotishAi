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
from app.services.astrology.calculators.dasamsa_calculator import DasamsaCalculator
from app.services.astrology.utils import (
    longitude_to_degree,
    longitude_to_nakshatra,
    longitude_to_pada,
    longitude_to_sign,
)


def build_ascendant(longitude: float) -> Ascendant:
    return Ascendant(
        zodiac_sign=longitude_to_sign(longitude),
        longitude=longitude,
        nakshatra=longitude_to_nakshatra(longitude),
        pada=longitude_to_pada(longitude),
        degree_within_sign=longitude_to_degree(longitude),
    )


def build_planet(planet_type: PlanetType, longitude: float) -> Planet:
    return Planet(
        planet=planet_type,
        longitude=longitude,
        latitude=0.0,
        zodiac_sign=longitude_to_sign(longitude),
        house_number=None,
        retrograde=False,
        nakshatra=longitude_to_nakshatra(longitude),
        pada=longitude_to_pada(longitude),
        degree_within_sign=longitude_to_degree(longitude),
    )


def build_birth_chart(ascendant_longitude: float, planets: tuple[Planet, ...]) -> Chart:
    return Chart(
        ascendant=build_ascendant(ascendant_longitude),
        planets=planets,
        houses=(
            House(
                house_number=HouseNumber.FIRST,
                start_longitude=0.0,
                end_longitude=30.0,
            ),
        ),
    )


def test_dasamsa_uses_odd_even_sign_start_rules() -> None:
    calculator = DasamsaCalculator()
    chart = build_birth_chart(
        0.0,
        (
            build_planet(PlanetType.SUN, 0.0),
            build_planet(PlanetType.MOON, 30.0),
        ),
    )

    dasamsa = asyncio.run(calculator.calculate_dasamsa(chart))

    assert dasamsa.planets[0].zodiac_sign.value == "Aries"
    assert dasamsa.planets[1].zodiac_sign.value == "Capricorn"


def test_dasamsa_scales_degree_within_division() -> None:
    calculator = DasamsaCalculator()
    chart = build_birth_chart(
        0.0,
        (
            build_planet(PlanetType.SUN, 1.0),
            build_planet(PlanetType.MOON, 3.0),
        ),
    )

    dasamsa = asyncio.run(calculator.calculate_dasamsa(chart))

    assert dasamsa.planets[0].zodiac_sign.value == "Aries"
    assert dasamsa.planets[0].degree_within_sign == 10.0
    assert dasamsa.planets[1].zodiac_sign.value == "Taurus"
    assert dasamsa.planets[1].degree_within_sign == 0.0


def test_dasamsa_assigns_whole_sign_houses_from_dasamsa_ascendant() -> None:
    calculator = DasamsaCalculator()
    chart = build_birth_chart(
        30.0,
        (
            build_planet(PlanetType.SUN, 30.0),
            build_planet(PlanetType.MOON, 0.0),
        ),
    )

    dasamsa = asyncio.run(calculator.calculate_dasamsa(chart))

    assert dasamsa.ascendant.zodiac_sign.value == "Capricorn"
    assert dasamsa.houses[0].start_longitude == 270.0
    assert dasamsa.planets[0].house_number == HouseNumber.FIRST
    assert dasamsa.planets[1].house_number == HouseNumber.FOURTH


def test_dasamsa_returns_immutable_chart_collections() -> None:
    calculator = DasamsaCalculator()
    chart = build_birth_chart(0.0, (build_planet(PlanetType.SUN, 0.0),))

    dasamsa = asyncio.run(calculator.calculate_dasamsa(chart))

    assert isinstance(dasamsa.planets, tuple)
    assert isinstance(dasamsa.houses, tuple)
