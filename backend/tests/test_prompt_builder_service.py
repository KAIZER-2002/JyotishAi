"""
Comprehensive tests for PromptBuilderService and the StructuredPrompt domain.

Coverage:
  - Returns a StructuredPrompt instance
  - Sections are present with correct section types
  - INSTRUCTION section is always the first section
  - USER_QUERY section is only added when a query is provided
  - System message uses INSTRUCTION body
  - User message contains all non-instruction sections
  - to_chat_dicts() renders {"role", "content"} dicts
  - Planet positions appear in the BIRTH_CHART section
  - Yoga names appear in the YOGA_SUMMARY section
  - Interpretation data appears in the INTERPRETATION section
  - Dasha data appears in the DASHA section
  - Metadata keys are populated correctly
  - StructuredPrompt helpers: sections_by_type, messages_by_role, get_metadata
  - Empty dasha list renders gracefully
  - Retrograde flag appears in birth chart section
  - Determinism: same input → same output
"""

from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.domain.ascendant import Ascendant
from app.domain.astrology_analysis import AstrologyAnalysis
from app.domain.chart import Chart
from app.domain.dasha import Antardasha, DashaLord, DashaLevel, Mahadasha
from app.domain.house import House
from app.domain.house_number import HouseNumber
from app.domain.interpretation import (
    Interpretation,
    InterpretationCategory,
    InterpretationEvidence,
    InterpretationReport,
    InterpretationSentiment,
    InterpretationSeverity,
)
from app.domain.nakshatra import Nakshatra
from app.domain.planet import Planet
from app.domain.planet_type import PlanetType
from app.domain.prompt import (
    PromptRole,
    PromptSectionType,
    StructuredPrompt,
)
from app.domain.yoga import Yoga, YogaResult, YogaStrength, YogaType
from app.domain.yoga_analysis import YogaAnalysis
from app.domain.zodiac import ZodiacSign
from app.services.astrology.prompt_builder_service import PromptBuilderService


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

_DT_START = datetime(2010, 1, 1, tzinfo=timezone.utc)
_DT_END   = datetime(2017, 1, 1, tzinfo=timezone.utc)
_DT_A_END = datetime(2011, 6, 1, tzinfo=timezone.utc)


def _planet(
    planet_type: PlanetType,
    sign: ZodiacSign,
    house: HouseNumber,
    retrograde: bool = False,
) -> Planet:
    return Planet(
        planet=planet_type,
        longitude=float(list(ZodiacSign).index(sign) * 30),
        latitude=0.0,
        zodiac_sign=sign,
        house_number=house,
        retrograde=retrograde,
        nakshatra=Nakshatra.ASHWINI,
        pada=1,
        degree_within_sign=5.0,
    )


def _chart(*planets: Planet, sign: ZodiacSign = ZodiacSign.ARIES) -> Chart:
    asc_idx = list(ZodiacSign).index(sign)
    return Chart(
        ascendant=Ascendant(
            zodiac_sign=sign,
            longitude=float(asc_idx * 30),
            nakshatra=Nakshatra.ASHWINI,
            pada=1,
            degree_within_sign=3.14,
        ),
        planets=planets,
        houses=tuple(
            House(
                house_number=hn,
                start_longitude=float(((asc_idx + i) % 12) * 30),
                end_longitude=float(((asc_idx + i + 1) % 12) * 30),
            )
            for i, hn in enumerate(HouseNumber)
        ),
    )


def _mahadasha_with_antardasha() -> Mahadasha:
    antar = Antardasha(
        lord=DashaLord.MOON,
        start_datetime=_DT_START,
        end_datetime=_DT_A_END,
    )
    return Mahadasha(
        lord=DashaLord.KETU,
        start_datetime=_DT_START,
        end_datetime=_DT_END,
        sub_periods=(antar,),
    )


def _empty_chart() -> Chart:
    return _chart()


def _analysis(
    *planets: Planet,
    dashas: tuple = (),
    sign: ZodiacSign = ZodiacSign.ARIES,
) -> AstrologyAnalysis:
    birth = _chart(*planets, sign=sign)
    empty = _chart(sign=ZodiacSign.ARIES)
    return AstrologyAnalysis(
        birth_chart=birth,
        navamsa_chart=empty,
        dasamsa_chart=empty,
        shastiamsa_chart=empty,
        vimshottari_dashas=dashas,
    )


