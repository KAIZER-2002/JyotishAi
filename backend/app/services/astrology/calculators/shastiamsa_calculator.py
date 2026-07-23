from app.domain.chart import Chart
from app.services.astrology.calculators.divisional_chart_calculator import (
    DivisionalChartCalculator,
)


SHASTIAMSA_DIVISIONS = 60
SHASTIAMSA_START_SIGN_INDEX = 0


class ShastiamsaCalculator(DivisionalChartCalculator):
    """
    Calculator for generating the Shastiamsa (D60) chart from a Rasi chart.
    """

    async def calculate_shastiamsa(self, birth_chart: Chart) -> Chart:
        return await self.calculate_divisional_chart(birth_chart)

    def _calculate_divisional_longitude(self, longitude: float) -> float:
        return self._calculate_cyclic_divisional_longitude(
            longitude=longitude,
            divisions=SHASTIAMSA_DIVISIONS,
            start_sign_index=SHASTIAMSA_START_SIGN_INDEX,
        )
