from datetime import datetime
from typing import TypeVar

from app.domain.ascendant import Ascendant
from app.domain.ayanamsa import Ayanamsa
from app.domain.chart import Chart
from app.domain.dasha import Antardasha, DashaPeriod, Mahadasha, PratyantarDasha
from app.domain.house import House
from app.domain.house_number import HouseNumber
from app.domain.planet import Planet
from app.schemas.astrology import (
    AscendantPosition,
    AntardashaResponse,
    BirthChartResponse,
    DasamsaChartResponse,
    HousePosition,
    MahadashaResponse,
    NavamsaChartResponse,
    PlanetPosition,
    PratyantarDashaResponse,
    ShastiamsaChartResponse,
    VimshottariDashaResponse,
)
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


ChartResponseT = TypeVar("ChartResponseT", bound=BirthChartResponse)


class AstrologyService:
    def __init__(
        self,
        birth_chart_calculator: BirthChartCalculator,
        navamsa_calculator: NavamsaCalculator,
        dasamsa_calculator: DasamsaCalculator,
        shastiamsa_calculator: ShastiamsaCalculator,
        vimshottari_dasha_calculator: VimshottariDashaCalculator | None = None,
    ) -> None:
        self._birth_chart_calculator = birth_chart_calculator
        self._navamsa_calculator = navamsa_calculator
        self._dasamsa_calculator = dasamsa_calculator
        self._shastiamsa_calculator = shastiamsa_calculator
        self._vimshottari_dasha_calculator = (
            vimshottari_dasha_calculator or VimshottariDashaCalculator()
        )

    async def generate_birth_chart(
        self,
        birth_datetime: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: Ayanamsa,
        house_system: int,
    ) -> BirthChartResponse:
        chart = await self._birth_chart_calculator.calculate_chart(
            birth_datetime=birth_datetime,
            latitude=latitude,
            longitude=longitude,
            ayanamsa=ayanamsa,
            house_system=house_system,
        )
        return self._to_chart_response(chart, BirthChartResponse)

    async def generate_navamsa_chart(
        self,
        birth_datetime: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: Ayanamsa,
        house_system: int,
    ) -> NavamsaChartResponse:
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
        return self._to_chart_response(navamsa_chart, NavamsaChartResponse)

    async def generate_dasamsa_chart(
        self,
        birth_datetime: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: Ayanamsa,
        house_system: int,
    ) -> DasamsaChartResponse:
        birth_chart = await self._birth_chart_calculator.calculate_chart(
            birth_datetime=birth_datetime,
            latitude=latitude,
            longitude=longitude,
            ayanamsa=ayanamsa,
            house_system=house_system,
        )
        dasamsa_chart = await self._dasamsa_calculator.calculate_dasamsa(
            birth_chart
        )
        return self._to_chart_response(dasamsa_chart, DasamsaChartResponse)

    async def generate_shastiamsa_chart(
        self,
        birth_datetime: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: Ayanamsa,
        house_system: int,
    ) -> ShastiamsaChartResponse:
        birth_chart = await self._birth_chart_calculator.calculate_chart(
            birth_datetime=birth_datetime,
            latitude=latitude,
            longitude=longitude,
            ayanamsa=ayanamsa,
            house_system=house_system,
        )
        shastiamsa_chart = await self._shastiamsa_calculator.calculate_shastiamsa(
            birth_chart
        )
        return self._to_chart_response(shastiamsa_chart, ShastiamsaChartResponse)

    async def generate_vimshottari_dasha(
        self,
        birth_datetime: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: Ayanamsa,
        house_system: int,
    ) -> VimshottariDashaResponse:
        birth_chart = await self._birth_chart_calculator.calculate_chart(
            birth_datetime=birth_datetime,
            latitude=latitude,
            longitude=longitude,
            ayanamsa=ayanamsa,
            house_system=house_system,
        )
        mahadashas = await self._vimshottari_dasha_calculator.generate_mahadasha_sequence(
            birth_chart,
            birth_datetime,
        )
        return VimshottariDashaResponse(
            mahadashas=[
                self._to_mahadasha_response(mahadasha)
                for mahadasha in mahadashas
            ]
        )

    def _to_chart_response(
        self,
        chart: Chart,
        response_type: type[ChartResponseT],
    ) -> ChartResponseT:
        return response_type(
            ascendant=self._to_ascendant_position(chart.ascendant),
            planets=[
                self._to_planet_position(planet)
                for planet in chart.planets
            ],
            houses=[
                self._to_house_position(house)
                for house in chart.houses
            ],
        )

    def _to_planet_position(self, planet: Planet) -> PlanetPosition:
        house_number = self._require_house_number(planet)

        return PlanetPosition(
            planet=planet.planet,
            longitude=planet.longitude,
            zodiac_sign=planet.zodiac_sign,
            house_number=house_number,
            retrograde=planet.retrograde,
            nakshatra=planet.nakshatra,
            pada=planet.pada,
            degree_within_sign=planet.degree_within_sign,
        )

    def _require_house_number(self, planet: Planet) -> HouseNumber:
        if planet.house_number is None:
            raise ValueError(f"Planet {planet.planet.value} is missing house assignment.")
        return planet.house_number

    def _to_house_position(self, house: House) -> HousePosition:
        return HousePosition(
            house_number=house.house_number,
            start_longitude=house.start_longitude,
            end_longitude=house.end_longitude,
        )

    def _to_ascendant_position(self, ascendant: Ascendant) -> AscendantPosition:
        return AscendantPosition(
            zodiac_sign=ascendant.zodiac_sign,
            longitude=ascendant.longitude,
            nakshatra=ascendant.nakshatra,
            pada=ascendant.pada,
            degree_within_sign=ascendant.degree_within_sign,
        )

    def _to_mahadasha_response(self, mahadasha: Mahadasha) -> MahadashaResponse:
        return MahadashaResponse(
            **self._to_dasha_period_fields(mahadasha),
            antardashas=[
                self._to_antardasha_response(antardasha)
                for antardasha in mahadasha.sub_periods
            ],
        )

    def _to_antardasha_response(self, antardasha: Antardasha) -> AntardashaResponse:
        return AntardashaResponse(
            **self._to_dasha_period_fields(antardasha),
            pratyantars=[
                self._to_pratyantar_response(pratyantar)
                for pratyantar in antardasha.sub_periods
            ],
        )

    def _to_pratyantar_response(
        self,
        pratyantar: PratyantarDasha,
    ) -> PratyantarDashaResponse:
        return PratyantarDashaResponse(
            **self._to_dasha_period_fields(pratyantar),
        )

    def _to_dasha_period_fields(self, period: DashaPeriod) -> dict:
        return {
            "lord": period.lord,
            "start_datetime": period.start_datetime,
            "end_datetime": period.end_datetime,
            "duration_days": period.duration.total_seconds() / 86400,
            "level": period.level,
        }
