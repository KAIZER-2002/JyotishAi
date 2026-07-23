from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Mapping, Protocol, Sequence, Tuple, TypeAlias

from app.domain.astrology_analysis import AstrologyAnalysis
from app.domain.chart import Chart
from app.domain.chart_type import ChartType
from app.domain.house import House
from app.domain.house_number import HouseNumber
from app.domain.planet import Planet
from app.domain.planet_type import PlanetType
from app.domain.yoga import Yoga, YogaResult, YogaStrength
from app.domain.zodiac import ZodiacSign
from app.services.astrology.utils import longitude_to_sign


YogaRuleEvaluation: TypeAlias = (
    Yoga | YogaResult | Sequence[Yoga | YogaResult] | None
)


SIGN_LORDS: Final[Mapping[ZodiacSign, PlanetType]] = MappingProxyType(
    {
        ZodiacSign.ARIES: PlanetType.MARS,
        ZodiacSign.TAURUS: PlanetType.VENUS,
        ZodiacSign.GEMINI: PlanetType.MERCURY,
        ZodiacSign.CANCER: PlanetType.MOON,
        ZodiacSign.LEO: PlanetType.SUN,
        ZodiacSign.VIRGO: PlanetType.MERCURY,
        ZodiacSign.LIBRA: PlanetType.VENUS,
        ZodiacSign.SCORPIO: PlanetType.MARS,
        ZodiacSign.SAGITTARIUS: PlanetType.JUPITER,
        ZodiacSign.CAPRICORN: PlanetType.SATURN,
        ZodiacSign.AQUARIUS: PlanetType.SATURN,
        ZodiacSign.PISCES: PlanetType.JUPITER,
    }
)

EXALTATION_SIGNS: Final[Mapping[PlanetType, ZodiacSign]] = MappingProxyType(
    {
        PlanetType.SUN: ZodiacSign.ARIES,
        PlanetType.MOON: ZodiacSign.TAURUS,
        PlanetType.MARS: ZodiacSign.CAPRICORN,
        PlanetType.MERCURY: ZodiacSign.VIRGO,
        PlanetType.JUPITER: ZodiacSign.CANCER,
        PlanetType.VENUS: ZodiacSign.PISCES,
        PlanetType.SATURN: ZodiacSign.LIBRA,
        PlanetType.RAHU: ZodiacSign.TAURUS,
        PlanetType.KETU: ZodiacSign.SCORPIO,
    }
)

DEBILITATION_SIGNS: Final[Mapping[PlanetType, ZodiacSign]] = MappingProxyType(
    {
        PlanetType.SUN: ZodiacSign.LIBRA,
        PlanetType.MOON: ZodiacSign.SCORPIO,
        PlanetType.MARS: ZodiacSign.CANCER,
        PlanetType.MERCURY: ZodiacSign.PISCES,
        PlanetType.JUPITER: ZodiacSign.CAPRICORN,
        PlanetType.VENUS: ZodiacSign.VIRGO,
        PlanetType.SATURN: ZodiacSign.ARIES,
        PlanetType.RAHU: ZodiacSign.SCORPIO,
        PlanetType.KETU: ZodiacSign.TAURUS,
    }
)

VASHI_ASPECT_OFFSETS: Final[Mapping[PlanetType, Tuple[int, ...]]] = MappingProxyType(
    {
        PlanetType.SUN: (7,),
        PlanetType.MOON: (7,),
        PlanetType.MERCURY: (7,),
        PlanetType.VENUS: (7,),
        PlanetType.RAHU: (7,),
        PlanetType.KETU: (7,),
        PlanetType.MARS: (4, 7, 8),
        PlanetType.JUPITER: (5, 7, 9),
        PlanetType.SATURN: (3, 7, 10),
    }
)

KENDRA_OFFSETS: Final[Tuple[int, ...]] = (1, 4, 7, 10)

KENDRA_HOUSES: Final[Tuple[HouseNumber, ...]] = (
    HouseNumber.FIRST,
    HouseNumber.FOURTH,
    HouseNumber.SEVENTH,
    HouseNumber.TENTH,
)

TRIKONA_HOUSES: Final[Tuple[HouseNumber, ...]] = (
    HouseNumber.FIRST,
    HouseNumber.FIFTH,
    HouseNumber.NINTH,
)

DUSTHANA_HOUSES: Final[Tuple[HouseNumber, ...]] = (
    HouseNumber.SIXTH,
    HouseNumber.EIGHTH,
    HouseNumber.TWELFTH,
)


