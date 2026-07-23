from typing import Tuple

from app.domain.house_number import HouseNumber
from app.domain.planet_type import PlanetType
from app.domain.yoga import Yoga, YogaResult, YogaStrength, YogaType
from app.domain.yoga_detection import SIGN_LORDS, YogaContext

# ---------------------------------------------------------------------------
# Classical Dhana Yoga rule set adopted by this project
# ---------------------------------------------------------------------------
# Primary Dhana (wealth) houses: 2nd (accumulated wealth, family assets)
# and 11th (gains, income).
# Supporting prosperity houses: 1st (self / overall strength),
# 5th (purva punya, intelligence, investments), 9th (dharma, fortune / luck).
#
# Dhana Yoga is formed when the lord of a primary Dhana house (2 or 11)
# forms a Sambandha (conjunction, mutual aspect, or parivartana) with the lord
# of another prosperity-supporting house (1, 2, 5, 9, 11) — provided the two
# lords are distinct planets.
#
# Strength grading:
#   EXCEPTIONAL  – either planet is exalted
#   STRONG       – either planet is in its own sign
#   MODERATE     – otherwise
# ---------------------------------------------------------------------------

# Primary wealth houses
DHANA_HOUSES: Tuple[HouseNumber, ...] = (
    HouseNumber.SECOND,
    HouseNumber.ELEVENTH,
)

# All prosperity-related houses that can participate in Dhana Yoga
PROSPERITY_HOUSES: Tuple[HouseNumber, ...] = (
    HouseNumber.FIRST,
    HouseNumber.SECOND,
    HouseNumber.FIFTH,
    HouseNumber.NINTH,
    HouseNumber.ELEVENTH,
)


class DhanaYogaRule:
    """
    Dhana Yoga is formed when the lord of a primary Dhana house (2nd or 11th)
    forms a Sambandha (conjunction, mutual aspect, or parivartana) with the
    lord of another prosperity-supporting house (1st, 2nd, 5th, 9th, 11th),
    provided the two lords are distinct planets.
    """

    def evaluate(self, context: YogaContext) -> Tuple[YogaResult, ...]:
        results: list[YogaResult] = []
        evaluated_pairs: set[tuple[str, str]] = set()

        for dhana_house in DHANA_HOUSES:
            dhana_lord = context.house_lord(dhana_house)
            if dhana_lord is None:
                continue

            for prosperity_house in PROSPERITY_HOUSES:
                prosperity_lord = context.house_lord(prosperity_house)
                if prosperity_lord is None:
                    continue

                # Cannot pair a planet with itself
                if dhana_lord == prosperity_lord:
                    continue

                # Evaluate each unique pair only once (regardless of order)
                pair = tuple(sorted([dhana_lord.value, prosperity_lord.value]))
                if pair in evaluated_pairs:
                    continue
                evaluated_pairs.add(pair)

                if context.are_related(dhana_lord, prosperity_lord):
                    results.append(
                        self._create_yoga_result(
                            context,
                            dhana_lord,
                            prosperity_lord,
                            dhana_house,
                            prosperity_house,
                        )
                    )

        return tuple(results)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _create_yoga_result(
        self,
        context: YogaContext,
        dhana_lord: PlanetType,
        prosperity_lord: PlanetType,
        dhana_house: HouseNumber,
        prosperity_house: HouseNumber,
    ) -> YogaResult:
        p1 = context.planet(dhana_lord)
        p2 = context.planet(prosperity_lord)

        involved_planets = (dhana_lord, prosperity_lord)
        involved_houses = tuple(
            h
            for h in (
                p1.house_number if p1 else None,
                p2.house_number if p2 else None,
            )
            if h is not None
        )

        evidence = (
            f"{dhana_lord.value} is lord of Dhana house {dhana_house.value}.",
            f"{prosperity_lord.value} is lord of prosperity house {prosperity_house.value}.",
            f"{dhana_lord.value} and {prosperity_lord.value} are related (Sambandha).",
        )

        # Key is alphabetically sorted to ensure uniqueness regardless of argument order
        sorted_lords = sorted([dhana_lord.value.lower(), prosperity_lord.value.lower()])
        key = f"dhana_yoga_{'_'.join(sorted_lords)}"

        return YogaResult(
            yoga=Yoga(
                key=key,
                name=f"Dhana Yoga ({dhana_lord.value} and {prosperity_lord.value})",
                yoga_type=YogaType.DHANA_YOGA,
                description=(
                    f"Dhana Yoga formed by relationship between Dhana lord "
                    f"({dhana_lord.value}, house {dhana_house.value}) and "
                    f"prosperity lord ({prosperity_lord.value}, house {prosperity_house.value})."
                ),
            ),
            strength=self._strength(context, dhana_lord, prosperity_lord),
            involved_planets=involved_planets,
            involved_houses=involved_houses,
            evidence=evidence,
        )

    def _strength(
        self,
        context: YogaContext,
        dhana_lord: PlanetType,
        prosperity_lord: PlanetType,
    ) -> YogaStrength:
        if context.is_exalted(dhana_lord) or context.is_exalted(prosperity_lord):
            return YogaStrength.EXCEPTIONAL

        if self._is_own_sign(context, dhana_lord) or self._is_own_sign(
            context, prosperity_lord
        ):
            return YogaStrength.STRONG

        return YogaStrength.MODERATE

    def _is_own_sign(self, context: YogaContext, planet: PlanetType) -> bool:
        sign = context.sign_of_planet(planet)
        if sign is None:
            return False
        return SIGN_LORDS[sign] == planet
