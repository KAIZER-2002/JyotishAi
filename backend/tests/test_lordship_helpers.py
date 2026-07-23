from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.domain.ascendant import Ascendant
from app.domain.astrology_analysis import AstrologyAnalysis
from app.domain.chart import Chart
from app.domain.house import House
from app.domain.house_number import HouseNumber
from app.domain.nakshatra import Nakshatra
from app.domain.planet import Planet
from app.domain.planet_type import PlanetType
from app.domain.yoga_detection import YogaContext
from app.domain.zodiac import ZodiacSign


def planet(
    planet_type: PlanetType,
    sign: ZodiacSign,
    house_number: HouseNumber,
) -> Planet:
    return Planet(
        planet=planet_type,
        longitude=float(list(ZodiacSign).index(sign) * 30),
        latitude=0.0,
        zodiac_sign=sign,
        house_number=house_number,
        retrograde=False,
        nakshatra=Nakshatra.ASHWINI,
        pada=1,
        degree_within_sign=0.0,
    )


def chart_with_ascendant(ascendant_sign: ZodiacSign, *planets: Planet) -> Chart:
    asc_index = list(ZodiacSign).index(ascendant_sign)
    return Chart(
        ascendant=Ascendant(
            zodiac_sign=ascendant_sign,
            longitude=float(asc_index * 30),
            nakshatra=Nakshatra.ASHWINI,
            pada=1,
            degree_within_sign=0.0,
        ),
        planets=planets,
        houses=tuple(
            House(
                house_number=house_number,
                start_longitude=float(((asc_index + index) % 12) * 30),
                end_longitude=float(((asc_index + index + 1) % 12) * 30),
            )
            for index, house_number in enumerate(HouseNumber)
        ),
    )


def context_with_ascendant(ascendant_sign: ZodiacSign, *planets: Planet) -> YogaContext:
    birth_chart = chart_with_ascendant(ascendant_sign, *planets)
    return YogaContext(
        AstrologyAnalysis(
            birth_chart=birth_chart,
            navamsa_chart=chart_with_ascendant(ZodiacSign.ARIES),
            dasamsa_chart=chart_with_ascendant(ZodiacSign.ARIES),
            shastiamsa_chart=chart_with_ascendant(ZodiacSign.ARIES),
            vimshottari_dashas=(),
        )
    )


def test_lord_lookup_and_multiple_sign_ownership() -> None:
    # Aries Ascendant:
    # House 1: Aries (Mars)
    # House 2: Taurus (Venus)
    # House 3: Gemini (Mercury)
    # House 7: Libra (Venus)
    # House 8: Scorpio (Mars)
    context = context_with_ascendant(ZodiacSign.ARIES)

    assert context.house_lord(HouseNumber.FIRST) == PlanetType.MARS
    assert context.house_lord(HouseNumber.SECOND) == PlanetType.VENUS
    assert context.house_lord(HouseNumber.THIRD) == PlanetType.MERCURY
    assert context.house_lord(HouseNumber.SEVENTH) == PlanetType.VENUS
    assert context.house_lord(HouseNumber.EIGHTH) == PlanetType.MARS

    # Venus owns House 2 and House 7 for Aries Ascendant
    venus_houses = context.houses_owned_by(PlanetType.VENUS)
    assert set(venus_houses) == {HouseNumber.SECOND, HouseNumber.SEVENTH}

    # Mars owns House 1 and House 8 for Aries Ascendant
    mars_houses = context.houses_owned_by(PlanetType.MARS)
    assert set(mars_houses) == {HouseNumber.FIRST, HouseNumber.EIGHTH}


