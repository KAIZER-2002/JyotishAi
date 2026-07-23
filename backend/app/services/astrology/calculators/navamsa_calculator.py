from app.domain.chart import Chart
from app.domain.zodiac import ZodiacSign
from app.services.astrology.calculators.divisional_chart_calculator import (
    DivisionalChartCalculator,
    SIGN_SIZE,
)


NAVAMSA_DIVISIONS = 9


class NavamsaCalculator(DivisionalChartCalculator):
    """
    Calculator for generating the Navamsa (D9) chart from a Rasi chart.
    """

    async def calculate_navamsa(self, birth_chart: Chart) -> Chart:
        return await self.calculate_divisional_chart(birth_chart)

    def _calculate_divisional_longitude(self, longitude: float) -> float:
        sign_index = int((longitude % 360.0) // SIGN_SIZE)
        return self._calculate_cyclic_divisional_longitude(
            longitude=longitude,
            divisions=NAVAMSA_DIVISIONS,
            start_sign_index=self._navamsa_start_sign_index(sign_index),
        )

    def _navamsa_start_sign_index(self, sign_index: int) -> int:
        sign_position = sign_index % 3
        if sign_position == 0:
            return sign_index
        if sign_position == 1:
            return sign_index + 8
        return sign_index + 4
