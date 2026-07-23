from app.domain.chart import Chart
from app.services.astrology.calculators.divisional_chart_calculator import (
    DivisionalChartCalculator,
    SIGN_SIZE,
)


DASAMSA_DIVISIONS = 10


class DasamsaCalculator(DivisionalChartCalculator):
    """
    Calculator for generating the Dasamsa (D10) chart from a Rasi chart.
    """

    async def calculate_dasamsa(self, birth_chart: Chart) -> Chart:
        return await self.calculate_divisional_chart(birth_chart)

    def _calculate_divisional_longitude(self, longitude: float) -> float:
        sign_index = int((longitude % 360.0) // SIGN_SIZE)
        return self._calculate_cyclic_divisional_longitude(
            longitude=longitude,
            divisions=DASAMSA_DIVISIONS,
            start_sign_index=self._dasamsa_start_sign_index(sign_index),
        )

    def _dasamsa_start_sign_index(self, sign_index: int) -> int:
        if sign_index % 2 == 0:
            return sign_index
        return sign_index + 8
