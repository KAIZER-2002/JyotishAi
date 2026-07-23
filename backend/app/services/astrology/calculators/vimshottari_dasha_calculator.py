from dataclasses import dataclass
from datetime import datetime, timedelta
from math import isclose
from typing import Final, Tuple

from app.domain.chart import Chart
from app.domain.dasha import (
    Antardasha,
    DashaLord,
    Mahadasha,
    PLANETARY_PERIOD_YEARS,
    PratyantarDasha,
    VIMSHOTTARI_SEQUENCE,
)
from app.domain.nakshatra import Nakshatra
from app.domain.planet import Planet
from app.domain.planet_type import PlanetType
from app.services.astrology.utils import (
    NAKSHATRA_SIZE,
    longitude_to_nakshatra,
    normalize_longitude,
)


VIMSHOTTARI_YEAR_DAYS: Final[float] = 365.25
NAKSHATRA_BOUNDARY_TOLERANCE: Final[float] = 1e-12


@dataclass(frozen=True)
class MahadashaBalance:
    """
    Starting Vimshottari Mahadasha balance at birth.
    """
    mahadasha: Mahadasha
    moon_nakshatra: Nakshatra
    dasha_lord: DashaLord
    fraction_completed: float
    fraction_remaining: float
    remaining_years: float


