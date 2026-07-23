from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.domain.ascendant import Ascendant
from app.domain.astrology_analysis import AstrologyAnalysis
from app.domain.chart import Chart
from app.domain.house import House
from app.domain.house_number import HouseNumber
from app.domain.nakshatra import Nakshatra
from app.domain.pancha_mahapurusha_yoga import PanchaMahapurushaYogaRule
from app.domain.planet import Planet
from app.domain.planet_type import PlanetType
from app.domain.yoga import YogaStrength, YogaType
from app.domain.yoga_detection import YogaContext, YogaDetectionEngine
from app.domain.zodiac import ZodiacSign


def planet(
    planet_type: PlanetType,
    sign: ZodiacSign,
    house_number: HouseNumber,
) -> Planet:
    return Planet(
        planet=planet_type,
        longitude=float(list(ZodiacSign).index(sign) * 30),
        latitude=0.0,
        zodiac_sign=sign,
        house_number=house_number,
        retrograde=False,
        nakshatra=Nakshatra.ASHWINI,
        pada=1,
        degree_within_sign=0.0,
    )


def chart(*planets: Planet) -> Chart:
    return Chart(
        ascendant=Ascendant(
            zodiac_sign=ZodiacSign.ARIES,
            longitude=0.0,
            nakshatra=Nakshatra.ASHWINI,
            pada=1,
            degree_within_sign=0.0,
        ),
        planets=planets,
        houses=tuple(
            House(
                house_number=house_number,
                start_longitude=float(index * 30),
                end_longitude=float((index + 1) * 30),
            )
            for index, house_number in enumerate(HouseNumber)
        ),
    )


def context_with(*planets: Planet) -> YogaContext:
    birth_chart = chart(*planets)
    return YogaContext(
        AstrologyAnalysis(
            birth_chart=birth_chart,
            navamsa_chart=chart(),
            dasamsa_chart=chart(),
            shastiamsa_chart=chart(),
            vimshottari_dashas=(),
        )
    )


@pytest.mark.parametrize(
    ("planet_type", "sign", "expected_key", "expected_name"),
    [
        (PlanetType.MARS, ZodiacSign.ARIES, "ruchaka", "Ruchaka Yoga"),
        (PlanetType.MERCURY, ZodiacSign.GEMINI, "bhadra", "Bhadra Yoga"),
        (PlanetType.JUPITER, ZodiacSign.SAGITTARIUS, "hamsa", "Hamsa Yoga"),
        (PlanetType.VENUS, ZodiacSign.TAURUS, "malavya", "Malavya Yoga"),
        (PlanetType.SATURN, ZodiacSign.CAPRICORN, "sasa", "Sasa Yoga"),
    ],
)
def test_pancha_mahapurusha_detects_each_own_sign_yoga(
    planet_type: PlanetType,
    sign: ZodiacSign,
    expected_key: str,
    expected_name: str,
) -> None:
    rule = PanchaMahapurushaYogaRule()

    results = rule.evaluate(
        context_with(planet(planet_type, sign, HouseNumber.FIRST))
    )

    assert len(results) == 1
    assert results[0].yoga.key == expected_key
    assert results[0].yoga.name == expected_name
    assert results[0].yoga.yoga_type is YogaType.PANCHA_MAHAPURUSHA_YOGA
    assert results[0].strength is YogaStrength.STRONG
    assert results[0].involved_planets == (planet_type,)
    assert results[0].involved_houses == (HouseNumber.FIRST,)


@pytest.mark.parametrize(
    ("planet_type", "exaltation_sign", "expected_key"),
    [
        (PlanetType.MARS, ZodiacSign.CAPRICORN, "ruchaka"),
        (PlanetType.MERCURY, ZodiacSign.VIRGO, "bhadra"),
        (PlanetType.JUPITER, ZodiacSign.CANCER, "hamsa"),
        (PlanetType.VENUS, ZodiacSign.PISCES, "malavya"),
        (PlanetType.SATURN, ZodiacSign.LIBRA, "sasa"),
    ],
)
def test_pancha_mahapurusha_detects_exaltation_with_exceptional_strength(
    planet_type: PlanetType,
    exaltation_sign: ZodiacSign,
    expected_key: str,
) -> None:
    rule = PanchaMahapurushaYogaRule()

    results = rule.evaluate(
        context_with(planet(planet_type, exaltation_sign, HouseNumber.TENTH))
    )

    assert len(results) == 1
    assert results[0].yoga.key == expected_key
    assert results[0].strength is YogaStrength.EXCEPTIONAL
    assert results[0].involved_houses == (HouseNumber.TENTH,)


def test_pancha_mahapurusha_requires_kendra_house() -> None:
    rule = PanchaMahapurushaYogaRule()

    results = rule.evaluate(
        context_with(planet(PlanetType.MARS, ZodiacSign.ARIES, HouseNumber.SECOND))
    )

    assert results == ()


def test_pancha_mahapurusha_requires_own_sign_or_exaltation() -> None:
    rule = PanchaMahapurushaYogaRule()

    results = rule.evaluate(
        context_with(planet(PlanetType.MARS, ZodiacSign.LEO, HouseNumber.FIRST))
    )

    assert results == ()


def test_pancha_mahapurusha_ignores_non_mahapurusha_planets() -> None:
    rule = PanchaMahapurushaYogaRule()

    results = rule.evaluate(
        context_with(planet(PlanetType.SUN, ZodiacSign.ARIES, HouseNumber.FIRST))
    )

    assert results == ()


def test_pancha_mahapurusha_detects_multiple_yogas_deterministically() -> None:
    rule = PanchaMahapurushaYogaRule()

    results = rule.evaluate(
        context_with(
            planet(PlanetType.SATURN, ZodiacSign.LIBRA, HouseNumber.SEVENTH),
            planet(PlanetType.MARS, ZodiacSign.ARIES, HouseNumber.FIRST),
            planet(PlanetType.VENUS, ZodiacSign.TAURUS, HouseNumber.FOURTH),
        )
    )

    assert tuple(result.yoga.key for result in results) == (
        "ruchaka",
        "malavya",
        "sasa",
    )


def test_pancha_mahapurusha_integrates_with_detection_engine() -> None:
    engine = YogaDetectionEngine(rules=(PanchaMahapurushaYogaRule(),))

    results = engine.detect(
        context_with(planet(PlanetType.JUPITER, ZodiacSign.CANCER, HouseNumber.FOURTH))
    )

    assert len(results) == 1
    assert results[0].yoga.key == "hamsa"
    assert results[0].strength is YogaStrength.EXCEPTIONAL
