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
from app.services.astrology.calculators.shastiamsa_calculator import (
    ShastiamsaCalculator,
)
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


def test_shastiamsa_uses_half_degree_divisions_from_aries() -> None:
    calculator = ShastiamsaCalculator()
    chart = build_birth_chart(
        0.0,
        (
            build_planet(PlanetType.SUN, 0.0),
            build_planet(PlanetType.MOON, 0.5),
            build_planet(PlanetType.MARS, 5.5),
            build_planet(PlanetType.MERCURY, 6.0),
        ),
    )

    shastiamsa = asyncio.run(calculator.calculate_shastiamsa(chart))

    assert shastiamsa.planets[0].zodiac_sign.value == "Aries"
    assert shastiamsa.planets[1].zodiac_sign.value == "Taurus"
    assert shastiamsa.planets[2].zodiac_sign.value == "Pisces"
    assert shastiamsa.planets[3].zodiac_sign.value == "Aries"


def test_shastiamsa_ignores_rasi_sign_for_divisional_sign() -> None:
    calculator = ShastiamsaCalculator()
    chart = build_birth_chart(
        30.0,
        (
            build_planet(PlanetType.SUN, 30.0),
            build_planet(PlanetType.MOON, 30.5),
        ),
    )

    shastiamsa = asyncio.run(calculator.calculate_shastiamsa(chart))

    assert shastiamsa.ascendant.zodiac_sign.value == "Aries"
    assert shastiamsa.planets[0].zodiac_sign.value == "Aries"
    assert shastiamsa.planets[1].zodiac_sign.value == "Taurus"


def test_shastiamsa_assigns_whole_sign_houses_from_shastiamsa_ascendant() -> None:
    calculator = ShastiamsaCalculator()
    chart = build_birth_chart(
        0.5,
        (
            build_planet(PlanetType.SUN, 0.5),
            build_planet(PlanetType.MOON, 1.5),
        ),
    )

    shastiamsa = asyncio.run(calculator.calculate_shastiamsa(chart))

    assert shastiamsa.ascendant.zodiac_sign.value == "Taurus"
    assert shastiamsa.planets[0].house_number == HouseNumber.FIRST
    assert shastiamsa.planets[1].house_number == HouseNumber.THIRD
    assert shastiamsa.houses[0].start_longitude == 30.0


def test_shastiamsa_returns_immutable_chart_collections() -> None:
    calculator = ShastiamsaCalculator()
    chart = build_birth_chart(0.0, (build_planet(PlanetType.SUN, 0.0),))

    shastiamsa = asyncio.run(calculator.calculate_shastiamsa(chart))

    assert isinstance(shastiamsa.planets, tuple)
    assert isinstance(shastiamsa.houses, tuple)
