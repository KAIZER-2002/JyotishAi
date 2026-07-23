"""
InterpretationService — deterministic, rule-based astrology interpretation.

Consumes AstrologyAnalysis + YogaAnalysis and produces an InterpretationReport.
No AI, no LLM, no external I/O.

Design
------
Each life-area category is handled by a private _interpret_<category> method
that:
  1. Reads the relevant pre-computed score from YogaAnalysis.
  2. Collects yoga-level evidence from YogaAnalysis.detected_yogas.
  3. Applies a deterministic threshold table to assign severity and sentiment.
  4. Returns a single Interpretation for that category.

Score → Severity mapping (shared across all categories):
    0–19  → NEUTRAL   / NEUTRAL
   20–39  → MILD      / NEUTRAL  (slightly favourable baseline)
   40–59  → MODERATE  / POSITIVE
   60–79  → SIGNIFICANT / POSITIVE
   80–100 → PROMINENT / POSITIVE

A category with relevant detected yogas always gets at least MILD severity
and POSITIVE sentiment, regardless of score, so that named yogas are never
silently omitted.
"""

from app.domain.astrology_analysis import AstrologyAnalysis
from app.domain.interpretation import (
    Interpretation,
    InterpretationCategory,
    InterpretationEvidence,
    InterpretationReport,
    InterpretationSentiment,
    InterpretationSeverity,
)
from app.domain.yoga import YogaResult, YogaStrength, YogaType
from app.domain.yoga_analysis import YogaAnalysis


# ---------------------------------------------------------------------------
# Threshold tables
# ---------------------------------------------------------------------------

# (min_score_inclusive, InterpretationSeverity, InterpretationSentiment)
# Evaluated top-down; first match wins.
_SCORE_THRESHOLDS: tuple[
    tuple[int, InterpretationSeverity, InterpretationSentiment], ...
] = (
    (80, InterpretationSeverity.PROMINENT,    InterpretationSentiment.POSITIVE),
    (60, InterpretationSeverity.SIGNIFICANT,  InterpretationSentiment.POSITIVE),
    (40, InterpretationSeverity.MODERATE,     InterpretationSentiment.POSITIVE),
    (20, InterpretationSeverity.MILD,         InterpretationSentiment.NEUTRAL),
    (0,  InterpretationSeverity.NEUTRAL,      InterpretationSentiment.NEUTRAL),
)

# YogaType → set of categories that yoga contributes evidence for
_YOGA_CATEGORY_MAP: dict[YogaType, tuple[InterpretationCategory, ...]] = {
    YogaType.DHANA_YOGA:              (InterpretationCategory.WEALTH,),
    YogaType.RAJ_YOGA:                (InterpretationCategory.CAREER,),
    YogaType.PANCHA_MAHAPURUSHA_YOGA: (
        InterpretationCategory.CAREER,
        InterpretationCategory.PERSONALITY,
    ),
    YogaType.GAJA_KESARI_YOGA:        (
        InterpretationCategory.RELATIONSHIPS,
        InterpretationCategory.CAREER,
        InterpretationCategory.WEALTH,
    ),
    YogaType.BUDHADITYA_YOGA:         (
        InterpretationCategory.CAREER,
        InterpretationCategory.EDUCATION,
        InterpretationCategory.PERSONALITY,
    ),
    YogaType.CHANDRA_MANGALA_YOGA:    (
        InterpretationCategory.WEALTH,
        InterpretationCategory.RELATIONSHIPS,
    ),
    YogaType.VIPAREETA_YOGA:          (InterpretationCategory.SPIRITUALITY,),
    YogaType.NEECHA_BHANGA_RAJA_YOGA: (InterpretationCategory.CAREER,),
    YogaType.OTHER:                   (),
}

