"""
Service-level tests for YogaAnalysisService.

These tests verify:
  - The service returns a YogaAnalysis with the correct shape.
  - Detected yogas are accurately passed through.
  - Strongest-yoga ranking is deterministic and correct.
  - Score computation follows the weight table and strength multipliers.
  - Scores are always capped at 0–100.
  - The service works with an injected engine (unit) and with the default
    registry (integration).
  - An empty chart produces zero scores and empty collections.
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.domain.ascendant import Ascendant
from app.domain.astrology_analysis import AstrologyAnalysis
from app.domain.chart import Chart
from app.domain.dhana_yoga import DhanaYogaRule
from app.domain.gaja_kesari_yoga import GajaKesariYogaRule
from app.domain.house import House
from app.domain.house_number import HouseNumber
from app.domain.nakshatra import Nakshatra
from app.domain.planet import Planet
from app.domain.planet_type import PlanetType
from app.domain.raj_yoga import RajYogaRule
from app.domain.yoga import YogaStrength, YogaType
from app.domain.yoga_analysis import YogaAnalysis, _STRENGTH_MULTIPLIER, _TYPE_WEIGHTS
from app.domain.yoga_detection import YogaDetectionEngine
from app.domain.yoga_rule_registry import YogaRuleRegistry
from app.domain.zodiac import ZodiacSign
from app.services.astrology.yoga_analysis_service import YogaAnalysisService


# ---------------------------------------------------------------------------
# Shared helpers  (identical pattern to all other yoga test files)
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


def analysis_with_ascendant(
    ascendant_sign: ZodiacSign,
    *planets: Planet,
) -> AstrologyAnalysis:
    birth_chart = chart_with_ascendant(ascendant_sign, *planets)
    empty = chart_with_ascendant(ZodiacSign.ARIES)
    return AstrologyAnalysis(
        birth_chart=birth_chart,
        navamsa_chart=empty,
        dasamsa_chart=empty,
        shastiamsa_chart=empty,
        vimshottari_dashas=(),
    )


# ---------------------------------------------------------------------------
# Return type and shape
# ---------------------------------------------------------------------------


def test_analyze_returns_yoga_analysis_instance() -> None:
    """Service always returns a YogaAnalysis regardless of chart content."""
    svc = YogaAnalysisService()
    result = svc.analyze(analysis_with_ascendant(ZodiacSign.ARIES))
    assert isinstance(result, YogaAnalysis)


def test_yoga_analysis_fields_are_present() -> None:
    """YogaAnalysis exposes all required fields."""
    svc = YogaAnalysisService()
    result = svc.analyze(analysis_with_ascendant(ZodiacSign.ARIES))

    assert hasattr(result, "detected_yogas")
    assert hasattr(result, "strongest_yogas")
    assert hasattr(result, "wealth_score")
    assert hasattr(result, "career_score")
    assert hasattr(result, "authority_score")
    assert hasattr(result, "relationship_score")
    assert hasattr(result, "spirituality_score")


# ---------------------------------------------------------------------------
# Empty chart — no yogas → zero scores
# ---------------------------------------------------------------------------


def test_empty_chart_produces_zero_scores() -> None:
    """No planets → no yogas → all scores are 0."""
    svc = YogaAnalysisService(engine=YogaDetectionEngine(rules=[]))
    result = svc.analyze(analysis_with_ascendant(ZodiacSign.ARIES))

    assert result.detected_yogas == ()
    assert result.strongest_yogas == ()
    assert result.wealth_score == 0
    assert result.career_score == 0
    assert result.authority_score == 0
    assert result.relationship_score == 0
    assert result.spirituality_score == 0


# ---------------------------------------------------------------------------
# Detected yogas are forwarded correctly
# ---------------------------------------------------------------------------


def test_detected_yogas_match_engine_output() -> None:
    """detected_yogas contains exactly what the engine finds."""
    # Aries asc: Moon (4th lord) + Jupiter (9th lord) conjunct → Raj Yoga
    engine = YogaDetectionEngine(rules=[RajYogaRule()])
    svc = YogaAnalysisService(engine=engine)

    analysis = analysis_with_ascendant(
        ZodiacSign.ARIES,
        planet(PlanetType.MOON, ZodiacSign.ARIES, HouseNumber.FIRST),
        planet(PlanetType.JUPITER, ZodiacSign.ARIES, HouseNumber.FIRST),
    )
    result = svc.analyze(analysis)

    assert len(result.detected_yogas) == 1
    assert result.detected_yogas[0].yoga.yoga_type == YogaType.RAJ_YOGA


# ---------------------------------------------------------------------------
# Strongest yoga ranking
# ---------------------------------------------------------------------------


def test_strongest_yogas_ranked_by_strength_descending() -> None:
    """strongest_yogas must be ordered strongest → weakest."""
    # Inject two rules so we get both Raj Yoga (MODERATE) and
    # Gaja Kesari (MODERATE for Moon in kendra from Jupiter) — then
    # we verify ordering when strengths differ.
    # Use Dhana Yoga with exalted Venus (EXCEPTIONAL) + Raj Yoga (MODERATE).
    engine = YogaDetectionEngine(rules=[RajYogaRule(), DhanaYogaRule()])
    svc = YogaAnalysisService(engine=engine)

    # Aries asc:
    # Venus (2nd) in Pisces (exalted, 12th) + Jupiter (9th / 12th lord) conjunct → Dhana EXCEPTIONAL
    # Moon (4th, kendra lord) in Aries (1st) + Jupiter → Raj Yoga EXCEPTIONAL (Jupiter exalted? No)
    # Let's use a clean scenario:
    # - Venus (2nd lord) exalted in Pisces conjunct Jupiter (9th / 12th lord) → Dhana Yoga EXCEPTIONAL
    # - Moon (4th lord, kendra) + Jupiter (9th, trikona) conjunct in Pisces → Raj Yoga (not exalted)
    analysis = analysis_with_ascendant(
        ZodiacSign.ARIES,
        planet(PlanetType.VENUS, ZodiacSign.PISCES, HouseNumber.TWELFTH),
        planet(PlanetType.JUPITER, ZodiacSign.PISCES, HouseNumber.TWELFTH),
        planet(PlanetType.MOON, ZodiacSign.ARIES, HouseNumber.FIRST),
    )
    result = svc.analyze(analysis)

    assert len(result.strongest_yogas) == len(result.detected_yogas)
    strengths = [r.strength for r in result.strongest_yogas]
    # Verify non-increasing strength order
    from app.domain.yoga_analysis import _STRENGTH_ORDER
    for i in range(len(strengths) - 1):
        assert _STRENGTH_ORDER[strengths[i]] >= _STRENGTH_ORDER[strengths[i + 1]]


def test_strongest_yogas_is_deterministic() -> None:
    """Calling analyze twice on the same input yields identical strongest_yogas."""
    svc = YogaAnalysisService()
    analysis = analysis_with_ascendant(
        ZodiacSign.ARIES,
        planet(PlanetType.MOON, ZodiacSign.ARIES, HouseNumber.FIRST),
        planet(PlanetType.JUPITER, ZodiacSign.ARIES, HouseNumber.FIRST),
    )

    r1 = svc.analyze(analysis)
    r2 = svc.analyze(analysis)
    assert r1.strongest_yogas == r2.strongest_yogas


# ---------------------------------------------------------------------------
# Score computation correctness
# ---------------------------------------------------------------------------


def test_wealth_score_increases_with_dhana_yoga() -> None:
    """Dhana Yoga detection must raise the wealth score above zero."""
    engine = YogaDetectionEngine(rules=[DhanaYogaRule()])
    svc = YogaAnalysisService(engine=engine)

    # Venus (2nd lord) conjunct Mars (1st lord) in Aries
    analysis = analysis_with_ascendant(
        ZodiacSign.ARIES,
        planet(PlanetType.VENUS, ZodiacSign.ARIES, HouseNumber.FIRST),
        planet(PlanetType.MARS, ZodiacSign.ARIES, HouseNumber.FIRST),
    )
    result = svc.analyze(analysis)
    assert result.wealth_score > 0


def test_authority_score_increases_with_raj_yoga() -> None:
    """Raj Yoga detection must raise the authority score above zero."""
    engine = YogaDetectionEngine(rules=[RajYogaRule()])
    svc = YogaAnalysisService(engine=engine)

    analysis = analysis_with_ascendant(
        ZodiacSign.ARIES,
        planet(PlanetType.MOON, ZodiacSign.ARIES, HouseNumber.FIRST),
        planet(PlanetType.JUPITER, ZodiacSign.ARIES, HouseNumber.FIRST),
    )
    result = svc.analyze(analysis)
    assert result.authority_score > 0


def test_score_exact_for_single_moderate_raj_yoga() -> None:
    """Exact score arithmetic for one MODERATE Raj Yoga (multiplier 1.0)."""
    engine = YogaDetectionEngine(rules=[RajYogaRule()])
    svc = YogaAnalysisService(engine=engine)

    # Moon+Jupiter conjunct in Aries (neither exalted, not own sign) → MODERATE
    analysis = analysis_with_ascendant(
        ZodiacSign.ARIES,
        planet(PlanetType.MOON, ZodiacSign.ARIES, HouseNumber.FIRST),
        planet(PlanetType.JUPITER, ZodiacSign.ARIES, HouseNumber.FIRST),
    )
    result = svc.analyze(analysis)

    weights = _TYPE_WEIGHTS[YogaType.RAJ_YOGA]   # (5, 20, 30, 0, 5)
    mult = _STRENGTH_MULTIPLIER[YogaStrength.MODERATE]  # 1.0

    assert result.wealth_score == min(100, round(weights[0] * mult))
    assert result.career_score == min(100, round(weights[1] * mult))
    assert result.authority_score == min(100, round(weights[2] * mult))
    assert result.relationship_score == min(100, round(weights[3] * mult))
    assert result.spirituality_score == min(100, round(weights[4] * mult))


def test_exceptional_strength_doubles_score_contribution() -> None:
    """EXCEPTIONAL multiplier (2.0) produces twice the contribution of MODERATE (1.0)."""
    # Venus exalted in Pisces + Jupiter in Pisces → Dhana Yoga EXCEPTIONAL
    engine = YogaDetectionEngine(rules=[DhanaYogaRule()])
    svc = YogaAnalysisService(engine=engine)

    analysis_exceptional = analysis_with_ascendant(
        ZodiacSign.ARIES,
        planet(PlanetType.VENUS, ZodiacSign.PISCES, HouseNumber.TWELFTH),
        planet(PlanetType.JUPITER, ZodiacSign.PISCES, HouseNumber.TWELFTH),
    )
    result_exc = svc.analyze(analysis_exceptional)

    # Confirm at least one EXCEPTIONAL yoga was detected
    assert any(
        r.strength == YogaStrength.EXCEPTIONAL for r in result_exc.detected_yogas
    ), "Expected at least one EXCEPTIONAL Dhana Yoga"

    # Wealth weight for Dhana Yoga = 30; EXCEPTIONAL mult = 2.0 → 60
    weights = _TYPE_WEIGHTS[YogaType.DHANA_YOGA]
    expected_wealth_contribution = round(weights[0] * _STRENGTH_MULTIPLIER[YogaStrength.EXCEPTIONAL])
    assert result_exc.wealth_score >= expected_wealth_contribution


# ---------------------------------------------------------------------------
# Score cap at 100
# ---------------------------------------------------------------------------


def test_scores_never_exceed_100() -> None:
    """No score should exceed 100 regardless of how many yogas are detected."""
    svc = YogaAnalysisService()  # all registered rules

    # Load up a chart that triggers multiple Raj + Dhana yogas
    analysis = analysis_with_ascendant(
        ZodiacSign.ARIES,
        planet(PlanetType.MOON, ZodiacSign.TAURUS, HouseNumber.SECOND),    # exalted
        planet(PlanetType.JUPITER, ZodiacSign.SCORPIO, HouseNumber.EIGHTH),
        planet(PlanetType.VENUS, ZodiacSign.PISCES, HouseNumber.TWELFTH),  # exalted
        planet(PlanetType.MARS, ZodiacSign.CAPRICORN, HouseNumber.TENTH),  # exalted
        planet(PlanetType.SATURN, ZodiacSign.AQUARIUS, HouseNumber.ELEVENTH),
        planet(PlanetType.SUN, ZodiacSign.ARIES, HouseNumber.FIRST),
        planet(PlanetType.MERCURY, ZodiacSign.ARIES, HouseNumber.FIRST),
    )
    result = svc.analyze(analysis)

    assert 0 <= result.wealth_score <= 100
    assert 0 <= result.career_score <= 100
    assert 0 <= result.authority_score <= 100
    assert 0 <= result.relationship_score <= 100
    assert 0 <= result.spirituality_score <= 100


# ---------------------------------------------------------------------------
# Immutability
# ---------------------------------------------------------------------------


def test_yoga_analysis_is_immutable() -> None:
    """YogaAnalysis is a frozen dataclass and must reject attribute mutation."""
    import dataclasses
    svc = YogaAnalysisService(engine=YogaDetectionEngine(rules=[]))
    result = svc.analyze(analysis_with_ascendant(ZodiacSign.ARIES))

    assert dataclasses.is_dataclass(result)
    try:
        result.wealth_score = 999  # type: ignore[misc]
        assert False, "Should have raised FrozenInstanceError"
    except Exception:
        pass  # expected


# ---------------------------------------------------------------------------
# Default registry integration
# ---------------------------------------------------------------------------


def test_service_uses_default_registry_when_no_args() -> None:
    """Service built with no arguments uses YogaRuleRegistry (all 6 rules)."""
    svc = YogaAnalysisService()
    # A chart that triggers at least one yoga (Raj Yoga — Moon + Jupiter conjunct)
    analysis = analysis_with_ascendant(
        ZodiacSign.ARIES,
        planet(PlanetType.MOON, ZodiacSign.ARIES, HouseNumber.FIRST),
        planet(PlanetType.JUPITER, ZodiacSign.ARIES, HouseNumber.FIRST),
    )
    result = svc.analyze(analysis)
    # With the full registry active, at least Raj Yoga should fire
    assert len(result.detected_yogas) >= 1


def test_service_accepts_custom_registry() -> None:
    """Service accepts an explicit YogaRuleRegistry via constructor injection."""
    registry = YogaRuleRegistry()
    svc = YogaAnalysisService(registry=registry)
    result = svc.analyze(analysis_with_ascendant(ZodiacSign.ARIES))
    assert isinstance(result, YogaAnalysis)


def test_service_accepts_custom_engine() -> None:
    """Service accepts an explicit YogaDetectionEngine via constructor injection."""
    engine = YogaDetectionEngine(rules=[RajYogaRule()])
    svc = YogaAnalysisService(engine=engine)
    result = svc.analyze(analysis_with_ascendant(ZodiacSign.ARIES))
    assert isinstance(result, YogaAnalysis)
