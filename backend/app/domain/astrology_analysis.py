from dataclasses import dataclass
from typing import Tuple

from app.domain.chart import Chart
from app.domain.dasha import Mahadasha


@dataclass(frozen=True)
class AstrologyAnalysis:
    """
    Immutable aggregate for a complete astrology analysis calculation.
    """
    birth_chart: Chart
    navamsa_chart: Chart
    dasamsa_chart: Chart
    shastiamsa_chart: Chart
    vimshottari_dashas: Tuple[Mahadasha, ...]