def test_kendra_trikona_dusthana_ownership() -> None:
    # Aries Ascendant:
    # Kendra houses: 1 (Mars), 4 (Moon), 7 (Venus), 10 (Saturn)
    # Trikona houses: 1 (Mars), 5 (Sun), 9 (Jupiter)
    # Dusthana houses: 6 (Mercury), 8 (Mars), 12 (Jupiter)
    context = context_with_ascendant(ZodiacSign.ARIES)

    assert context.is_kendra_lord(PlanetType.MARS) is True  # owns 1
    assert context.is_kendra_lord(PlanetType.MOON) is True  # owns 4
    assert context.is_kendra_lord(PlanetType.SUN) is False   # owns 5 (Trikona only)

    assert context.is_trikona_lord(PlanetType.SUN) is True   # owns 5
    assert context.is_trikona_lord(PlanetType.JUPITER) is True  # owns 9
    assert context.is_trikona_lord(PlanetType.SATURN) is False  # owns 10, 11 (Kendra only)

    assert context.is_dusthana_lord(PlanetType.MERCURY) is True  # owns 6
    assert context.is_dusthana_lord(PlanetType.MARS) is True     # owns 8
    assert context.is_dusthana_lord(PlanetType.SUN) is False      # owns 5


def test_yogakaraka_detection() -> None:
    # For Taurus Ascendant:
    # House 1: Taurus (Venus)
    # House 5: Virgo (Mercury)
    # House 9: Capricorn (Saturn) -> Trikona
    # House 10: Aquarius (Saturn) -> Kendra
    # Saturn is Yogakaraka
    context = context_with_ascendant(ZodiacSign.TAURUS)

    assert context.is_yogakaraka(PlanetType.SATURN) is True
    assert context.is_yogakaraka(PlanetType.MARS) is False  # owns 7 (Kendra) and 12 (Dusthana)


def test_parivartana_detection() -> None:
    # Aries Ascendant: House 1 (Mars), House 2 (Venus)
    # Place Mars in House 2 (Taurus) and Venus in House 1 (Aries)
    context = context_with_ascendant(
        ZodiacSign.ARIES,
        planet(PlanetType.MARS, ZodiacSign.TAURUS, HouseNumber.SECOND),
        planet(PlanetType.VENUS, ZodiacSign.ARIES, HouseNumber.FIRST),
    )

    assert context.is_parivartana(HouseNumber.FIRST, HouseNumber.SECOND) is True
    assert context.is_parivartana(HouseNumber.FIRST, HouseNumber.THIRD) is False


def test_planet_relationships() -> None:
    # 1. Conjunction: Mars and Venus both in Aries
    context_conj = context_with_ascendant(
        ZodiacSign.ARIES,
        planet(PlanetType.MARS, ZodiacSign.ARIES, HouseNumber.FIRST),
        planet(PlanetType.VENUS, ZodiacSign.ARIES, HouseNumber.FIRST),
    )
    assert context_conj.are_related(PlanetType.MARS, PlanetType.VENUS) is True

    # 2. Aspect: Moon in Aries, Mars in Libra (7th aspect mutual)
    context_aspect = context_with_ascendant(
        ZodiacSign.ARIES,
        planet(PlanetType.MOON, ZodiacSign.ARIES, HouseNumber.FIRST),
        planet(PlanetType.MARS, ZodiacSign.LIBRA, HouseNumber.SEVENTH),
    )
    assert context_aspect.are_related(PlanetType.MOON, PlanetType.MARS) is True

    # 3. Sign Exchange (Parivartana relationship): Mars in Taurus, Venus in Aries
    context_exchange = context_with_ascendant(
        ZodiacSign.ARIES,
        planet(PlanetType.MARS, ZodiacSign.TAURUS, HouseNumber.SECOND),
        planet(PlanetType.VENUS, ZodiacSign.ARIES, HouseNumber.FIRST),
    )
    assert context_exchange.are_related(PlanetType.MARS, PlanetType.VENUS) is True

    # 4. Not related: Sun in Aries, Moon in Gemini
    context_none = context_with_ascendant(
        ZodiacSign.ARIES,
        planet(PlanetType.SUN, ZodiacSign.ARIES, HouseNumber.FIRST),
        planet(PlanetType.MOON, ZodiacSign.GEMINI, HouseNumber.THIRD),
    )
    assert context_none.are_related(PlanetType.SUN, PlanetType.MOON) is False