def _yoga_result(yoga_type: YogaType, strength: YogaStrength) -> YogaResult:
    return YogaResult(
        yoga=Yoga(
            key=f"test_{yoga_type.name.lower()}",
            name=yoga_type.value,
            yoga_type=yoga_type,
            description=f"Test {yoga_type.value} description.",
        ),
        strength=strength,
        involved_planets=(),
        involved_houses=(),
        evidence=("Test evidence.",),
    )


def _yoga_analysis(
    *,
    wealth: int = 0,
    career: int = 0,
    authority: int = 0,
    relationship: int = 0,
    spirituality: int = 0,
    yogas: tuple = (),
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


def _interpretation(
    category: InterpretationCategory,
    severity: InterpretationSeverity = InterpretationSeverity.MODERATE,
    score: int = 50,
) -> Interpretation:
    return Interpretation(
        category=category,
        title=f"{category.value} title",
        summary=f"{category.value} summary.",
        severity=severity,
        sentiment=InterpretationSentiment.POSITIVE,
        score=score,
        evidence=(
            InterpretationEvidence(
                source="Test Yoga",
                detail="Test evidence detail.",
            ),
        ),
    )


def _report(*categories: InterpretationCategory) -> InterpretationReport:
    return InterpretationReport(
        interpretations=tuple(_interpretation(c) for c in categories)
    )


def _full_report() -> InterpretationReport:
    return _report(*InterpretationCategory)


# ---------------------------------------------------------------------------
# Return type
# ---------------------------------------------------------------------------


def test_build_returns_structured_prompt() -> None:
    svc = PromptBuilderService()
    result = svc.build(_analysis(), _yoga_analysis(), _full_report())
    assert isinstance(result, StructuredPrompt)


# ---------------------------------------------------------------------------
# Section presence and order
# ---------------------------------------------------------------------------


def test_sections_contain_expected_types_without_query() -> None:
    svc = PromptBuilderService()
    result = svc.build(_analysis(), _yoga_analysis(), _full_report())
    types = [s.section_type for s in result.sections]
    assert PromptSectionType.INSTRUCTION    in types
    assert PromptSectionType.BIRTH_CHART   in types
    assert PromptSectionType.DASHA         in types
    assert PromptSectionType.YOGA_SUMMARY  in types
    assert PromptSectionType.INTERPRETATION in types
    assert PromptSectionType.USER_QUERY    not in types


def test_first_section_is_always_instruction() -> None:
    svc = PromptBuilderService()
    result = svc.build(_analysis(), _yoga_analysis(), _full_report())
    assert result.sections[0].section_type is PromptSectionType.INSTRUCTION


def test_user_query_section_added_when_provided() -> None:
    svc = PromptBuilderService()
    result = svc.build(
        _analysis(), _yoga_analysis(), _full_report(),
        user_query="What is my career outlook?"
    )
    types = [s.section_type for s in result.sections]
    assert PromptSectionType.USER_QUERY in types


def test_user_query_section_absent_for_blank_string() -> None:
    svc = PromptBuilderService()
    result = svc.build(_analysis(), _yoga_analysis(), _full_report(), user_query="   ")
    types = [s.section_type for s in result.sections]
    assert PromptSectionType.USER_QUERY not in types


def test_user_query_body_matches_input() -> None:
    svc = PromptBuilderService()
    query = "Tell me about my wealth prospects."
    result = svc.build(_analysis(), _yoga_analysis(), _full_report(), user_query=query)
    q_sections = result.sections_by_type(PromptSectionType.USER_QUERY)
    assert len(q_sections) == 1
    assert q_sections[0].body == query.strip()


# ---------------------------------------------------------------------------
# Messages
# ---------------------------------------------------------------------------


def test_exactly_two_messages_produced() -> None:
    svc = PromptBuilderService()
    result = svc.build(_analysis(), _yoga_analysis(), _full_report())
    assert len(result.messages) == 2


def test_system_message_contains_instruction_text() -> None:
    svc = PromptBuilderService()
    result = svc.build(_analysis(), _yoga_analysis(), _full_report())
    system_msgs = result.messages_by_role(PromptRole.SYSTEM)
    assert len(system_msgs) == 1
    assert "JyotishAI" in system_msgs[0].content


def test_user_message_contains_birth_chart_heading() -> None:
    svc = PromptBuilderService()
    result = svc.build(_analysis(), _yoga_analysis(), _full_report())
    user_msgs = result.messages_by_role(PromptRole.USER)
    assert len(user_msgs) == 1
    assert "Birth Chart" in user_msgs[0].content


def test_user_message_contains_yoga_summary_heading() -> None:
    svc = PromptBuilderService()
    result = svc.build(_analysis(), _yoga_analysis(), _full_report())
    user_msg = result.messages_by_role(PromptRole.USER)[0]
    assert "Yoga" in user_msg.content


def test_user_message_contains_interpretation_heading() -> None:
    svc = PromptBuilderService()
    result = svc.build(_analysis(), _yoga_analysis(), _full_report())
    user_msg = result.messages_by_role(PromptRole.USER)[0]
    assert "Interpretation" in user_msg.content


# ---------------------------------------------------------------------------
# to_chat_dicts
# ---------------------------------------------------------------------------


def test_to_chat_dicts_returns_correct_keys() -> None:
    svc = PromptBuilderService()
    result = svc.build(_analysis(), _yoga_analysis(), _full_report())
    dicts = result.to_chat_dicts()
    assert len(dicts) == 2
    for d in dicts:
        assert "role" in d
        assert "content" in d


def test_to_chat_dicts_role_values_are_strings() -> None:
    svc = PromptBuilderService()
    result = svc.build(_analysis(), _yoga_analysis(), _full_report())
    dicts = result.to_chat_dicts()
    for d in dicts:
        assert isinstance(d["role"], str)
        assert d["role"] in ("system", "user", "assistant")


# ---------------------------------------------------------------------------
# Birth chart content
# ---------------------------------------------------------------------------


def test_planet_name_appears_in_birth_chart_section() -> None:
    svc = PromptBuilderService()
    result = svc.build(
        _analysis(_planet(PlanetType.JUPITER, ZodiacSign.CANCER, HouseNumber.FOURTH)),
        _yoga_analysis(),
        _full_report(),
    )
    bc_section = result.sections_by_type(PromptSectionType.BIRTH_CHART)[0]
    assert "Jupiter" in bc_section.body


def test_zodiac_sign_appears_in_birth_chart_section() -> None:
    svc = PromptBuilderService()
    result = svc.build(
        _analysis(
            _planet(PlanetType.VENUS, ZodiacSign.PISCES, HouseNumber.TWELFTH),
            sign=ZodiacSign.ARIES,
        ),
        _yoga_analysis(),
        _full_report(),
    )
    bc_section = result.sections_by_type(PromptSectionType.BIRTH_CHART)[0]
    assert "Pisces" in bc_section.body


def test_retrograde_flag_in_birth_chart_section() -> None:
    svc = PromptBuilderService()
    result = svc.build(
        _analysis(
            _planet(PlanetType.SATURN, ZodiacSign.LIBRA, HouseNumber.SEVENTH, retrograde=True)
        ),
        _yoga_analysis(),
        _full_report(),
    )
    bc_section = result.sections_by_type(PromptSectionType.BIRTH_CHART)[0]
    assert "[R]" in bc_section.body


def test_ascendant_sign_in_birth_chart_section() -> None:
    svc = PromptBuilderService()
    result = svc.build(
        _analysis(sign=ZodiacSign.SCORPIO),
        _yoga_analysis(),
        _full_report(),
    )
    bc_section = result.sections_by_type(PromptSectionType.BIRTH_CHART)[0]
    assert "Scorpio" in bc_section.body


# ---------------------------------------------------------------------------
# Yoga summary content
# ---------------------------------------------------------------------------


def test_detected_yoga_name_in_yoga_summary() -> None:
    raj = _yoga_result(YogaType.RAJ_YOGA, YogaStrength.STRONG)
    svc = PromptBuilderService()
    result = svc.build(
        _analysis(),
        _yoga_analysis(career=60, yogas=(raj,)),
        _full_report(),
    )
    yoga_section = result.sections_by_type(PromptSectionType.YOGA_SUMMARY)[0]
    assert "Raj Yoga" in yoga_section.body


def test_no_yogas_message_when_empty() -> None:
    svc = PromptBuilderService()
    result = svc.build(_analysis(), _yoga_analysis(), _full_report())
    yoga_section = result.sections_by_type(PromptSectionType.YOGA_SUMMARY)[0]
    assert "No significant Yogas" in yoga_section.body


def test_life_area_scores_in_yoga_summary() -> None:
    svc = PromptBuilderService()
    ya = _yoga_analysis(wealth=42, career=77)
    result = svc.build(_analysis(), ya, _full_report())
    yoga_section = result.sections_by_type(PromptSectionType.YOGA_SUMMARY)[0]
    assert "42" in yoga_section.body
    assert "77" in yoga_section.body


# ---------------------------------------------------------------------------
# Interpretation content
# ---------------------------------------------------------------------------


def test_category_label_in_interpretation_section() -> None:
    svc = PromptBuilderService()
    result = svc.build(_analysis(), _yoga_analysis(), _full_report())
    interp_section = result.sections_by_type(PromptSectionType.INTERPRETATION)[0]
    assert "Career" in interp_section.body


def test_evidence_source_in_interpretation_section() -> None:
    report = _full_report()
    svc = PromptBuilderService()
    result = svc.build(_analysis(), _yoga_analysis(), report)
    interp_section = result.sections_by_type(PromptSectionType.INTERPRETATION)[0]
    assert "Test Yoga" in interp_section.body


# ---------------------------------------------------------------------------
# Dasha content
# ---------------------------------------------------------------------------


def test_dasha_lord_in_dasha_section() -> None:
    maha = _mahadasha_with_antardasha()
    svc = PromptBuilderService()
    result = svc.build(_analysis(dashas=(maha,)), _yoga_analysis(), _full_report())
    dasha_section = result.sections_by_type(PromptSectionType.DASHA)[0]
    assert "Ketu" in dasha_section.body


def test_antardasha_lord_in_dasha_section() -> None:
    maha = _mahadasha_with_antardasha()
    svc = PromptBuilderService()
    result = svc.build(_analysis(dashas=(maha,)), _yoga_analysis(), _full_report())
    dasha_section = result.sections_by_type(PromptSectionType.DASHA)[0]
    assert "Moon" in dasha_section.body


def test_empty_dasha_renders_gracefully() -> None:
    svc = PromptBuilderService()
    result = svc.build(_analysis(dashas=()), _yoga_analysis(), _full_report())
    dasha_section = result.sections_by_type(PromptSectionType.DASHA)[0]
    assert "No Dasha data" in dasha_section.body


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------


def test_metadata_ascendant_sign_key() -> None:
    svc = PromptBuilderService()
    result = svc.build(_analysis(sign=ZodiacSign.TAURUS), _yoga_analysis(), _full_report())
    assert result.get_metadata("ascendant_sign") == "Taurus"


def test_metadata_planet_count() -> None:
    svc = PromptBuilderService()
    planets = (
        _planet(PlanetType.SUN, ZodiacSign.ARIES, HouseNumber.FIRST),
        _planet(PlanetType.MOON, ZodiacSign.TAURUS, HouseNumber.SECOND),
    )
    result = svc.build(_analysis(*planets), _yoga_analysis(), _full_report())
    assert result.get_metadata("planet_count") == "2"


def test_metadata_missing_key_returns_none() -> None:
    svc = PromptBuilderService()
    result = svc.build(_analysis(), _yoga_analysis(), _full_report())
    assert result.get_metadata("nonexistent_key") is None


def test_metadata_builder_version_present() -> None:
    svc = PromptBuilderService()
    result = svc.build(_analysis(), _yoga_analysis(), _full_report())
    assert result.get_metadata("builder_version") is not None


# ---------------------------------------------------------------------------
# StructuredPrompt helpers
# ---------------------------------------------------------------------------


def test_sections_by_type_returns_correct_subset() -> None:
    svc = PromptBuilderService()
    result = svc.build(_analysis(), _yoga_analysis(), _full_report())
    bc_sections = result.sections_by_type(PromptSectionType.BIRTH_CHART)
    assert len(bc_sections) == 1
    assert bc_sections[0].section_type is PromptSectionType.BIRTH_CHART


def test_messages_by_role_returns_correct_subset() -> None:
    svc = PromptBuilderService()
    result = svc.build(_analysis(), _yoga_analysis(), _full_report())
    system_msgs = result.messages_by_role(PromptRole.SYSTEM)
    assert all(m.role is PromptRole.SYSTEM for m in system_msgs)


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_build_is_deterministic() -> None:
    svc = PromptBuilderService()
    aa  = _analysis(_planet(PlanetType.JUPITER, ZodiacSign.CANCER, HouseNumber.FOURTH))
    ya  = _yoga_analysis(career=55, yogas=(_yoga_result(YogaType.RAJ_YOGA, YogaStrength.STRONG),))
    ir  = _full_report()

    r1 = svc.build(aa, ya, ir, user_query="What are my prospects?")
    r2 = svc.build(aa, ya, ir, user_query="What are my prospects?")
    assert r1.sections  == r2.sections
    assert r1.messages  == r2.messages
    assert r1.metadata  == r2.metadata
