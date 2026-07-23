from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.domain.ascendant import Ascendant
from app.domain.astrology_analysis import AstrologyAnalysis
from app.domain.chart import Chart
from app.domain.budhaditya_yoga import BudhadityaYogaRule
from app.domain.house import House
from app.domain.house_number import HouseNumber
from app.domain.nakshatra import Nakshatra
from app.domain.planet import Planet
from app.domain.planet_type import PlanetType
from app.domain.yoga import YogaStrength, YogaType
from app.domain.yoga_detection import YogaContext, YogaDetectionEngine
from app.domain.yoga_rule_registry import YogaRuleRegistry
from app.domain.zodiac import ZodiacSign
from app.domain.pancha_mahapurusha_yoga import PanchaMahapurushaYogaRule


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


def test_budhaditya_positive_cases() -> None:
    rule = BudhadityaYogaRule()
    # Sun and Mercury in the same sign (Gemini)
    context = context_with(
        planet(PlanetType.SUN, ZodiacSign.GEMINI, HouseNumber.THIRD),
        planet(PlanetType.MERCURY, ZodiacSign.GEMINI, HouseNumber.THIRD),
    )
    result = rule.evaluate(context)
    assert result is not None
    assert result.yoga.key == "budhaditya"
    assert result.yoga.yoga_type == YogaType.BUDHADITYA_YOGA
    assert result.strength == YogaStrength.STRONG  # Gemini is own sign of Mercury
    assert result.involved_planets == (PlanetType.SUN, PlanetType.MERCURY)
    assert result.involved_houses == (HouseNumber.THIRD, HouseNumber.THIRD)


def test_budhaditya_negative_cases_different_signs() -> None:
    rule = BudhadityaYogaRule()
    # Sun in Aries, Mercury in Taurus
    context = context_with(
        planet(PlanetType.SUN, ZodiacSign.ARIES, HouseNumber.FIRST),
        planet(PlanetType.MERCURY, ZodiacSign.TAURUS, HouseNumber.SECOND),
    )
    result = rule.evaluate(context)
    assert result is None


def test_budhaditya_negative_cases_missing_planet() -> None:
    rule = BudhadityaYogaRule()
    context = context_with(
        planet(PlanetType.SUN, ZodiacSign.ARIES, HouseNumber.FIRST),
    )
    result = rule.evaluate(context)
    assert result is None


@pytest.mark.parametrize(
    ("sign", "expected_strength"),
    [
        (ZodiacSign.ARIES, YogaStrength.EXCEPTIONAL),  # Sun exalted
        (ZodiacSign.VIRGO, YogaStrength.EXCEPTIONAL),  # Mercury exalted
        (ZodiacSign.LEO, YogaStrength.STRONG),        # Sun own sign
        (ZodiacSign.GEMINI, YogaStrength.STRONG),     # Mercury own sign
        (ZodiacSign.CANCER, YogaStrength.MODERATE),   # Ordinary sign
    ],
)
def test_budhaditya_strengths_and_boundaries(sign: ZodiacSign, expected_strength: YogaStrength) -> None:
    rule = BudhadityaYogaRule()
    context = context_with(
        planet(PlanetType.SUN, sign, HouseNumber.FIRST),
        planet(PlanetType.MERCURY, sign, HouseNumber.FIRST),
    )
    result = rule.evaluate(context)
    assert result is not None
    assert result.strength == expected_strength


def test_multiple_simultaneous_yogas_with_engine() -> None:
    # Sun and Mercury in Aries (Budhaditya)
    # Mars in Aries (Pancha Mahapurusha - Ruchaka since Aries is Mars' own sign and in first house)
    engine = YogaDetectionEngine(
        rules=(
            BudhadityaYogaRule(),
            PanchaMahapurushaYogaRule(),
        )
    )
    context = context_with(
        planet(PlanetType.SUN, ZodiacSign.ARIES, HouseNumber.FIRST),
        planet(PlanetType.MERCURY, ZodiacSign.ARIES, HouseNumber.FIRST),
        planet(PlanetType.MARS, ZodiacSign.ARIES, HouseNumber.FIRST),
    )
    results = engine.detect(context)
    keys = {r.yoga.key for r in results}
    assert "budhaditya" in keys
    assert "ruchaka" in keys


def test_yoga_detection_engine_integration() -> None:
    engine = YogaDetectionEngine(rules=(BudhadityaYogaRule(),))
    context = context_with(
        planet(PlanetType.SUN, ZodiacSign.LEO, HouseNumber.FIFTH),
        planet(PlanetType.MERCURY, ZodiacSign.LEO, HouseNumber.FIFTH),
    )
    results = engine.detect(context)
    assert len(results) == 1
    assert results[0].yoga.key == "budhaditya"


def test_yoga_rule_registry_integration() -> None:
    registry = YogaRuleRegistry()
    rules = registry.get_rules()
    assert any(isinstance(rule, BudhadityaYogaRule) for rule in rules)
