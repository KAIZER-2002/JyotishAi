from dataclasses import dataclass
from typing import Tuple

from app.domain.yoga import YogaResult, YogaStrength, YogaType


# ---------------------------------------------------------------------------
# Score weights
# ---------------------------------------------------------------------------
# Each YogaType contributes deterministically to one or more life-area scores.
# Scores are additive, capped at 100, and are integers (0–100).
#
# Weight table (per YogaResult, before strength multiplier):
#
#  YogaType                 | wealth | career | authority | relationship | spirituality
#  -------------------------|--------|--------|-----------|--------------|-------------
#  DHANA_YOGA               |  30    |   5    |    0      |     0        |     0
#  RAJ_YOGA                 |   5    |  20    |   30      |     0        |     5
#  PANCHA_MAHAPURUSHA_YOGA  |   5    |  20    |   20      |    10        |     5
#  GAJA_KESARI_YOGA         |  10    |  10    |   10      |    15        |    10
#  BUDHADITYA_YOGA          |   5    |  15    |    5      |     5        |     5
#  CHANDRA_MANGALA_YOGA     |  15    |   5    |    0      |    10        |     5
#  VIPAREETA_YOGA           |   5    |   5    |    5      |     0        |    15
#  NEECHA_BHANGA_RAJA_YOGA  |   5    |  10    |   15      |     0        |     5
#  OTHER                    |   2    |   2    |    2      |     2        |     2
#
# Strength multipliers:
#   WEAK        → 0.5
#   MODERATE    → 1.0
#   STRONG      → 1.5
#   EXCEPTIONAL → 2.0
# ---------------------------------------------------------------------------

_STRENGTH_MULTIPLIER: dict[YogaStrength, float] = {
    YogaStrength.WEAK: 0.5,
    YogaStrength.MODERATE: 1.0,
    YogaStrength.STRONG: 1.5,
    YogaStrength.EXCEPTIONAL: 2.0,
}

# (wealth, career, authority, relationship, spirituality)
_TYPE_WEIGHTS: dict[YogaType, tuple[int, int, int, int, int]] = {
    YogaType.DHANA_YOGA:             (30,  5,  0,  0,  0),
    YogaType.RAJ_YOGA:               ( 5, 20, 30,  0,  5),
    YogaType.PANCHA_MAHAPURUSHA_YOGA:( 5, 20, 20, 10,  5),
    YogaType.GAJA_KESARI_YOGA:       (10, 10, 10, 15, 10),
    YogaType.BUDHADITYA_YOGA:        ( 5, 15,  5,  5,  5),
    YogaType.CHANDRA_MANGALA_YOGA:   (15,  5,  0, 10,  5),
    YogaType.VIPAREETA_YOGA:         ( 5,  5,  5,  0, 15),
    YogaType.NEECHA_BHANGA_RAJA_YOGA:( 5, 10, 15,  0,  5),
    YogaType.OTHER:                  ( 2,  2,  2,  2,  2),
}

_STRENGTH_ORDER: dict[YogaStrength, int] = {
    YogaStrength.WEAK: 0,
    YogaStrength.MODERATE: 1,
    YogaStrength.STRONG: 2,
    YogaStrength.EXCEPTIONAL: 3,
}


@dataclass(frozen=True)
class YogaAnalysis:
    """
    Immutable aggregate of deterministic Yoga analysis results.

    Scores (0–100) are computed from the detected YogaResults using
    fixed weight tables; no AI or LLM is involved.
    """

    # All yogas detected
    detected_yogas: Tuple[YogaResult, ...]

    # Ordered from strongest to weakest (ties broken by YogaType name)
    strongest_yogas: Tuple[YogaResult, ...]

    # Life-area scores (0–100, higher is better)
    wealth_score: int
    career_score: int
    authority_score: int
    relationship_score: int
    spirituality_score: int
