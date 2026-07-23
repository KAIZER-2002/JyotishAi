from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.domain.ascendant import Ascendant
from app.domain.astrology_analysis import AstrologyAnalysis
from app.domain.chart import Chart
from app.domain.raj_yoga import RajYogaRule
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


def chart_with_ascendant(ascendant_sign: ZodiacSign, *planets: Planet) -> Chart:
    asc_index = list(ZodiacSign).index(ascendant_sign)
    return Chart(
        ascendant=Ascendant(
            zodiac_sign=ascendant_sign,
            longitude=float(asc_index * 30),
            nakshatra=Nakshatra.ASHWINI,
            pada=1,
            degree_within_sign=0.0,
        ),
        planets=planets,
        houses=tuple(
            House(
                house_number=house_number,
                start_longitude=float(((asc_index + index) % 12) * 30),
                end_longitude=float(((asc_index + index + 1) % 12) * 30),
            )
            for index, house_number in enumerate(HouseNumber)
        ),
    )


def context_with_ascendant(ascendant_sign: ZodiacSign, *planets: Planet) -> YogaContext:
    birth_chart = chart_with_ascendant(ascendant_sign, *planets)
    return YogaContext(
        AstrologyAnalysis(
            birth_chart=birth_chart,
            navamsa_chart=chart_with_ascendant(ZodiacSign.ARIES),
            dasamsa_chart=chart_with_ascendant(ZodiacSign.ARIES),
            shastiamsa_chart=chart_with_ascendant(ZodiacSign.ARIES),
            vimshottari_dashas=(),
        )
    )


def test_raj_yoga_positive_conjunction() -> None:
    rule = RajYogaRule()
    # Aries Ascendant:
    # Kendra lord: Moon (4th)
    # Trikona lord: Jupiter (9th)
    # Place them conjunct in Aries (1st house)
    context = context_with_ascendant(
        ZodiacSign.ARIES,
        planet(PlanetType.MOON, ZodiacSign.ARIES, HouseNumber.FIRST),
        planet(PlanetType.JUPITER, ZodiacSign.ARIES, HouseNumber.FIRST),
    )

    results = rule.evaluate(context)
    assert len(results) == 1
    result = results[0]
    assert result.yoga.yoga_type == YogaType.RAJ_YOGA
    assert result.yoga.key == "raj_yoga_moon_jupiter"
    assert result.involved_planets == (PlanetType.MOON, PlanetType.JUPITER)
    assert result.involved_houses == (HouseNumber.FIRST, HouseNumber.FIRST)
    assert result.strength == YogaStrength.MODERATE


def test_raj_yoga_positive_aspect() -> None:
    rule = RajYogaRule()
    # Aries Ascendant:
    # Kendra lord: Moon (4th)
    # Trikona lord: Jupiter (9th)
    # Place Moon in Aries (1st house), Jupiter in Libra (7th house) -> aspecting each other
    context = context_with_ascendant(
        ZodiacSign.ARIES,
        planet(PlanetType.MOON, ZodiacSign.ARIES, HouseNumber.FIRST),
        planet(PlanetType.JUPITER, ZodiacSign.LIBRA, HouseNumber.SEVENTH),
    )

    results = rule.evaluate(context)
    assert len(results) == 1
    result = results[0]
    assert result.yoga.key == "raj_yoga_moon_jupiter"
    assert set(result.involved_houses) == {HouseNumber.FIRST, HouseNumber.SEVENTH}


def test_raj_yoga_positive_parivartana() -> None:
    rule = RajYogaRule()
    # Aries Ascendant:
    # Kendra lord: Moon (owns Cancer, 4th house)
    # Trikona lord: Jupiter (owns Sagittarius, 9th house)
    # Place Moon in Sagittarius (9th house), Jupiter in Cancer (4th house) -> Parivartana
    context = context_with_ascendant(
        ZodiacSign.ARIES,
        planet(PlanetType.MOON, ZodiacSign.SAGITTARIUS, HouseNumber.NINTH),
        planet(PlanetType.JUPITER, ZodiacSign.CANCER, HouseNumber.FOURTH),
    )

    results = rule.evaluate(context)
    assert len(results) == 1
    result = results[0]
    assert result.yoga.key == "raj_yoga_moon_jupiter"
    assert set(result.involved_houses) == {HouseNumber.NINTH, HouseNumber.FOURTH}
    assert result.strength == YogaStrength.EXCEPTIONAL  # Jupiter is exalted in Cancer


