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
from app.services.astrology.calculators.navamsa_calculator import NavamsaCalculator
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


def test_navamsa_uses_standard_movable_fixed_dual_sign_rules() -> None:
    calculator = NavamsaCalculator()
    chart = build_birth_chart(
        0.0,
        (
            build_planet(PlanetType.SUN, 0.0),
            build_planet(PlanetType.MOON, 30.0),
            build_planet(PlanetType.MARS, 60.0),
        ),
    )

    navamsa = asyncio.run(calculator.calculate_navamsa(chart))

    assert navamsa.planets[0].zodiac_sign.value == "Aries"
    assert navamsa.planets[1].zodiac_sign.value == "Capricorn"
    assert navamsa.planets[2].zodiac_sign.value == "Libra"


def test_navamsa_scales_degree_within_division() -> None:
    calculator = NavamsaCalculator()
    chart = build_birth_chart(
        0.0,
        (
            build_planet(PlanetType.SUN, 1.0),
            build_planet(PlanetType.MOON, 3.3333333333333335),
        ),
    )

    navamsa = asyncio.run(calculator.calculate_navamsa(chart))

    assert navamsa.planets[0].zodiac_sign.value == "Aries"
    assert navamsa.planets[0].degree_within_sign == 9.0
    assert navamsa.planets[1].zodiac_sign.value == "Taurus"
    assert navamsa.planets[1].degree_within_sign == 0.0


def test_navamsa_builds_whole_sign_houses_from_navamsa_ascendant() -> None:
    calculator = NavamsaCalculator()
    chart = build_birth_chart(60.0, (build_planet(PlanetType.SUN, 0.0),))

    navamsa = asyncio.run(calculator.calculate_navamsa(chart))

    assert navamsa.ascendant.zodiac_sign.value == "Libra"
    assert navamsa.houses[0].house_number == HouseNumber.FIRST
    assert navamsa.houses[0].start_longitude == 180.0
    assert navamsa.houses[0].end_longitude == 210.0
    assert navamsa.houses[-1].house_number == HouseNumber.TWELFTH
    assert navamsa.houses[-1].start_longitude == 150.0
    assert navamsa.houses[-1].end_longitude == 180.0


def test_navamsa_assigns_planets_to_houses_from_navamsa_ascendant() -> None:
    calculator = NavamsaCalculator()
    chart = build_birth_chart(
        0.0,
        (
            build_planet(PlanetType.SUN, 0.0),
            build_planet(PlanetType.MOON, 30.0),
        ),
    )

    navamsa = asyncio.run(calculator.calculate_navamsa(chart))

    assert navamsa.planets[0].house_number == HouseNumber.FIRST
    assert navamsa.planets[1].house_number == HouseNumber.TENTH


def test_navamsa_returns_immutable_chart_collections() -> None:
    calculator = NavamsaCalculator()
    chart = build_birth_chart(0.0, (build_planet(PlanetType.SUN, 0.0),))

    navamsa = asyncio.run(calculator.calculate_navamsa(chart))

    assert isinstance(navamsa.planets, tuple)
    assert isinstance(navamsa.houses, tuple)
