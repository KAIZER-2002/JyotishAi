"""
PromptBuilderService — converts deterministic interpretation data into a
provider-agnostic StructuredPrompt.

No LLM calls are made here.  No provider-specific keys are used.

Design
------
The service renders six ordered sections:
  1. INSTRUCTION  — system persona + task framing
  2. BIRTH_CHART  — ascendant, planet positions from Rasi chart
  3. DASHA        — current / upcoming Mahadasha sequence
  4. YOGA_SUMMARY — detected yogas with strength + per-area scores
  5. INTERPRETATION — one paragraph per InterpretationCategory
  6. USER_QUERY   — optional free-text question (appended when provided)

These sections are assembled into two PromptMessages:
  • SYSTEM  → INSTRUCTION body
  • USER    → all remaining sections concatenated

The messages tuple is the primary output consumed by LLM adapters.
"""

from datetime import datetime, timezone

from app.domain.astrology_analysis import AstrologyAnalysis
from app.domain.interpretation import InterpretationCategory, InterpretationReport
from app.domain.prompt import (
    PromptMessage,
    PromptRole,
    PromptSection,
    PromptSectionType,
    StructuredPrompt,
)
from app.domain.yoga_analysis import YogaAnalysis


# ---------------------------------------------------------------------------
# Static instruction text
# ---------------------------------------------------------------------------

_SYSTEM_INSTRUCTION = (
    "You are JyotishAI, a classical Vedic astrology expert. "
    "You interpret birth charts using the Parashari system with Lahiri ayanamsa. "
    "You reason from provided astrological data only — do not invent facts. "
    "Your tone is warm, scholarly, and precise. "
    "Provide actionable insights grounded in classical principles."
)

