import asyncio
from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.domain.ascendant import Ascendant
from app.domain.chart import Chart
from app.domain.dasha import (
    DashaLevel,
    DashaLord,
    PLANETARY_PERIOD_YEARS,
    VIMSHOTTARI_SEQUENCE,
)
from app.domain.house import House
from app.domain.house_number import HouseNumber
from app.domain.nakshatra import Nakshatra
from app.domain.planet import Planet
from app.domain.planet_type import PlanetType
from app.services.astrology.calculators.vimshottari_dasha_calculator import (
    VIMSHOTTARI_YEAR_DAYS,
    VimshottariDashaCalculator,
)
from app.services.astrology.utils import (
    NAKSHATRA_SIZE,
    longitude_to_degree,
    longitude_to_nakshatra,
    longitude_to_pada,
    longitude_to_sign,
)


BIRTH_DATETIME = datetime(2000, 1, 1, tzinfo=timezone.utc)


def build_ascendant(longitude: float) -> Ascendant:
    return Ascendant(
        zodiac_sign=longitude_to_sign(longitude),
        longitude=longitude,
        nakshatra=longitude_to_nakshatra(longitude),
        pada=longitude_to_pada(longitude),
        degree_within_sign=longitude_to_degree(longitude),
    )


def build_planet(planet_type: PlanetType, longitude: float) -> Planet:
    return Planet(
        planet=planet_type,
        longitude=longitude,
        latitude=0.0,
        zodiac_sign=longitude_to_sign(longitude),
        house_number=None,
        retrograde=False,
        nakshatra=longitude_to_nakshatra(longitude),
        pada=longitude_to_pada(longitude),
        degree_within_sign=longitude_to_degree(longitude),
    )


def build_birth_chart(moon_longitude: float) -> Chart:
    return Chart(
        ascendant=build_ascendant(0.0),
        planets=(build_planet(PlanetType.MOON, moon_longitude),),
        houses=(
            House(
                house_number=HouseNumber.FIRST,
                start_longitude=0.0,
                end_longitude=30.0,
            ),
        ),
    )


def calculate_balance(moon_longitude: float):
    calculator = VimshottariDashaCalculator()
    return asyncio.run(
        calculator.calculate_starting_mahadasha(
            build_birth_chart(moon_longitude),
            BIRTH_DATETIME,
        )
    )


def generate_sequence(moon_longitude: float):
    calculator = VimshottariDashaCalculator()
    return asyncio.run(
        calculator.generate_mahadasha_sequence(
            build_birth_chart(moon_longitude),
            BIRTH_DATETIME,
        )
    )


def years_between(start: datetime, end: datetime) -> float:
    return (end - start).total_seconds() / (VIMSHOTTARI_YEAR_DAYS * 24 * 60 * 60)


def duration_years(duration) -> float:
    return duration.total_seconds() / (VIMSHOTTARI_YEAR_DAYS * 24 * 60 * 60)


def test_starting_mahadasha_for_first_nakshatra() -> None:
    balance = calculate_balance(1.0)

    assert balance.moon_nakshatra == Nakshatra.ASHWINI
    assert balance.dasha_lord == DashaLord.KETU
    assert balance.mahadasha.lord == DashaLord.KETU


def test_starting_mahadasha_for_last_nakshatra() -> None:
    balance = calculate_balance(26 * NAKSHATRA_SIZE)

    assert balance.moon_nakshatra == Nakshatra.C_REVATI
    assert balance.dasha_lord == DashaLord.MERCURY
    assert balance.remaining_years == 17.0


def test_starting_mahadasha_at_nakshatra_boundary() -> None:
    balance = calculate_balance(NAKSHATRA_SIZE)

    assert balance.moon_nakshatra == Nakshatra.BHARANI
    assert balance.dasha_lord == DashaLord.VENUS
    assert balance.fraction_completed == 0.0
    assert balance.fraction_remaining == 1.0


def test_starting_mahadasha_when_moon_is_exactly_zero_degrees() -> None:
    balance = calculate_balance(0.0)

    assert balance.moon_nakshatra == Nakshatra.ASHWINI
    assert balance.dasha_lord == DashaLord.KETU
    assert balance.fraction_completed == 0.0
    assert balance.remaining_years == 7.0


