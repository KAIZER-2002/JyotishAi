"""
Comprehensive unit tests for DhanaYogaRule.

Dhana Yoga forms when the lord of a primary Dhana house (2nd or 11th)
is in Sambandha (conjunction, mutual aspect, or parivartana) with the lord
of a prosperity-supporting house (1st, 2nd, 5th, 9th, 11th).

Ascendant used throughout: Aries (♈)
  House 1  → Aries    → lord: Mars
  House 2  → Taurus   → lord: Venus   [PRIMARY DHANA]
  House 3  → Gemini   → lord: Mercury
  House 4  → Cancer   → lord: Moon
  House 5  → Leo      → lord: Sun
  House 6  → Virgo    → lord: Mercury
  House 7  → Libra    → lord: Venus
  House 8  → Scorpio  → lord: Mars
  House 9  → Sagittarius → lord: Jupiter
  House 10 → Capricorn  → lord: Saturn
  House 11 → Aquarius   → lord: Saturn [PRIMARY DHANA]
  House 12 → Pisces     → lord: Jupiter
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.domain.ascendant import Ascendant
from app.domain.astrology_analysis import AstrologyAnalysis
from app.domain.chart import Chart
from app.domain.dhana_yoga import DhanaYogaRule
from app.domain.house import House
from app.domain.house_number import HouseNumber
from app.domain.nakshatra import Nakshatra
from app.domain.planet import Planet
from app.domain.planet_type import PlanetType
from app.domain.yoga import YogaStrength, YogaType
from app.domain.yoga_detection import YogaContext, YogaDetectionEngine
from app.domain.yoga_rule_registry import YogaRuleRegistry
from app.domain.zodiac import ZodiacSign


# ---------------------------------------------------------------------------
# Test helpers (same pattern as test_raj_yoga.py)
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Positive cases — conjunction
# ---------------------------------------------------------------------------


def test_dhana_yoga_positive_conjunction_2nd_lord_and_1st_lord() -> None:
    """Venus (2nd lord) conjunct Mars (1st lord) in Aries → Dhana Yoga."""
    rule = DhanaYogaRule()
    # Aries Ascendant:
    # Venus = lord of 2nd (Taurus) [primary Dhana]
    # Mars  = lord of 1st (Aries)  [prosperity]
    context = context_with_ascendant(
        ZodiacSign.ARIES,
        planet(PlanetType.VENUS, ZodiacSign.ARIES, HouseNumber.FIRST),
        planet(PlanetType.MARS, ZodiacSign.ARIES, HouseNumber.FIRST),
    )

    results = rule.evaluate(context)
    assert len(results) == 1
    result = results[0]
    assert result.yoga.yoga_type == YogaType.DHANA_YOGA
    assert result.yoga.key == "dhana_yoga_mars_venus"
    assert PlanetType.VENUS in result.involved_planets
    assert PlanetType.MARS in result.involved_planets
    assert result.strength == YogaStrength.STRONG  # Mars is in Aries (own sign)


def test_dhana_yoga_positive_conjunction_2nd_lord_and_9th_lord() -> None:
    """Venus (2nd lord) conjunct Jupiter (9th lord) → Dhana Yoga."""
    rule = DhanaYogaRule()
    # Aries Ascendant:
    # Venus   = lord of 2nd [primary Dhana]
    # Jupiter = lord of 9th [prosperity]
    context = context_with_ascendant(
        ZodiacSign.ARIES,
        planet(PlanetType.VENUS, ZodiacSign.GEMINI, HouseNumber.THIRD),
        planet(PlanetType.JUPITER, ZodiacSign.GEMINI, HouseNumber.THIRD),
    )

    results = rule.evaluate(context)
    assert len(results) >= 1
    keys = {r.yoga.key for r in results}
    assert "dhana_yoga_jupiter_venus" in keys


def test_dhana_yoga_positive_conjunction_11th_lord_and_5th_lord() -> None:
    """Saturn (11th lord) conjunct Sun (5th lord) → Dhana Yoga."""
    rule = DhanaYogaRule()
    # Aries Ascendant:
    # Saturn = lord of 11th (Aquarius) [primary Dhana]
    # Sun    = lord of 5th  (Leo)      [prosperity]
    context = context_with_ascendant(
        ZodiacSign.ARIES,
        planet(PlanetType.SATURN, ZodiacSign.LEO, HouseNumber.FIFTH),
        planet(PlanetType.SUN, ZodiacSign.LEO, HouseNumber.FIFTH),
    )

    results = rule.evaluate(context)
    assert len(results) >= 1
    keys = {r.yoga.key for r in results}
    assert "dhana_yoga_saturn_sun" in keys


# ---------------------------------------------------------------------------
# Positive cases — aspect
# ---------------------------------------------------------------------------


def test_dhana_yoga_positive_aspect_7th_mutual() -> None:
    """Venus (2nd lord) in Aries aspects Jupiter (9th lord) in Libra via 7th aspect."""
    rule = DhanaYogaRule()
    # Venus in Aries (1st), Jupiter in Libra (7th) → mutual 7th-house aspects
    context = context_with_ascendant(
        ZodiacSign.ARIES,
        planet(PlanetType.VENUS, ZodiacSign.ARIES, HouseNumber.FIRST),
        planet(PlanetType.JUPITER, ZodiacSign.LIBRA, HouseNumber.SEVENTH),
    )

    results = rule.evaluate(context)
    assert len(results) >= 1
    keys = {r.yoga.key for r in results}
    assert "dhana_yoga_jupiter_venus" in keys


def test_dhana_yoga_positive_aspect_saturn_special() -> None:
    """Saturn (11th lord) uses 3rd / 10th special aspects to relate to Venus (2nd lord)."""
    rule = DhanaYogaRule()
    # Aries Ascendant:
    # Saturn in Aries (1st), Venus in Gemini (3rd).
    # Saturn aspects the 3rd house from itself (3rd aspect) → hits Gemini where Venus sits.
    context = context_with_ascendant(
        ZodiacSign.ARIES,
        planet(PlanetType.SATURN, ZodiacSign.ARIES, HouseNumber.FIRST),
        planet(PlanetType.VENUS, ZodiacSign.GEMINI, HouseNumber.THIRD),
    )

    results = rule.evaluate(context)
    assert len(results) >= 1
    keys = {r.yoga.key for r in results}
    assert "dhana_yoga_saturn_venus" in keys


# ---------------------------------------------------------------------------
# Positive cases — parivartana
# ---------------------------------------------------------------------------


def test_dhana_yoga_positive_parivartana_2nd_and_9th() -> None:
    """Venus (2nd) in Sagittarius and Jupiter (9th) in Taurus → Parivartana Dhana Yoga."""
    rule = DhanaYogaRule()
    # Venus owns Taurus (2nd). Jupiter owns Sagittarius (9th).
    # Venus placed in Sagittarius, Jupiter placed in Taurus → mutual exchange.
    context = context_with_ascendant(
        ZodiacSign.ARIES,
        planet(PlanetType.VENUS, ZodiacSign.SAGITTARIUS, HouseNumber.NINTH),
        planet(PlanetType.JUPITER, ZodiacSign.TAURUS, HouseNumber.SECOND),
    )

    results = rule.evaluate(context)
    assert len(results) >= 1
    keys = {r.yoga.key for r in results}
    assert "dhana_yoga_jupiter_venus" in keys


def test_dhana_yoga_positive_parivartana_11th_and_5th() -> None:
    """Saturn (11th) in Leo and Sun (5th) in Aquarius → Parivartana Dhana Yoga."""
    rule = DhanaYogaRule()
    # Saturn owns Aquarius (11th). Sun owns Leo (5th).
    # Exchange: Saturn in Leo, Sun in Aquarius.
    context = context_with_ascendant(
        ZodiacSign.ARIES,
        planet(PlanetType.SATURN, ZodiacSign.LEO, HouseNumber.FIFTH),
        planet(PlanetType.SUN, ZodiacSign.AQUARIUS, HouseNumber.ELEVENTH),
    )

    results = rule.evaluate(context)
    assert len(results) >= 1
    keys = {r.yoga.key for r in results}
    assert "dhana_yoga_saturn_sun" in keys


# ---------------------------------------------------------------------------
# Strength grading
# ---------------------------------------------------------------------------


def test_dhana_yoga_strength_exceptional_when_exalted() -> None:
    """Venus (2nd lord) exalted in Pisces → EXCEPTIONAL strength."""
    rule = DhanaYogaRule()
    # Venus in Pisces (12th, but exalted). Jupiter in Aries (1st) aspects Pisces.
    # Venus exalted → EXCEPTIONAL.
    context = context_with_ascendant(
        ZodiacSign.ARIES,
        planet(PlanetType.VENUS, ZodiacSign.PISCES, HouseNumber.TWELFTH),
        planet(PlanetType.JUPITER, ZodiacSign.PISCES, HouseNumber.TWELFTH),
    )

    results = rule.evaluate(context)
    assert len(results) >= 1
    dhana_results = [r for r in results if "venus" in r.yoga.key]
    assert any(r.strength == YogaStrength.EXCEPTIONAL for r in dhana_results)


def test_dhana_yoga_strength_strong_when_own_sign() -> None:
    """Saturn (11th lord) in Aquarius (own sign) → STRONG strength."""
    rule = DhanaYogaRule()
    # Saturn in Aquarius (own sign = 11th house) conjunct Venus (2nd lord) in Aquarius.
    context = context_with_ascendant(
        ZodiacSign.ARIES,
        planet(PlanetType.SATURN, ZodiacSign.AQUARIUS, HouseNumber.ELEVENTH),
        planet(PlanetType.VENUS, ZodiacSign.AQUARIUS, HouseNumber.ELEVENTH),
    )

    results = rule.evaluate(context)
    assert len(results) >= 1
    dhana_results = [r for r in results if "saturn" in r.yoga.key and "venus" in r.yoga.key]
    assert any(r.strength == YogaStrength.STRONG for r in dhana_results)


# ---------------------------------------------------------------------------
# Negative cases
# ---------------------------------------------------------------------------


def test_dhana_yoga_negative_no_relationship() -> None:
    """Venus (2nd lord) and Jupiter (9th lord) without Sambandha → no Dhana Yoga."""
    rule = DhanaYogaRule()
    # Venus in Aries (1st), Jupiter in Taurus (2nd) — no conjunction, aspect, or exchange
    context = context_with_ascendant(
        ZodiacSign.ARIES,
        planet(PlanetType.VENUS, ZodiacSign.ARIES, HouseNumber.FIRST),
        planet(PlanetType.JUPITER, ZodiacSign.TAURUS, HouseNumber.SECOND),
    )

    results = rule.evaluate(context)
    # Jupiter is in Taurus, which Venus owns — Venus and Jupiter sign exchange? No.
    # Venus is in Aries (Mars sign), Jupiter in Taurus (Venus sign) — not a mutual exchange.
    # No direct aspect either (Aries to Taurus = 2nd house offset, not an aspect offset).
    assert all("venus" not in r.yoga.key or "jupiter" not in r.yoga.key for r in results)


def test_dhana_yoga_negative_self_pairing() -> None:
    """Saturn owns both 10th (Capricorn) and 11th (Aquarius) — cannot pair with itself."""
    rule = DhanaYogaRule()
    context = context_with_ascendant(
        ZodiacSign.ARIES,
        planet(PlanetType.SATURN, ZodiacSign.CAPRICORN, HouseNumber.TENTH),
    )

    results = rule.evaluate(context)
    for r in results:
        lords = r.involved_planets
        assert lords[0] != lords[1], "A planet must not pair with itself."


def test_dhana_yoga_negative_no_dhana_lord_present() -> None:
    """Only non-wealth planets present → no Dhana Yoga."""
    rule = DhanaYogaRule()
    # Only Moon (4th lord) and Sun (5th lord) — neither is a 2nd or 11th lord
    # (for Aries asc, Moon=4th, Sun=5th)
    # Place them conjunct — should not produce Dhana Yoga because neither is a Dhana lord.
    # NOTE: Saturn rules the 11th for Aries asc and is absent from this chart,
    # so Saturn-related pairs will not fire. Venus rules the 2nd and is also absent.
    context = context_with_ascendant(
        ZodiacSign.ARIES,
        planet(PlanetType.MOON, ZodiacSign.LEO, HouseNumber.FIFTH),
        planet(PlanetType.SUN, ZodiacSign.LEO, HouseNumber.FIFTH),
    )

    results = rule.evaluate(context)
    assert len(results) == 0


# ---------------------------------------------------------------------------
# Multiple simultaneous Dhana Yogas
# ---------------------------------------------------------------------------


def test_dhana_yoga_multiple_simultaneous() -> None:
    """Multiple distinct Dhana Yoga combinations detected at once."""
    rule = DhanaYogaRule()
    # Aries Ascendant:
    # Venus (2nd lord) conjunct Mars (1st lord) in Aries  → Dhana Yoga 1
    # Saturn (11th lord) conjunct Sun (5th lord) in Leo   → Dhana Yoga 2
    # Venus (2nd) and Saturn (11th) are both lords of Dhana houses; their
    # mutual relationship (if any) would also qualify — but they are in different
    # signs here without direct aspect, so only the above two fire.
    context = context_with_ascendant(
        ZodiacSign.ARIES,
        planet(PlanetType.VENUS, ZodiacSign.ARIES, HouseNumber.FIRST),
        planet(PlanetType.MARS, ZodiacSign.ARIES, HouseNumber.FIRST),
        planet(PlanetType.SATURN, ZodiacSign.LEO, HouseNumber.FIFTH),
        planet(PlanetType.SUN, ZodiacSign.LEO, HouseNumber.FIFTH),
    )

    results = rule.evaluate(context)
    keys = {r.yoga.key for r in results}
    # Venus–Mars pair and Saturn–Sun pair must both be detected
    assert "dhana_yoga_mars_venus" in keys
    assert "dhana_yoga_saturn_sun" in keys
    # All detected yogas must be Dhana Yogas
    for r in results:
        assert r.yoga.yoga_type == YogaType.DHANA_YOGA


# ---------------------------------------------------------------------------
# Engine integration
# ---------------------------------------------------------------------------


def test_dhana_yoga_detection_engine_integration() -> None:
    """DhanaYogaRule integrates correctly with YogaDetectionEngine."""
    engine = YogaDetectionEngine(rules=(DhanaYogaRule(),))
    context = context_with_ascendant(
        ZodiacSign.ARIES,
        planet(PlanetType.VENUS, ZodiacSign.ARIES, HouseNumber.FIRST),
        planet(PlanetType.MARS, ZodiacSign.ARIES, HouseNumber.FIRST),
    )

    results = engine.detect(context)
    assert len(results) == 1
    assert results[0].yoga.yoga_type == YogaType.DHANA_YOGA
    assert results[0].yoga.key == "dhana_yoga_mars_venus"


# ---------------------------------------------------------------------------
# Registry integration
# ---------------------------------------------------------------------------


def test_dhana_yoga_registry_integration() -> None:
    """DhanaYogaRule is registered in YogaRuleRegistry."""
    registry = YogaRuleRegistry()
    rules = registry.get_rules()
    assert any(isinstance(rule, DhanaYogaRule) for rule in rules)
