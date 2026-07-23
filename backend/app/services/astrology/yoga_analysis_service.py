from app.domain.astrology_analysis import AstrologyAnalysis
from app.domain.yoga import YogaResult, YogaStrength, YogaType
from app.domain.yoga_analysis import (
    YogaAnalysis,
    _STRENGTH_MULTIPLIER,
    _STRENGTH_ORDER,
    _TYPE_WEIGHTS,
)
from app.domain.yoga_detection import YogaContext, YogaDetectionEngine
from app.domain.yoga_rule_registry import YogaRuleRegistry


class YogaAnalysisService:
    """
    Deterministic application-layer service that:

    1. Wraps an AstrologyAnalysis in a YogaContext.
    2. Runs all registered YogaRules through YogaDetectionEngine.
    3. Aggregates the results into an immutable YogaAnalysis.

    No AI, no LLM, no external I/O.
    """

    def __init__(
        self,
        registry: YogaRuleRegistry | None = None,
        engine: YogaDetectionEngine | None = None,
    ) -> None:
        # Allow injection for testing; build defaults from registry when not supplied.
        if engine is not None:
            self._engine = engine
        else:
            _registry = registry or YogaRuleRegistry()
            self._engine = YogaDetectionEngine(rules=_registry.get_rules())

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(self, analysis: AstrologyAnalysis) -> YogaAnalysis:
        """
        Run yoga detection and compute aggregated scores.

        Parameters
        ----------
        analysis:
            A fully computed AstrologyAnalysis (charts + dashas).

        Returns
        -------
        YogaAnalysis
            Immutable analysis aggregate.
        """
        context = YogaContext(analysis)
        detected = self._engine.detect(context)

        strongest = self._rank_yogas(detected)
        wealth, career, authority, relationship, spirituality = self._compute_scores(
            detected
        )

        return YogaAnalysis(
            detected_yogas=detected,
            strongest_yogas=strongest,
            wealth_score=wealth,
            career_score=career,
            authority_score=authority,
            relationship_score=relationship,
            spirituality_score=spirituality,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _rank_yogas(yogas: tuple[YogaResult, ...]) -> tuple[YogaResult, ...]:
        """
        Return yogas sorted strongest-first.

        Primary sort key  : strength (descending)
        Secondary sort key: yoga_type name (ascending, for determinism)
        """
        return tuple(
            sorted(
                yogas,
                key=lambda r: (
                    -_STRENGTH_ORDER[r.strength],
                    r.yoga.yoga_type.value,
                ),
            )
        )

    @staticmethod
    def _compute_scores(
        yogas: tuple[YogaResult, ...],
    ) -> tuple[int, int, int, int, int]:
        """
        Accumulate weighted scores for each life area, then cap at 100.

        Returns (wealth, career, authority, relationship, spirituality).
        """
        wealth = 0.0
        career = 0.0
        authority = 0.0
        relationship = 0.0
        spirituality = 0.0

        for result in yogas:
            yoga_type: YogaType = result.yoga.yoga_type
            multiplier: float = _STRENGTH_MULTIPLIER[result.strength]
            weights = _TYPE_WEIGHTS.get(yoga_type, _TYPE_WEIGHTS[YogaType.OTHER])

            w, ca, au, re, sp = weights
            wealth       += w  * multiplier
            career       += ca * multiplier
            authority    += au * multiplier
            relationship += re * multiplier
            spirituality += sp * multiplier

        def _cap(value: float) -> int:
            return min(100, max(0, round(value)))

        return (
            _cap(wealth),
            _cap(career),
            _cap(authority),
            _cap(relationship),
            _cap(spirituality),
        )