class VimshottariDashaCalculator:
    async def generate_mahadasha_sequence(
        self,
        chart: Chart,
        birth_datetime: datetime,
    ) -> Tuple[Mahadasha, ...]:
        balance = await self.calculate_starting_mahadasha(
            chart,
            birth_datetime,
        )
        mahadashas = [
            Mahadasha(
                lord=balance.dasha_lord,
                start_datetime=birth_datetime,
                end_datetime=birth_datetime
                + self._years_to_timedelta(balance.remaining_years),
            )
        ]

        sequence_index = self._sequence_index(balance.dasha_lord)
        current_start = mahadashas[0].end_datetime
        generated_years = balance.remaining_years

        while generated_years < 120.0:
            sequence_index = (sequence_index + 1) % len(VIMSHOTTARI_SEQUENCE)
            lord = VIMSHOTTARI_SEQUENCE[sequence_index]
            duration_years = PLANETARY_PERIOD_YEARS[lord]
            current_end = current_start + self._years_to_timedelta(duration_years)
            mahadashas.append(
                Mahadasha(
                    lord=lord,
                    start_datetime=current_start,
                    end_datetime=current_end,
                )
            )
            current_start = current_end
            generated_years += duration_years

        return tuple(
            Mahadasha(
                lord=mahadasha.lord,
                start_datetime=mahadasha.start_datetime,
                end_datetime=mahadasha.end_datetime,
                sub_periods=self._generate_antardashas(mahadasha),
            )
            for mahadasha in mahadashas
        )

    async def calculate_starting_mahadasha(
        self,
        chart: Chart,
        birth_datetime: datetime,
    ) -> MahadashaBalance:
        moon = self._find_moon(chart)
        moon_longitude = normalize_longitude(moon.longitude)
        moon_nakshatra = longitude_to_nakshatra(moon_longitude)
        dasha_lord = self._dasha_lord_for_nakshatra(moon_nakshatra)

        fraction_completed = self._fraction_nakshatra_completed(moon_longitude)
        fraction_remaining = 1.0 - fraction_completed
        period_years = PLANETARY_PERIOD_YEARS[dasha_lord]
        elapsed_years = period_years * fraction_completed
        remaining_years = period_years * fraction_remaining

        mahadasha = Mahadasha(
            lord=dasha_lord,
            start_datetime=birth_datetime - self._years_to_timedelta(elapsed_years),
            end_datetime=birth_datetime + self._years_to_timedelta(remaining_years),
        )

        return MahadashaBalance(
            mahadasha=mahadasha,
            moon_nakshatra=moon_nakshatra,
            dasha_lord=dasha_lord,
            fraction_completed=fraction_completed,
            fraction_remaining=fraction_remaining,
            remaining_years=remaining_years,
        )

    def _find_moon(self, chart: Chart) -> Planet:
        for planet in chart.planets:
            if planet.planet is PlanetType.MOON:
                return planet
        raise ValueError("Birth chart is missing Moon position.")

    def _dasha_lord_for_nakshatra(self, nakshatra: Nakshatra) -> DashaLord:
        nakshatra_index = list(Nakshatra).index(nakshatra)
        return VIMSHOTTARI_SEQUENCE[nakshatra_index % len(VIMSHOTTARI_SEQUENCE)]

    def _sequence_index(self, lord: DashaLord) -> int:
        return VIMSHOTTARI_SEQUENCE.index(lord)

    def _years_to_timedelta(self, years: float) -> timedelta:
        return timedelta(days=years * VIMSHOTTARI_YEAR_DAYS)

    def _generate_antardashas(self, mahadasha: Mahadasha) -> Tuple[Antardasha, ...]:
        antardashas = []
        parent_snapshot = Mahadasha(
            lord=mahadasha.lord,
            start_datetime=mahadasha.start_datetime,
            end_datetime=mahadasha.end_datetime,
        )

        for lord, current_start, current_end in self._generate_child_boundaries(
            mahadasha.lord,
            mahadasha.start_datetime,
            mahadasha.end_datetime,
        ):
            antardasha_snapshot = Antardasha(
                lord=lord,
                start_datetime=current_start,
                end_datetime=current_end,
                parent_mahadasha=parent_snapshot,
            )
            antardashas.append(
                Antardasha(
                    lord=lord,
                    start_datetime=current_start,
                    end_datetime=current_end,
                    sub_periods=self._generate_pratyantars(antardasha_snapshot),
                    parent_mahadasha=parent_snapshot,
                )
            )

        return tuple(antardashas)

    def _generate_pratyantars(
        self,
        antardasha: Antardasha,
    ) -> Tuple[PratyantarDasha, ...]:
        pratyantars = []
        parent_snapshot = Antardasha(
            lord=antardasha.lord,
            start_datetime=antardasha.start_datetime,
            end_datetime=antardasha.end_datetime,
            parent_mahadasha=antardasha.parent_mahadasha,
        )

        for lord, current_start, current_end in self._generate_child_boundaries(
            antardasha.lord,
            antardasha.start_datetime,
            antardasha.end_datetime,
        ):
            pratyantars.append(
                PratyantarDasha(
                    lord=lord,
                    start_datetime=current_start,
                    end_datetime=current_end,
                    parent_antardasha=parent_snapshot,
                )
            )

        return tuple(pratyantars)

    def _generate_child_boundaries(
        self,
        start_lord: DashaLord,
        parent_start: datetime,
        parent_end: datetime,
    ) -> Tuple[Tuple[DashaLord, datetime, datetime], ...]:
        boundaries = []
        parent_duration = parent_end - parent_start
        current_start = parent_start

        for offset, lord in enumerate(self._ordered_lords_from(start_lord)):
            if offset == len(VIMSHOTTARI_SEQUENCE) - 1:
                current_end = parent_end
            else:
                current_end = current_start + self._proportional_duration(
                    parent_duration,
                    PLANETARY_PERIOD_YEARS[lord],
                )
            boundaries.append((lord, current_start, current_end))
            current_start = current_end

        return tuple(boundaries)

    def _ordered_lords_from(self, start_lord: DashaLord) -> Tuple[DashaLord, ...]:
        sequence_index = self._sequence_index(start_lord)
        return tuple(
            VIMSHOTTARI_SEQUENCE[
                (sequence_index + offset) % len(VIMSHOTTARI_SEQUENCE)
            ]
            for offset in range(len(VIMSHOTTARI_SEQUENCE))
        )

    def _proportional_duration(
        self,
        parent_duration: timedelta,
        child_period_years: int,
    ) -> timedelta:
        return parent_duration * (child_period_years / 120.0)

    def _fraction_nakshatra_completed(self, longitude: float) -> float:
        position_in_nakshatra = normalize_longitude(longitude) % NAKSHATRA_SIZE
        if isclose(
            position_in_nakshatra,
            0.0,
            abs_tol=NAKSHATRA_BOUNDARY_TOLERANCE,
        ) or isclose(
            position_in_nakshatra,
            NAKSHATRA_SIZE,
            abs_tol=NAKSHATRA_BOUNDARY_TOLERANCE,
        ):
            return 0.0
        return position_in_nakshatra / NAKSHATRA_SIZE