# Category-level titles and summaries keyed by (category, severity)
_TITLES: dict[
    InterpretationCategory,
    dict[InterpretationSeverity, str],
] = {
    InterpretationCategory.CAREER: {
        InterpretationSeverity.NEUTRAL:     "Moderate Career Foundations",
        InterpretationSeverity.MILD:        "Developing Career Potential",
        InterpretationSeverity.MODERATE:    "Solid Career Prospects",
        InterpretationSeverity.SIGNIFICANT: "Strong Career Potential",
        InterpretationSeverity.PROMINENT:   "Exceptional Career Destiny",
    },
    InterpretationCategory.WEALTH: {
        InterpretationSeverity.NEUTRAL:     "Modest Wealth Indications",
        InterpretationSeverity.MILD:        "Gradual Wealth Accumulation",
        InterpretationSeverity.MODERATE:    "Good Wealth Prospects",
        InterpretationSeverity.SIGNIFICANT: "Strong Wealth Potential",
        InterpretationSeverity.PROMINENT:   "Exceptional Wealth Yoga",
    },
    InterpretationCategory.RELATIONSHIPS: {
        InterpretationSeverity.NEUTRAL:     "Ordinary Social Life",
        InterpretationSeverity.MILD:        "Warm Social Connections",
        InterpretationSeverity.MODERATE:    "Harmonious Relationships",
        InterpretationSeverity.SIGNIFICANT: "Strong Relationship Blessings",
        InterpretationSeverity.PROMINENT:   "Exceptional Relational Grace",
    },
    InterpretationCategory.MARRIAGE: {
        InterpretationSeverity.NEUTRAL:     "Standard Marital Indications",
        InterpretationSeverity.MILD:        "Favourable Marriage Timing",
        InterpretationSeverity.MODERATE:    "Harmonious Marriage Prospect",
        InterpretationSeverity.SIGNIFICANT: "Strong Marital Blessings",
        InterpretationSeverity.PROMINENT:   "Exceptional Marital Fortune",
    },
    InterpretationCategory.HEALTH: {
        InterpretationSeverity.NEUTRAL:     "Average Vitality Indications",
        InterpretationSeverity.MILD:        "Generally Stable Health",
        InterpretationSeverity.MODERATE:    "Good Constitutional Strength",
        InterpretationSeverity.SIGNIFICANT: "Robust Vitality",
        InterpretationSeverity.PROMINENT:   "Exceptional Physical Resilience",
    },
    InterpretationCategory.EDUCATION: {
        InterpretationSeverity.NEUTRAL:     "Standard Learning Capacity",
        InterpretationSeverity.MILD:        "Inquisitive Mind",
        InterpretationSeverity.MODERATE:    "Good Academic Aptitude",
        InterpretationSeverity.SIGNIFICANT: "Sharp Intellect and Learning",
        InterpretationSeverity.PROMINENT:   "Exceptional Scholarly Potential",
    },
    InterpretationCategory.SPIRITUALITY: {
        InterpretationSeverity.NEUTRAL:     "Ordinary Spiritual Interest",
        InterpretationSeverity.MILD:        "Growing Spiritual Inclination",
        InterpretationSeverity.MODERATE:    "Notable Spiritual Depth",
        InterpretationSeverity.SIGNIFICANT: "Strong Spiritual Orientation",
        InterpretationSeverity.PROMINENT:   "Exceptional Spiritual Potential",
    },
    InterpretationCategory.PERSONALITY: {
        InterpretationSeverity.NEUTRAL:     "Balanced Personality",
        InterpretationSeverity.MILD:        "Notable Personal Qualities",
        InterpretationSeverity.MODERATE:    "Distinguished Character",
        InterpretationSeverity.SIGNIFICANT: "Powerful Personality Presence",
        InterpretationSeverity.PROMINENT:   "Exceptional Personal Magnetism",
    },
}