def test_raj_yoga_negative_no_relationship() -> None:
    rule = RajYogaRule()
    # Moon in Aries, Jupiter in Taurus (no conjunction, aspect, or exchange)
    context = context_with_ascendant(
        ZodiacSign.ARIES,
        planet(PlanetType.MOON, ZodiacSign.ARIES, HouseNumber.FIRST),
        planet(PlanetType.JUPITER, ZodiacSign.TAURUS, HouseNumber.SECOND),
    )

    results = rule.evaluate(context)
    assert len(results) == 0


def test_raj_yoga_negative_self_relationship() -> None:
    rule = RajYogaRule()
    # Mars is lord of 1 (Kendra & Trikona). Mars cannot form a Raj Yoga with itself.
    context = context_with_ascendant(
        ZodiacSign.ARIES,
        planet(PlanetType.MARS, ZodiacSign.ARIES, HouseNumber.FIRST),
    )

    results = rule.evaluate(context)
    # Ensure Mars is not paired with itself
    assert len(results) == 0


def test_raj_yoga_multiple_simultaneous() -> None:
    rule = RajYogaRule()
    # Aries Ascendant:
    # 1. Moon (Kendra 4) conjunct Jupiter (Trikona 9) in Aries (House 1) -> Raj Yoga 1
    # 2. Saturn (Kendra 10) conjunct Sun (Trikona 5) in Leo (House 5) -> Raj Yoga 2
    # Note: Jupiter in Aries aspects Saturn in Leo (5th aspect offset), creating a 3rd Raj Yoga!
    context = context_with_ascendant(
        ZodiacSign.ARIES,
        planet(PlanetType.MOON, ZodiacSign.ARIES, HouseNumber.FIRST),
        planet(PlanetType.JUPITER, ZodiacSign.ARIES, HouseNumber.FIRST),
        planet(PlanetType.SATURN, ZodiacSign.LEO, HouseNumber.FIFTH),
        planet(PlanetType.SUN, ZodiacSign.LEO, HouseNumber.FIFTH),
    )

    results = rule.evaluate(context)
    assert len(results) == 3
    keys = {r.yoga.key for r in results}
    assert "raj_yoga_moon_jupiter" in keys
    assert "raj_yoga_saturn_sun" in keys
    assert "raj_yoga_jupiter_saturn" in keys or "raj_yoga_saturn_jupiter" in keys


def test_raj_yoga_exaltation_exceptional_strength() -> None:
    rule = RajYogaRule()
    # Moon in Taurus (exalted), Jupiter in Scorpio (7th aspect to Taurus)
    context = context_with_ascendant(
        ZodiacSign.ARIES,
        planet(PlanetType.MOON, ZodiacSign.TAURUS, HouseNumber.SECOND),
        planet(PlanetType.JUPITER, ZodiacSign.SCORPIO, HouseNumber.EIGHTH),
    )

    results = rule.evaluate(context)
    assert len(results) == 1
    assert results[0].strength == YogaStrength.EXCEPTIONAL


def test_raj_yoga_detection_engine_integration() -> None:
    engine = YogaDetectionEngine(rules=(RajYogaRule(),))
    context = context_with_ascendant(
        ZodiacSign.ARIES,
        planet(PlanetType.MOON, ZodiacSign.ARIES, HouseNumber.FIRST),
        planet(PlanetType.JUPITER, ZodiacSign.ARIES, HouseNumber.FIRST),
    )

    results = engine.detect(context)
    assert len(results) == 1
    assert results[0].yoga.key == "raj_yoga_moon_jupiter"


def test_raj_yoga_registry_integration() -> None:
    registry = YogaRuleRegistry()
    rules = registry.get_rules()
    assert any(isinstance(rule, RajYogaRule) for rule in rules)
