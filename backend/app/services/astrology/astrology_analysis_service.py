from datetime import datetime

from app.domain.astrology_analysis import AstrologyAnalysis
from app.domain.ayanamsa import Ayanamsa
from app.services.astrology.calculators.birth_chart_calculator import (
    BirthChartCalculator,
)
from app.services.astrology.calculators.dasamsa_calculator import DasamsaCalculator
from app.services.astrology.calculators.navamsa_calculator import NavamsaCalculator
from app.services.astrology.calculators.shastiamsa_calculator import (
    ShastiamsaCalculator,
)
from app.services.astrology.calculators.vimshottari_dasha_calculator import (
    VimshottariDashaCalculator,
)


class AstrologyAnalysisService:
    def __init__(
        self,
        birth_chart_calculator: BirthChartCalculator,
        navamsa_calculator: NavamsaCalculator,
        dasamsa_calculator: DasamsaCalculator,
        shastiamsa_calculator: ShastiamsaCalculator,
        vimshottari_dasha_calculator: VimshottariDashaCalculator,
    ) -> None:
        self._birth_chart_calculator = birth_chart_calculator
        self._navamsa_calculator = navamsa_calculator
        self._dasamsa_calculator = dasamsa_calculator
        self._shastiamsa_calculator = shastiamsa_calculator
        self._vimshottari_dasha_calculator = vimshottari_dasha_calculator

    async def generate_analysis(
        self,
        birth_datetime: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: Ayanamsa,
        house_system: int,
    ) -> AstrologyAnalysis:
        birth_chart = await self._birth_chart_calculator.calculate_chart(
            birth_datetime=birth_datetime,
            latitude=latitude,
            longitude=longitude,
            ayanamsa=ayanamsa,
            house_system=house_system,
        )
        navamsa_chart = await self._navamsa_calculator.calculate_navamsa(
            birth_chart
        )
        dasamsa_chart = await self._dasamsa_calculator.calculate_dasamsa(
            birth_chart
        )
        shastiamsa_chart = await self._shastiamsa_calculator.calculate_shastiamsa(
            birth_chart
        )
        vimshottari_dashas = (
            await self._vimshottari_dasha_calculator.generate_mahadasha_sequence(
                birth_chart,
                birth_datetime,
            )
        )

        return AstrologyAnalysis(
            birth_chart=birth_chart,
            navamsa_chart=navamsa_chart,
            dasamsa_chart=dasamsa_chart,
            shastiamsa_chart=shastiamsa_chart,
            vimshottari_dashas=vimshottari_dashas,
        )
