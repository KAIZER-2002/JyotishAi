"""
Interpretation domain models.

Immutable, pure-Python domain layer for deterministic astrology interpretation.
No AI, no LLM, no FastAPI, no Pydantic, no SQLAlchemy.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Tuple


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class InterpretationCategory(Enum):
    """
    Life-area categories that an interpretation can address.

    Designed to be exhaustive for classical Vedic astrology coverage
    without requiring schema changes when new categories are interpreted.
    """
    PERSONALITY    = "Personality"
    CAREER         = "Career"
    WEALTH         = "Wealth"
    RELATIONSHIPS  = "Relationships"
    MARRIAGE       = "Marriage"
    HEALTH         = "Health"
    EDUCATION      = "Education"
    SPIRITUALITY   = "Spirituality"


class InterpretationSeverity(Enum):
    """
    Qualitative strength / prominence of an interpretation finding.

    Used by consumers (e.g. API serialisers or UI) to decide
    visual weight, ordering, and filtering.

    Ordering (weakest → strongest):
        NEUTRAL < MILD < MODERATE < SIGNIFICANT < PROMINENT
    """
    NEUTRAL     = "Neutral"     # Informational; neither strongly positive nor negative
    MILD        = "Mild"        # Subtle influence
    MODERATE    = "Moderate"    # Clearly present but not dominant
    SIGNIFICANT = "Significant" # Strong influence shaping the life area
    PROMINENT   = "Prominent"   # Dominant / defining influence


class InterpretationSentiment(Enum):
    """
    Whether the interpretation describes a favourable, unfavourable, or
    neutral condition.
    """
    POSITIVE = "Positive"
    NEGATIVE = "Negative"
    NEUTRAL  = "Neutral"
    MIXED    = "Mixed"


# ---------------------------------------------------------------------------
# Supporting value objects
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class InterpretationEvidence:
    """
    A single piece of astrological evidence that supports an interpretation.

    Attributes
    ----------
    source:
        Human-readable label for the astrological factor (e.g. "Raj Yoga",
        "Sun in 10th house", "Saturn aspects Moon").
    detail:
        Concise explanation of why this factor contributes to the finding.
    """
    source: str
    detail: str


# ---------------------------------------------------------------------------
# Core domain model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Interpretation:
    """
    A single deterministic astrology interpretation for one life-area category.

    An Interpretation is produced by rule-based logic from AstrologyAnalysis /
    YogaAnalysis data.  It carries enough context for a consumer to render a
    meaningful, evidence-backed statement without additional computation.

    Attributes
    ----------
    category:
        The life-area this interpretation addresses.
    title:
        Short headline (e.g. "Strong Career Potential").
    summary:
        One-to-three sentence human-readable summary of the finding.
    severity:
        How prominent / influential this finding is.
    sentiment:
        Whether the finding is broadly favourable, unfavourable, or mixed.
    score:
        Normalised 0–100 score for the category, inherited from
        YogaAnalysis or computed by the interpretation rule.
        Allows consumers to rank or compare findings numerically.
    evidence:
        Ordered tuple of InterpretationEvidence items that justify the finding.
        Empty tuple is valid (e.g. for a neutral/default interpretation).
    tags:
        Optional free-form labels for filtering (e.g. "yoga", "house",
        "planetary_strength").  Stored as a sorted immutable tuple.
    """
    category:  InterpretationCategory
    title:     str
    summary:   str
    severity:  InterpretationSeverity
    sentiment: InterpretationSentiment
    score:     int                               # 0–100
    evidence:  Tuple[InterpretationEvidence, ...] = ()
    tags:      Tuple[str, ...]                   = ()


# ---------------------------------------------------------------------------
# Aggregate
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class InterpretationReport:
    """
    Immutable collection of all Interpretation findings for a single chart.

    Provides convenience helpers for filtering and ranking without mutating
    state; all helpers return new tuples.

    Attributes
    ----------
    interpretations:
        All findings, in the order they were produced by the service.
    """
    interpretations: Tuple[Interpretation, ...]

    # ------------------------------------------------------------------
    # Read-only helpers (return new collections — no mutation)
    # ------------------------------------------------------------------

    def by_category(
        self,
        category: InterpretationCategory,
    ) -> Tuple[Interpretation, ...]:
        """Return all interpretations for the given category."""
        return tuple(i for i in self.interpretations if i.category is category)

    def by_sentiment(
        self,
        sentiment: InterpretationSentiment,
    ) -> Tuple[Interpretation, ...]:
        """Return all interpretations with the given sentiment."""
        return tuple(i for i in self.interpretations if i.sentiment is sentiment)

    def ranked_by_severity(self) -> Tuple[Interpretation, ...]:
        """
        Return all interpretations ordered most-prominent first.
        Ties broken by category name for determinism.
        """
        _ORDER = {
            InterpretationSeverity.NEUTRAL:     0,
            InterpretationSeverity.MILD:        1,
            InterpretationSeverity.MODERATE:    2,
            InterpretationSeverity.SIGNIFICANT: 3,
            InterpretationSeverity.PROMINENT:   4,
        }
        return tuple(
            sorted(
                self.interpretations,
                key=lambda i: (-_ORDER[i.severity], i.category.value),
            )
        )

    def ranked_by_score(self) -> Tuple[Interpretation, ...]:
        """Return all interpretations ordered highest-score first."""
        return tuple(
            sorted(
                self.interpretations,
                key=lambda i: (-i.score, i.category.value),
            )
        )