_CATEGORY_ORDER = (
    InterpretationCategory.PERSONALITY,
    InterpretationCategory.CAREER,
    InterpretationCategory.WEALTH,
    InterpretationCategory.RELATIONSHIPS,
    InterpretationCategory.MARRIAGE,
    InterpretationCategory.HEALTH,
    InterpretationCategory.EDUCATION,
    InterpretationCategory.SPIRITUALITY,
)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class PromptBuilderService:
    """
    Builds a StructuredPrompt from AstrologyAnalysis, YogaAnalysis, and
    InterpretationReport.

    Parameters
    ----------
    user_query:
        Optional free-text question from the user.  When provided, it is
        appended as an explicit USER_QUERY section so the LLM knows what
        to focus on.
    """

    def build(
        self,
        astrology_analysis: AstrologyAnalysis,
        yoga_analysis: YogaAnalysis,
        interpretation_report: InterpretationReport,
        user_query: str | None = None,
    ) -> StructuredPrompt:
        sections = self._build_sections(
            astrology_analysis, yoga_analysis, interpretation_report, user_query
        )
        messages = self._build_messages(sections)
        metadata = self._build_metadata(astrology_analysis)

        return StructuredPrompt(
            sections=sections,
            messages=messages,
            metadata=metadata,
        )

    # ------------------------------------------------------------------
    # Section builders
    # ------------------------------------------------------------------

    def _build_sections(
        self,
        aa: AstrologyAnalysis,
        ya: YogaAnalysis,
        ir: InterpretationReport,
        user_query: str | None,
    ) -> tuple[PromptSection, ...]:
        sections: list[PromptSection] = [
            self._instruction_section(),
            self._birth_chart_section(aa),
            self._dasha_section(aa),
            self._yoga_summary_section(ya),
            self._interpretation_section(ir),
        ]
        if user_query and user_query.strip():
            sections.append(self._user_query_section(user_query))
        return tuple(sections)

    @staticmethod
    def _instruction_section() -> PromptSection:
        return PromptSection(
            section_type=PromptSectionType.INSTRUCTION,
            heading="System Instruction",
            body=_SYSTEM_INSTRUCTION,
        )

    @staticmethod
    def _birth_chart_section(aa: AstrologyAnalysis) -> PromptSection:
        chart = aa.birth_chart
        asc = chart.ascendant
        lines: list[str] = [
            f"Ascendant (Lagna): {asc.zodiac_sign.value} "
            f"({asc.degree_within_sign:.2f}°), Nakshatra: {asc.nakshatra.value}",
        ]
        for planet in sorted(chart.planets, key=lambda p: p.planet.value):
            retro = " [R]" if planet.retrograde else ""
            house = (
                f"House {planet.house_number.value}"
                if planet.house_number is not None
                else "house unknown"
            )
            lines.append(
                f"  {planet.planet.value}: {planet.zodiac_sign.value} "
                f"{planet.degree_within_sign:.2f}°{retro} | {house} | "
                f"Nakshatra: {planet.nakshatra.value}"
            )

        return PromptSection(
            section_type=PromptSectionType.BIRTH_CHART,
            heading="Birth Chart (Rasi)",
            body="\n".join(lines),
        )

    @staticmethod
    def _dasha_section(aa: AstrologyAnalysis) -> PromptSection:
        if not aa.vimshottari_dashas:
            return PromptSection(
                section_type=PromptSectionType.DASHA,
                heading="Vimshottari Dasha Sequence",
                body="No Dasha data available.",
            )

        lines: list[str] = []
        for maha in aa.vimshottari_dashas[:3]:   # show up to 3 Mahadashas
            start = maha.start_datetime.strftime("%Y-%m-%d")
            end   = maha.end_datetime.strftime("%Y-%m-%d")
            lines.append(f"  {maha.lord.value} Mahadasha: {start} → {end}")
            for antar in maha.sub_periods[:3]:   # show up to 3 Antardashas each
                a_start = antar.start_datetime.strftime("%Y-%m-%d")
                a_end   = antar.end_datetime.strftime("%Y-%m-%d")
                lines.append(
                    f"    └─ {antar.lord.value} Antardasha: {a_start} → {a_end}"
                )

        return PromptSection(
            section_type=PromptSectionType.DASHA,
            heading="Vimshottari Dasha Sequence",
            body="\n".join(lines),
        )

    @staticmethod
    def _yoga_summary_section(ya: YogaAnalysis) -> PromptSection:
        lines: list[str] = []

        # Detected yogas
        if ya.detected_yogas:
            lines.append("Detected Yogas:")
            for result in ya.strongest_yogas:
                lines.append(
                    f"  • {result.yoga.name} [{result.strength.value}]"
                    + (f" — {result.yoga.description}" if result.yoga.description else "")
                )
        else:
            lines.append("No significant Yogas detected.")

        # Life-area scores
        lines.append("")
        lines.append("Life-Area Scores (0–100):")
        lines.append(f"  Wealth:        {ya.wealth_score}")
        lines.append(f"  Career:        {ya.career_score}")
        lines.append(f"  Authority:     {ya.authority_score}")
        lines.append(f"  Relationships: {ya.relationship_score}")
        lines.append(f"  Spirituality:  {ya.spirituality_score}")

        return PromptSection(
            section_type=PromptSectionType.YOGA_SUMMARY,
            heading="Yoga Analysis Summary",
            body="\n".join(lines),
        )

    @staticmethod
    def _interpretation_section(ir: InterpretationReport) -> PromptSection:
        lines: list[str] = []
        for category in _CATEGORY_ORDER:
            items = ir.by_category(category)
            if not items:
                continue
            interp = items[0]
            lines.append(
                f"{category.value} [{interp.severity.value} / "
                f"{interp.sentiment.value}] (score: {interp.score})"
            )
            lines.append(f"  {interp.title}")
            lines.append(f"  {interp.summary}")
            if interp.evidence:
                for ev in interp.evidence:
                    lines.append(f"  Evidence: {ev.source} — {ev.detail}")
            lines.append("")

        return PromptSection(
            section_type=PromptSectionType.INTERPRETATION,
            heading="Deterministic Interpretation",
            body="\n".join(lines).rstrip(),
        )

    @staticmethod
    def _user_query_section(user_query: str) -> PromptSection:
        return PromptSection(
            section_type=PromptSectionType.USER_QUERY,
            heading="User Question",
            body=user_query.strip(),
        )

    # ------------------------------------------------------------------
    # Message assembly
    # ------------------------------------------------------------------

    @staticmethod
    def _build_messages(
        sections: tuple[PromptSection, ...],
    ) -> tuple[PromptMessage, ...]:
        system_body = ""
        user_parts: list[str] = []

        for section in sections:
            if section.section_type is PromptSectionType.INSTRUCTION:
                system_body = section.body
            else:
                user_parts.append(f"## {section.heading}\n{section.body}")

        messages: list[PromptMessage] = []
        if system_body:
            messages.append(
                PromptMessage(role=PromptRole.SYSTEM, content=system_body)
            )
        if user_parts:
            messages.append(
                PromptMessage(
                    role=PromptRole.USER,
                    content="\n\n".join(user_parts),
                )
            )
        return tuple(messages)

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    @staticmethod
    def _build_metadata(aa: AstrologyAnalysis) -> tuple[tuple[str, str], ...]:
        asc = aa.birth_chart.ascendant
        return (
            ("ascendant_sign",   asc.zodiac_sign.value),
            ("ascendant_nakshatra", asc.nakshatra.value),
            ("planet_count",    str(len(aa.birth_chart.planets))),
            ("dasha_count",     str(len(aa.vimshottari_dashas))),
            ("builder_version", "1.0"),
        )
