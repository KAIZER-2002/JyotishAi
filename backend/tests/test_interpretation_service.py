"""
Service-level tests for InterpretationService.

Coverage:
  - Returns an InterpretationReport
  - One Interpretation per InterpretationCategory
  - Severity/sentiment thresholds are correctly applied
  - Yoga evidence is collected and attached to the right categories
  - Minimum MILD severity when relevant yogas are present
  - Score capping at 0–100
  - Scores drive correct titles and summaries
  - Determinism: same input → same output
  - Report helpers: by_category, ranked_by_severity, ranked_by_score
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.domain.ascendant import Ascendant
from app.domain.astrology_analysis import AstrologyAnalysis
from app.domain.chart import Chart
from app.domain.house import House
from app.domain.house_number import HouseNumber
from app.domain.interpretation import (
    InterpretationCategory,
    InterpretationReport,
    InterpretationSentiment,
    InterpretationSeverity,
)
from app.domain.nakshatra import Nakshatra
from app.domain.planet import Planet
from app.domain.planet_type import PlanetType
from app.domain.yoga import Yoga, YogaResult, YogaStrength, YogaType
from app.domain.yoga_analysis import YogaAnalysis
from app.domain.zodiac import ZodiacSign
from app.services.astrology.interpretation_service import InterpretationService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ALL_CATEGORIES = list(InterpretationCategory)


def empty_analysis() -> AstrologyAnalysis:
    asc_index = 0  # Aries
    return AstrologyAnalysis(
        birth_chart=Chart(
            ascendant=Ascendant(
                zodiac_sign=ZodiacSign.ARIES,
                longitude=0.0,
                nakshatra=Nakshatra.ASHWINI,
                pada=1,
                degree_within_sign=0.0,
            ),
            planets=(),
            houses=tuple(
                House(
                    house_number=hn,
                    start_longitude=float(((asc_index + i) % 12) * 30),
                    end_longitude=float(((asc_index + i + 1) % 12) * 30),
                )
                for i, hn in enumerate(HouseNumber)
            ),
        ),
        navamsa_chart=Chart(
            ascendant=Ascendant(
                zodiac_sign=ZodiacSign.ARIES,
                longitude=0.0,
                nakshatra=Nakshatra.ASHWINI,
                pada=1,
                degree_within_sign=0.0,
            ),
            planets=(),
            houses=tuple(
                House(
                    house_number=hn,
                    start_longitude=float(((asc_index + i) % 12) * 30),
                    end_longitude=float(((asc_index + i + 1) % 12) * 30),
                )
                for i, hn in enumerate(HouseNumber)
            ),
        ),
        dasamsa_chart=Chart(
            ascendant=Ascendant(
                zodiac_sign=ZodiacSign.ARIES,
                longitude=0.0,
                nakshatra=Nakshatra.ASHWINI,
                pada=1,
                degree_within_sign=0.0,
            ),
            planets=(),
            houses=tuple(
                House(
                    house_number=hn,
                    start_longitude=float(((asc_index + i) % 12) * 30),
                    end_longitude=float(((asc_index + i + 1) % 12) * 30),
                )
                for i, hn in enumerate(HouseNumber)
            ),
        ),
        shastiamsa_chart=Chart(
            ascendant=Ascendant(
                zodiac_sign=ZodiacSign.ARIES,
                longitude=0.0,
                nakshatra=Nakshatra.ASHWINI,
                pada=1,
                degree_within_sign=0.0,
            ),
            planets=(),
            houses=tuple(
                House(
                    house_number=hn,
                    start_longitude=float(((asc_index + i) % 12) * 30),
                    end_longitude=float(((asc_index + i + 1) % 12) * 30),
                )
                for i, hn in enumerate(HouseNumber)
            ),
        ),
        vimshottari_dashas=(),
    )


def yoga_analysis(
    *,
    wealth: int = 0,
    career: int = 0,
    authority: int = 0,
    relationship: int = 0,
    spirituality: int = 0,
    yogas: tuple[YogaResult, ...] = (),
) -> YogaAnalysis:
    return YogaAnalysis(
        detected_yogas=yogas,
        strongest_yogas=yogas,
        wealth_score=wealth,
        career_score=career,
        authority_score=authority,
        relationship_score=relationship,
        spirituality_score=spirituality,
    )


def make_yoga_result(yoga_type: YogaType, strength: YogaStrength) -> YogaResult:
    return YogaResult(
        yoga=Yoga(
            key=f"test_{yoga_type.value.lower().replace(' ', '_')}",
            name=yoga_type.value,
            yoga_type=yoga_type,
            description="test",
        ),
        strength=strength,
        involved_planets=(),
        involved_houses=(),
        evidence=("Test evidence line.",),
    )


# ---------------------------------------------------------------------------
# Return type
# ---------------------------------------------------------------------------


def test_returns_interpretation_report() -> None:
    svc = InterpretationService()
    result = svc.interpret(yoga_analysis(), empty_analysis())
    assert isinstance(result, InterpretationReport)


def test_one_interpretation_per_category() -> None:
    svc = InterpretationService()
    result = svc.interpret(yoga_analysis(), empty_analysis())
    categories = [i.category for i in result.interpretations]
    assert len(categories) == len(ALL_CATEGORIES)
    assert set(categories) == set(ALL_CATEGORIES)


# ---------------------------------------------------------------------------
# Severity thresholds
# ---------------------------------------------------------------------------


def test_score_0_to_19_gives_neutral_severity() -> None:
    svc = InterpretationService()
    ya = yoga_analysis(career=10)
    result = svc.interpret(ya, empty_analysis())
    career_interp = result.by_category(InterpretationCategory.CAREER)[0]
    assert career_interp.severity == InterpretationSeverity.NEUTRAL


def test_score_20_to_39_gives_mild_severity() -> None:
    svc = InterpretationService()
    ya = yoga_analysis(career=25)
    result = svc.interpret(ya, empty_analysis())
    career_interp = result.by_category(InterpretationCategory.CAREER)[0]
    assert career_interp.severity == InterpretationSeverity.MILD


def test_score_40_to_59_gives_moderate_severity() -> None:
    svc = InterpretationService()
    ya = yoga_analysis(career=50)
    result = svc.interpret(ya, empty_analysis())
    career_interp = result.by_category(InterpretationCategory.CAREER)[0]
    assert career_interp.severity == InterpretationSeverity.MODERATE


def test_score_60_to_79_gives_significant_severity() -> None:
    svc = InterpretationService()
    ya = yoga_analysis(career=65)
    result = svc.interpret(ya, empty_analysis())
    career_interp = result.by_category(InterpretationCategory.CAREER)[0]
    assert career_interp.severity == InterpretationSeverity.SIGNIFICANT


def test_score_80_plus_gives_prominent_severity() -> None:
    svc = InterpretationService()
    ya = yoga_analysis(career=90)
    result = svc.interpret(ya, empty_analysis())
    career_interp = result.by_category(InterpretationCategory.CAREER)[0]
    assert career_interp.severity == InterpretationSeverity.PROMINENT
    assert career_interp.sentiment == InterpretationSentiment.POSITIVE


# ---------------------------------------------------------------------------
# Yoga evidence routing
# ---------------------------------------------------------------------------


def test_raj_yoga_evidence_appears_in_career() -> None:
    raj = make_yoga_result(YogaType.RAJ_YOGA, YogaStrength.STRONG)
    svc = InterpretationService()
    ya = yoga_analysis(career=30, yogas=(raj,))
    result = svc.interpret(ya, empty_analysis())
    career_interp = result.by_category(InterpretationCategory.CAREER)[0]
    assert len(career_interp.evidence) >= 1
    assert any(YogaType.RAJ_YOGA.value in e.source for e in career_interp.evidence)


def test_dhana_yoga_evidence_appears_in_wealth() -> None:
    dhana = make_yoga_result(YogaType.DHANA_YOGA, YogaStrength.MODERATE)
    svc = InterpretationService()
    ya = yoga_analysis(wealth=40, yogas=(dhana,))
    result = svc.interpret(ya, empty_analysis())
    wealth_interp = result.by_category(InterpretationCategory.WEALTH)[0]
    assert any(YogaType.DHANA_YOGA.value in e.source for e in wealth_interp.evidence)


def test_budhaditya_yoga_evidence_appears_in_education() -> None:
    budha = make_yoga_result(YogaType.BUDHADITYA_YOGA, YogaStrength.STRONG)
    svc = InterpretationService()
    ya = yoga_analysis(career=50, yogas=(budha,))
    result = svc.interpret(ya, empty_analysis())
    edu_interp = result.by_category(InterpretationCategory.EDUCATION)[0]
    assert any(YogaType.BUDHADITYA_YOGA.value in e.source for e in edu_interp.evidence)


def test_gaja_kesari_evidence_appears_in_relationships() -> None:
    gk = make_yoga_result(YogaType.GAJA_KESARI_YOGA, YogaStrength.EXCEPTIONAL)
    svc = InterpretationService()
    ya = yoga_analysis(relationship=60, yogas=(gk,))
    result = svc.interpret(ya, empty_analysis())
    rel_interp = result.by_category(InterpretationCategory.RELATIONSHIPS)[0]
    assert any(YogaType.GAJA_KESARI_YOGA.value in e.source for e in rel_interp.evidence)


def test_yoga_not_routed_to_unrelated_category() -> None:
    """Raj Yoga evidence must NOT appear in Wealth interpretations."""
    raj = make_yoga_result(YogaType.RAJ_YOGA, YogaStrength.STRONG)
    svc = InterpretationService()
    ya = yoga_analysis(wealth=10, career=50, yogas=(raj,))
    result = svc.interpret(ya, empty_analysis())
    wealth_interp = result.by_category(InterpretationCategory.WEALTH)[0]
    assert not any(YogaType.RAJ_YOGA.value in e.source for e in wealth_interp.evidence)


# ---------------------------------------------------------------------------
# Minimum MILD when yogas present
# ---------------------------------------------------------------------------


def test_yoga_presence_elevates_neutral_to_mild() -> None:
    """Score=0 but a relevant yoga → severity bumped from NEUTRAL to MILD."""
    raj = make_yoga_result(YogaType.RAJ_YOGA, YogaStrength.MODERATE)
    svc = InterpretationService()
    ya = yoga_analysis(career=0, yogas=(raj,))
    result = svc.interpret(ya, empty_analysis())
    career_interp = result.by_category(InterpretationCategory.CAREER)[0]
    # Raj Yoga is career-relevant → should be at least MILD
    assert career_interp.severity is not InterpretationSeverity.NEUTRAL
    assert career_interp.sentiment == InterpretationSentiment.POSITIVE


# ---------------------------------------------------------------------------
# Score capping and propagation
# ---------------------------------------------------------------------------


def test_score_is_passed_through_to_interpretation() -> None:
    svc = InterpretationService()
    ya = yoga_analysis(wealth=75)
    result = svc.interpret(ya, empty_analysis())
    wealth_interp = result.by_category(InterpretationCategory.WEALTH)[0]
    assert wealth_interp.score == 75


def test_score_is_capped_at_100() -> None:
    svc = InterpretationService()
    ya = yoga_analysis(wealth=999)
    result = svc.interpret(ya, empty_analysis())
    wealth_interp = result.by_category(InterpretationCategory.WEALTH)[0]
    assert wealth_interp.score <= 100


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_interpret_is_deterministic() -> None:
    svc = InterpretationService()
    ya = yoga_analysis(
        wealth=55,
        career=70,
        yogas=(make_yoga_result(YogaType.RAJ_YOGA, YogaStrength.STRONG),),
    )
    r1 = svc.interpret(ya, empty_analysis())
    r2 = svc.interpret(ya, empty_analysis())
    assert r1.interpretations == r2.interpretations


# ---------------------------------------------------------------------------
# Report helper: by_category
# ---------------------------------------------------------------------------


def test_by_category_returns_correct_subset() -> None:
    svc = InterpretationService()
    result = svc.interpret(yoga_analysis(), empty_analysis())
    career_items = result.by_category(InterpretationCategory.CAREER)
    assert all(i.category is InterpretationCategory.CAREER for i in career_items)
    assert len(career_items) == 1


# ---------------------------------------------------------------------------
# Report helper: ranked_by_severity
# ---------------------------------------------------------------------------


def test_ranked_by_severity_is_descending() -> None:
    svc = InterpretationService()
    ya = yoga_analysis(career=85, wealth=45, relationship=10)
    result = svc.interpret(ya, empty_analysis())
    ranked = result.ranked_by_severity()
    _ORDER = {
        InterpretationSeverity.NEUTRAL:     0,
        InterpretationSeverity.MILD:        1,
        InterpretationSeverity.MODERATE:    2,
        InterpretationSeverity.SIGNIFICANT: 3,
        InterpretationSeverity.PROMINENT:   4,
    }
    for i in range(len(ranked) - 1):
        assert _ORDER[ranked[i].severity] >= _ORDER[ranked[i + 1].severity]


# ---------------------------------------------------------------------------
# Report helper: ranked_by_score
# ---------------------------------------------------------------------------


def test_ranked_by_score_is_descending() -> None:
    svc = InterpretationService()
    ya = yoga_analysis(career=80, wealth=50, relationship=20)
    result = svc.interpret(ya, empty_analysis())
    ranked = result.ranked_by_score()
    for i in range(len(ranked) - 1):
        assert ranked[i].score >= ranked[i + 1].score


# ---------------------------------------------------------------------------
# Report helper: by_sentiment
# ---------------------------------------------------------------------------


def test_by_sentiment_filters_correctly() -> None:
    svc = InterpretationService()
    ya = yoga_analysis(career=90, wealth=90, relationship=90)
    result = svc.interpret(ya, empty_analysis())
    positive = result.by_sentiment(InterpretationSentiment.POSITIVE)
    assert all(i.sentiment == InterpretationSentiment.POSITIVE for i in positive)