def test_starting_mahadasha_when_moon_is_exactly_at_end_of_nakshatra() -> None:
    balance = calculate_balance(NAKSHATRA_SIZE)

    assert balance.moon_nakshatra == Nakshatra.BHARANI
    assert balance.fraction_completed == 0.0
    assert balance.remaining_years == 20.0


def test_mahadasha_balance_calculation() -> None:
    balance = calculate_balance(NAKSHATRA_SIZE / 4)

    assert balance.dasha_lord == DashaLord.KETU
    assert balance.fraction_completed == 0.25
    assert balance.fraction_remaining == 0.75
    assert balance.remaining_years == 5.25
    assert balance.mahadasha.start_datetime < BIRTH_DATETIME
    assert balance.mahadasha.end_datetime > BIRTH_DATETIME


def test_mahadasha_sequence_starts_with_each_possible_birth_lord() -> None:
    for index, lord in enumerate(VIMSHOTTARI_SEQUENCE):
        sequence = generate_sequence((index + 0.5) * NAKSHATRA_SIZE)

        assert sequence[0].lord == lord
        assert sequence[0].level == DashaLevel.MAHADASHA
        assert sequence[0].start_datetime == BIRTH_DATETIME


def test_mahadasha_sequence_follows_standard_planetary_order() -> None:
    sequence = generate_sequence(NAKSHATRA_SIZE)
    expected_lords = (
        DashaLord.VENUS,
        DashaLord.SUN,
        DashaLord.MOON,
        DashaLord.MARS,
        DashaLord.RAHU,
        DashaLord.JUPITER,
        DashaLord.SATURN,
        DashaLord.MERCURY,
        DashaLord.KETU,
    )

    assert tuple(period.lord for period in sequence[:9]) == expected_lords


def test_mahadasha_sequence_uses_correct_durations() -> None:
    sequence = generate_sequence(NAKSHATRA_SIZE / 2)

    assert years_between(
        sequence[0].start_datetime,
        sequence[0].end_datetime,
    ) == 3.5
    for period in sequence[1:]:
        assert years_between(
            period.start_datetime,
            period.end_datetime,
        ) == PLANETARY_PERIOD_YEARS[period.lord]
        assert period.duration == period.end_datetime - period.start_datetime


def test_mahadasha_sequence_uses_contiguous_start_and_end_dates() -> None:
    sequence = generate_sequence(0.0)

    assert sequence[0].start_datetime == BIRTH_DATETIME
    for previous, current in zip(sequence, sequence[1:]):
        assert current.start_datetime == previous.end_datetime


def test_mahadasha_sequence_covers_complete_120_year_cycle() -> None:
    sequence = generate_sequence(NAKSHATRA_SIZE / 2)
    total_years = years_between(
        sequence[0].start_datetime,
        sequence[-1].end_datetime,
    )
    total_before_last = years_between(
        sequence[0].start_datetime,
        sequence[-2].end_datetime,
    )

    assert total_years >= 120.0
    assert total_before_last < 120.0


def test_mahadasha_sequence_wraps_from_mercury_to_ketu() -> None:
    sequence = generate_sequence(26 * NAKSHATRA_SIZE)

    assert sequence[0].lord == DashaLord.MERCURY
    assert sequence[1].lord == DashaLord.KETU


def test_antardasha_order_starts_from_parent_mahadasha_lord() -> None:
    sequence = generate_sequence(0.0)
    antardashas = sequence[0].sub_periods

    assert tuple(period.lord for period in antardashas) == VIMSHOTTARI_SEQUENCE
    assert all(period.level == DashaLevel.ANTARDASHA for period in antardashas)


def test_antardasha_duration_proportionality() -> None:
    parent = generate_sequence(0.0)[0]

    for antardasha in parent.sub_periods:
        expected_years = (
            duration_years(parent.duration)
            * PLANETARY_PERIOD_YEARS[antardasha.lord]
            / 120.0
        )
        actual_years = duration_years(antardasha.duration)

        assert abs(actual_years - expected_years) < 1e-9


def test_antardasha_durations_sum_to_parent_mahadasha() -> None:
    parent = generate_sequence(NAKSHATRA_SIZE / 2)[0]
    total_antardasha_seconds = sum(
        period.duration.total_seconds()
        for period in parent.sub_periods
    )

    assert abs(total_antardasha_seconds - parent.duration.total_seconds()) < 1e-6
    assert parent.sub_periods[0].start_datetime == parent.start_datetime
    assert parent.sub_periods[-1].end_datetime == parent.end_datetime


