from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.domain.ascendant import Ascendant
from app.domain.astrology_analysis import AstrologyAnalysis
from app.domain.chart import Chart
from app.domain.chandra_mangala_yoga import ChandraMangalaYogaRule
from app.domain.house import House
from app.domain.house_number import HouseNumber
from app.domain.nakshatra import Nakshatra
from app.domain.planet import Planet
from app.domain.planet_type import PlanetType
from app.domain.yoga import YogaStrength, YogaType
from app.domain.yoga_detection import YogaContext, YogaDetectionEngine
from app.domain.yoga_rule_registry import YogaRuleRegistry
from app.domain.zodiac import ZodiacSign
from app.domain.budhaditya_yoga import BudhadityaYogaRule


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


def test_chandra_mangala_positive_conjunction() -> None:
    rule = ChandraMangalaYogaRule()
    # Conjunction in Aries
    context = context_with(
        planet(PlanetType.MOON, ZodiacSign.ARIES, HouseNumber.FIRST),
        planet(PlanetType.MARS, ZodiacSign.ARIES, HouseNumber.FIRST),
    )
    result = rule.evaluate(context)
    assert result is not None
    assert result.yoga.key == "chandra_mangala"
    assert result.yoga.yoga_type == YogaType.CHANDRA_MANGALA_YOGA
    assert result.strength == YogaStrength.STRONG  # Mars in Aries (own sign)
    assert result.involved_planets == (PlanetType.MOON, PlanetType.MARS)
    assert result.involved_houses == (HouseNumber.FIRST, HouseNumber.FIRST)
    assert "conjunct" in result.evidence[-1]


def test_chandra_mangala_aspect_7th() -> None:
    rule = ChandraMangalaYogaRule()
    # Moon in Aries, Mars in Libra (7 signs apart)
    context = context_with(
        planet(PlanetType.MOON, ZodiacSign.ARIES, HouseNumber.FIRST),
        planet(PlanetType.MARS, ZodiacSign.LIBRA, HouseNumber.SEVENTH),
    )
    result = rule.evaluate(context)
    assert result is not None
    assert result.yoga.key == "chandra_mangala"
    assert "aspect" in result.evidence[-1]


def test_chandra_mangala_aspect_4th() -> None:
    rule = ChandraMangalaYogaRule()
    # Mars in Aries, Moon in Cancer (Mars aspects 4th house target Cancer)
    context = context_with(
        planet(PlanetType.MARS, ZodiacSign.ARIES, HouseNumber.FIRST),
        planet(PlanetType.MOON, ZodiacSign.CANCER, HouseNumber.FOURTH),
    )
    result = rule.evaluate(context)
    assert result is not None
    assert result.yoga.key == "chandra_mangala"
    assert result.strength == YogaStrength.STRONG  # Mars in Aries (own sign), Moon in Cancer (own sign)


def test_chandra_mangala_aspect_8th() -> None:
    rule = ChandraMangalaYogaRule()
    # Mars in Aries, Moon in Scorpio (Mars aspects 8th house target Scorpio)
    context = context_with(
        planet(PlanetType.MARS, ZodiacSign.ARIES, HouseNumber.FIRST),
        planet(PlanetType.MOON, ZodiacSign.SCORPIO, HouseNumber.EIGHTH),
    )
    result = rule.evaluate(context)
    assert result is not None
    assert result.yoga.key == "chandra_mangala"
    assert result.strength == YogaStrength.STRONG  # Mars in Aries/Scorpio (own signs)


def test_chandra_mangala_negative_cases() -> None:
    rule = ChandraMangalaYogaRule()
    # Moon in Aries, Mars in Taurus (2 signs apart, no special aspect or conjunction)
    context = context_with(
        planet(PlanetType.MOON, ZodiacSign.ARIES, HouseNumber.FIRST),
        planet(PlanetType.MARS, ZodiacSign.TAURUS, HouseNumber.SECOND),
    )
    result = rule.evaluate(context)
    assert result is None


def test_chandra_mangala_negative_missing_planet() -> None:
    rule = ChandraMangalaYogaRule()
    context = context_with(
        planet(PlanetType.MOON, ZodiacSign.ARIES, HouseNumber.FIRST),
    )
    result = rule.evaluate(context)
    assert result is None


@pytest.mark.parametrize(
    ("sign", "expected_strength"),
    [
        (ZodiacSign.TAURUS, YogaStrength.EXCEPTIONAL),  # Moon exalted
        (ZodiacSign.CAPRICORN, YogaStrength.EXCEPTIONAL),  # Mars exalted
        (ZodiacSign.CANCER, YogaStrength.STRONG),  # Moon own sign
        (ZodiacSign.ARIES, YogaStrength.STRONG),  # Mars own sign
        (ZodiacSign.GEMINI, YogaStrength.MODERATE),  # Ordinary signs
    ],
)
def test_chandra_mangala_strengths_and_boundaries(
    sign: ZodiacSign,
    expected_strength: YogaStrength,
) -> None:
    rule = ChandraMangalaYogaRule()
    # Conjunction triggers evaluation
    context = context_with(
        planet(PlanetType.MOON, sign, HouseNumber.FIRST),
        planet(PlanetType.MARS, sign, HouseNumber.FIRST),
    )
    result = rule.evaluate(context)
    assert result is not None
    assert result.strength == expected_strength


def test_multiple_simultaneous_yogas_with_engine() -> None:
    # Moon and Mars conjunct in Aries (Chandra Mangala)
    # Sun and Mercury conjunct in Leo (Budhaditya)
    engine = YogaDetectionEngine(
        rules=(
            ChandraMangalaYogaRule(),
            BudhadityaYogaRule(),
        )
    )
    context = context_with(
        planet(PlanetType.MOON, ZodiacSign.ARIES, HouseNumber.FIRST),
        planet(PlanetType.MARS, ZodiacSign.ARIES, HouseNumber.FIRST),
        planet(PlanetType.SUN, ZodiacSign.LEO, HouseNumber.FIFTH),
        planet(PlanetType.MERCURY, ZodiacSign.LEO, HouseNumber.FIFTH),
    )
    results = engine.detect(context)
    keys = {r.yoga.key for r in results}
    assert "chandra_mangala" in keys
    assert "budhaditya" in keys


def test_yoga_detection_engine_integration() -> None:
    engine = YogaDetectionEngine(rules=(ChandraMangalaYogaRule(),))
    context = context_with(
        planet(PlanetType.MOON, ZodiacSign.ARIES, HouseNumber.FIRST),
        planet(PlanetType.MARS, ZodiacSign.ARIES, HouseNumber.FIRST),
    )
    results = engine.detect(context)
    assert len(results) == 1
    assert results[0].yoga.key == "chandra_mangala"


def test_yoga_rule_registry_integration() -> None:
    registry = YogaRuleRegistry()
    rules = registry.get_rules()
    assert any(isinstance(rule, ChandraMangalaYogaRule) for rule in rules)