_SUMMARIES: dict[
    InterpretationCategory,
    dict[InterpretationSeverity, str],
] = {
    InterpretationCategory.CAREER: {
        InterpretationSeverity.NEUTRAL:     "The chart shows ordinary career indications without standout astrological support.",
        InterpretationSeverity.MILD:        "There are developing career indications that may strengthen over time.",
        InterpretationSeverity.MODERATE:    "The chart supports a steady and respectable professional life.",
        InterpretationSeverity.SIGNIFICANT: "Strong astrological combinations support career success and recognition.",
        InterpretationSeverity.PROMINENT:   "Exceptional career yogas indicate outstanding professional achievement and public renown.",
    },
    InterpretationCategory.WEALTH: {
        InterpretationSeverity.NEUTRAL:     "The chart shows modest wealth indications with steady but unremarkable financial prospects.",
        InterpretationSeverity.MILD:        "Gradual wealth accumulation is indicated through consistent effort.",
        InterpretationSeverity.MODERATE:    "The chart supports good financial growth and material comfort.",
        InterpretationSeverity.SIGNIFICANT: "Strong Dhana yogas indicate considerable wealth and financial security.",
        InterpretationSeverity.PROMINENT:   "Exceptional wealth yogas are present, indicating great material prosperity.",
    },
    InterpretationCategory.RELATIONSHIPS: {
        InterpretationSeverity.NEUTRAL:     "The chart shows an ordinary social life with typical relationship patterns.",
        InterpretationSeverity.MILD:        "Warm and generally harmonious social connections are indicated.",
        InterpretationSeverity.MODERATE:    "The chart supports fulfilling relationships and positive social bonds.",
        InterpretationSeverity.SIGNIFICANT: "Strong astrological factors bless the native with enriching relationships.",
        InterpretationSeverity.PROMINENT:   "Exceptional relational grace is indicated; relationships are a defining strength.",
    },
    InterpretationCategory.MARRIAGE: {
        InterpretationSeverity.NEUTRAL:     "Standard marital indications are present without notable astrological emphasis.",
        InterpretationSeverity.MILD:        "Favourable timing for marriage is suggested with generally supportive combinations.",
        InterpretationSeverity.MODERATE:    "The chart supports a harmonious and stable marital life.",
        InterpretationSeverity.SIGNIFICANT: "Strong marital blessings are present, indicating a fulfilling partnership.",
        InterpretationSeverity.PROMINENT:   "Exceptional marital fortune is indicated; the spouse brings great benefit.",
    },
    InterpretationCategory.HEALTH: {
        InterpretationSeverity.NEUTRAL:     "Average vitality with no outstanding astrological indications for health.",
        InterpretationSeverity.MILD:        "Generally stable health with reasonable constitutional strength.",
        InterpretationSeverity.MODERATE:    "Good vitality and constitutional resilience are supported.",
        InterpretationSeverity.SIGNIFICANT: "Robust vitality and strong physical constitution are indicated.",
        InterpretationSeverity.PROMINENT:   "Exceptional physical resilience and vitality are strongly indicated.",
    },
    InterpretationCategory.EDUCATION: {
        InterpretationSeverity.NEUTRAL:     "Standard learning capacity with ordinary academic potential.",
        InterpretationSeverity.MILD:        "An inquisitive mind that benefits from structured learning.",
        InterpretationSeverity.MODERATE:    "Good academic aptitude and capacity for higher learning.",
        InterpretationSeverity.SIGNIFICANT: "Sharp intellect strongly supports academic and professional knowledge.",
        InterpretationSeverity.PROMINENT:   "Exceptional scholarly potential; the native is gifted with outstanding intelligence.",
    },
    InterpretationCategory.SPIRITUALITY: {
        InterpretationSeverity.NEUTRAL:     "An ordinary interest in spiritual matters with no standout indications.",
        InterpretationSeverity.MILD:        "A growing spiritual inclination that deepens over time.",
        InterpretationSeverity.MODERATE:    "Notable spiritual depth and a genuine interest in higher knowledge.",
        InterpretationSeverity.SIGNIFICANT: "Strong spiritual orientation; dharmic principles guide key life decisions.",
        InterpretationSeverity.PROMINENT:   "Exceptional spiritual potential; the native is drawn powerfully toward liberation.",
    },
    InterpretationCategory.PERSONALITY: {
        InterpretationSeverity.NEUTRAL:     "A balanced and unremarkable personality without standout astrological emphasis.",
        InterpretationSeverity.MILD:        "Notable personal qualities that set the native apart in subtle ways.",
        InterpretationSeverity.MODERATE:    "A distinguished character that earns respect from peers.",
        InterpretationSeverity.SIGNIFICANT: "A powerful personality presence that commands attention and admiration.",
        InterpretationSeverity.PROMINENT:   "Exceptional personal magnetism; the native is a natural leader and influencer.",
    },
}


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class InterpretationService:
    """
    Deterministic, rule-based service that converts YogaAnalysis +
    AstrologyAnalysis into an InterpretationReport.

    One Interpretation is produced for each InterpretationCategory.
    Scores come directly from YogaAnalysis; yoga evidence is collected by
    matching YogaType to the relevant category via _YOGA_CATEGORY_MAP.
    """

    def interpret(
        self,
        yoga_analysis: YogaAnalysis,
        astrology_analysis: AstrologyAnalysis,  # reserved for future house/planet rules
    ) -> InterpretationReport:
        interpretations = (
            self._interpret_career(yoga_analysis),
            self._interpret_wealth(yoga_analysis),
            self._interpret_relationships(yoga_analysis),
            self._interpret_marriage(yoga_analysis),
            self._interpret_health(yoga_analysis),
            self._interpret_education(yoga_analysis),
            self._interpret_spirituality(yoga_analysis),
            self._interpret_personality(yoga_analysis),
        )
        return InterpretationReport(interpretations=interpretations)

    # ------------------------------------------------------------------
    # Per-category interpreters
    # ------------------------------------------------------------------

    def _interpret_career(self, ya: YogaAnalysis) -> Interpretation:
        return self._build(
            category=InterpretationCategory.CAREER,
            score=ya.career_score,
            yogas=ya.detected_yogas,
            tags=("career", "yoga"),
        )

    def _interpret_wealth(self, ya: YogaAnalysis) -> Interpretation:
        return self._build(
            category=InterpretationCategory.WEALTH,
            score=ya.wealth_score,
            yogas=ya.detected_yogas,
            tags=("wealth", "yoga"),
        )

    def _interpret_relationships(self, ya: YogaAnalysis) -> Interpretation:
        return self._build(
            category=InterpretationCategory.RELATIONSHIPS,
            score=ya.relationship_score,
            yogas=ya.detected_yogas,
            tags=("relationships", "yoga"),
        )

    def _interpret_marriage(self, ya: YogaAnalysis) -> Interpretation:
        # Marriage score: proxy using relationship_score (no separate score yet)
        return self._build(
            category=InterpretationCategory.MARRIAGE,
            score=ya.relationship_score,
            yogas=ya.detected_yogas,
            tags=("marriage", "relationships", "yoga"),
        )

    def _interpret_health(self, ya: YogaAnalysis) -> Interpretation:
        # Health has no dedicated yoga score yet; defaults to NEUTRAL
        return self._build(
            category=InterpretationCategory.HEALTH,
            score=0,
            yogas=ya.detected_yogas,
            tags=("health",),
        )

    def _interpret_education(self, ya: YogaAnalysis) -> Interpretation:
        # Education is driven primarily by Budhaditya / career proxy score
        return self._build(
            category=InterpretationCategory.EDUCATION,
            score=ya.career_score // 2,   # career_score is the closest proxy
            yogas=ya.detected_yogas,
            tags=("education", "intellect", "yoga"),
        )

    def _interpret_spirituality(self, ya: YogaAnalysis) -> Interpretation:
        return self._build(
            category=InterpretationCategory.SPIRITUALITY,
            score=ya.spirituality_score,
            yogas=ya.detected_yogas,
            tags=("spirituality", "yoga"),
        )

    def _interpret_personality(self, ya: YogaAnalysis) -> Interpretation:
        # Personality: use authority_score as the primary driver
        return self._build(
            category=InterpretationCategory.PERSONALITY,
            score=ya.authority_score,
            yogas=ya.detected_yogas,
            tags=("personality", "yoga"),
        )

    # ------------------------------------------------------------------
    # Shared builder
    # ------------------------------------------------------------------

    @staticmethod
    def _build(
        category: InterpretationCategory,
        score: int,
        yogas: tuple[YogaResult, ...],
        tags: tuple[str, ...] = (),
    ) -> Interpretation:
        # Collect relevant yoga evidence
        evidence = InterpretationService._collect_evidence(category, yogas)

        # Determine severity / sentiment from score
        severity, sentiment = InterpretationService._classify(score)

        # If we have direct yoga evidence, ensure at least MILD severity
        if evidence and severity is InterpretationSeverity.NEUTRAL:
            severity = InterpretationSeverity.MILD
            sentiment = InterpretationSentiment.POSITIVE

        title = _TITLES[category][severity]
        summary = _SUMMARIES[category][severity]

        return Interpretation(
            category=category,
            title=title,
            summary=summary,
            severity=severity,
            sentiment=sentiment,
            score=min(100, max(0, score)),
            evidence=evidence,
            tags=tuple(sorted(tags)),
        )

    @staticmethod
    def _classify(
        score: int,
    ) -> tuple[InterpretationSeverity, InterpretationSentiment]:
        for min_score, severity, sentiment in _SCORE_THRESHOLDS:
            if score >= min_score:
                return severity, sentiment
        return InterpretationSeverity.NEUTRAL, InterpretationSentiment.NEUTRAL

    @staticmethod
    def _collect_evidence(
        category: InterpretationCategory,
        yogas: tuple[YogaResult, ...],
    ) -> tuple[InterpretationEvidence, ...]:
        evidence: list[InterpretationEvidence] = []
        for result in yogas:
            yoga_type = result.yoga.yoga_type
            relevant_categories = _YOGA_CATEGORY_MAP.get(yoga_type, ())
            if category in relevant_categories:
                evidence.append(
                    InterpretationEvidence(
                        source=result.yoga.name,
                        detail=(
                            f"{result.yoga.name} detected with "
                            f"{result.strength.value} strength. "
                            + (result.evidence[0] if result.evidence else "")
                        ),
                    )
                )
        return tuple(evidence)