def test_antardasha_first_and_last_periods_reference_parent() -> None:
    parent = generate_sequence(NAKSHATRA_SIZE)[0]
    first = parent.sub_periods[0]
    last = parent.sub_periods[-1]

    assert first.lord == DashaLord.VENUS
    assert last.lord == DashaLord.KETU
    assert first.parent_mahadasha is not None
    assert first.parent_mahadasha.lord == parent.lord
    assert first.parent_mahadasha.start_datetime == parent.start_datetime
    assert first.parent_mahadasha.end_datetime == parent.end_datetime


def test_antardasha_sequence_wraps_after_mercury() -> None:
    parent = generate_sequence(26 * NAKSHATRA_SIZE)[0]

    assert parent.lord == DashaLord.MERCURY
    assert parent.sub_periods[0].lord == DashaLord.MERCURY
    assert parent.sub_periods[1].lord == DashaLord.KETU


def test_antardasha_boundary_conditions_are_contiguous() -> None:
    parent = generate_sequence(NAKSHATRA_SIZE)[0]

    assert parent.sub_periods[0].start_datetime == parent.start_datetime
    assert parent.sub_periods[-1].end_datetime == parent.end_datetime
    for previous, current in zip(parent.sub_periods, parent.sub_periods[1:]):
        assert current.start_datetime == previous.end_datetime


def test_pratyantar_order_starts_from_parent_antardasha_lord() -> None:
    antardasha = generate_sequence(0.0)[0].sub_periods[0]
    pratyantars = antardasha.sub_periods

    assert tuple(period.lord for period in pratyantars) == VIMSHOTTARI_SEQUENCE
    assert all(period.level == DashaLevel.PRATYANTAR_DASHA for period in pratyantars)


def test_pratyantar_duration_proportionality() -> None:
    antardasha = generate_sequence(0.0)[0].sub_periods[0]

    for pratyantar in antardasha.sub_periods:
        expected_years = (
            duration_years(antardasha.duration)
            * PLANETARY_PERIOD_YEARS[pratyantar.lord]
            / 120.0
        )
        actual_years = duration_years(pratyantar.duration)

        assert abs(actual_years - expected_years) < 1e-9


def test_pratyantar_durations_sum_to_parent_antardasha() -> None:
    antardasha = generate_sequence(NAKSHATRA_SIZE / 2)[0].sub_periods[0]
    total_pratyantar_seconds = sum(
        period.duration.total_seconds()
        for period in antardasha.sub_periods
    )

    assert abs(total_pratyantar_seconds - antardasha.duration.total_seconds()) < 1e-6
    assert antardasha.sub_periods[0].start_datetime == antardasha.start_datetime
    assert antardasha.sub_periods[-1].end_datetime == antardasha.end_datetime


def test_pratyantar_parent_references() -> None:
    antardasha = generate_sequence(NAKSHATRA_SIZE)[0].sub_periods[0]
    pratyantar = antardasha.sub_periods[0]

    assert pratyantar.parent_antardasha is not None
    assert pratyantar.parent_antardasha.lord == antardasha.lord
    assert pratyantar.parent_antardasha.start_datetime == antardasha.start_datetime
    assert pratyantar.parent_antardasha.end_datetime == antardasha.end_datetime
    assert pratyantar.parent_antardasha.parent_mahadasha is not None


def test_pratyantar_sequence_wraps_after_mercury() -> None:
    mercury_antardasha = generate_sequence(26 * NAKSHATRA_SIZE)[0].sub_periods[0]

    assert mercury_antardasha.lord == DashaLord.MERCURY
    assert mercury_antardasha.sub_periods[0].lord == DashaLord.MERCURY
    assert mercury_antardasha.sub_periods[1].lord == DashaLord.KETU


def test_pratyantar_boundary_conditions_are_contiguous() -> None:
    antardasha = generate_sequence(NAKSHATRA_SIZE)[0].sub_periods[0]

    assert antardasha.sub_periods[0].start_datetime == antardasha.start_datetime
    assert antardasha.sub_periods[-1].end_datetime == antardasha.end_datetime
    for previous, current in zip(antardasha.sub_periods, antardasha.sub_periods[1:]):
        assert current.start_datetime == previous.end_datetime