@dataclass(frozen=True)
class YogaContext:
    """
    Read-only helper context used by Yoga detection rules.
    """
    analysis: AstrologyAnalysis

    def chart(self, chart_type: ChartType = ChartType.RASI) -> Chart:
        if chart_type is ChartType.RASI:
            return self.analysis.birth_chart
        if chart_type is ChartType.NAVAMSA:
            return self.analysis.navamsa_chart
        if chart_type is ChartType.DASAMSA:
            return self.analysis.dasamsa_chart
        if chart_type is ChartType.SHASTIAMSA:
            return self.analysis.shastiamsa_chart
        raise ValueError(f"Unsupported chart type for Yoga context: {chart_type.value}")

    def planet(
        self,
        planet_type: PlanetType,
        chart_type: ChartType = ChartType.RASI,
    ) -> Planet | None:
        for planet in self.chart(chart_type).planets:
            if planet.planet is planet_type:
                return planet
        return None

    def house(
        self,
        house_number: HouseNumber,
        chart_type: ChartType = ChartType.RASI,
    ) -> House | None:
        for house in self.chart(chart_type).houses:
            if house.house_number is house_number:
                return house
        return None

    def sign_of_planet(
        self,
        planet_type: PlanetType,
        chart_type: ChartType = ChartType.RASI,
    ) -> ZodiacSign | None:
        planet = self.planet(planet_type, chart_type)
        if planet is None:
            return None
        return planet.zodiac_sign

    def house_lord(
        self,
        house_number: HouseNumber,
        chart_type: ChartType = ChartType.RASI,
    ) -> PlanetType | None:
        house = self.house(house_number, chart_type)
        if house is None:
            return None
        return SIGN_LORDS[longitude_to_sign(house.start_longitude)]

    def planets_in_house(
        self,
        house_number: HouseNumber,
        chart_type: ChartType = ChartType.RASI,
    ) -> Tuple[Planet, ...]:
        return tuple(
            planet
            for planet in self.chart(chart_type).planets
            if planet.house_number is house_number
        )

    def planets_in_sign(
        self,
        sign: ZodiacSign,
        chart_type: ChartType = ChartType.RASI,
    ) -> Tuple[Planet, ...]:
        return tuple(
            planet
            for planet in self.chart(chart_type).planets
            if planet.zodiac_sign is sign
        )

    def are_conjunct(
        self,
        first: PlanetType,
        second: PlanetType,
        chart_type: ChartType = ChartType.RASI,
    ) -> bool:
        first_planet = self.planet(first, chart_type)
        second_planet = self.planet(second, chart_type)
        if first_planet is None or second_planet is None:
            return False
        return first_planet.zodiac_sign is second_planet.zodiac_sign

    def is_planet_in_kendra_from_planet(
        self,
        target_planet: PlanetType,
        reference_planet: PlanetType,
        chart_type: ChartType = ChartType.RASI,
    ) -> bool:
        target = self.planet(target_planet, chart_type)
        reference = self.planet(reference_planet, chart_type)
        if target is None or reference is None:
            return False

        reference_index = list(ZodiacSign).index(reference.zodiac_sign)
        target_index = list(ZodiacSign).index(target.zodiac_sign)
        offset = ((target_index - reference_index) % len(ZodiacSign)) + 1
        return offset in KENDRA_OFFSETS

    def has_aspect(
        self,
        from_planet: PlanetType,
        to_planet: PlanetType,
        chart_type: ChartType = ChartType.RASI,
    ) -> bool:
        source = self.planet(from_planet, chart_type)
        target = self.planet(to_planet, chart_type)
        if source is None or target is None:
            return False

        source_index = list(ZodiacSign).index(source.zodiac_sign)
        target_index = list(ZodiacSign).index(target.zodiac_sign)
        offset = ((target_index - source_index) % len(ZodiacSign)) + 1
        return offset in VASHI_ASPECT_OFFSETS[from_planet]

    def is_exalted(
        self,
        planet_type: PlanetType,
        chart_type: ChartType = ChartType.RASI,
    ) -> bool:
        return self.sign_of_planet(planet_type, chart_type) is EXALTATION_SIGNS[
            planet_type
        ]

    def is_debilitated(
        self,
        planet_type: PlanetType,
        chart_type: ChartType = ChartType.RASI,
    ) -> bool:
        return self.sign_of_planet(planet_type, chart_type) is DEBILITATION_SIGNS[
            planet_type
        ]

    def houses_owned_by(
        self,
        planet_type: PlanetType,
        chart_type: ChartType = ChartType.RASI,
    ) -> Tuple[HouseNumber, ...]:
        """
        Finds all houses owned by a given planetary lord.
        """
        owned = []
        for house in self.chart(chart_type).houses:
            lord = self.house_lord(house.house_number, chart_type)
            if lord == planet_type:
                owned.append(house.house_number)
        return tuple(owned)

    def is_kendra_lord(
        self,
        planet_type: PlanetType,
        chart_type: ChartType = ChartType.RASI,
    ) -> bool:
        """
        Checks if a planet owns a Kendra house (1st, 4th, 7th, 10th).
        """
        owned = self.houses_owned_by(planet_type, chart_type)
        return any(h in KENDRA_HOUSES for h in owned)

    def is_trikona_lord(
        self,
        planet_type: PlanetType,
        chart_type: ChartType = ChartType.RASI,
    ) -> bool:
        """
        Checks if a planet owns a Trikona house (1st, 5th, 9th).
        """
        owned = self.houses_owned_by(planet_type, chart_type)
        return any(h in TRIKONA_HOUSES for h in owned)

    def is_dusthana_lord(
        self,
        planet_type: PlanetType,
        chart_type: ChartType = ChartType.RASI,
    ) -> bool:
        """
        Checks if a planet owns a Dusthana house (6th, 8th, 12th).
        """
        owned = self.houses_owned_by(planet_type, chart_type)
        return any(h in DUSTHANA_HOUSES for h in owned)

    def is_yogakaraka(
        self,
        planet_type: PlanetType,
        chart_type: ChartType = ChartType.RASI,
    ) -> bool:
        """
        In Vedic astrology, a planet is a Yogakaraka if it owns both a Kendra
        and a Trikona house simultaneously.
        """
        return self.is_kendra_lord(planet_type, chart_type) and self.is_trikona_lord(
            planet_type, chart_type
        )

    def is_parivartana(
        self,
        first_house: HouseNumber,
        second_house: HouseNumber,
        chart_type: ChartType = ChartType.RASI,
    ) -> bool:
        """
        Parivartana occurs when the lord of first_house is placed in second_house,
        and the lord of second_house is placed in first_house.
        """
        lord_first = self.house_lord(first_house, chart_type)
        lord_second = self.house_lord(second_house, chart_type)

        if lord_first is None or lord_second is None:
            return False

        planet_first = self.planet(lord_first, chart_type)
        planet_second = self.planet(lord_second, chart_type)

        if planet_first is None or planet_second is None:
            return False

        return (
            planet_first.house_number == second_house
            and planet_second.house_number == first_house
        )

    def are_related(
        self,
        first: PlanetType,
        second: PlanetType,
        chart_type: ChartType = ChartType.RASI,
    ) -> bool:
        """
        Two planets are related (Sambandha) if they are conjunct, mutually aspecting,
        or in a parivartana (mutual sign exchange) relationship.
        """
        if first == second:
            return False

        p1 = self.planet(first, chart_type)
        p2 = self.planet(second, chart_type)

        if p1 is None or p2 is None:
            return False

        # 1. Conjunction
        if self.are_conjunct(first, second, chart_type):
            return True

        # 2. Aspect relationship
        if self.has_aspect(first, second, chart_type) or self.has_aspect(
            second,
            first,
            chart_type,
        ):
            return True

        # 3. Parivartana (sign exchange)
        sign1 = p1.zodiac_sign
        sign2 = p2.zodiac_sign
        if SIGN_LORDS[sign1] == second and SIGN_LORDS[sign2] == first:
            return True

        return False


