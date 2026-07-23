from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.domain.ascendant import Ascendant
from app.domain.astrology_analysis import AstrologyAnalysis
from app.domain.chart import Chart
from app.domain.gaja_kesari_yoga import GajaKesariYogaRule
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
    ("jupiter_sign", "jupiter_house"),
    [
        (ZodiacSign.CANCER, HouseNumber.FIRST),
        (ZodiacSign.LIBRA, HouseNumber.FOURTH),
        (ZodiacSign.CAPRICORN, HouseNumber.SEVENTH),
        (ZodiacSign.ARIES, HouseNumber.TENTH),
    ],
)
def test_gaja_kesari_detects_jupiter_in_kendra_from_moon(
    jupiter_sign: ZodiacSign,
    jupiter_house: HouseNumber,
) -> None:
    rule = GajaKesariYogaRule()

    result = rule.evaluate(
        context_with(
            planet(PlanetType.MOON, ZodiacSign.CANCER, HouseNumber.FIRST),
            planet(PlanetType.JUPITER, jupiter_sign, jupiter_house),
        )
    )

    assert result is not None
    assert result.yoga.key == "gaja_kesari"
    assert result.yoga.name == "Gaja Kesari Yoga"
    assert result.yoga.yoga_type is YogaType.GAJA_KESARI_YOGA
    assert result.involved_planets == (PlanetType.MOON, PlanetType.JUPITER)
    assert result.involved_houses == (HouseNumber.FIRST, jupiter_house)


def test_gaja_kesari_exalted_jupiter_has_exceptional_strength() -> None:
    rule = GajaKesariYogaRule()

    result = rule.evaluate(
        context_with(
            planet(PlanetType.MOON, ZodiacSign.CANCER, HouseNumber.FIRST),
            planet(PlanetType.JUPITER, ZodiacSign.CANCER, HouseNumber.FIRST),
        )
    )

    assert result is not None
    assert result.strength is YogaStrength.EXCEPTIONAL


@pytest.mark.parametrize("own_sign", [ZodiacSign.SAGITTARIUS, ZodiacSign.PISCES])
def test_gaja_kesari_own_sign_jupiter_has_strong_strength(
    own_sign: ZodiacSign,
) -> None:
    rule = GajaKesariYogaRule()

    result = rule.evaluate(
        context_with(
            planet(PlanetType.MOON, own_sign, HouseNumber.FIRST),
            planet(PlanetType.JUPITER, own_sign, HouseNumber.FIRST),
        )
    )

    assert result is not None
    assert result.strength is YogaStrength.STRONG


def test_gaja_kesari_non_exalted_non_own_sign_has_moderate_strength() -> None:
    rule = GajaKesariYogaRule()

    result = rule.evaluate(
        context_with(
            planet(PlanetType.MOON, ZodiacSign.LEO, HouseNumber.FIRST),
            planet(PlanetType.JUPITER, ZodiacSign.SCORPIO, HouseNumber.FOURTH),
        )
    )

    assert result is not None
    assert result.strength is YogaStrength.MODERATE


@pytest.mark.parametrize(
    ("moon_sign", "jupiter_sign"),
    [
        (ZodiacSign.CANCER, ZodiacSign.LEO),
        (ZodiacSign.CANCER, ZodiacSign.VIRGO),
        (ZodiacSign.CANCER, ZodiacSign.SCORPIO),
    ],
)
def test_gaja_kesari_rejects_non_kendra_jupiter_from_moon(
    moon_sign: ZodiacSign,
    jupiter_sign: ZodiacSign,
) -> None:
    rule = GajaKesariYogaRule()

    result = rule.evaluate(
        context_with(
            planet(PlanetType.MOON, moon_sign, HouseNumber.FIRST),
            planet(PlanetType.JUPITER, jupiter_sign, HouseNumber.SECOND),
        )
    )

    assert result is None


def test_gaja_kesari_requires_moon() -> None:
    rule = GajaKesariYogaRule()

    result = rule.evaluate(
        context_with(planet(PlanetType.JUPITER, ZodiacSign.CANCER, HouseNumber.FIRST))
    )

    assert result is None


def test_gaja_kesari_requires_jupiter() -> None:
    rule = GajaKesariYogaRule()

    result = rule.evaluate(
        context_with(planet(PlanetType.MOON, ZodiacSign.CANCER, HouseNumber.FIRST))
    )

    assert result is None


def test_gaja_kesari_boundary_wraps_from_moon_to_tenth_sign() -> None:
    rule = GajaKesariYogaRule()

    result = rule.evaluate(
        context_with(
            planet(PlanetType.MOON, ZodiacSign.PISCES, HouseNumber.FIRST),
            planet(PlanetType.JUPITER, ZodiacSign.SAGITTARIUS, HouseNumber.TENTH),
        )
    )

    assert result is not None
    assert result.yoga.key == "gaja_kesari"


def test_gaja_kesari_detects_multiple_yogas_with_engine() -> None:
    engine = YogaDetectionEngine(
        rules=(
            GajaKesariYogaRule(),
            PanchaMahapurushaYogaRule(),
        )
    )

    results = engine.detect(
        context_with(
            planet(PlanetType.MOON, ZodiacSign.CANCER, HouseNumber.FIRST),
            planet(PlanetType.JUPITER, ZodiacSign.CANCER, HouseNumber.FOURTH),
        )
    )

    assert tuple(result.yoga.key for result in results) == (
        "gaja_kesari",
        "hamsa",
    )


def test_gaja_kesari_integrates_with_detection_engine() -> None:
    engine = YogaDetectionEngine(rules=(GajaKesariYogaRule(),))

    results = engine.detect(
        context_with(
            planet(PlanetType.MOON, ZodiacSign.TAURUS, HouseNumber.FIRST),
            planet(PlanetType.JUPITER, ZodiacSign.SCORPIO, HouseNumber.SEVENTH),
        )
    )

    assert len(results) == 1
    assert results[0].yoga.key == "gaja_kesari"
