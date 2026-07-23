from typing import Tuple
from app.domain.planet_type import PlanetType
from app.domain.yoga import Yoga, YogaResult, YogaStrength, YogaType
from app.domain.yoga_detection import (
    YogaContext,
    KENDRA_HOUSES,
    TRIKONA_HOUSES,
    SIGN_LORDS,
)


class RajYogaRule:
    """
    Raj Yoga (specifically Kendra-Trikona Raj Yoga) is formed when
    a Kendra lord (1, 4, 7, 10) and a Trikona lord (1, 5, 9) form
    a relationship (Sambandha) via conjunction, aspect, or parivartana.
    """

    def evaluate(self, context: YogaContext) -> Tuple[YogaResult, ...]:
        results: list[YogaResult] = []

        # Find all unique Kendra lords
        kendra_lords = {
            context.house_lord(h)
            for h in KENDRA_HOUSES
            if context.house_lord(h) is not None
        }

        # Find all unique Trikona lords
        trikona_lords = {
            context.house_lord(h)
            for h in TRIKONA_HOUSES
            if context.house_lord(h) is not None
        }

        # Check relationships between distinct Kendra and Trikona lords
        evaluated_pairs = set()

        for k_lord in kendra_lords:
            for t_lord in trikona_lords:
                if k_lord == t_lord:
                    continue

                # Ensure we only evaluate each pair once
                pair = tuple(sorted([k_lord.value, t_lord.value]))
                if pair in evaluated_pairs:
                    continue
                evaluated_pairs.add(pair)

                if context.are_related(k_lord, t_lord):
                    results.append(self._create_yoga_result(context, k_lord, t_lord))

        return tuple(results)

    def _create_yoga_result(
        self,
        context: YogaContext,
        k_lord: PlanetType,
        t_lord: PlanetType,
    ) -> YogaResult:
        # Determine the houses owned by the lords that qualify them as Kendra/Trikona lords
        k_houses_owned = [h for h in KENDRA_HOUSES if context.house_lord(h) == k_lord]
        t_houses_owned = [h for h in TRIKONA_HOUSES if context.house_lord(h) == t_lord]

        k_house_str = ", ".join(str(h.value) for h in k_houses_owned)
        t_house_str = ", ".join(str(h.value) for h in t_houses_owned)

        p1 = context.planet(k_lord)
        p2 = context.planet(t_lord)

        involved_planets = (k_lord, t_lord)
        involved_houses = tuple(
            h
            for h in (p1.house_number if p1 else None, p2.house_number if p2 else None)
            if h is not None
        )

        evidence = (
            f"{k_lord.value} is lord of Kendra house(s) {k_house_str}.",
            f"{t_lord.value} is lord of Trikona house(s) {t_house_str}.",
            f"{k_lord.value} and {t_lord.value} are related (Sambandha).",
        )

        return YogaResult(
            yoga=Yoga(
                key=f"raj_yoga_{k_lord.value.lower()}_{t_lord.value.lower()}",
                name=f"Raj Yoga ({k_lord.value} and {t_lord.value})",
                yoga_type=YogaType.RAJ_YOGA,
                description=f"Raj Yoga formed by relationship between Kendra lord ({k_lord.value}) and Trikona lord ({t_lord.value}).",
            ),
            strength=self._strength(context, k_lord, t_lord),
            involved_planets=involved_planets,
            involved_houses=involved_houses,
            evidence=evidence,
        )

    def _strength(
        self,
        context: YogaContext,
        k_lord: PlanetType,
        t_lord: PlanetType,
    ) -> YogaStrength:
        if context.is_exalted(k_lord) or context.is_exalted(t_lord):
            return YogaStrength.EXCEPTIONAL

        if self._is_own_sign(context, k_lord) or self._is_own_sign(context, t_lord):
            return YogaStrength.STRONG

        return YogaStrength.MODERATE

    def _is_own_sign(self, context: YogaContext, planet: PlanetType) -> bool:
        sign = context.sign_of_planet(planet)
        if sign is None:
            return False
        return SIGN_LORDS[sign] == planet