class YogaRule(Protocol):
    """
    Interface for a single Yoga detection rule.
    """

    def evaluate(self, context: YogaContext) -> YogaRuleEvaluation:
        """
        Evaluate a Yoga context and return detected Yoga data or None.
        """


class YogaEvaluator:
    def __init__(
        self,
        default_strength: YogaStrength = YogaStrength.MODERATE,
        isolate_rule_errors: bool = True,
    ) -> None:
        self._default_strength = default_strength
        self._isolate_rule_errors = isolate_rule_errors

    def evaluate_rule(
        self,
        rule: YogaRule,
        context: YogaContext,
    ) -> Tuple[YogaResult, ...]:
        try:
            evaluation = rule.evaluate(context)
        except Exception:
            if not self._isolate_rule_errors:
                raise
            return ()

        return self._to_results(evaluation)

    def _to_results(
        self,
        evaluation: YogaRuleEvaluation,
    ) -> Tuple[YogaResult, ...]:
        if evaluation is None:
            return ()

        if isinstance(evaluation, Yoga):
            return (self._to_result(evaluation),)

        if isinstance(evaluation, YogaResult):
            return (evaluation,)

        return tuple(
            result
            if isinstance(result, YogaResult)
            else self._to_result(result)
            for result in evaluation
        )

    def _to_result(self, yoga: Yoga) -> YogaResult:
        return YogaResult(
            yoga=yoga,
            strength=self._default_strength,
        )


class YogaDetectionEngine:
    def __init__(
        self,
        rules: Sequence[YogaRule],
        evaluator: YogaEvaluator | None = None,
    ) -> None:
        self._rules = tuple(rules)
        self._evaluator = evaluator or YogaEvaluator()

    def detect(self, context: YogaContext) -> Tuple[YogaResult, ...]:
        results: list[YogaResult] = []

        for rule in self._rules:
            results.extend(
                self._evaluator.evaluate_rule(
                    rule,
                    context,
                )
            )

        return tuple(results)
